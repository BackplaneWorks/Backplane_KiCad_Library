#!/usr/bin/env python3

import fnmatch
import multiprocessing
import pathlib

import click
import requests
import tqdm
from bs4 import BeautifulSoup


def fetch(partnum):
    response = requests.get(f"https://www.st.com/resource/en/datasheet/{partnum}.pdf")
    return partnum, response


@click.command()
@click.option(
    "--part-number",
    "-p",
    "part_number_pattern",
    default="*",
    help="Filter part numbers by glob",
)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(file_okay=False, dir_okay=True, path_type=pathlib.Path),
    default="stm32_datasheets",
    help="Output directory",
)
@click.argument(
    "cubemx_mcu_db_dir",
    type=click.Path(file_okay=False, dir_okay=True, path_type=pathlib.Path),
)
def download_datasheets(cubemx_mcu_db_dir, part_number_pattern, output_dir):

    soup = BeautifulSoup(
        (cubemx_mcu_db_dir / "families.xml").read_text(), features="xml"
    )
    part_numbers = [tag["RPN"].lower() for tag in soup.find_all("Mcu", recursive=True)]
    part_numbers = {
        pn
        for pn in part_numbers
        if fnmatch.fnmatch(pn.lower(), part_number_pattern.lower())
    }
    already_downloaded = {
        pn for pn in part_numbers if (output_dir / f"{pn}.pdf").is_file()
    }
    print(
        f"Found {len(part_numbers)} parts, of which {len(already_downloaded)} "
        "were already downloaded."
    )
    part_numbers -= already_downloaded
    print(f"Downloading {len(part_numbers)} remaining datasheets...")
    progress = tqdm.tqdm(total=len(part_numbers))
    output_dir.mkdir(exist_ok=True, parents=True)

    with multiprocessing.Pool(50) as pool:

        def save_pdf(tup):
            partnum, response = tup
            (output_dir / f"{partnum}.pdf").write_bytes(response.content)
            progress.write(f"Downloaded {partnum}.pdf")
            progress.update()
            progress.refresh()

        def error(exc):
            progress.write(f"Error downloading {exc.url}")

        for pn in part_numbers:
            pool.apply_async(
                fetch, (pn,), callback=save_pdf, error_callback=error
            ).wait()
        pool.close()
        pool.join()
    progress.close()


if __name__ == "__main__":
    download_datasheets()
