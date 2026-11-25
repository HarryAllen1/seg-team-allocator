from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from allocations.choices import Ethnicity, Gender
from allocations.models import Team, User


def create_test_user():
    return User.objects.create_user(
        username='johndoe',
        first_name='John',
        last_name='Doe',
        email='johndoe@example.org',
        password='Allocation123',
    )


class TeamModelTestCase(TestCase):
    def test_team_can_have_members(self):
        team = Team.objects.create(name='Team Alpha')
        user = create_test_user()

        team.members.add(user)

        self.assertEqual(list(team.members.all()), [user])
        self.assertEqual(list(user.teams.all()), [team])

    def test_team_name_is_required_and_unique(self):
        team = Team(name='')
        with self.assertRaises(ValidationError):
            team.full_clean()

        Team.objects.create(name='Team Alpha')
        duplicate = Team(name='Team Alpha')
        with self.assertRaises(ValidationError):
            duplicate.full_clean()

    def test_c_score_must_be_between_zero_and_one_hundred(self):
        user = create_test_user()

        user.c_score = Decimal('-0.01')
        with self.assertRaises(ValidationError):
            user.full_clean()

        user.c_score = Decimal('100.01')
        with self.assertRaises(ValidationError):
            user.full_clean()

    def test_profile_attributes_are_optional(self):
        user = create_test_user()

        user.full_clean()

    def test_gender_accepts_only_defined_codes(self):
        user = create_test_user()

        for gender in Gender.values:
            user.gender = gender
            user.full_clean()

        user.gender = max(Gender.values) + 1
        with self.assertRaises(ValidationError):
            user.full_clean()

    def test_ethnicity_accepts_only_defined_codes(self):
        user = create_test_user()

        for ethnicity in Ethnicity.values:
            user.ethnicity = ethnicity
            user.full_clean()

        user.ethnicity = max(Ethnicity.values) + 1
        with self.assertRaises(ValidationError):
            user.full_clean()
