_FORMULA_TRIGGER_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def safe_cell(value):
    """Neutralize Excel/CSV formula injection (CWE-1236): a leading '=', '+', '-'
    or '@' makes some spreadsheet apps treat a cell as a formula. Any string
    field in an exported workbook can ultimately trace back to user-submitted
    text (ticket description, resolution comment, a name typed during bot
    registration, etc.), so every string cell is sanitized rather than trying
    to guess which fields are "safe"."""
    # len > 1 so a bare "-" placeholder (used everywhere in these exports for
    # "no value") isn't needlessly mangled — a single trigger character alone
    # can't form a working formula/DDE payload.
    if isinstance(value, str) and len(value) > 1 and value.startswith(_FORMULA_TRIGGER_PREFIXES):
        return "'" + value
    return value


def safe_row(row: list) -> list:
    return [safe_cell(v) for v in row]
