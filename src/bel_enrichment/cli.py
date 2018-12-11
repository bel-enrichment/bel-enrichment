# -*- coding: utf-8 -*-

"""The command line interface for BEL enrichment."""

import os

import click

from pybel.cli import graph_pickle_argument
from .ranking import process_rank_genes
from .workflow import export_separate


@click.group()
def main():
    """BEL Enrichment."""


@main.command()
@graph_pickle_argument
@click.option('-n', '--number', type=int)
@click.option('-s', '--sep', default='\t')
def ranks(graph, number, sep):
    """Rank the genes in a graph."""
    gene_map = process_rank_genes(graph)
    for (namespace, name), rank in gene_map.most_common(n=number):
        click.echo(f'{rank:.2f}{sep}{namespace}{sep}{name}')


@main.command()
@graph_pickle_argument
@click.option('-d', '--directory', type=click.Path(file_okay=False, dir_okay=True), default=os.getcwd())
@click.option('--info-cutoff', type=float, default=1.0, help='Minimum inverse node degree. Lower allows more genes.')
@click.option('--belief-cutoff', type=float, default=0.30, help='Minimum belief score. Lower gets more statements.')
def make_sheet(graph, directory, info_cutoff, belief_cutoff):
    """Rank the genes in a graph."""
    export_separate(
        graph=graph,
        directory=directory,
        minimum_information_density=info_cutoff,
        minimum_belief=belief_cutoff,
    )


if __name__ == '__main__':
    main()
