"""Saving a validated cohort to the database.

This is separate from csv_import.py so that parsing and validating a file can
be tested, and reused, without a database.
"""

from django.db import transaction
from django.db.models.functions import Lower

from allocations.models import User
from allocations.services.csv_import import ImportIssue, ImportResult

STUDENT_FIELDS = ['first_name', 'last_name', 'email', 'gender', 'ethnicity', 'c_score']


def save_students(result: ImportResult) -> tuple[int, int] | None:
    """Create or update a user for every student of a valid import result.

    Students are users of the application. They are matched on email address,
    ignoring case: a student whose email is already in the database is updated
    from the file, any other student gets a new account with an unusable
    password (students do not log in). Users who are not in the file are never
    changed or deleted.

    The import is all or nothing. Staff accounts must never be overwritten by a
    cohort file, so an email that belongs to a staff member (or a username that
    another account already uses) is added to ``result.errors``, and then
    nothing is saved and None is returned. Otherwise returns a tuple with the
    number of users created and updated.
    """
    if not result.is_valid:
        raise ValueError('Refusing to save a cohort that failed validation.')

    emails = [row.email for row in result.students]
    existing = {
        user.email.lower(): user
        for user in User.objects.annotate(lower_email=Lower('email')).filter(lower_email__in=emails)
    }
    new_emails = [email for email in emails if email not in existing]
    usernames_in_use = set(User.objects.filter(username__in=new_emails).values_list('username', flat=True))

    for row in result.students:
        user = existing.get(row.email)
        if user is not None and (user.is_staff or user.is_superuser):
            message = f"'{row.email}' belongs to a staff account, which a cohort file cannot change."
        elif user is None and row.email in usernames_in_use:
            message = f"The username '{row.email}' is already used by another account."
        else:
            continue
        result.errors.append(ImportIssue(message, row=row.row_number, column='email'))
    if not result.is_valid:
        return None

    to_create, to_update = [], []
    for row in result.students:
        user = existing.get(row.email)
        if user is None:
            user = User(username=row.email)
            user.set_unusable_password()
            to_create.append(user)
        else:
            to_update.append(user)
        user.first_name = row.first_name
        user.last_name = row.last_name
        user.email = row.email
        user.gender = row.gender
        user.ethnicity = row.ethnicity
        user.c_score = row.c_score

    with transaction.atomic():
        User.objects.bulk_create(to_create, batch_size=200)
        User.objects.bulk_update(to_update, STUDENT_FIELDS, batch_size=200)
    return len(to_create), len(to_update)
