# -*- coding: utf-8 -*-

"""Utilities for finding interesting and novel nodes around which to expand curation."""

import collections
from typing import Counter, Tuple

from pybel import BELGraph, Pipeline
from pybel.constants import ABUNDANCE
from pybel.dsl import BaseEntity, Gene
from pybel.struct import (
    collapse_all_variants, collapse_to_genes, enrich_protein_and_rna_origins, function_inclusion_filter_builder,
    remove_associations, remove_biological_processes, remove_filtered_nodes, remove_pathologies,
)
from pybel.struct.pipeline import in_place_transformation

__all__ = [
    'process_graph',
    'rank_genes',
    'process_rank_genes',
]


@in_place_transformation
def remove_abundances(graph: BELGraph) -> None:
    """Remove biological process nodes from the graph."""
    remove_filtered_nodes(graph, node_predicates=function_inclusion_filter_builder({ABUNDANCE}))


#: The pipeline to remove questionable content from the graph and make re-curation easier.
process_graph: Pipeline = Pipeline.from_functions([
    enrich_protein_and_rna_origins,
    collapse_to_genes,
    collapse_all_variants,
    remove_associations,
    remove_biological_processes,
    remove_pathologies,
    remove_abundances,
])


def rank_genes(graph: BELGraph) -> Counter[Tuple[str, str]]:
    r"""Rank the genes by their inverse sum of in- and out-degrees.

    .. math:: rank(n) = \frac{1}{1 + degree_{in}(n) + degree_{out}(n)}
    """
    return collections.Counter({
        (node.namespace, node.name): 1 / (1 + degree)
        for node, degree in graph.degree()
        if isinstance(node, Gene)
    })


def process_rank_genes(graph: BELGraph) -> Counter[BaseEntity]:
    """Process the graph then rank the genes."""
    return rank_genes(process_graph(graph))
