from dataclasses import dataclass, field


@dataclass(frozen=True)
class Violation:
    team_name: str
    message: str
    severity: int = 1


@dataclass
class PolicyResult:
    policy_name: str
    is_hard: bool
    priority: int = 1
    violations: list[Violation] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def is_satisfied(self):
        return len(self.violations) == 0


class Policy:
    name = "Policy"

    def __init__(self, is_hard, priority=1):
        self.is_hard = is_hard
        self.priority = priority

    def evaluate(self, allocation):
        result = PolicyResult(self.name, self.is_hard, self.priority)
        for team_name, students in allocation.items():
            v = self.check_team(team_name,students)
            if v is not None:
                result.violations.append(v)
        return result

    def check_team(self, team_name, students):
        raise NotImplementedError

