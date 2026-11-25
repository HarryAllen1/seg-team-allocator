"""Cohort CSV parsing and validation.

Saving to the database is a separate step (see ``save_students`` in ``cohort_store.py``).

Design decisions (copy these into your README / report):

1. Structural problems reject the whole file: empty file, undecodable file,
   missing ``first_name`` / ``last_name`` / ``email`` column, duplicate column
   names, or no student rows.
2. Row-level errors (blank or too long name or email, malformed or duplicate
   email, gender/ethnicity code outside the allowed set, non-integer or
   out-of-range c-score, wrong number of fields) make the import invalid.
   The save step adds one more: an email that belongs to a staff account. Nothing is
   imported, but *every* problem is reported with its row number and column,
   so staff can fix the file in one pass. No student is ever silently dropped.
3. Harmless differences are tolerated and reported as warnings:
   - leading/trailing whitespace is trimmed and emails are lower-cased;
   - a missing ``gender`` / ``ethnicity`` column, or a blank value, is read as
     0 ("not provided");
   - a missing ``c-score`` column, or a blank value, is read as None. Whether
     that matters is decided later by any policy that needs a c-score;
   - completely blank lines are skipped;
   - ``c_score`` / ``c score`` are accepted as aliases for ``c-score``.
4. Any other column is read, as text, into ``StudentRow.extra`` and is never
   an error. The User model has no field for them yet, so the save step does
   not store them and the upload page says so.
"""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field

from allocations.choices import Ethnicity, Gender

REQUIRED_COLUMNS = ('first_name', 'last_name', 'email')
GENDER_COLUMN = 'gender'
ETHNICITY_COLUMN = 'ethnicity'
C_SCORE_COLUMN = 'c-score'
KNOWN_COLUMNS = REQUIRED_COLUMNS + (GENDER_COLUMN, ETHNICITY_COLUMN, C_SCORE_COLUMN)

BLANK_VALUE_NOTES = {
    GENDER_COLUMN: f'treated as {Gender.NOT_PROVIDED.value} ({Gender.NOT_PROVIDED.label.lower()})',
    ETHNICITY_COLUMN: f'treated as {Ethnicity.NOT_PROVIDED.value} ({Ethnicity.NOT_PROVIDED.label.lower()})',
    C_SCORE_COLUMN: 'left empty',
}
C_SCORE_MIN, C_SCORE_MAX = 0, 100
# Limits of the User model: names are 50 characters, and the email is also used as the username (150).
MAX_NAME_LENGTH = 50
MAX_EMAIL_LENGTH = 150

HEADER_ALIASES = {'c_score': C_SCORE_COLUMN, 'c score': C_SCORE_COLUMN, 'cscore': C_SCORE_COLUMN}

# Deliberately simple: something@something.tld, no spaces.
_EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


@dataclass(frozen=True)
class ImportIssue:
    """A problem or note about the file. ``row`` is the spreadsheet row
    number (the header is row 1), or None for file-level issues."""

    message: str
    row: int | None = None
    column: str | None = None


@dataclass
class StudentRow:
    row_number: int
    first_name: str
    last_name: str
    email: str
    gender: int = Gender.NOT_PROVIDED.value
    ethnicity: int = Ethnicity.NOT_PROVIDED.value
    c_score: int | None = None
    extra: dict = field(default_factory=dict)


@dataclass
class ImportResult:
    students: list[StudentRow] = field(default_factory=list)
    errors: list[ImportIssue] = field(default_factory=list)
    warnings: list[ImportIssue] = field(default_factory=list)
    extra_columns: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.errors

# Decodes the bytes, rejects an empty file, picks the separator, finds the header (the first non-blank line), 
# validates it, validates every row, and adds an error if there were no student rows.
def parse_cohort_csv(raw: bytes | str) -> ImportResult:
    """Parse and validate a cohort file. Never raises for bad content."""
    result = ImportResult()

    text = _decode(raw, result)
    if text is None:
        return result
    if not text.strip():
        result.errors.append(ImportIssue('The file is empty.'))
        return result

    rows = list(csv.reader(io.StringIO(text, newline=''), _detect_dialect(text)))
    header_line_index = next((i for i, r in enumerate(rows) if any(c.strip() for c in r)), None)
    if header_line_index is None:
        result.errors.append(ImportIssue('The file is empty.'))
        return result

    columns = _validate_header(rows[header_line_index], result)
    if columns is None:
        return result

    _validate_rows(rows[header_line_index + 1 :], header_line_index + 2, columns, result)

    if not result.students and result.is_valid:
        result.errors.append(ImportIssue('The file has a header but no student rows.'))
    return result


# --------------------------------------------------------------------------
# Decoding and header handling
# --------------------------------------------------------------------------

