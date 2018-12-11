# -*- coding: utf-8 -*-

"""Utilities for finding interesting and novel nodes around which to expand curation."""

import logging
import os
import sys
from collections import Counter
from operator import itemgetter
from typing import Callable, List, Optional, Tuple

import click

from pybel import BELGraph, Manager, Pipeline
from pybel.constants import ABUNDANCE, FUNCTION, GENE, NAMESPACE
from pybel.dsl import BaseEntity, Gene
from pybel.struct import (
    collapse_all_variants, collapse_to_genes, enrich_protein_and_rna_origins, function_inclusion_filter_builder,
    namespace_inclusion_builder, remove_associations, remove_biological_processes, remove_filtered_nodes,
    remove_pathologies,
)
from pybel.struct.pipeline import in_place_transformation

logging.getLogger('indra.pybel_assembler').setLevel(logging.ERROR)

log = logging.getLogger(__name__)

EdgePredicate = Callable[[BELGraph, BaseEntity, BaseEntity, int], bool]


@in_place_transformation
def remove_abundances(graph: BELGraph):
    """Remove biological process nodes from the graph."""
    remove_filtered_nodes(graph, node_predicates=function_inclusion_filter_builder({ABUNDANCE}))


#: The pipeline to remove questionable content from the graph and make re-curation easier.
process_graph = Pipeline.from_functions([
    enrich_protein_and_rna_origins,
    collapse_to_genes,
    collapse_all_variants,
    remove_associations,
    remove_biological_processes,
    remove_pathologies,
    remove_abundances,
])

node_is_human = namespace_inclusion_builder({'EGID', 'entrez', 'ncbigene', 'hgnc', 'HGNC'})


def rank_genes(graph: BELGraph) -> Counter:
    """Rank the genes by their inverse sum of in- and out-degrees."""
    return Counter(dict(
        ((node.namespace, node.name), 1 / (1 + degree))
        for node, degree in graph.degree()
        if isinstance(node, Gene)
    ))


class FindInterestingNodes:
    """A class that contains the functions used to find novel genes in a BEL graph."""

    def __init__(self,
                 graph: BELGraph,
                 manager: Optional[Manager] = None,
                 path: Optional[str] = None
                 ) -> None:
        """Initialize with a BEL graph that will be used for many operations.

        :param graph: The graph on which the algorithm will be run
        :param path: The folder in which files will be stored
        """
        self.graph = graph
        self.manager = manager if manager is None else Manager

        log.info('preprocessing %s', self.graph)
        #: A pre-processed version of the graph
        self.preprocessed_graph = process_graph.run(self.graph)

        self.ranks = rank_genes(self.preprocessed_graph)

    @staticmethod
    def keep_node(graph: BELGraph, node: BaseEntity) -> bool:
        """Pass for nodes that are HGNC genes."""
        data = graph.nodes[node]

        if data[FUNCTION] != GENE:
            return False

        namespace = data.get(NAMESPACE)

        if namespace is None:
            return False

        return namespace.lower() == 'hgnc'

    def get_kept_node_degrees(self) -> List[Tuple[BaseEntity, int]]:
        """Get a list of pairs of nodes and their integer degrees."""
        return [
            (self.preprocessed_graph.nodes[node], degree)
            for node, degree in self.preprocessed_graph.degree()
            if self.keep_node(self.preprocessed_graph, node)
        ]

    def get_missing_genes(self, maximum_degree: int = 0) -> List[BaseEntity]:
        """Get a list of genes node tuples whose degree is less than the given number."""
        degrees = self.get_kept_node_degrees()

        return [
            node
            for node, degree in degrees
            if degree <= maximum_degree
        ]

    def get_novel_genes(self, nodes: List[BaseEntity]) -> List[BaseEntity]:
        """Get a list of novel genes, which do no appear in the PyBEL graph cache and are not miRNAs."""
        novel_genes = []

        for node in nodes:
            node_model = self.manager.get_node_by_dsl(node)
            if node_model is not None:
                print(f'skipping: {node_model}')
                continue

            if 'MIR' in node[2]:
                print(f'skipping miRNA: {node}')
                continue

            novel_genes.append(node)

        print(f'there are {len(novel_genes)} novel genes')

        return novel_genes

    def _get_gene_directory(self, gene_symbol: str):
        """Ensure a directory exists for the given gene and return it."""
        gene_directory = os.path.join(self.path, gene_symbol)
        os.makedirs(gene_directory, exist_ok=True)
        return gene_directory

    def run(self, limit: Optional[int] = None) -> Counter:
        """Run the whole pipeline."""
        missing_genes = self.get_missing_genes(maximum_degree=2)
        novel_genes = self.get_novel_genes(missing_genes)
        r = self.run_novel_genes(novel_genes, limit=limit)
        return Counter(r)


@click.command()
@click.option('-o', '--output', type=click.File('w'), default=sys.stdout)
def main(output):
    """Run the interesting node finding algorithm."""
    logging.getLogger('pybel.parser').setLevel(logging.ERROR)
    manager = Manager()
    graph = get_graph(manager=manager, use_cached=True)

    curation_path = os.path.join(CURATION_DIRECTORY, 'enrichment-2')
    os.makedirs(curation_path, exist_ok=True)

    fin = FindInterestingNodes(graph=graph, manager=manager, path=curation_path)

    nodes = []
    for node, degree in sorted(fin.get_kept_node_degrees(), key=itemgetter(1))[:100]:
        # print(node, degree)
        nodes.append(node)

    r = fin.run_novel_genes(nodes, limit=20)
    click.echo(r, file=output)


if __name__ == '__main__':
    main()
