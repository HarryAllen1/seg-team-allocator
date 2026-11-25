from unittest import TestCase

from allocations.choices import Gender
from allocations.policies.gender import GenderPolicy

W, M = Gender.WOMAN, Gender.MAN
NB, U = Gender.OTHER_NON_BINARY, Gender.NOT_PROVIDED


def person(name, gender):
    return {"first_name": name, "last_name": "Test", "gender": gender}


class GenderPolicyTest(TestCase):

    def setUp(self):
        self.policy = GenderPolicy(is_hard=False)

    def test_lone_woman_is_a_violation_when_she_could_be_paired(self):
        allocation = {
            "Team A": [person("Ada", W), person("Ben", M), person("Cal", M), person("Dan", M)],
            "Team B": [person("Eve", W), person("Fay", W), person("Gus", M), person("Hal", M)],
        }
        result = self.policy.evaluate(allocation)

        self.assertEqual(len(result.violations), 1)
        self.assertEqual(result.violations[0].team_name, "Team A")
        self.assertIn("Ada", result.violations[0].message)

    def test_mixed_team_with_no_one_alone_is_satisfied(self):
        allocation = {"Team B": [person("A", W), person("B", W),
                                 person("C", M), person("D", M), person("E", M)]}
        self.assertTrue(self.policy.evaluate(allocation).is_satisfied)

    def test_single_gender_team_is_satisfied(self):
        allocation = {"Team C": [person("A", M), person("B", M),
                                 person("C", M), person("D", U)]}
        self.assertTrue(self.policy.evaluate(allocation).is_satisfied)

    def test_unique_non_binary_student_in_diverse_team_is_satisfied(self):
        allocation = {"Team D": [person("Sam", NB), person("B", M), person("C", M),
                                 person("D", W), person("E", W)]}
        self.assertTrue(self.policy.evaluate(allocation).is_satisfied)

    def test_unique_non_binary_student_in_non_diverse_team_is_a_violation(self):
        allocation = {
            "Team E": [person("Sam", NB), person("B", U), person("C", U), person("D", U)],
            "Team X": [person("E", M), person("F", M), person("G", W), person("H", W)],
        }
        result = self.policy.evaluate(allocation)

        self.assertEqual(len(result.violations), 1)
        self.assertEqual(result.violations[0].team_name, "Team E")
        self.assertIn("Sam", result.violations[0].message)
        self.assertIn(Gender.OTHER_NON_BINARY.label, result.violations[0].message)

    def test_lone_non_binary_student_is_a_violation_when_others_exist(self):
        allocation = {
            "Team 1": [person("Sam", NB), person("B", M), person("C", M),
                       person("D", W), person("E", W)],
            "Team 2": [person("Kai", NB), person("Lee", NB), person("F", M), person("G", M)],
        }
        result = self.policy.evaluate(allocation)

        self.assertEqual(len(result.violations), 1)
        self.assertEqual(result.violations[0].team_name, "Team 1")

    def test_woman_with_only_undisclosed_teammates_is_a_violation(self):
        # Documented decision: the literal reading of the brief.
        allocation = {
            "Team F": [person("Ada", W), person("B", U), person("C", U), person("D", U)],
            "Team G": [person("E", W), person("F", W), person("G", M), person("H", M)],
        }
        result = self.policy.evaluate(allocation)

        self.assertEqual(len(result.violations), 1)
        self.assertEqual(result.violations[0].team_name, "Team F")

    def test_missing_gender_is_treated_as_undisclosed(self):
        allocation = {"Team H": [{"first_name": "Ivy"}, person("B", M),
                                 person("C", M), person("D", M)]}
        self.assertTrue(self.policy.evaluate(allocation).is_satisfied)

    def test_two_lone_students_in_one_team_give_two_violations(self):
        allocation = {
            "Team D": [person("Sam", NB), person("Ben", M), person("C", W), person("D", W)],
            "Team Y": [person("Kai", NB), person("Lee", NB), person("E", M), person("F", M)],
        }
        result = self.policy.evaluate(allocation)

        self.assertEqual(len(result.violations), 2)

    def test_result_carries_the_policy_settings(self):
        policy = GenderPolicy(is_hard=False, priority=10)
        result = policy.evaluate({"Team 1": [person("A", M), person("B", M)]})

        self.assertEqual(result.policy_name, "Gender representation")
        self.assertFalse(result.is_hard)
        self.assertEqual(result.priority, 10)