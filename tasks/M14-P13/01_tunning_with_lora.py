"""
Fine-tunning LLM with LoRA
"""

# imports

import gc
import json
import time
from threading import Thread, Event

import torch
import torch.cuda
from tabulate import tabulate

from colorize import colorize
from global_state import Trainer, monitor_state, TrainerConfig
from utils import get_dataset

# dataset

datasets = get_dataset()


def convert_duration_to_seconds(duration: str) -> int:
    """Convert 00:00:00 into 000000 seconds"""
    parts = duration.split(':')

    return (
            (int(parts[0]) * 3600) +
            (int(parts[1]) * 60) +
            int(parts[2])
    )


def release_resources(trainer: Trainer) -> None:
    trainer.trainer.accelerator.free_memory()

    del trainer
    gc.collect()

    if torch.cuda.is_available():
        torch.cuda.empty_cache()


rankers = [4, 16]
target_module_list: list[str | list[str]] = [
    ['q_proj', 'v_proj'],
    ['q_proj', 'k_proj', 'v_proj', 'o_proj'],
]
epochs_list = [5, 20]
batch_size_list: list[int] = [1, 10]

if __name__ == '__main__':

    iterations_count = len(rankers) * len(target_module_list) * len(epochs_list) * len(batch_size_list)
    i = 0

    for ranker in rankers:
        for target_modules in target_module_list:
            for epochs in epochs_list:
                for batch_size in batch_size_list:
                    """Iterate through combinations"""

                    i += 1

                    config = TrainerConfig(ranker, target_modules, epochs, batch_size)

                    trainer = Trainer(config, i - 1, datasets, f'Training {i}/{iterations_count}')
                    stop = Event()

                    monitor = Thread(
                        target=monitor_state,
                        args=(trainer, stop),
                        name='state-monitor',
                    )

                    monitor.start()

                    try:
                        (
                            trainer
                            .train()
                            .test()
                            .save()
                        )

                        time.sleep(.5)

                    finally:
                        stop.set()
                        monitor.join()
                        trainer.show_state()
                        release_resources(trainer)

headers_metrics = ['Label', 'Duration ▼', 'Loss ▼', 'Accuracy ▲', 'Entropy ▼']
headers_configs = ['Label', 'r/alph', 'Targets', 'Ep', 'Btch']
table_metrics = []
table_configs = []

best_metrics: dict[str, None | int | float] = {
    'duration': None,
    'loss': None,
    'accuracy': None,
    'entropy': None,
}

for result in Trainer.results:
    data = json.load(result.open())

    duration_seconds: int = convert_duration_to_seconds(data['duration'])

    if best_metrics['duration'] is None or best_metrics['duration'] > duration_seconds:
        best_metrics['duration'] = duration_seconds

    if best_metrics['loss'] is None or best_metrics['loss'] > data['results']['eval_loss']:
        best_metrics['loss'] = data['results']['eval_loss']

    if best_metrics['accuracy'] is None or best_metrics['accuracy'] < data['results']['eval_mean_token_accuracy']:
        best_metrics['accuracy'] = data['results']['eval_mean_token_accuracy']

    if best_metrics['entropy'] is None or best_metrics['entropy'] > data['results']['eval_entropy']:
        best_metrics['entropy'] = data['results']['eval_entropy']

    line_metrics = [
        data['label'],
        data['duration'],
        data['results']['eval_loss'],
        data['results']['eval_mean_token_accuracy'],
        data['results']['eval_entropy']
    ]

    line_configs = [
        data['label'],
        f'{data["trainer"]["config"]["ranker"]} / {data["trainer"]["config"]["alpha"]}',
        str(data['trainer']['config']['targets']),
        data['trainer']['config']['epochs'],
        data['trainer']['config']['batch_size']
    ]

    table_metrics.append(line_metrics)
    table_configs.append(line_configs)

for metric_row in table_metrics:
    if convert_duration_to_seconds(metric_row[1]) == best_metrics['duration']:
        metric_row[1] = colorize(metric_row[1], 'green')

    if metric_row[2] == best_metrics['loss']:
        metric_row[2] = colorize(metric_row[2], 'green')

    if metric_row[3] == best_metrics['accuracy']:
        metric_row[3] = colorize(metric_row[3], 'green')

    if metric_row[4] == best_metrics['entropy']:
        metric_row[4] = colorize(metric_row[4], 'green')

print()
print(tabulate(table_metrics, headers=headers_metrics, tablefmt='rounded_grid'))
print()
print(tabulate(table_configs, headers=headers_configs, tablefmt='rounded_grid'))