# Decodes as UTF-8 and strips the invisible marker Excel adds at the start.
def _decode(raw: bytes | str, result: ImportResult) -> str | None:
    if isinstance(raw, str):
        return raw.lstrip('﻿')
    try:
        return raw.decode('utf-8-sig')  # also strips an Excel BOM
    except UnicodeDecodeError:
        result.errors.append(
            ImportIssue(
                'The file is not valid UTF-8 text. In Excel, use '
                "'Save As > CSV UTF-8 (Comma delimited)' and upload again."
            )
        )
        return None

# Counts commas, semicolons and tabs in the first non-blank line and uses the most common one (comma if none).
# Note: Not sure if we need this or not
def _detect_dialect(text: str):
    """Comma by default; also accept semicolons or tabs (common from European Excel)."""
    first_line = next((ln for ln in text.splitlines() if ln.strip()), '')
    counts = {d: first_line.count(d) for d in (',', ';', '\t')}
    best = max(counts, key=counts.get)

    class _Dialect(csv.excel):
        delimiter = best if counts[best] > 0 else ','

    return _Dialect

# Trims a column name and removes a stray marker character. Known columns are lower-cased and aliases are mapped to c-score.
# Other column names keep their original case.
def _normalise_header(name: str) -> str:
    cleaned = name.strip().lstrip('﻿')
    lowered = cleaned.lower()
    if lowered in KNOWN_COLUMNS:
        return lowered
    return HEADER_ALIASES.get(lowered, cleaned)

# Errors for an empty column name, a repeated name (ignoring case) and missing required columns.
# Warnings for a c-score alias and for missing optional columns. (Since they aren't required)
def _validate_header(header: list[str], result: ImportResult) -> list[str] | None:
    columns = [_normalise_header(h) for h in header]
    ok = True

    seen: set[str] = set()
    for original, col in zip(header, columns):
        if not col:
            result.errors.append(ImportIssue('A column has no name in the header row.', row=1))
            ok = False
        elif col.lower() in seen:
            result.errors.append(ImportIssue(f"Column '{col}' appears more than once.", row=1, column=col))
            ok = False
        seen.add(col.lower())
        if original.strip().lower() in HEADER_ALIASES:
            result.warnings.append(ImportIssue(f"Column '{original.strip()}' was read as '{C_SCORE_COLUMN}'.", row=1))

    missing = [c for c in REQUIRED_COLUMNS if c not in columns]
    if missing:
        result.errors.append(
            ImportIssue(
                'Required column(s) missing: ' + ', '.join(missing) + '. '
                'The file must contain first_name, last_name and email.'
            )
        )
        ok = False

    if not ok:
        return None

    for optional, meaning in BLANK_VALUE_NOTES.items():
        if optional not in columns:
            result.warnings.append(ImportIssue(f"No '{optional}' column: {meaning} for every student."))

    result.extra_columns = [c for c in columns if c not in KNOWN_COLUMNS]
    return columns


# --------------------------------------------------------------------------
# Row handling
# --------------------------------------------------------------------------

# Loops over the rows. Skips blank lines and counts them. A row with the wrong number of values is an error.
# Otherwise it checks names, email, gender, ethnicity and c-score.
# It builds a StudentRow only if the row had no new errors, so every problem is reported but no bad student is kept.
# Note: What to do (maybe a fix?) with the reported rows is to be dcided.
def _validate_rows(data_rows: list[list[str]], first_row_number: int, columns: list[str], result: ImportResult) -> None:
    first_row_of_email: dict[str, int] = {}
    blank_lines = 0
    lowered_emails = 0
    blank_defaults = {GENDER_COLUMN: 0, ETHNICITY_COLUMN: 0, C_SCORE_COLUMN: 0}  # blank cells defaulted

    for offset, cells in enumerate(data_rows):
        row_number = first_row_number + offset
        if not any(c.strip() for c in cells):
            blank_lines += 1
            continue

        if len(cells) != len(columns):
            result.errors.append(
                ImportIssue(
                    f'Row has {len(cells)} value(s) but the header has {len(columns)} column(s). '
                    'Check for a stray comma or an unquoted comma inside a value.',
                    row=row_number,
                )
            )
            continue

        values = dict(zip(columns, (c.strip() for c in cells)))
        errors_before = len(result.errors)

        first_name = _required_text(values, 'first_name', row_number, result)
        last_name = _required_text(values, 'last_name', row_number, result)
        email = _email(values['email'], row_number, first_row_of_email, result)
        if email and email != values['email']:
            lowered_emails += 1

        gender = _code(values, GENDER_COLUMN, Gender, row_number, result)
        ethnicity = _code(values, ETHNICITY_COLUMN, Ethnicity, row_number, result)
        c_score = _c_score(values, row_number, result)

        if len(result.errors) > errors_before:
            continue  # row is invalid; do not build a StudentRow for it

        for col in (GENDER_COLUMN, ETHNICITY_COLUMN, C_SCORE_COLUMN):
            if col in values and values[col] == '':
                blank_defaults[col] += 1

        extra = {c: (values[c] or None) for c in result.extra_columns}
        result.students.append(
            StudentRow(
                row_number=row_number,
                first_name=first_name,
                last_name=last_name,
                email=email,
                gender=gender,
                ethnicity=ethnicity,
                c_score=c_score,
                extra=extra,
            )
        )

    _summary_warnings(result, blank_lines, lowered_emails, blank_defaults)

