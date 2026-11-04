"""
Methods to help development
"""

def print_replace(lines: str) -> None:
    count_lines = len(lines.splitlines())
    backlines = f'\033[{count_lines}F\033[J'
    
    print(f'{backlines}{lines}', end='\n', flush=True)