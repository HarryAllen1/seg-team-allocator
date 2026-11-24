from collections import Counter

from allocations.policies.base import Policy, PolicyResult, Violation

# Constants
UNDISCLOSED = 0
GENDER_LABELS = {1: "woman", 2: "man", 3: "non-binary student"}


def describe_student(student):
    """Return a student's full name, falling back to their email."""
    first = student.get("first_name", "")
    last = student.get("last_name", "")
    full_name = f"{first} {last}".strip()
    return full_name or student.get("email", "A student")


def gender_of(student):
    """Return the student's gender code; a missing value counts as undisclosed."""
    return student.get("gender", UNDISCLOSED)


class GenderPolicy(Policy):
    """Avoids leaving a student as the only member of their disclosed gender in a team.
    (Undisclosed gender (code 0) is ignored)
    """

    name = "Gender representation"

    def evaluate(self, allocation):
        result = PolicyResult(self.name, self.is_hard, self.priority)

        cohort_counts = Counter(
            gender_of(student)
            for students in allocation.values()
            for student in students
            if gender_of(student) != UNDISCLOSED
        )

        for team_name, students in allocation.items():
            result.violations.extend(
                self.team_violations(team_name, students, cohort_counts)
            )
        return result

    def team_violations(self, team_name, students, cohort_counts):
        """Return every gender violation in one team (there can be several)."""
        disclosed = [s for s in students if gender_of(s) != UNDISCLOSED]
        team_counts = Counter(gender_of(s) for s in disclosed)
        is_diverse = len(team_counts) > 1

        violations = []
        for student in disclosed:
            gender = gender_of(student)

            if team_counts.get(gender) != 1:
                continue

            label = GENDER_LABELS.get(gender, "student of their gender")
            name = describe_student(student)

            if team_counts.get(gender) == 1 and cohort_counts.get(gender) > 1:
                violations.append(Violation(
                    team_name,
                    f"{name} is the only {label} in {team_name}, although other "
                    f"students of the same gender in the cohort could have been "
                    f"placed with them.",
                ))
            elif not is_diverse:
                violations.append(Violation(
                    team_name,
                    f"{name} is the only {label} in the cohort and could not be "
                    f"paired, but {team_name} contains no other disclosed gender.",
                ))
        return violations