# -*- coding: utf-8 -*-

"""Command line interface for :mod:`zenodo_client`.

Why does this file exist, and why not put this in ``__main__``? You might be tempted to import things from ``__main__``
later, but that will cause problems--the code will get executed twice:

- When you run ``python3 -m zenodo_client`` python will execute``__main__.py`` as a script.
  That means there won't be any ``zenodo_client.__main__`` in ``sys.modules``.
- When you import __main__ it will get executed again (as a module) because
  there's no ``zenodo_client.__main__`` in ``sys.modules``.

.. seealso:: https://click.palletsprojects.com/en/7.x/setuptools/#setuptools-integration
"""

import logging

import click
from more_click import verbose_option

from .api import update_zenodo

__all__ = ['main']

logger = logging.getLogger(__name__)


@click.group()
@click.argument('deposition')
@click.argument('paths', nargs=-1)
@verbose_option
@click.version_option()
def main(deposition, paths):
    """CLI for Zenodo Client."""
    update_zenodo(deposition, paths)


if __name__ == '__main__':
    main()
