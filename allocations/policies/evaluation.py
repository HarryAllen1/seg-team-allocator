from dataclasses import dataclass

from allocations.policies.base import PolicyResult


@dataclass
class PolicyEvaluation:
    """The combined result of checking an allocation against each of the policies"""

    results: list[PolicyResult]

    @property
    def is_valid(self):
        """An allocation is valid when every hard policy is satisfied."""
        return all(r.is_satisfied for r in self.results if r.is_hard)

    @property
    def soft_results(self):
        return [r for r in self.results if not r.is_hard]

    @property
    def penalty(self):
        """Total of priority x severity over all soft violations (lower is better)."""
        return sum(
            result.priority * violation.severity
            for result in self.soft_results
            for violation in result.violations
        )

    @property
    def soft_violations_by_priority(self):
        """(result, violation) pairs, most important first, for the inspect page."""
        pairs = [(r, v) for r in self.soft_results for v in r.violations]
        return sorted(pairs, key=lambda pair: pair[0].priority, reverse=True)


def evaluate_policies(policies, allocation):
    """Evaluate every policy against the allocation."""
    return PolicyEvaluation([policy.evaluate(allocation) for policy in policies])