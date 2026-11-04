"""
Has the orchestrator class with the patter design builder
"""


# imports


from typing_extensions import Self
from utils import print_replace
import time
from typing import Any
from threading import Event
from itertools import cycle
from colorize import colorize
from peft import LoraConfig


# pre-configs

# global state class


class Datasets:
    train: list
    test: list
    validation: list


class TrainerConfig:
    def __init__(self, ranker: int, target_modules: str|list[str], epochs: int, batch_size: int):
        self.ranker = ranker
        self.alpha = ranker * 2
        self.target_modules = target_modules
        self.epochs = epochs
        self.batch_size = batch_size


class Trainer:
    loader_frame = cycle("⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏")
    datasets: Datasets


    def __init__(self, lora_config: TrainerConfig, dataset: list, label: str):
        self.lora_config = lora_config
        self.dataset = dataset
        self.global_state = {
            'dataset': (False, 'Prepare datasets', 'Datasets are ready'),
            'train': (False, 'Training', 'Training is done'),
            'test': (False, 'Testing', 'Testing is done'),
            'validate': (False, 'Validating', 'Validation is done'),
            'save': (False, 'Saving adapter', 'Adapter was saved successfully'),
        }
        self.label = label


    def generate_global_state_str(self):
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

        return '\n'.join([self.label, '', progress, '', *lines])


    def update_state(self, step: str) -> Self:
        time.sleep(3)
        self.global_state[step] = (True, *self.global_state[step][1:])

        return self


    def show_state(self) -> None:
        print_replace(self.generate_global_state_str())

    
    def split_dataset(self) -> Self:
        # HACER MAS COSAS AQUI ANTES DE UPDATE_STATE
        self.update_state('dataset')
        
        return self
    
    
    def train(self) -> Self:
        # HACER MAS COSAS AQUI ANTES DE UPDATE_STATE
        self.update_state('train')

        # HACER MAS COSAS AQUI ANTES DE UPDATE_STATE
        self.update_state('test')
        
        return self
    
    
    def validate(self) -> Self:
        # HACER MAS COSAS AQUI ANTES DE UPDATE_STATE
        self.update_state('validate')
        
        return self
    
    
    def save(self) -> Self:
        # HACER MAS COSAS AQUI ANTES DE UPDATE_STATE
        self.update_state('save')
        
        return self


def monitor_state(trainer: Trainer, stop: Event) -> None:
    while not stop.wait(timeout=.05):
        trainer.show_state()