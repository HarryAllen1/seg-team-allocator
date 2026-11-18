from allocations.policies.base import Violation, Policy


class TeamSizePolicy(Policy):
    """Checks that every team's size is between the configured minimum and maximum"""

    name = "Team size"

    def __init__(self, min_size, max_size, is_hard=True, priority=1):
        super().__init__(is_hard, priority)
        self.min_size = min_size
        self.max_size = max_size

    def check_team(self, team_name, students):
        size = len(students)
        if size < self.min_size:
                difference = self.min_size - size
                return Violation(team_name, f"{team_name} has {size} students; Teams must have at least {self.min_size}", difference)
        elif size > self.max_size:
                difference = size - self.max_size
                return Violation(team_name, f"{team_name} has {size} students; Teams must have no more than {self.max_size}", difference)
        return None

    def is_feasible(self, student_count):
        """Return True if student_count students can be split into teams
        within the constraints of the team size"""

        if student_count == 0:
            return True
        max_teams = student_count // self.min_size
        for team_count in range(1, max_teams + 1):
            if student_count >= (team_count*self.min_size) and student_count <= (team_count*self.max_size):
                return True
        return False