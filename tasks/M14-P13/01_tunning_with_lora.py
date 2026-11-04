"""
Fine-tunning LLM with LoRA
"""


# imports


from global_state import Trainer, monitor_state, TrainerConfig
from threading import Thread, Event


# pre-config
# dataset
# LoRA configs
# train
# save model

rankers = [4, 8, 16]
target_module_list: list[str|list[str]] = [
    ['q_proj', 'v_proj'],
    ['q_proj', 'k_proj', 'q_proj', 'o_proj'],
    'all-linear',
]
epochs_list = [3, 5, 10]
batch_size_list: list[int] = [1, 5, 10]

if __name__ == '__main__':

    iterations_count = len(rankers) * len(target_module_list) * len(epochs_list) * len(batch_size_list)
    i = 1

    for ranker in rankers:
        for target_modules in target_module_list:
            for epochs in epochs_list:
                for batch_size in batch_size_list:
                    """Iterate through combinations"""

                    config = TrainerConfig(ranker, target_modules, epochs, batch_size)

                    trainer = Trainer(config, [], f'Training {i}/{iterations_count}')
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
                                .split_dataset()
                                .train()
                                .validate()
                                .save()
                        )
                    finally:
                        i = i + 1
                        stop.set()
                        monitor.join()
                        trainer.show_state()
