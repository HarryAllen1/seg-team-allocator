from unittest import TestCase

from allocations.models import User
from allocations.policies.ethnicity import EthnicityDiversityPolicy


def team(*codes):
    return [{"ethnicity": code} for code in codes]


class EthnicityDiversityPolicyTest(TestCase):

    def setUp(self):
        self.policy = EthnicityDiversityPolicy()

    def test_diverse_team_is_satisfied(self):
        result = self.policy.evaluate({
            "Team 1": team(
                User.Ethnicity.ASIAN,
                User.Ethnicity.WHITE,
                User.Ethnicity.WHITE,
                User.Ethnicity.BLACK,
            )
        })
        self.assertTrue(result.is_satisfied)

    def test_single_category_team_is_a_violation(self):
        allocation = {
            "Team 1": team(
                User.Ethnicity.WHITE,
                User.Ethnicity.WHITE,
                User.Ethnicity.WHITE,
                User.Ethnicity.WHITE,
            ),
            "Team 2": team(
                User.Ethnicity.ASIAN,
                User.Ethnicity.BLACK,
                User.Ethnicity.MIXED,
                User.Ethnicity.OTHER,
            ),
        }
        result = self.policy.evaluate(allocation)

        self.assertEqual(len(result.violations), 1)
        self.assertEqual(result.violations[0].team_name, "Team 1")
        self.assertEqual(result.violations[0].severity, 1)

    def test_undisclosed_students_do_not_add_diversity(self):
        allocation = {
            "Team 1": team(
                User.Ethnicity.WHITE,
                User.Ethnicity.WHITE,
                User.Ethnicity.NOT_PROVIDED,
                User.Ethnicity.NOT_PROVIDED,
            ),
            "Team 2": team(
                User.Ethnicity.ASIAN,
                User.Ethnicity.BLACK,
                User.Ethnicity.MIXED,
                User.Ethnicity.OTHER,
            ),
        }
        result = self.policy.evaluate(allocation)

        self.assertEqual(len(result.violations), 1)
        self.assertEqual(result.violations[0].team_name, "Team 1")

    def test_two_disclosed_categories_among_undisclosed_is_satisfied(self):
        result = self.policy.evaluate({
            "Team 1": team(
                User.Ethnicity.WHITE,
                User.Ethnicity.ASIAN,
                User.Ethnicity.NOT_PROVIDED,
                User.Ethnicity.NOT_PROVIDED,
            )
        })
        self.assertTrue(result.is_satisfied)

    def test_team_with_one_disclosed_student_gets_a_note_not_a_violation(self):
        allocation = {
            "Team 1": team(
                User.Ethnicity.WHITE,
                User.Ethnicity.NOT_PROVIDED,
                User.Ethnicity.NOT_PROVIDED,
                User.Ethnicity.NOT_PROVIDED,
            ),
            "Team 2": team(
                User.Ethnicity.ASIAN,
                User.Ethnicity.BLACK,
                User.Ethnicity.MIXED,
                User.Ethnicity.OTHER,
            ),
        }
        result = self.policy.evaluate(allocation)

        self.assertTrue(result.is_satisfied)
        self.assertTrue(any("Team 1" in note for note in result.notes))

    def test_requirement_is_lowered_when_cohort_has_one_category(self):
        result = self.policy.evaluate({
            "Team 1": team(User.Ethnicity.WHITE, User.Ethnicity.WHITE),
            "Team 2": team(User.Ethnicity.WHITE, User.Ethnicity.WHITE),
        })
        self.assertTrue(result.is_satisfied)
        self.assertEqual(len(result.notes), 1)

    def test_severity_is_number_of_missing_categories(self):
        policy = EthnicityDiversityPolicy(min_categories=3)
        allocation = {
            "Team 1": team(
                User.Ethnicity.WHITE,
                User.Ethnicity.WHITE,
                User.Ethnicity.ASIAN,
                User.Ethnicity.ASIAN,
            ),
            "Team 2": team(
                User.Ethnicity.BLACK,
                User.Ethnicity.MIXED,
                User.Ethnicity.OTHER,
                User.Ethnicity.WHITE,
            ),
        }
        result = policy.evaluate(allocation)

        self.assertEqual(len(result.violations), 1)
        self.assertEqual(result.violations[0].severity, 1)

    def test_missing_ethnicity_is_treated_as_undisclosed(self):
        result = self.policy.evaluate({
            "Team 1": [
                {},
                {"ethnicity": User.Ethnicity.WHITE},
                {"ethnicity": User.Ethnicity.ASIAN},
            ]
        })
        self.assertTrue(result.is_satisfied)

    def test_policy_is_soft_by_default(self):
        result = self.policy.evaluate({
            "Team 1": team(User.Ethnicity.WHITE, User.Ethnicity.ASIAN)
        })
        self.assertFalse(result.is_hard)
        self.assertEqual(result.policy_name, "Ethnicity diversity")