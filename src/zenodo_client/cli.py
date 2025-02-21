"""Command line interface for :mod:`zenodo_client`.

Why does this file exist, and why not put this in ``__main__``? You might be tempted to
import things from ``__main__`` later, but that will cause problems--the code will get
executed twice:

- When you run ``python3 -m zenodo_client`` python will execute``__main__.py`` as a
  script. That means there won't be any ``zenodo_client.__main__`` in ``sys.modules``.
- When you import __main__ it will get executed again (as a module) because there's no
  ``zenodo_client.__main__`` in ``sys.modules``.

.. seealso::

    https://click.palletsprojects.com/en/7.x/setuptools/#setuptools-integration
"""

import logging

import click
from more_click import verbose_option

from .api import download_zenodo, download_zenodo_latest, update_zenodo

__all__ = ["main"]

logger = logging.getLogger(__name__)


@click.group()
def main() -> None:
    """CLI for Zenodo Client."""


@main.command()
@click.argument("deposition")
@click.argument("path")
@click.option("--force", is_flag=True)
@click.option("--latest", is_flag=True)
def download(deposition: str, path: str, force: bool, latest: bool) -> None:
    """Ensure a record is downloaded."""
    if latest:
        download_zenodo_latest(deposition, path, force=force)
    else:
        download_zenodo(deposition, path, force=force)


@main.command()
@click.argument("deposition")
@click.argument("paths", nargs=-1)
@verbose_option  # type:ignore[misc]
@click.version_option()
def update(deposition: str, paths: list[str]) -> None:
    """Update the record and given files."""
    update_zenodo(deposition, paths)


if __name__ == "__main__":
    main()
