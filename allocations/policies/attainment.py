from allocations.policies.base import Policy, Violation


def known_scores(students):
    """Return the c-scores of the students who have one."""
    return [s["c_score"] for s in students if s.get("c_score") is not None]


class AttainmentSpreadPolicy(Policy):
    """Keeps prior attainment (c-score) similar within each team by checking the spread
       of the scores between the students.
    """

    name = "Prior attainment spread"

    def __init__(self, max_spread, is_hard=False, priority=1):
        super().__init__(is_hard, priority)
        self.max_spread = max_spread

    def evaluate(self, allocation):
        result = super().evaluate(allocation)
        for team_name, students in allocation.items():
            if len(known_scores(students)) < 2:
                result.notes.append(
                    f"{team_name}: fewer than two students have a c-score, "
                    f"so the spread could not be checked."
                )
        return result

    def check_team(self, team_name, students):
        scores = known_scores(students)
        if len(scores) < 2:
            return None

        lowest, highest = min(scores), max(scores)
        spread = highest - lowest
        if spread > self.max_spread:
            return Violation(
                team_name,
                f"{team_name}: c-scores range from {lowest} to {highest} "
                f"(a gap of {spread}); the limit is {self.max_spread}.",
                spread - self.max_spread,
            )
        return None