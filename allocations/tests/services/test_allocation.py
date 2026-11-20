from dataclasses import replace
from decimal import Decimal
from unittest import TestCase
from unittest.mock import patch

from allocations.services.allocation import (
    MAX_STUDENTS, AllocationError, AllocationOptions, Student, allocate_students,
    gender_issues, team_cost, validate_students,
)
from allocations.tests.allocation_helpers import students


class AllocationTests(TestCase):
    def assert_partition(self, cohort, result):
        self.assertEqual(sorted(s.email for s in cohort), sorted(s.email for team in result.teams for s in team))
        for team in result.teams:
            self.assertIn(len(team), (4, 5))
            self.assertEqual(len({s.committed for s in team}), 1)

    def test_valid_small_cohort_sizes(self):
        for count in range(4, 51):
            feasible = any(4 * teams <= count <= 5 * teams for teams in range(1, count))
            with self.subTest(count=count):
                if feasible:
                    cohort = students(count)
                    self.assert_partition(cohort, allocate_students(cohort))
                else:
                    with self.assertRaises(AllocationError):
                        allocate_students(students(count))

    def test_minimum_cohort(self):
        result = allocate_students(students(4))
        self.assertEqual(len(result.teams), 1)
        self.assertEqual(result.warnings, ())

    def test_maximum_cohort(self):
        cohort = students(MAX_STUDENTS)
        result = allocate_students(cohort)
        self.assert_partition(cohort, result)
        self.assertTrue(result.search_limited)

    def test_over_maximum(self):
        with self.assertRaisesRegex(AllocationError, 'at most 1000'):
            allocate_students(students(MAX_STUDENTS + 1))

    def test_commitment_groups_stay_separate(self):
        cohort = students(9)
        cohort = [replace(s, committed=index < 4) for index, s in enumerate(cohort)]
        result = allocate_students(cohort)
        self.assert_partition(cohort, result)
        self.assertEqual([len(team) for team in result.teams], [4, 5])

    def test_infeasible_commitment_group_rejects_whole_cohort(self):
        cohort = students(8)
        cohort[-1] = replace(cohort[-1], committed=False)
        with self.assertRaisesRegex(AllocationError, 'commitment Yes group has 7'):
            allocate_students(cohort)

    def test_feasibility_is_checked_before_improvement(self):
        cohort = students(11)
        cohort = [replace(s, committed=index < 8) for index, s in enumerate(cohort)]
        with (
            patch('allocations.services.allocation._improve_teams') as improve,
            self.assertRaisesRegex(AllocationError, 'commitment No group has 3'),
        ):
            allocate_students(cohort)
        improve.assert_not_called()

    def test_mark_bands_respect_target_when_possible(self):
        cohort = students(10)
        cohort = [replace(s, c_score=Decimal(30 if index < 5 else 80)) for index, s in enumerate(cohort)]
        result = allocate_students(cohort)
        self.assertEqual(result.warnings, ())
        self.assertEqual({m['c_score_spread'] for m in result.metrics}, {'0'})

    def test_unavoidable_mark_spread_is_returned_as_warning(self):
        cohort = students(4)
        cohort[-1] = replace(cohort[-1], c_score=Decimal(100))
        result = allocate_students(cohort)
        self.assertIn('spread 40 exceeds the target 10', result.warnings[0])
        self.assertTrue(result.metrics[0]['c_score_exceeded'])

    def test_decimal_marks_and_zero_target(self):
        cohort = students(4, c_score=Decimal('60.01'))
        cohort[-1] = replace(cohort[-1], c_score=Decimal('60.02'))
        result = allocate_students(cohort, AllocationOptions(c_score_target=Decimal('0')))
        self.assertEqual(result.metrics[0]['c_score_spread'], '0.01')
        self.assertEqual(result.metrics[0]['high_penalty'], 4)

    def test_missing_optional_values_have_no_penalty(self):
        self.assertEqual(team_cost(students(5), AllocationOptions()), (0, 0))

    def test_gender_singletons_are_counted_only_for_answered_students(self):
        cohort = students(4, gender='man')
        cohort[0] = replace(cohort[0], gender='woman')
        self.assertEqual(gender_issues(cohort), [cohort[0].email])
        cohort[0] = replace(cohort[0], gender='')
        self.assertEqual(gender_issues(cohort), [])

    def test_other_gender_prefers_diverse_teammates(self):
        cohort = students(4)
        cohort[0] = replace(cohort[0], gender='other')
        self.assertIn(cohort[0].email, gender_issues(cohort))
        cohort[1] = replace(cohort[1], gender='man')
        self.assertNotIn(cohort[0].email, gender_issues(cohort))

    def test_other_gender_with_same_category_peer(self):
        self.assertEqual(gender_issues(students(4, gender='other')), [])

    def test_configurable_team_size_limits(self):
        for minimum, maximum, count in ((2, 3, 7), (3, 3, 9), (6, 10, 17), (1, 1, 4)):
            with self.subTest(minimum=minimum, maximum=maximum):
                result = allocate_students(students(count), AllocationOptions(min_team_size=minimum, max_team_size=maximum))
                self.assertEqual(sum(map(len, result.teams)), count)
                self.assertTrue(all(minimum <= len(team) <= maximum for team in result.teams))

    def test_soft_commitment_handles_small_minority_group(self):
        cohort = students(8)
        cohort[-1] = replace(cohort[-1], committed=False)
        result = allocate_students(cohort, AllocationOptions(commitment_mode='soft'))
        self.assertEqual(sum(map(len, result.teams)), 8)
        self.assertTrue(any(m['mixed_commitment'] for m in result.metrics))
        self.assertTrue(any('commitment answers differ' in warning for warning in result.warnings))

    def test_minimal_records_with_unused_attributes_omitted(self):
        cohort = [replace(s, c_score=None, committed=None) for s in students(4)]
        result = allocate_students(cohort, AllocationOptions(use_c_score=False, commitment_mode='ignore'))
        self.assertEqual(len(result.teams[0]), 4)
        self.assertIsNone(result.metrics[0]['c_score_spread'])
        self.assertEqual(result.metrics[0]['commitment_label'], 'Unanswered')

    def test_soft_commitment_ignores_missing_answers(self):
        cohort = students(4, committed=None)
        result = allocate_students(cohort, AllocationOptions(commitment_mode='soft'))
        self.assertFalse(result.metrics[0]['mixed_commitment'])

    def test_gender_improvement_keeps_paired_women(self):
        cohort = students(8, gender='man')
        cohort = [replace(s, gender='woman' if index in (0, 4) else 'man') for index, s in enumerate(cohort)]
        result = allocate_students(cohort)
        self.assertFalse(any(m['gender_issues'] for m in result.metrics))

    def test_conflicting_high_tier_preferences_are_reported(self):
        cohort = students(4, gender='man')
        cohort[0] = replace(cohort[0], gender='woman', c_score=Decimal(10))
        result = allocate_students(cohort)
        self.assertEqual(len(result.warnings), 2)

    def test_lower_tier_cannot_trade_away_high_tier(self):
        cohort = students(8, workload='meet', ethnicity='asian')
        cohort = [replace(s, c_score=Decimal(0 if index < 4 else 100),
                          workload='reduce' if index % 2 else 'exceed',
                          ethnicity='white' if index < 4 else 'asian') for index, s in enumerate(cohort)]
        result = allocate_students(cohort, AllocationOptions(c_score_target=Decimal(0)))
        self.assertTrue(all(m['high_penalty'] == 0 for m in result.metrics))
        self.assertTrue(all(len({s.ethnicity for s in team}) == 1 for team in result.teams))

    def test_workload_similarity_improves_within_high_tier_ties(self):
        cohort = [replace(s, workload='reduce' if index % 2 else 'exceed') for index, s in enumerate(students(8))]
        result = allocate_students(cohort, AllocationOptions(use_ethnicity=False))
        self.assertTrue(all(len({s.workload for s in team}) == 1 for team in result.teams))

    def test_ethnic_diversity_improves_within_high_tier_ties(self):
        cohort = [replace(s, ethnicity='asian' if index < 4 else 'white') for index, s in enumerate(students(8))]
        result = allocate_students(cohort, AllocationOptions(use_workload=False))
        self.assertTrue(all(len({s.ethnicity for s in team}) == 2 for team in result.teams))

    def test_disabled_preferences_have_no_effect(self):
        cohort = students(4, gender='man', workload='exceed', ethnicity='asian')
        cohort[0] = replace(cohort[0], gender='woman', workload='reduce')
        options = AllocationOptions(use_gender=False, use_workload=False, use_ethnicity=False)
        self.assertEqual(team_cost(cohort, options), (0, 0))
        self.assertEqual(allocate_students(cohort, options).warnings, ())

    def test_tied_solutions_are_deterministic_and_input_order_independent(self):
        cohort = students(13)
        result = allocate_students(cohort)
        self.assertEqual(result, allocate_students(reversed(cohort)))
        self.assertEqual(result, allocate_students(cohort))

    def test_input_is_not_mutated(self):
        cohort = students(8)
        before = list(cohort)
        allocate_students(cohort)
        self.assertEqual(cohort, before)

    def test_duplicate_emails_are_rejected_case_insensitively(self):
        cohort = students(4)
        cohort[1] = replace(cohort[1], email=' ' + cohort[0].email.upper() + ' ')
        with self.assertRaisesRegex(AllocationError, 'Duplicate student email'):
            allocate_students(cohort)

    def test_same_names_with_distinct_emails_are_allowed(self):
        cohort = students(4, first_name='Alex', last_name='Smith')
        self.assert_partition(cohort, allocate_students(cohort))

    def test_required_names_and_email_are_normalized(self):
        student = students(1, first_name=' Alex ', last_name=' Smith ', email=' ALEX@EXAMPLE.ORG ')[0]
        cleaned = validate_students([student])[0]
        self.assertEqual((cleaned.first_name, cleaned.last_name, cleaned.email), ('Alex', 'Smith', 'alex@example.org'))

    def test_invalid_student_fields(self):
        invalid = {
            'first_name': ['', ' ' * 2, 'a' * 51, None],
            'last_name': ['', 'a' * 51, 12],
            'email': ['', 'invalid', 'a@b', 'a b@example.org', 'a' * 255, None],
            'committed': [None, 1, 'yes'],
            'c_score': ['bad', -1, 101, True, None, Decimal('NaN'), float('inf'), Decimal('60.001'), Decimal('1e-1000000')],
            'gender': ['unknown', None], 'workload': ['high', None], 'ethnicity': ['unknown', None],
        }
        for field, values in invalid.items():
            for value in values:
                with self.subTest(field=field, value=value), self.assertRaises(AllocationError):
                    allocate_students(students(4, **{field: value}))

    def test_empty_and_malformed_cohort(self):
        for cohort in ([], None, [None], ['student']):
            with self.subTest(cohort=cohort), self.assertRaises(AllocationError):
                allocate_students(cohort)

    def test_invalid_options(self):
        for options in (None, {}, AllocationOptions(c_score_target='bad'),
                        AllocationOptions(c_score_target=Decimal('NaN')),
                        AllocationOptions(use_gender=1), AllocationOptions(use_workload='yes'),
                        AllocationOptions(use_ethnicity=None), AllocationOptions(use_c_score=1),
                        AllocationOptions(commitment_mode='invalid'), AllocationOptions(min_team_size=0),
                        AllocationOptions(min_team_size=True), AllocationOptions(max_team_size=11),
                        AllocationOptions(min_team_size=6, max_team_size=5)):
            with self.subTest(options=options), self.assertRaises(AllocationError):
                allocate_students(students(4), options)

    def test_search_budget_is_reported(self):
        with patch('allocations.services.allocation.MAX_SWAP_CHECKS', 0):
            result = allocate_students(students(8))
        self.assertTrue(result.search_limited)
        self.assertIn('search reached its limit', result.warnings[-1])
