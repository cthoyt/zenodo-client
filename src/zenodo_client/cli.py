"""Command line interface for :mod:`zenodo_client`."""

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
