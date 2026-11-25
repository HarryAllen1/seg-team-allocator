from unittest import TestCase

from allocations.policies.base import Policy, PolicyResult, Violation


class PolicyResultTest(TestCase):

    def test_result_with_no_violations_is_satisfied(self):
        result = PolicyResult("Team size", True)
        self.assertTrue(result.is_satisfied)

    def test_result_with_a_violation_is_not_satisfied(self):
        result = PolicyResult("Team size", True)
        result.violations.append(Violation("Team 2", "Too small"))
        self.assertFalse(result.is_satisfied)

    def test_result_with_only_notes_is_satisfied(self):
        result = PolicyResult("Team size", True)
        result.notes.append("Team 6: only one student has a c-score, so the spread could not be checked.")
        self.assertTrue(result.is_satisfied)


class FakePolicy(Policy):
    """A minimal policy used only to test the Policy base class."""

    name = "Fake policy"

    def check_team(self, team_name, students):
        if team_name == "Bad team":
            return Violation(team_name, "This team is bad.")
        return None


class PolicyTest(TestCase):

    def test_evaluate_reports_only_the_failing_team(self):
        policy = FakePolicy(is_hard=True)
        allocation = {"Bad team": [], "Good team": []}

        result = policy.evaluate(allocation)

        self.assertEqual(len(result.violations), 1)
        self.assertEqual(result.violations[0].team_name, "Bad team")
        self.assertFalse(result.is_satisfied)

    def test_result_carries_the_policy_settings(self):
        policy = FakePolicy(is_hard=False, priority=5)

        result = policy.evaluate({"Good team": []})

        self.assertEqual(result.policy_name, "Fake policy")
        self.assertFalse(result.is_hard)
        self.assertEqual(result.priority, 5)

    def test_priority_defaults_to_one(self):
        policy = FakePolicy(is_hard=True)

        result = policy.evaluate({"Good team": []})

        self.assertEqual(result.priority, 1)

    def test_empty_allocation_is_satisfied(self):
        policy = FakePolicy(is_hard=True)

        result = policy.evaluate({})

        self.assertTrue(result.is_satisfied)

    def test_base_policy_cannot_check_a_team_itself(self):
        policy = Policy(is_hard=True)

        with self.assertRaises(NotImplementedError):
            policy.evaluate({"Team 1": []})

