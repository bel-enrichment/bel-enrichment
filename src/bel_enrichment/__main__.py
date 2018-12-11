# -*- coding: utf-8 -*-

"""The entry point module, in case you use ``python -m bel_enrichment``.

Why does this file exist, and why ``__main__``? For more information, read:

- https://www.python.org/dev/peps/pep-0338/
- https://docs.python.org/3/using/cmdline.html#cmdoption-m
"""

from .cli import main

if __name__ == '__main__':
    main()
