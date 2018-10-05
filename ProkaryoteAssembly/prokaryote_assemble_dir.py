#!/usr/bin/env python3

import os
import click
import logging

from pathlib import Path
from ProkaryoteAssembly.prokaryote_assemble import assembly_pipeline, clean_up
from ProkaryoteAssembly.accessories import print_version, convert_to_path

script = os.path.basename(__file__)
logger = logging.getLogger()
logging.basicConfig(
    format=f'\033[92m \033[1m {script}:\033[0m %(message)s ',
    level=logging.DEBUG)


@click.command()
@click.option('-i', '--input_dir',
              type=click.Path(exists=False),
              required=True,
              help='Directory containing all *.fastq.gz files to assemble.',
              callback=convert_to_path)
@click.option('-o', '--out_dir',
              type=click.Path(exists=False),
              required=True,
              help='Root directory to store all output files.',
              callback=convert_to_path)
@click.option('-f', '--fwd_id',
              type=click.STRING,
              required=False,
              default="_R1",
              help='Pattern to detect forward reads. Defaults to "_R1".')
@click.option('-r', '--rev_id',
              type=click.STRING,
              required=False,
              default="_R2",
              help='Pattern to detect reverse reads. Defaults to "_R2".')
@click.option('--version',
              help='Specify this flag to print the version and exit.',
              is_flag=True,
              is_eager=True,
              callback=print_version,
              expose_value=False)
def assemble_dir(input_dir, out_dir, fwd_id, rev_id):
    os.makedirs(out_dir, exist_ok=True)
    logging.info(f"Created output directory {out_dir}")

    logging.info(f"Finding FASTQ files in {input_dir}")
    fastq_file_list = retrieve_fastqgz(input_dir)

    logging.info(f"Finding Sample IDs")
    sample_ids = retrieve_sampleids(fastq_file_list)

    logging.info(f"Found {len(sample_ids)} unique sample IDs")

    for sample_id in sample_ids:
        r1, r2 = get_readpair(sample_id=sample_id, fastq_file_list=fastq_file_list,
                              forward_id=fwd_id, reverse_id=rev_id)
        sample_out_dir = out_dir / sample_id
        os.makedirs(sample_out_dir, exist_ok=True)
        assembly_pipeline(fwd_reads=r1, rev_reads=r2, out_dir=sample_out_dir, sample_id=sample_id)
        clean_up(input_dir=sample_out_dir)
    logging.info(f"Pipeline complete! Results available in {out_dir}")


def retrieve_fastqgz(directory: Path) -> [Path]:
    """
    :param directory: Path to folder containing output from MiSeq run
    :return: LIST of all .fastq.gz files in directory
    """
    fastq_file_list = list(directory.glob("*.f*q*"))
    return fastq_file_list


def retrieve_sampleids(fastq_file_list: [Path]) -> list:
    """
    :param fastq_file_list: List of fastq.gz filepaths generated by retrieve_fastqgz()
    :return: List of Sample IDs
    """
    # Iterate through all of the fastq files and grab the sampleID, append to list
    sample_id_list = list()
    for f in fastq_file_list:
        sample_id = f.name.split('_')[0]
        sample_id_list.append(sample_id)

    # Get unique sample IDs
    sample_id_list = list(set(sample_id_list))
    return sample_id_list


def get_readpair(sample_id: str, fastq_file_list: [Path], forward_id: str,
                 reverse_id: str) -> (list, None):
    """
    :param sample_id: String of sample ID
    :param fastq_file_list: List of fastq.gz file paths generated by retrieve_fastqgz()
    :param forward_id: ID indicating forward read in filename (e.g. _R1)
    :param reverse_id: ID indicating reverse read in filename (e.g. _R2)
    :return: the absolute filepaths of R1 and R2 for a given sample ID
    """

    r1, r2 = None, None
    for f in fastq_file_list:
        if sample_id in f.name:
            if forward_id in f.name:
                r1 = f
            elif reverse_id in f.name:
                r2 = f
    if r1 is not None and r2 is not None:
        return [r1, r2]
    else:
        logger.info('Could not pair {}'.format(sample_id))
        return None


if __name__ == "__main__":
    assemble_dir()
