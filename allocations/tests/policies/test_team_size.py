from unittest import TestCase

from allocations.policies.team_size import TeamSizePolicy


def make_students(n):
    return [{} for i in range(n)]


class TeamSizePolicyTest(TestCase):

    def setUp(self):
        self.policy = TeamSizePolicy(min_size=4, max_size=5)

    # exactly min and exactly max are allowed

    def test_team_of_exactly_min_size_is_allowed(self):
        self.assertIsNone(self.policy.check_team("Team 1", make_students(4)))

    def test_team_of_exactly_max_size_is_allowed(self):
        self.assertIsNone(self.policy.check_team("Team 1", make_students(5)))

    # too small

    def test_team_one_below_min_is_a_violation_of_severity_one(self):
        violation = self.policy.check_team("Team 1", make_students(3))

        self.assertIsNotNone(violation)
        self.assertEqual(violation.severity, 1)

    def test_empty_team_is_a_violation_of_severity_min_size(self):
        violation = self.policy.check_team("Team 1", make_students(0))

        self.assertIsNotNone(violation)
        self.assertEqual(violation.severity, 4)

    # too big

    def test_team_two_above_max_is_a_violation_of_severity_two(self):
        violation = self.policy.check_team("Team 1", make_students(7))

        self.assertIsNotNone(violation)
        self.assertEqual(violation.severity, 2)

    # violations identify the right team and explain themselves correctly

    def test_violation_names_the_team_that_broke_the_rule(self):
        violation = self.policy.check_team("Team 9", make_students(3))

        self.assertEqual(violation.team_name, "Team 9")

    def test_violation_message_mentions_actual_size_and_limit(self):
        violation = self.policy.check_team("Team 1", make_students(7))

        self.assertIn("7", violation.message)
        self.assertIn("5", violation.message)

    # whole allocations via evaluate() 

    def test_only_the_failing_team_is_reported(self):
        allocation = {
            "Team 1": make_students(4),
            "Team 2": make_students(6),
            "Team 3": make_students(5),
        }

        result = self.policy.evaluate(allocation)

        self.assertEqual(len(result.violations), 1)
        self.assertEqual(result.violations[0].team_name, "Team 2")

    def test_allocation_with_all_valid_teams_is_satisfied(self):
        allocation = {"Team 1": make_students(4), "Team 2": make_students(5)}

        result = self.policy.evaluate(allocation)

        self.assertTrue(result.is_satisfied)

    def test_result_is_hard_by_default(self):
        result = self.policy.evaluate({"Team 1": make_students(4)})

        self.assertTrue(result.is_hard)
        self.assertEqual(result.policy_name, "Team size")


class TeamSizeFeasibilityTest(TestCase):

    def setUp(self):
        self.policy = TeamSizePolicy(min_size=4, max_size=5)

    def test_nine_students_is_feasible(self):
        self.assertTrue(self.policy.is_feasible(9))

    def test_eight_students_is_feasible(self):
        self.assertTrue(self.policy.is_feasible(8))

    def test_thirteen_students_is_feasible(self):
        self.assertTrue(self.policy.is_feasible(13))

    def test_three_hundred_students_is_feasible(self):
        self.assertTrue(self.policy.is_feasible(300))

    def test_seven_students_is_infeasible(self):
        self.assertFalse(self.policy.is_feasible(7))

    def test_eleven_students_is_infeasible(self):
        self.assertFalse(self.policy.is_feasible(11))

    def test_zero_students_is_feasible(self):
        self.assertTrue(self.policy.is_feasible(0))