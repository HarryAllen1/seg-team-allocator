"""Convert other parts of the system's data - i.e. the allocator - into the format the policies take."""

STUDENT_FIELDS = ("first_name", "last_name", "email", "gender", "c_score")


def student_to_dict(student):
    """Turn any object with the student fields into the dict the policies use."""
    return {field: getattr(student, field) for field in STUDENT_FIELDS}


def teams_to_allocation(teams):
    """Turn a sequence of teams (each a sequence of students) into a named allocation.

    Teams are named "Team 1", "Team 2", ... in the order given, matching the
    numbering the allocator uses in its warnings.
    """
    return {
        f"Team {number}": [student_to_dict(student) for student in team]
        for number, team in enumerate(teams, start=1)
    }