"""
Methods to help development
"""

from colorize import colorize
import shutil


terminal_size = shutil.get_terminal_size().columns
steps_progress: dict[str,tuple[bool,str,str]] = {
    'retrieve': (False, 'Retrieving chunks', 'orange'),
    'reranking': (False, 'Reranking chunks', 'orange'),
    'assess': (False, 'Validate if chunks are enough', 'yellow'),
    'threshold': (False, 'Generating threshold', 'yellow'),
    'response': (False, 'Generating response', 'yellow'),
    'end': (False, 'Response generated', 'green'),
}
steps_progress_total = len(steps_progress.values())


def show_progress(total: int, step: int, step_label: str='', color: str='white') -> None:
    size = 20
    progress_percentage = step / total
    progress_steps = int(progress_percentage * size)

    bar = ("█" * progress_steps) + ("░" * (size - progress_steps))
    print(colorize(f"\r\033[2K{bar} {progress_percentage:.0%} {step_label}", color), end='', flush=True)

    if total == step:
        print()

    return


def update_progress(step_name: str) -> None:
    global steps_progress, steps_progress_total
    
    current_step = steps_progress[step_name]
    if not current_step:
        raise TypeError('Non-recognized step')

    step, (is_completed, label, color) = list(steps_progress).index(step_name), current_step

    show_progress(steps_progress_total, step+1, label, color)


def print_line_splitter() -> None:
    global terminal_size

    print(colorize(f' {"_" * (terminal_size - 2)} ', 'gray'))