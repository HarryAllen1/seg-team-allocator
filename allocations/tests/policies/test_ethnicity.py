from unittest import TestCase

from allocations.policies.ethnicity import EthnicityDiversityPolicy


ASIAN, BLACK, MIXED, WHITE, OTHER, U = 1, 2, 3, 4, 5, 0


def team(*codes):
    return [{"ethnicity": code} for code in codes]


class EthnicityDiversityPolicyTest(TestCase):

    def setUp(self):
        self.policy = EthnicityDiversityPolicy()

    def test_diverse_team_is_satisfied(self):
        result = self.policy.evaluate({"Team 1": team(ASIAN, WHITE, WHITE, BLACK)})
        self.assertTrue(result.is_satisfied)

    def test_single_category_team_is_a_violation(self):
        allocation = {"Team 1": team(WHITE, WHITE, WHITE, WHITE),
                      "Team 2": team(ASIAN, BLACK, MIXED, OTHER)}
        result = self.policy.evaluate(allocation)

        self.assertEqual(len(result.violations), 1)
        self.assertEqual(result.violations[0].team_name, "Team 1")
        self.assertEqual(result.violations[0].severity, 1)

    def test_undisclosed_students_do_not_add_diversity(self):
        allocation = {"Team 1": team(WHITE, WHITE, U, U),
                      "Team 2": team(ASIAN, BLACK, MIXED, OTHER)}
        result = self.policy.evaluate(allocation)

        self.assertEqual(len(result.violations), 1)
        self.assertEqual(result.violations[0].team_name, "Team 1")

    def test_two_disclosed_categories_among_undisclosed_is_satisfied(self):
        result = self.policy.evaluate({"Team 1": team(WHITE, ASIAN, U, U)})
        self.assertTrue(result.is_satisfied)

    def test_team_with_one_disclosed_student_gets_a_note_not_a_violation(self):
        allocation = {"Team 1": team(WHITE, U, U, U),
                      "Team 2": team(ASIAN, BLACK, MIXED, OTHER)}
        result = self.policy.evaluate(allocation)

        self.assertTrue(result.is_satisfied)
        self.assertTrue(any("Team 1" in note for note in result.notes))

    def test_requirement_is_lowered_when_cohort_has_one_category(self):
        result = self.policy.evaluate({"Team 1": team(WHITE, WHITE),
                                       "Team 2": team(WHITE, WHITE)})
        self.assertTrue(result.is_satisfied)
        self.assertEqual(len(result.notes), 1)

    def test_severity_is_number_of_missing_categories(self):
        policy = EthnicityDiversityPolicy(min_categories=3)
        allocation = {"Team 1": team(WHITE, WHITE, ASIAN, ASIAN),
                      "Team 2": team(BLACK, MIXED, OTHER, WHITE)}
        result = policy.evaluate(allocation)

        self.assertEqual(len(result.violations), 1)
        self.assertEqual(result.violations[0].severity, 1)

    def test_missing_ethnicity_is_treated_as_undisclosed(self):
        result = self.policy.evaluate({"Team 1": [{}, {"ethnicity": WHITE}, {"ethnicity": ASIAN}]})
        self.assertTrue(result.is_satisfied)

    def test_policy_is_soft_by_default(self):
        result = self.policy.evaluate({"Team 1": team(WHITE, ASIAN)})
        self.assertFalse(result.is_hard)
        self.assertEqual(result.policy_name, "Ethnicity diversity")