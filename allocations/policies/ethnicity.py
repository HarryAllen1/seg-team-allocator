from allocations.policies.base import Policy, PolicyResult, Violation


# Constants
UNDISCLOSED = 0
ETHNICITY_LABELS = {1: "Asian", 2: "Black", 3: "Mixed", 4: "White", 5: "Other"}


def ethnicity_of(student):
    """Return the student's ethnicity code; a missing value counts as undisclosed."""
    return student.get("ethnicity", UNDISCLOSED)


class EthnicityDiversityPolicy(Policy):
    """Promotes diversity of disclosed ethnicity within each team.

    Diversity is measured as the number of different disclosed ethnicity
    categories in a team. A team violates the policy when it has fewer than
    min_categories. Undisclosed ethnicity (code 0) is ignored. If the whole
    cohort has fewer categories than min_categories, the requirement is lowered
    to what the cohort can provide. A team with too few disclosed students to
    reach the requirement gets a note instead of a violation.
    """

    name = "Ethnicity diversity"

    def __init__(self, min_categories=2, is_hard=False, priority=1):
        super().__init__(is_hard, priority)
        self.min_categories = min_categories

    def evaluate(self, allocation):
        result = PolicyResult(self.name, self.is_hard, self.priority)

        cohort_categories = {
            ethnicity_of(student)
            for students in allocation.values()
            for student in students
            if ethnicity_of(student) != UNDISCLOSED
        }
        required = min(self.min_categories, len(cohort_categories))
        if required < self.min_categories:
            result.notes.append(
                f"The cohort only has {len(cohort_categories)} disclosed ethnicity "
                f"categories, so each team is expected to have {required}."
            )

        for team_name, students in allocation.items():
            disclosed = [ethnicity_of(s) for s in students if ethnicity_of(s) != UNDISCLOSED]
            categories = set(disclosed)

            if len(disclosed) < required:
                result.notes.append(
                    f"{team_name}: only {len(disclosed)} student(s) disclosed an "
                    f"ethnicity, so diversity could not be fully checked."
                )
                continue

            if len(categories) < required:
                names = ", ".join(sorted(ETHNICITY_LABELS.get(c, "Unknown") for c in categories))
                result.violations.append(Violation(
                    team_name,
                    f"{team_name} has {len(categories)} disclosed ethnicity "
                    f"category/categories ({names}); at least {required} expected.",
                    required - len(categories),
                ))
        return result