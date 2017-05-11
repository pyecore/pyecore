"""
Post-generation code formatters.

The module provides simple functions taking the raw input string and returning the result string
after application of the corresponding format. The function can be given to the `Generator` during
construction.
"""


def format_raw(raw: str) -> str:
    return raw


def format_autopep8(raw: str) -> str:
    import autopep8
    return autopep8.fix_code(raw, options={'max_line_length': 100})
