import unittest

from allocations.services.csv_import import C_SCORE_COLUMN, parse_cohort_csv

HEADER = 'first_name,last_name,email,gender,ethnicity,c-score'


def csv_of(*lines, header=HEADER):
    return ('\n'.join([header, *lines]) + '\n').encode('utf-8')


def error_cells(result):
    return {(e.row, e.column) for e in result.errors}


class ValidFileTests(unittest.TestCase):
    def test_clean_file_imports_every_student(self):
        r = parse_cohort_csv(csv_of('Ann,Lee,ann@x.ac.uk,1,4,70', 'Bob,Ng,bob@x.ac.uk,2,1,55'))
        self.assertTrue(r.is_valid)
        self.assertEqual([s.email for s in r.students], ['ann@x.ac.uk', 'bob@x.ac.uk'])
        self.assertEqual((r.students[0].gender, r.students[0].ethnicity, r.students[0].c_score), (1, 4, 70))
        self.assertEqual(r.warnings, [])

    def test_row_numbers_are_spreadsheet_rows(self):
        r = parse_cohort_csv(csv_of('Ann,Lee,ann@x.ac.uk,1,4,70', 'Bob,Ng,bob@x.ac.uk,2,1,55'))
        self.assertEqual([s.row_number for s in r.students], [2, 3])

    def test_extra_columns_are_accepted_and_kept(self):
        raw = csv_of('Ann,Lee,ann@x.ac.uk,1,4,70,Maths,', header=HEADER + ',programme,notes')
        r = parse_cohort_csv(raw)
        self.assertTrue(r.is_valid)
        self.assertEqual(r.extra_columns, ['programme', 'notes'])
        self.assertEqual(r.students[0].extra, {'programme': 'Maths', 'notes': None})

    def test_excel_bom_does_not_break_first_header(self):
        r = parse_cohort_csv(b'\xef\xbb\xbf' + csv_of('Ann,Lee,ann@x.ac.uk,1,4,70'))
        self.assertTrue(r.is_valid)

    def test_semicolon_delimiter_is_detected(self):
        raw = b'first_name;last_name;email\nAnn;Lee;ann@x.ac.uk\n'
        r = parse_cohort_csv(raw)
        self.assertTrue(r.is_valid)
        self.assertEqual(r.students[0].email, 'ann@x.ac.uk')

    def test_quoted_comma_and_newline_inside_value(self):
        raw = b'first_name,last_name,email,programme\nAnn,"Lee, Jr",ann@x.ac.uk,"BSc\nMaths"\n'
        r = parse_cohort_csv(raw)
        self.assertTrue(r.is_valid)
        self.assertEqual(r.students[0].last_name, 'Lee, Jr')
        self.assertEqual(r.students[0].extra['programme'], 'BSc\nMaths')

    def test_windows_line_endings(self):
        r = parse_cohort_csv(csv_of('Ann,Lee,ann@x.ac.uk,1,4,70').replace(b'\n', b'\r\n'))
        self.assertTrue(r.is_valid)


