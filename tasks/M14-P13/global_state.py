"""
Has the orchestrator class with the patter design builder
"""

# imports


import json
import time
from datetime import datetime, timezone
from itertools import cycle
from pathlib import Path
from threading import Event

from datasets import disable_progress_bar
from peft import LoraConfig
from transformers import PrinterCallback, TrainerCallback
from transformers.utils import logging as hf_logging
from trl import SFTConfig, SFTTrainer
from typing_extensions import Self

from colorize import colorize

hf_logging.disable_progress_bar()
disable_progress_bar()

# pre-configs


LORA_FOLDER = './results/lora'
LORA_FOLDER_FINAL = './results/lora/adapters'
PERFORMANCE_FOLDER = './results/performance'
OPEN_MODEL_ID = 'Qwen/Qwen3-0.6B'
TRAINER_LOGS: list[str] = []


# global state class


class CaptureLogs(TrainerCallback):
    def on_log(self, args, state, control, logs=None, **kwargs):
        if logs:
            from utils import process_log_line

            Trainer.trainer_logs.append(process_log_line(json.dumps(logs, ensure_ascii=False)))

            Trainer.trainer_progress = (
                state.global_step / state.max_steps
                if state.max_steps > 0
                else 0
            )


class Datasets:
    def __init__(self, train: list, validation: list, test: list):
        self.train = train
        self.validation = validation
        self.test = test


class TrainerConfig:
    def __init__(self, ranker: int, target_modules: str | list[str], epochs: int, batch_size: int):
        self.ranker = ranker
        self.alpha = ranker * 2
        self.target_modules = target_modules
        self.epochs = epochs
        self.batch_size = batch_size


class Trainer:
    loader_frame = cycle("⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏")
    trainer_logs: list[str]
    trainer_progress: int
    results: list[Path] = []
    adapters: list[tuple[str, str]] = []
    global_started_at: None | datetime = None

    def __init__(self, lora_config: TrainerConfig, index: int, datasets: Datasets, label: str):
        self.lora_config = lora_config
        self.index = index
        self.datasets = datasets
        self.global_state = {
            # 'dataset': (False, 'Prepare datasets', 'Datasets are ready'),
            'train': (False, 'Train', 'Train is done'),
            'test': (False, 'Test', 'Test is done'),
            'results': (False, 'Generate stats', 'Stats generated'),
            'save': (False, 'Save adapter', 'Adapter was saved successfully'),
        }
        self.label = label
        Trainer.trainer_logs = []
        Trainer.trainer_progress = 0
        self.set_trainer()
        self.started_at = datetime.now(timezone.utc)
        Trainer.global_started_at = Trainer.global_started_at or self.started_at
        self.old_lines_count = None

    def generate_global_state_str(self):
        from utils import process_log_line
        loader = colorize(next(self.loader_frame), 'purple')

        total = len(self.global_state)
        completed = sum(done for done, _, _ in self.global_state.values())
        width = 20
        filled = round(width * completed / total)
        bar = ('█' * filled) + ('░' * (width - filled))
        progress = f'{bar} {completed / total:.0%}'

        lines = [
            f'✔️ {loaded_str}' if done else f'{loader}  {loading_str}'
            for (done, loading_str, loaded_str) in self.global_state.values()
        ]

        training_lines = [''] + Trainer.trainer_logs[-5:] if Trainer.trainer_logs else ['']
        training_progress_lines = process_log_line(f'{Trainer.trainer_progress:.0%}')

        return '\n'.join([
            self.label,
            '',
            progress,
            '',
            *lines,
            *training_lines,
            training_progress_lines,
        ])

    def update_state(self, step: str) -> Self:
        time.sleep(3)
        self.global_state[step] = (True, *self.global_state[step][1:])

        return self

    def show_state(self) -> None:
        from utils import print_replace

        lines = self.generate_global_state_str()

        print_replace(lines, self.old_lines_count)

        self.old_lines_count = len(lines)

    def set_trainer(self) -> None:
        lora = LoraConfig(
            r=self.lora_config.ranker,
            lora_alpha=self.lora_config.alpha,
            target_modules=self.lora_config.target_modules
        )

        config = SFTConfig(
            output_dir=LORA_FOLDER,
            num_train_epochs=self.lora_config.epochs,
            per_device_train_batch_size=self.lora_config.batch_size,
            per_device_eval_batch_size=self.lora_config.batch_size,
            eval_strategy='epoch',
            disable_tqdm=True,
            model_init_kwargs={"device_map": None},
        )

        self.trainer = SFTTrainer(
            model=OPEN_MODEL_ID,
            train_dataset=self.datasets.train,
            eval_dataset=self.datasets.validation,
            peft_config=lora,
            args=config,
        )

        self.trainer.remove_callback(PrinterCallback)
        self.trainer.add_callback(CaptureLogs())

    def train(self) -> Self:
        self.trainer.train()
        self.update_state('train')

        return self

    def test(self) -> Self:
        results = self.trainer.evaluate(eval_dataset=self.datasets.test)
        self.update_state('test')

        self.save_results(results)

        return self

    def save_results(self, results: dict) -> None:
        duration = datetime.now(timezone.utc) - self.started_at

        total_seconds = int(duration.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        info = {
            'label': self.label,
            'duration': duration_str,
            'trainer': {
                'config': {
                    'ranker': self.lora_config.ranker,
                    'alpha': self.lora_config.alpha,
                    'epochs': self.lora_config.epochs,
                    'targets': self.lora_config.target_modules,
                    'batch_size': self.lora_config.batch_size,
                },
            },
            'results': results,
        }

        info_str = json.dumps(info, indent=4, ensure_ascii=False)

        from utils import date_to_str

        self.global_date_str = date_to_str(Trainer.global_started_at)
        self.date_str = date_to_str(self.started_at)
        suffix = result_files_suffix(self.lora_config, self.index + 1)
        file_path = Path(PERFORMANCE_FOLDER) / self.global_date_str / f'results-{suffix}.json'

        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(info_str, encoding='utf-8')

        Trainer.results.insert(self.index, file_path)

        self.update_state('results')

    def save(self) -> Self:
        folder = LORA_FOLDER_FINAL + '/' + self.date_str
        self.trainer.save_model(folder)
        Trainer.adapters.insert(self.index, (self.label, folder))

        self.update_state('save')

        return self

    def release_resources(self) -> None:
        self.trainer.accelerator.free_momery()


def monitor_state(trainer: Trainer, stop: Event) -> None:
    while not stop.wait(timeout=.05):
        trainer.show_state()


def result_files_suffix(lora_config: TrainerConfig, version: int) -> str:
    r = lora_config.ranker
    a = lora_config.alpha
    ep = lora_config.epochs
    b = lora_config.batch_size

    return f'v{version}-r{r}_alpha{a}_ep{ep}_b{b}'
