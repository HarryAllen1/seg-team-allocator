from unittest import TestCase

from allocations.policies.attainment import AttainmentSpreadPolicy


def scored(*scores):
    return [{"c_score": s} for s in scores]


class AttainmentSpreadPolicyTest(TestCase):

    def setUp(self):
        self.policy = AttainmentSpreadPolicy(max_spread=15)

    def test_team_within_limit_is_satisfied(self):
        result = self.policy.evaluate({"Team 1": scored(62, 65, 70, 71)})
        self.assertTrue(result.is_satisfied)

    def test_identical_scores_are_satisfied(self):
        result = self.policy.evaluate({"Team 1": scored(50, 50, 50, 50)})
        self.assertTrue(result.is_satisfied)

    def test_score_of_zero_is_handled(self):
        result = self.policy.evaluate({"Team 1": scored(0, 10, 12, 14)})
        self.assertTrue(result.is_satisfied)

    def test_spread_exactly_at_limit_is_satisfied(self):
        result = self.policy.evaluate({"Team 1": scored(50, 65)})
        self.assertTrue(result.is_satisfied)

    def test_spread_above_limit_is_a_violation_with_excess_as_severity(self):
        result = self.policy.evaluate({"Team 2": scored(40, 55, 58, 80)})

        self.assertEqual(len(result.violations), 1)
        self.assertEqual(result.violations[0].team_name, "Team 2")
        self.assertEqual(result.violations[0].severity, 25)   # 40 - 15

    def test_missing_scores_are_ignored_in_the_spread(self):
        team = scored(60, 65) + [{"c_score": None}, {}]
        self.assertTrue(self.policy.evaluate({"Team 1": team}).is_satisfied)

    def test_team_with_one_known_score_gets_a_note_not_a_violation(self):
        team = scored(60) + [{"c_score": None}, {}]
        result = self.policy.evaluate({"Team 6": team})

        self.assertTrue(result.is_satisfied)
        self.assertEqual(len(result.notes), 1)
        self.assertIn("Team 6", result.notes[0])

    def test_policy_is_soft_by_default(self):
        result = self.policy.evaluate({"Team 1": scored(50, 55)})
        self.assertFalse(result.is_hard)