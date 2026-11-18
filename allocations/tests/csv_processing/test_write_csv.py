"""Tests of the CSV writing in allocations/csv_processing.py."""

import csv
import io

from django.test import SimpleTestCase

from allocations.csv_processing import write_csv


class WriteCsvTestCase(SimpleTestCase):
    """Tests of write_csv, which needs no database, so no TestCase is needed."""

    def setUp(self):
        self.output = io.StringIO()
        self.rows = [
            ('Rahul', 'Khan', 'rahul.khan@students.example', 'Alpaca'),
            ('Rami', 'Fahmy', 'rami.fahmy@students.example', 'Alpaca'),
            ('Mahmoud', 'Rahim', 'mahmoud.rahim@students.example', 'Llama'),
        ]

    def test_header_is_the_first_line(self):
        """The first line is the header the brief prescribes."""
        write_csv(self.output, self.rows)
        lines = self.output.getvalue().splitlines()
        self.assertEqual(lines[0], 'first_name,last_name,email,team')

    def test_one_line_per_row_after_the_header(self):
        """Every student gets exactly one line."""
        write_csv(self.output, self.rows)
        lines = self.output.getvalue().splitlines()
        self.assertEqual(len(lines), len(self.rows) + 1)

    def test_rows_are_written_in_order(self):
        """Students are written in the order given, with the right values."""
        write_csv(self.output, self.rows)
        lines = self.output.getvalue().splitlines()
        self.assertEqual(lines[1], 'Rahul,Khan,rahul.khan@students.example,Alpaca')
        self.assertEqual(lines[3], 'Mahmoud,Rahim,mahmoud.rahim@students.example,Llama')

    def test_no_rows_writes_only_the_header(self):
        """An empty allocation still produces a valid file."""
        write_csv(self.output, [])
        lines = self.output.getvalue().splitlines()
        self.assertEqual(lines, ['first_name,last_name,email,team'])

    def test_a_comma_in_a_name_stays_in_one_column(self):
        """A comma inside a value must not create an extra column."""
        rows = [('Sam', 'Smith, Jr', 'sam.smith@students.example', 'Alpaca')]
        write_csv(self.output, rows)
        parsed = list(csv.reader(self.output.getvalue().splitlines()))
        self.assertEqual(len(parsed[1]), 4)
        self.assertEqual(parsed[1][1], 'Smith, Jr')
