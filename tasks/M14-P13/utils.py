"""
Methods to help development
"""

# imports

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from datasets import Dataset
from transformers import PreTrainedModel, BatchEncoding
from peft import PeftModel

from global_state import Datasets
from torch import Tensor

folders = {
    'current': Path(__file__).parent,
    'assets': Path(__file__).parent / 'assets',
    'datasets': Path(__file__).parent / 'assets' / 'datasets',
}


def print_replace(lines: str, mandatory_count_lines: int | None = None) -> None:
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
    return date.strftime("%Y%m%d_%H%M%S")


def load_model(adapter_folder: None | str=None) -> PreTrainedModel | PeftModel:
    """Load model with or without LoRA adapter"""

    from transformers import AutoModelForCausalLM

    OPEN_MODEL_ID = 'Qwen/Qwen3-0.6B'

    model = AutoModelForCausalLM.from_pretrained(OPEN_MODEL_ID, device_map='auto')

    if not adapter_folder:
        model.eval()
        return model

    trained_model = PeftModel.from_pretrained(model, adapter_folder)
    trained_model.eval()

    return trained_model


def output_to_str(tokenizer, inputs: BatchEncoding, outputs: Tensor) -> str:
    prompt_length = inputs['input_ids'].shape[1]
    new_tokens = outputs[0][prompt_length:]

    return tokenizer