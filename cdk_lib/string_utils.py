import re


def snake(string: str) -> str:
    return re.sub(r'(?<!^)(?=[A-Z])', '_', string).lower()


def kebab(string: str) -> str:
    return re.sub(r'(?<!^)(?=[A-Z])', '-', string).lower()
