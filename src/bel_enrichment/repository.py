# -*- coding: utf-8 -*-

"""A wrapper for functions on a BEL sheets repository."""

import logging
import os
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Optional, Union

import click
import pandas as pd
from tqdm import tqdm

from bel_repository import BELMetadata, BELRepository
from pybel import BELGraph, from_pickle, to_json_path, to_pickle
from pybel.cli import echo_warnings_via_pager
from pybel.constants import ANNOTATIONS, CITATION
from pybel.parser import BELParser
from pybel.struct import get_subgraphs_by_annotation
from .sheets import _check_curation_template_columns, generate_curation_summary, get_sheets_paths, process_row
from .summary import count_indra_apis

__all__ = [
    'BELSheetsRepository',
]

logger = logging.getLogger(__name__)


@dataclass
class BELSheetsRepository:
    """A repository of BEL curation sheets."""

    directory: str
    output_directory: Optional[str] = None
    metadata: BELMetadata = None
    prior: Union[None, BELGraph, BELRepository] = None

    pickle_name: str = 'sheets.bel.pickle'
    json_name: str = 'sheets.bel.json'

    _cache_pickle_path: str = field(init=False)

    def __post_init__(self) -> None:  # noqa: D105
        if self.output_directory is None:
            self.output_directory = self.directory

        os.makedirs(self.output_directory, exist_ok=True)

        self._cache_pickle_path = os.path.join(self.output_directory, self.pickle_name)

    def get_prior(self) -> BELGraph:
        """Get the prior graph or load it."""
        if isinstance(self.prior, BELGraph):
            return self.prior
        elif isinstance(self.prior, BELRepository):
            return self.prior.get_graph()
        else:
            raise TypeError(f'wrong type: {self.prior}')

    def iterate_sheets_paths(self) -> Iterable[str]:
        """Iterate over the paths to all sheets."""
        return get_sheets_paths(self.directory)

    def get_graph(self,
                  use_cached: bool = True,
                  use_tqdm: bool = False,
                  tqdm_kwargs: Optional[Mapping[str, Any]] = None,
                  ) -> BELGraph:
        """Get the BEL graph from all sheets in this repository.

        .. warning:: This BEL graph isn't pre-filled with namespace and annotation URLs.
        """
        if use_cached and os.path.exists(self._cache_pickle_path):
            return from_pickle(self._cache_pickle_path)

        graph = BELGraph()
        if self.metadata is not None:
            self.metadata.update(graph)

        logger.info('streamlining parser')
        bel_parser = BELParser(graph)

        paths = self.iterate_sheets_paths()

        if use_tqdm:
            _tqdm_kwargs = dict(desc=f'Sheets in {self.directory}')
            if tqdm_kwargs:
                _tqdm_kwargs.update(tqdm_kwargs)
            paths = tqdm(list(paths), **_tqdm_kwargs)

        for path in paths:
            df = pd.read_excel(path)

            # Check columns in DataFrame exist
            if not _check_curation_template_columns(df, path):
                continue

            graph.path = path

            for line_number, row in df.iterrows():
                process_row(bel_parser=bel_parser, row=row, line_number=line_number)

        if self.prior is not None:  # assign edges to sub-graphs
            prior = self.get_prior()
            assign_subgraphs(graph=graph, prior=prior)

        to_pickle(graph, self._cache_pickle_path)
        to_json_path(graph, os.path.join(self.output_directory, self.json_name), indent=2)
        return graph

    def generate_curation_summary(self):
        """Generate a curation summary."""
        return generate_curation_summary(
            input_directory=self.directory,
            output_directory=self.output_directory,
        )

    def build_cli(self) -> click.Group:  # noqa: D202
        """Build a command line interface."""

        @click.group(help=f'Tools for the BEL repository at {self.directory}')
        @click.pass_context
        def main(ctx):
            """Group the commands."""
            ctx.obj = self

        self.append_click_group(main)
        return main

    @staticmethod
    def append_click_group(main: click.Group) -> None:  # noqa: D202, C901
        """Append a :py:class:`click.Group`."""

        @main.command()
        @click.option('-w', '--show-warnings', is_flag=True)
        @click.option('-r', '--reload', is_flag=True)
        @click.pass_obj
        def compile(repo: BELSheetsRepository, show_warnings: bool, reload: bool):
            """Generate all results and summaries."""
            graph = repo.get_graph(use_cached=(not reload), use_tqdm=True)
            graph.summarize()

            if graph.warnings:
                number_errored_documents = len({path for path, _, _ in graph.warnings})
                click.secho(f'Warnings: {number_errored_documents} documents')
                if show_warnings:
                    echo_warnings_via_pager(graph.warnings)
                    sys.exit(-1)

            # summarize API
            indra_api_histogram = count_indra_apis(graph)
            if indra_api_histogram:
                api_size = max(len(api) for api in indra_api_histogram)
                click.secho('Readers Used', fg='cyan', bold=True)
                for api, count in indra_api_histogram.most_common():
                    click.echo(f'  {api:{api_size}}: {count}')
                indra_api_df = pd.DataFrame.from_dict(indra_api_histogram, orient='index')
                indra_api_df.to_csv(os.path.join(repo.output_directory, 'api_summary.tsv'), sep='\t')

            if repo.prior is not None:
                prior = repo.get_prior()

                combine_graph = prior + graph
                click.secho('Enriched Graph', fg='cyan', bold=True)
                combine_graph.summarize()

                subgraphs: Mapping[str, BELGraph] = get_subgraphs_by_annotation(combine_graph, 'Subgraph')
                summary_df = pd.DataFrame.from_dict({
                    name: subgraph.summary_dict()
                    for name, subgraph in subgraphs.items()
                }, orient='index')
                summary_df.to_csv(os.path.join(repo.output_directory, 'subgraph_summary.tsv'), sep='\t')

            repo.generate_curation_summary()

        @main.command()
        @click.option('-p', '--path', type=click.Path())
        @click.pass_obj
        def html(repo: BELSheetsRepository, path: str):
            """Generate an HTML summary of the content."""
            graph = repo.get_graph()
            import pybel_tools.assembler.html
            with open(path or os.path.join(repo.output_directory, 'docs', 'index.html'), 'w') as file:
                print(pybel_tools.assembler.html.to_html(graph), file=file)


def assign_subgraphs(graph: BELGraph, prior: BELGraph, annotation: str = 'Subgraph') -> None:
    """Assign the sub-graphs to edges in the graph based on edges in the prior."""
    node_to_subgraph = defaultdict(set)
    for u, v, d in prior.edges(data=True):
        subgraphs = set(d.get(ANNOTATIONS, {}).get(annotation, ()))
        node_to_subgraph[u].update(subgraphs)
        node_to_subgraph[v].update(subgraphs)

    # Assign sub-graphs based on the sub-graphs in which the source and target participate in the prior
    for u, v, k, d in graph.edges(keys=True, data=True):
        if CITATION not in d:  # skip unqualified edges
            continue
        d.setdefault(ANNOTATIONS, {})
        d[ANNOTATIONS][annotation] = {
            subgraph: True
            for subgraph in node_to_subgraph[u] | node_to_subgraph[v]
        }