class TolerancesTests(unittest.TestCase):
    def test_whitespace_trimmed_and_email_lowercased_with_warning(self):
        r = parse_cohort_csv(csv_of('  Ann ,Lee, Ann@X.ac.uk ,1,4,70'))
        self.assertTrue(r.is_valid)
        s = r.students[0]
        self.assertEqual((s.first_name, s.email), ('Ann', 'ann@x.ac.uk'))
        self.assertTrue(any('lower case' in w.message for w in r.warnings))

    def test_header_case_and_spacing_tolerated(self):
        raw = b' First_Name , LAST_NAME ,Email\nAnn,Lee,ann@x.ac.uk\n'
        self.assertTrue(parse_cohort_csv(raw).is_valid)

    def test_blank_optional_values_default_with_warnings(self):
        r = parse_cohort_csv(csv_of('Ann,Lee,ann@x.ac.uk,,,'))
        self.assertTrue(r.is_valid)
        s = r.students[0]
        self.assertEqual((s.gender, s.ethnicity, s.c_score), (0, 0, None))
        self.assertEqual(len(r.warnings), 3)

    def test_missing_optional_columns_default_with_warnings(self):
        raw = b'first_name,last_name,email\nAnn,Lee,ann@x.ac.uk\n'
        r = parse_cohort_csv(raw)
        self.assertTrue(r.is_valid)
        self.assertEqual((r.students[0].gender, r.students[0].c_score), (0, None))
        self.assertEqual(len(r.warnings), 3)

    def test_c_score_aliases(self):
        for name in ('c_score', 'C-Score', 'c score'):
            raw = f'first_name,last_name,email,{name}\nAnn,Lee,ann@x.ac.uk,42\n'.encode()
            r = parse_cohort_csv(raw)
            self.assertTrue(r.is_valid, name)
            self.assertEqual(r.students[0].c_score, 42, name)

    def test_blank_lines_skipped_and_reported(self):
        r = parse_cohort_csv(csv_of('Ann,Lee,ann@x.ac.uk,1,4,70', '', ',,,,,', 'Bob,Ng,bob@x.ac.uk,2,1,55'))
        self.assertTrue(r.is_valid)
        self.assertEqual(len(r.students), 2)
        self.assertEqual([s.row_number for s in r.students], [2, 5])
        self.assertTrue(any('blank line' in w.message for w in r.warnings))

    def test_boundary_c_scores_accepted(self):
        r = parse_cohort_csv(csv_of('A,A,a@x.ac.uk,1,1,0', 'B,B,b@x.ac.uk,1,1,100'))
        self.assertTrue(r.is_valid)
        self.assertEqual([s.c_score for s in r.students], [0, 100])


class RejectedFileTests(unittest.TestCase):
    def assertRejected(self, result):
        self.assertFalse(result.is_valid)
        self.assertTrue(result.errors)

    def test_empty_file(self):
        self.assertRejected(parse_cohort_csv(b''))
        self.assertRejected(parse_cohort_csv(b'  \n\n'))

    def test_header_only(self):
        r = parse_cohort_csv(HEADER.encode() + b'\n')
        self.assertRejected(r)
        self.assertIn('no student rows', r.errors[0].message)

    def test_missing_required_columns_are_named(self):
        r = parse_cohort_csv(b'first_name,gender\nAnn,1\n')
        self.assertRejected(r)
        self.assertIn('last_name', r.errors[0].message)
        self.assertIn('email', r.errors[0].message)
        self.assertEqual(r.students, [])

    def test_not_utf8(self):
        r = parse_cohort_csv('first_name,last_name,email\nZoë,Lee,z@x.ac.uk\n'.encode('latin-1'))
        self.assertRejected(r)
        self.assertIn('UTF-8', r.errors[0].message)

    def test_duplicate_header(self):
        r = parse_cohort_csv(b'first_name,last_name,email,email\nA,B,a@x.ac.uk,a@x.ac.uk\n')
        self.assertRejected(r)

    def test_blank_email(self):
        r = parse_cohort_csv(csv_of('Ann,Lee,,1,4,70'))
        self.assertRejected(r)
        self.assertIn((2, 'email'), error_cells(r))

    def test_malformed_email(self):
        r = parse_cohort_csv(csv_of('Ann,Lee,not-an-email,1,4,70'))
        self.assertIn((2, 'email'), error_cells(r))

    def test_duplicate_email_case_insensitive_points_to_first_row(self):
        r = parse_cohort_csv(csv_of('Ann,Lee,ann@x.ac.uk,1,4,70', 'Anna,Lee,ANN@x.ac.uk,1,4,70'))
        self.assertRejected(r)
        self.assertIn((3, 'email'), error_cells(r))
        self.assertIn('row 2', r.errors[0].message)

    def test_blank_names(self):
        r = parse_cohort_csv(csv_of(',Lee,ann@x.ac.uk,1,4,70', 'Bob,,bob@x.ac.uk,1,4,70'))
        self.assertEqual(error_cells(r), {(2, 'first_name'), (3, 'last_name')})

    def test_invalid_gender_and_ethnicity_codes(self):
        r = parse_cohort_csv(csv_of('A,A,a@x.ac.uk,4,1,50', 'B,B,b@x.ac.uk,1,6,50', 'C,C,c@x.ac.uk,x,1,50'))
        self.assertEqual(error_cells(r), {(2, 'gender'), (3, 'ethnicity'), (4, 'gender')})

    def test_c_score_out_of_range_or_not_integer(self):
        r = parse_cohort_csv(
            csv_of('A,A,a@x.ac.uk,1,1,101', 'B,B,b@x.ac.uk,1,1,-1', 'C,C,c@x.ac.uk,1,1,72.5', 'D,D,d@x.ac.uk,1,1,abc')
        )
        self.assertEqual(
            error_cells(r), {(2, C_SCORE_COLUMN), (3, C_SCORE_COLUMN), (4, C_SCORE_COLUMN), (5, C_SCORE_COLUMN)}
        )

    def test_wrong_number_of_fields(self):
        r = parse_cohort_csv(csv_of('Ann,Lee,ann@x.ac.uk,1,4', 'Bob,Ng,bob@x.ac.uk,2,1,55,extra'))
        self.assertEqual({e.row for e in r.errors}, {2, 3})

    def test_all_errors_reported_in_one_pass(self):
        r = parse_cohort_csv(csv_of(',Lee,ann@x.ac.uk,9,4,150', 'Bob,Ng,,2,1,55'))
        self.assertGreaterEqual(len(r.errors), 4)

    def test_no_student_is_silently_dropped(self):
        """Every non-blank data row is either imported or has an error."""
        lines = ['A,A,a@x.ac.uk,1,1,50', 'B,B,bad,1,1,50', 'C,C,c@x.ac.uk,1,1,50', 'D,D,c@x.ac.uk,1,1,50']
        r = parse_cohort_csv(csv_of(*lines))
        error_rows = {e.row for e in r.errors}
        imported_rows = {s.row_number for s in r.students}
        self.assertEqual(error_rows | imported_rows, {2, 3, 4, 5})
        self.assertEqual(error_rows & imported_rows, set())

