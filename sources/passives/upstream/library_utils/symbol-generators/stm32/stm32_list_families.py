#!/usr/bin/env python3

import pathlib

import click
from bs4 import BeautifulSoup


@click.command()
@click.argument(
    "cubemx_mcu_db_dir",
    type=click.Path(file_okay=False, dir_okay=True, path_type=pathlib.Path),
)
def cli(cubemx_mcu_db_dir):

    soup = BeautifulSoup(
        (cubemx_mcu_db_dir / "families.xml").read_text(), features="xml"
    )
    for tag in soup.find_all("Family", recursive=True):
        print(tag["Name"])


if __name__ == "__main__":
    cli()
