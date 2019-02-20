# -*- coding: utf-8 -*-

"""Summary utilities."""

import typing
from collections import Counter

from pybel import BELGraph
from pybel.constants import ANNOTATIONS

__all__ = [
    'count_indra_apis',
]


def count_indra_apis(graph: BELGraph) -> typing.Counter[str]:
    """Count the APIs reported by INDRA."""
    return Counter(
        api
        for _, _, d in graph.edges(data=True)
        if ANNOTATIONS in d and 'INDRA_API' in d[ANNOTATIONS]
        for api in d[ANNOTATIONS]['INDRA_API']
        if api and isinstance(api, str) and api != 'nan'
    )
