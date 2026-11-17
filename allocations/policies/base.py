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
    violations: list[Violation] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def is_satisfied(self) -> bool:
        return len(self.violations) == 0