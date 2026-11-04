
def colorize(text: str, color: str) -> str:
    RESET = '\033[0m'

    colors = {
        'black': '\033[30m',
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'magenta': '\033[95m',
        'cyan': '\033[96m',
        'white': '\033[97m',
        'gray': '\033[90m',
        'orange': '\033[38;5;208m',
        'purple': '\033[38;5;129m',
        'pink': '\033[38;5;213m',
    }

    c = colors.get(color.lower(), colors['red'])

    return f'{c}{text}{RESET}'