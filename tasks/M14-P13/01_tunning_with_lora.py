"""
Fine-tunning LLM with LoRA
"""
import torch.cuda

# imports


from global_state import Trainer, monitor_state, TrainerConfig
from threading import Thread, Event
from utils import get_dataset
import sys
import time
import gc
import torch
from pathlib import Path
import json
from tabulate import tabulate


# pre-config
# dataset

datasets = get_dataset()


# LoRA configs
# train
# save model


def release_resources(trainer: Trainer) -> None:
    trainer.trainer.accelerator.free_memory()

    del trainer
    gc.collect()

    if torch.cuda.is_available():
        torch.cuda.empty_cache()


rankers = [4, 8, 16]
target_module_list: list[str|list[str]] = [
    ['q_proj', 'v_proj'],
    ['q_proj', 'k_proj', 'q_proj', 'o_proj'],
    'all-linear',
]
epochs_list = [3, 5, 10]
batch_size_list: list[int] = [1, 10, 20]


if __name__ == '__main__':

    iterations_count = len(rankers) * len(target_module_list) * len(epochs_list) * len(batch_size_list)
    i = 1

    for ranker in rankers:
        for target_modules in target_module_list:
            for epochs in epochs_list:
                for batch_size in batch_size_list:
                    """Iterate through combinations"""

                    config = TrainerConfig(ranker, target_modules, epochs, batch_size)

                    trainer = Trainer(config, datasets, f'Training {i}/{iterations_count}')
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

                        if i > 2:
                            break
                    finally:
                        stop.set()
                        monitor.join()
                        trainer.show_state()
                        release_resources(trainer)

                        i += 1

files = [
    Path('./results/performance/20261104_2227/results-r4_alpha8_ep3.json'),
    Path('./results/performance/20261104_2232/results-r4_alpha8_ep3.json'),
]

headers_metrics = ['Label', 'Loss ▼', 'Accuracy ▲', 'Entropy ▼']
headers_configs = ['Label', 'Duration', 'r/alph', 'Targets', 'Ep', 'Btch']
table_metrics = []
table_configs = []


#for result in files:
for result in Trainer.results:
    data = json.load(result.open())

    print(data)

    line_metrics = [data['label'], data['results']['eval_loss'], data['results']['eval_mean_token_accuracy'], data['results']['eval_entropy']]
    line_configs = [
        data['label'], data['duration'],
        f'{data["trainer"]["config"]["ranker"]} / {data["trainer"]["config"]["alpha"]}',
        str(data['trainer']['config']['targets']),
        data['trainer']['config']['epochs'],
        data['trainer']['config']['batch_size']
    ]

    table_metrics.append(line_metrics)
    table_configs.append(line_configs)


print()
print(tabulate(table_metrics, headers=headers_metrics, tablefmt='rounded_grid'))
print()
print(tabulate(table_configs, headers=headers_configs, tablefmt='rounded_grid'))
