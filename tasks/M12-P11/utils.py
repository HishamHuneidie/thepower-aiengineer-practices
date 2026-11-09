"""
Methods to help development
"""

import math
import re
import shutil

from colorize import colorize

terminal_size = shutil.get_terminal_size().columns
steps_progress: dict[str,tuple[bool,str,str]] = {
    'retrieve': (False, 'Retrieving chunks', 'orange'),
    'rerank': (False, 'Reranking chunks', 'orange'),
    'assess': (False, 'Validate if chunks are enough', 'yellow'),
    'threshold': (False, 'Generating threshold', 'yellow'),
    'response': (False, 'Generating response', 'yellow'),
    'end': (False, 'Response generated', 'green'),
}
steps_progress_total = len(steps_progress.values())
ADDITIONAL_LOGS: list[str] = []
LAST_LINES = 0  # terminal rows printed by the previous progress bar
ANSI_RE = re.compile(r'\033\[[0-9;]*[A-Za-z]')


def reset_progress() -> None:
    global LAST_LINES

    ADDITIONAL_LOGS.clear()
    LAST_LINES = 0


def show_progress(total: int, step: int, step_label: str = '', color: str = 'white', logs: list[str] = []) -> None:
    global LAST_LINES

    size = 20
    progress_percentage = step / total
    progress_steps = int(progress_percentage * size)

    logs_str = '\n\n' + '\n'.join(logs) if logs else ''

    # go back to where the previous bar started and clear it
    backlines = f'\033[{LAST_LINES}F\033[J' if LAST_LINES else ''

    bar = ("█" * progress_steps) + ("░" * (size - progress_steps))
    text = f"{bar} {progress_percentage:.0%} {step_label}{logs_str}"
    print(backlines + colorize(text, color), flush=True)

    # count real terminal rows: long lines wrap and take more than one row
    width = shutil.get_terminal_size().columns
    LAST_LINES = sum(
        max(1, math.ceil(len(ANSI_RE.sub('', line)) / width))
        for line in text.split('\n')
    )

    if total == step:
        print()

    return


def update_progress(step_name: str) -> None:
    global steps_progress, steps_progress_total
    
    current_step = steps_progress[step_name]
    if not current_step:
        raise TypeError('Non-recognized step')

    step, (is_completed, label, color) = list(steps_progress).index(step_name), current_step

    show_progress(steps_progress_total, step + 1, label, color, ADDITIONAL_LOGS)


def add_logs(log: list[str]) -> None:
    global ADDITIONAL_LOGS

    ADDITIONAL_LOGS.append(log)


def print_line_splitter() -> None:
    global terminal_size

    print(colorize(f' {"_" * (terminal_size - 2)} ', 'gray'))