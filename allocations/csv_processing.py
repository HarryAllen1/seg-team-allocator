"""Reading and writing the CSV files that the application imports and exports."""

import csv

EXPORT_HEADER = ("first_name", "last_name", "email", "team")


def write_csv(output, rows):
    """Write an allocation as CSV, with a header row, to a file-like object.

    output can be anything csv.writer accepts, such as an HttpResponse.
    Each item of rows is a sequence of four values, in the order of
    EXPORT_HEADER: first name, last name, email and team name.
    """
    writer = csv.writer(output)
    writer.writerow(EXPORT_HEADER)

    for row in rows:
        writer.writerow(row)