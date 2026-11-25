from typing import ClassVar

from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from allocations import choices


class User(AbstractUser):
    """A user of the group allocation application.

    AbstractUser already provides username, first_name, last_name, email,
    password and is_superuser (amongst others). We redefine first_name,
    last_name and email so that they are required, and so that no two users
    can share an email address.
    """

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)

    Gender = choices.Gender
    Ethnicity = choices.Ethnicity

    gender = models.PositiveSmallIntegerField(
        choices=Gender.choices,
        default=Gender.NOT_PROVIDED,
    )
    ethnicity = models.PositiveSmallIntegerField(
        choices=Ethnicity.choices,
        default=Ethnicity.NOT_PROVIDED,
    )
    # student's average mark between 0-100
    c_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )

    class Meta:
        ordering: ClassVar[list[str]] = ['last_name', 'first_name']

    def __str__(self):
        return f'{self.get_full_name()} ({self.username})'


class Team(models.Model):
    """A team whose members are users of the group allocation application."""

    name = models.CharField(max_length=100, unique=True)
    members = models.ManyToManyField(User, related_name='teams', blank=True)

    class Meta:
        ordering: ClassVar[list[str]] = ['name']

    def __str__(self):
        return self.name
