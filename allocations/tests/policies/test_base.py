from unittest import TestCase

from allocations.policies.base import Violation, PolicyResult


class PoliciesBaseTest(TestCase):

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