# Checks a name column: error if blank or longer than 50 characters.
def _required_text(values: dict, column: str, row: int, result: ImportResult) -> str:
    value = values[column]
    if not value:
        result.errors.append(ImportIssue(f"'{column}' is blank.", row=row, column=column))
    elif len(value) > MAX_NAME_LENGTH:
        result.errors.append(
            ImportIssue(f"'{column}' is longer than {MAX_NAME_LENGTH} characters.", row=row, column=column)
        )
    return value

# Checks the email: error if blank, not email-shaped, longer than 150 characters, or already seen.
# 'seen' maps each email to the first row that used it, so a duplicate error says which row.
# Returns the lower-cased email, or an empty string on error.
def _email(raw: str, row: int, seen: dict[str, int], result: ImportResult) -> str:
    if not raw:
        result.errors.append(
            ImportIssue("'email' is blank. Every student needs a unique email.", row=row, column='email')
        )
        return ''
    if not _EMAIL_RE.match(raw):
        result.errors.append(ImportIssue(f"'{raw}' is not a valid email address.", row=row, column='email'))
        return ''
    email = raw.lower()
    if len(email) > MAX_EMAIL_LENGTH:
        result.errors.append(
            ImportIssue(f'Email is longer than {MAX_EMAIL_LENGTH} characters.', row=row, column='email')
        )
        return ''
    if email in seen:
        result.errors.append(
            ImportIssue(f"Duplicate email '{email}' (first used on row {seen[email]}).", row=row, column='email')
        )
        return ''
    seen[email] = row
    return email

# Converts text to a whole number, or returns None if it is not one.
def _int_or_none(text: str) -> int | None:
    try:
        return int(text)
    except ValueError:
        return None

def _code(values: dict, column: str, choices: type[Gender] | type[Ethnicity], row: int, result: ImportResult) -> int:
    """Read a plain code or the numeric prefix of a labelled CSV cell."""
    text = values.get(column, '')
    if text == '':
        return choices.NOT_PROVIDED.value
    number = _int_or_none(text.split(':', 1)[0].strip())
    if number not in choices:
        valid = ', '.join(str(code) for code in choices.values)
        result.errors.append(
            ImportIssue(f"'{text}' is not a valid {column} code. Allowed values: {valid}.", row=row, column=column)
        )
        return choices.NOT_PROVIDED.value
    return number

# Reads the c-score. Blank gives None. Errors if it is not a whole number (so 55.5 is rejected) or is outside 0-100.
def _c_score(values: dict, row: int, result: ImportResult) -> int | None:
    text = values.get(C_SCORE_COLUMN, '')
    if text == '':
        return None
    number = _int_or_none(text)
    if number is None:
        result.errors.append(ImportIssue(f"'{text}' is not a whole number.", row=row, column=C_SCORE_COLUMN))
        return None
    if not C_SCORE_MIN <= number <= C_SCORE_MAX:
        result.errors.append(
            ImportIssue(
                f'c-score {number} is outside the allowed range {C_SCORE_MIN}-{C_SCORE_MAX}.',
                row=row,
                column=C_SCORE_COLUMN,
            )
        )
        return None
    return number

# Adds the summary notes: how many blank lines were skipped, how many emails were lower-cased, and how many blank gender,
# ethnicity and c-score values were defaulted.
def _summary_warnings(result: ImportResult, blank_lines: int, lowered_emails: int, blank_defaults: dict) -> None:
    if blank_lines:
        result.warnings.append(ImportIssue(f'{blank_lines} blank line(s) were skipped.'))
    if lowered_emails:
        result.warnings.append(ImportIssue(f'{lowered_emails} email address(es) were converted to lower case.'))
    for column, label in BLANK_VALUE_NOTES.items():
        count = blank_defaults.get(column, 0)
        if count:
            result.warnings.append(ImportIssue(f"{count} blank '{column}' value(s) were {label}."))
