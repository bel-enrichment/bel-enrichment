# -*- coding: utf-8 -*-

"""The command line interface for BEL enrichment."""

import click

from pybel.cli import graph_pickle_argument
from .find_interesting_nodes import process_graph, rank_genes


@click.group()
def main():
    """BEL Enrichment."""


@main.command()
@graph_pickle_argument
@click.option('-n', '--number', type=int)
@click.option('-s', '--sep', default='\t')
def ranks(graph, number, sep):
    """Rank the genes in a graph."""
    graph = process_graph(graph)
    gene_map = rank_genes(graph)
    for (namespace, name), rank in gene_map.most_common(n=number):
        click.echo(f'{rank:.2f}{sep}{namespace}{sep}{name}')
