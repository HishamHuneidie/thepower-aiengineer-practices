"""
Methods to help development
"""


# imports


import json
from pathlib import Path
from global_state import Datasets
from datasets import Dataset
from typing import Any
from datetime import datetime


folders = {
    'current': Path(__file__).parent,
    'assets': Path(__file__).parent / 'assets',
    'datasets': Path(__file__).parent / 'assets' / 'datasets',
}


def print_replace(lines: str, mandatory_count_lines: int|None = None) -> None:
    count_lines = mandatory_count_lines if mandatory_count_lines else len(lines.splitlines())
    backlines = f'\033[{count_lines}F\033[J'

    print(f'{backlines}{lines}', end='\n', flush=True)


def get_dataset() -> Datasets:
    path_file = folders['datasets'] / 'dataset.json'
    with path_file.open(encoding='utf-8') as file:
        dataset = json.load(file)

    if not dataset:
        raise RuntimeError('No dataset found')

    return Datasets(
        train=Dataset.from_list(dataset['train']),
        validation=Dataset.from_list(dataset['validation']),
        test=Dataset.from_list(dataset['test']),
    )


def process_log_line(log: Any) -> str:
    import shutil
    from colorize import colorize

    long = int(shutil.get_terminal_size().columns * 70 / 100)

    log_str = str(log).strip().replace('\n', '')

    return '│ ' + colorize(log_str[0:long] + '...', 'gray')


def date_to_str(date: datetime) -> str:
    return date.strftime("%Y%m%d_%H%M")