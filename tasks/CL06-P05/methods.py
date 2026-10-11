
def my_state_to_string(state: dict) -> str:
    YELLOW = '\033[93m'
    GREEN = '\033[92m'
    RESET = '\033[0m'

    lines = [
        f'    "{YELLOW}{key}{RESET}": "{GREEN}{value}{RESET}"'
        for key, value in state.items()
    ]

    return "{\n" + ",\n".join(lines) + "\n}"