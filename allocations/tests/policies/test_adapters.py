from types import SimpleNamespace
from unittest import TestCase

from allocations.policies.adapters import student_to_dict, teams_to_allocation


def fake_student(email, gender=0, c_score=None):
    return SimpleNamespace(first_name="A", last_name="B", email=email,
                           gender=gender, c_score=c_score, ethnicity=0)


class AdaptersTest(TestCase):

    def test_student_becomes_a_dict_with_the_policy_fields(self):
        result = student_to_dict(fake_student("a@x.ac.uk", gender=1, c_score=60))
        self.assertEqual(result["email"], "a@x.ac.uk")
        self.assertEqual(result["gender"], 1)
        self.assertEqual(result["c_score"], 60)

    def test_teams_are_named_in_order(self):
        teams = [(fake_student("a@x"),), (fake_student("b@x"),)]
        allocation = teams_to_allocation(teams)
        self.assertEqual(list(allocation), ["Team 1", "Team 2"])

    def test_every_student_appears_exactly_once(self):
        teams = [(fake_student("a@x"), fake_student("b@x")), (fake_student("c@x"),)]
        allocation = teams_to_allocation(teams)
        emails = [s["email"] for team in allocation.values() for s in team]
        self.assertEqual(sorted(emails), ["a@x", "b@x", "c@x"])