class LabelledCodeTests(unittest.TestCase):
    """The supplied data writes codes with labels, such as '2: Man'."""

    def test_labelled_codes_use_the_number_before_the_colon(self):
        r = parse_cohort_csv(
            csv_of(
                'Ann,Lee,ann@x.ac.uk,1: Woman,"1: Asian, or Asian British",70',
                'Bob,Ng,bob@x.ac.uk,3: Other/Non-binary,5 : Other ethnic group (e.g. Arab),55',
                'Cy,Fox,cy@x.ac.uk,0,0,60',
            )
        )
        self.assertTrue(r.is_valid)
        self.assertEqual([(s.gender, s.ethnicity) for s in r.students], [(1, 1), (3, 5), (0, 0)])

    def test_labelled_code_with_an_unknown_number_is_rejected(self):
        r = parse_cohort_csv(csv_of('Ann,Lee,ann@x.ac.uk,9: Alien,"7: Other",70'))
        self.assertEqual(error_cells(r), {(2, 'gender'), (2, 'ethnicity')})

    def test_label_without_a_number_is_rejected(self):
        r = parse_cohort_csv(csv_of('Ann,Lee,ann@x.ac.uk,Woman,White,70'))
        self.assertEqual(error_cells(r), {(2, 'gender'), (2, 'ethnicity')})

class LengthLimitTests(unittest.TestCase):
    def test_name_longer_than_50_characters_is_rejected(self):
        r = parse_cohort_csv(csv_of(f'{"A" * 51},Lee,ann@x.ac.uk,1,4,70', f'Bob,{"B" * 50},bob@x.ac.uk,1,4,70'))
        self.assertEqual(error_cells(r), {(2, 'first_name')})

    def test_email_longer_than_150_characters_is_rejected(self):
        r = parse_cohort_csv(csv_of(f'Ann,Lee,{"a" * 145}@x.ac.uk,1,4,70'))
        self.assertEqual(error_cells(r), {(2, 'email')})


class LargeCohortTests(unittest.TestCase):
    def test_300_students(self):
        lines = [f'S{i},T{i},s{i}@x.ac.uk,{i % 4},{i % 6},{i % 101}' for i in range(300)]
        r = parse_cohort_csv(csv_of(*lines))
        self.assertTrue(r.is_valid)
        self.assertEqual(len(r.students), 300)


if __name__ == '__main__':
    unittest.main()
