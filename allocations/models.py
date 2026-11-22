from typing import ClassVar

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator


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
    class Gender(models.IntegerChoices):
        NOT_PROVIDED = 0, 'Not provided'
        WOMAN = 1, 'Woman'
        MAN = 2, 'Man'
        OTHER_NON_BINARY = 3, 'Other/Non-binary'

    class Ethnicity(models.IntegerChoices):
        NOT_PROVIDED = 0, 'Not provided'
        ASIAN = 1, 'Asian, or Asian British'
        BLACK = 2, 'Black, Black British, Caribbean, or African'
        MIXED = 3, 'Mixed, or multiple ethnic groups'
        WHITE = 4, 'White'
        OTHER = 5, 'Other ethnic group (e.g. Arab)'

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
        ordering = ['name']

    def __str__(self):
        return self.name
