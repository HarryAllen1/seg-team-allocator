from collections import Counter
from dataclasses import dataclass, replace
from decimal import Decimal, InvalidOperation
from itertools import combinations
from fractions import Fraction
import re


MAX_STUDENTS = 1000
MAX_SWAP_CHECKS = 30000
MAX_SWAP_PASSES = 4
ALGORITHM_VERSION = '1'
GENDERS = ('woman', 'man', 'other', '')
ETHNICITIES = ('asian', 'black', 'mixed', 'white', 'other', '')
WORKLOADS = ('exceed', 'meet', 'reduce', '')


class AllocationError(ValueError):
    pass


@dataclass(frozen=True)
class Student:
    first_name: str
    last_name: str
    email: str
    c_score: Decimal | None = None
    committed: bool | None = None
    gender: str = ''
    workload: str = ''
    ethnicity: str = ''


@dataclass(frozen=True)
class AllocationOptions:
    c_score_target: Decimal = Decimal(10)
    use_gender: bool = True
    use_workload: bool = True
    use_ethnicity: bool = True
    use_c_score: bool = True
    commitment_mode: str = 'hard'
    min_team_size: int = 4
    max_team_size: int = 5


@dataclass(frozen=True)
class AllocationResult:
    teams: tuple[tuple[Student, ...], ...]
    metrics: tuple[dict, ...]
    warnings: tuple[str, ...]
    search_limited: bool


def percentage(value, label):
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
        raise AllocationError(f'{label} must be a number between 0 and 100.')
    try:
        number = Decimal(str(value))
    except InvalidOperation:
        raise AllocationError(f'{label} must be a number between 0 and 100.') from None
    if not number.is_finite() or not 0 <= number <= 100:
        raise AllocationError(f'{label} must be a number between 0 and 100.')
    if number != number.quantize(Decimal('0.01')):
        raise AllocationError(f'{label} must have at most two decimal places.')
    return number


def validate_options(options):
    if not isinstance(options, AllocationOptions):
        raise AllocationError('Allocation options are invalid.')
    for field in ('use_gender', 'use_workload', 'use_ethnicity', 'use_c_score'):
        if type(getattr(options, field)) is not bool:
            raise AllocationError(f'{field} must be true or false.')
    if options.commitment_mode not in ('hard', 'soft', 'ignore'):
        raise AllocationError('Choose hard, soft or ignored commitment.')
    for size in (options.min_team_size, options.max_team_size):
        if type(size) is not int or not 1 <= size <= 10:
            raise AllocationError('Team size limits must be whole numbers from 1 to 10.')
    if options.min_team_size > options.max_team_size:
        raise AllocationError('Minimum team size cannot exceed maximum team size.')
    return replace(options, c_score_target=percentage(options.c_score_target, 'C-score target'))


def validate_students(students):
    try:
        students = iter(students)
    except TypeError:
        raise AllocationError('The cohort must be a collection of students.') from None
    cleaned = []
    emails = set()
    for index, student in enumerate(students, start=1):
        if index > MAX_STUDENTS:
            raise AllocationError(f'A cohort can contain at most {MAX_STUDENTS} students.')
        if not isinstance(student, Student):
            raise AllocationError(f'Student {index} is invalid.')
        names = {}
        for field in ('first_name', 'last_name'):
            value = getattr(student, field)
            if not isinstance(value, str) or not value.strip() or len(value.strip()) > 50:
                raise AllocationError(f'Student {index}: {field} is required and must fit in 50 characters.')
            names[field] = value.strip()
        email = student.email
        if not isinstance(email, str) or len(email.strip()) > 254 or not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', email.strip()):
            raise AllocationError(f'Student {index}: provide a valid email address.')
        # check for duplicates after normalising so case and spaces cannot hide them
        email = email.strip().casefold()
        if email in emails:
            raise AllocationError(f'Duplicate student email: {email}.')
        emails.add(email)
        if student.committed is not None and type(student.committed) is not bool:
            raise AllocationError(f'Student {index}: commitment must be answered yes or no.')
        for field, choices in (('gender', GENDERS), ('workload', WORKLOADS), ('ethnicity', ETHNICITIES)):
            if getattr(student, field) not in choices:
                raise AllocationError(f'Student {index}: invalid {field}.')
        mark = percentage(student.c_score, f'Student {index} C-score') if student.c_score is not None else None
        cleaned.append(replace(student, **names, email=email, c_score=mark))
    if not cleaned:
        raise AllocationError('The cohort is empty. Provide at least one student.')
    return cleaned


def gender_issues(team):
    counts = Counter(student.gender for student in team if student.gender)
    affected = []
    for student in team:
        if student.gender in ('woman', 'man') and counts[student.gender] == 1:
            affected.append(student.email)
        elif student.gender == 'other' and counts['other'] == 1 and len(counts) < 2:
            affected.append(student.email)
    return affected


def team_cost(team, options):
    size = len(team)
    high = 0
    if options.use_c_score:
        spread = max(student.c_score for student in team) - min(student.c_score for student in team)
        excess = max(Decimal(0), spread - options.c_score_target)
        # scale the mark penalty so hundredths of a mark count in the integer score
        high += size * int(excess * 100)
    if options.use_gender:
        high += 10000 * len(gender_issues(team))
    if options.commitment_mode == 'soft':
        commitments = Counter(s.committed for s in team if s.committed is not None)
        high += 10000 * (sum(commitments.values()) - max(commitments.values(), default=0))

    low = Fraction(0)
    if options.use_workload:
        workload_values = {'reduce': 0, 'meet': 1, 'exceed': 2}
        pairs = list(combinations([workload_values[s.workload] for s in team if s.workload], 2))
        if pairs:
            low += size * Fraction(sum(abs(a - b) for a, b in pairs), 2 * len(pairs))
    if options.use_ethnicity:
        pairs = list(combinations([s.ethnicity for s in team if s.ethnicity], 2))
        if pairs:
            low += size * Fraction(sum(a == b for a, b in pairs), len(pairs))
    # the lower tier only decides between equal higher tier costs
    return high, low


def team_metrics(team, options):
    marks = [student.c_score for student in team if student.c_score is not None]
    commitments = {student.committed for student in team if student.committed is not None}
    workloads = [student.workload for student in team if student.workload]
    ethnicities = [student.ethnicity for student in team if student.ethnicity]
    high, low = team_cost(team, options)
    return {
        'size': len(team),
        'commitment_label': 'Mixed' if len(commitments) > 1 else ('Yes' if True in commitments else ('No' if False in commitments else 'Unanswered')),
        'mixed_commitment': options.commitment_mode != 'ignore' and len(commitments) > 1,
        'c_score_min': str(min(marks)) if marks else None,
        'c_score_max': str(max(marks)) if marks else None,
        'c_score_spread': str(max(marks) - min(marks)) if marks else None,
        'c_score_exceeded': options.use_c_score and bool(marks) and max(marks) - min(marks) > options.c_score_target,
        'gender_issues': gender_issues(team) if options.use_gender else [],
        'workload_mismatched_pairs': sum(a != b for a, b in combinations(workloads, 2)) if options.use_workload else 0,
        'ethnicity_repeated_pairs': sum(a == b for a, b in combinations(ethnicities, 2)) if options.use_ethnicity else 0,
        'high_penalty': high,
        'low_penalty': str(low),
    }


def _initial_teams(students, options):
    ordered = sorted(students, key=lambda student: (student.c_score if options.use_c_score else 0, student.email))
    # for the first n students keep the best cost and size of the last team
    costs = [None] * (len(ordered) + 1)
    previous = [None] * len(costs)
    costs[0] = (0, 0)
    for end in range(options.min_team_size, len(costs)):
        for size in range(options.max_team_size, options.min_team_size - 1, -1):
            start = end - size
            if start < 0 or costs[start] is None:
                continue
            high, low = team_cost(ordered[start:end], options)
            candidate = (costs[start][0] + high, costs[start][1] + low)
            if costs[end] is None or candidate < costs[end]:
                costs[end] = candidate
                previous[end] = size
    if costs[-1] is None:
        group = f'commitment {"Yes" if students[0].committed else "No"} group' if options.commitment_mode == 'hard' else 'cohort'
        raise AllocationError(
            f'The {group} has {len(students)} students and cannot form teams of {options.min_team_size} to {options.max_team_size}. '
            'No allocation was produced. Review the cohort or policy settings.'
        )
    teams = []
    end = len(ordered)
    while end:
        size = previous[end]
        teams.append(ordered[end - size:end])
        end -= size
    return list(reversed(teams))


def _improve_teams(teams, options):
    costs = [team_cost(team, options) for team in teams]
    checks = 0
    for _ in range(MAX_SWAP_PASSES):
        changed = False
        # try nearby mark bands first because distant swaps can widen the score spread
        for distance in range(1, len(teams)):
            for left in range(len(teams) - distance):
                right = left + distance
                for a in range(len(teams[left])):
                    for b in range(len(teams[right])):
                        if checks >= MAX_SWAP_CHECKS:
                            return teams, True
                        checks += 1
                        # only the two teams in the swap can change the total cost
                        old = (costs[left][0] + costs[right][0], costs[left][1] + costs[right][1])
                        teams[left][a], teams[right][b] = teams[right][b], teams[left][a]
                        left_cost = team_cost(teams[left], options)
                        right_cost = team_cost(teams[right], options)
                        new = (left_cost[0] + right_cost[0], left_cost[1] + right_cost[1])
                        if new < old:
                            costs[left], costs[right] = left_cost, right_cost
                            changed = True
                        else:
                            teams[left][a], teams[right][b] = teams[right][b], teams[left][a]
        if not changed:
            return teams, False
    return teams, True


def allocate_students(students, options=AllocationOptions()):
    options = validate_options(options)
    students = validate_students(students)
    for student in students:
        if options.use_c_score and student.c_score is None:
            raise AllocationError(f'{student.email}: C-score is required when prior attainment is considered.')
        if options.commitment_mode == 'hard' and student.committed is None:
            raise AllocationError(f'{student.email}: commitment must be answered for hard commitment matching.')
    teams = []
    search_limited = False
    initial_groups = []
    # check every group can form teams before beginning to work on swaps
    if options.commitment_mode == 'hard':
        for committed in (True, False):
            group = [student for student in students if student.committed == committed]
            if group:
                initial_groups.append(_initial_teams(group, options))
    else:
        initial_groups.append(_initial_teams(students, options))
    for initial in initial_groups:
        improved, limited = _improve_teams(initial, options)
        teams.extend(improved)
        search_limited = search_limited or limited
    teams = tuple(tuple(sorted(team, key=lambda student: student.email)) for team in teams)
    metrics = tuple(team_metrics(team, options) for team in teams)
    warnings = allocation_warnings(metrics, options)
    if search_limited:
        warnings.append('The improvement search reached its limit. Further improvements may be possible.')
    return AllocationResult(teams, metrics, tuple(warnings), search_limited)


def allocation_warnings(metrics, options):
    warnings = []
    for number, metric in enumerate(metrics, start=1):
        if metric['c_score_exceeded']:
            warnings.append(f'Team {number}: C-score spread {metric["c_score_spread"]} exceeds the target {options.c_score_target}.')
        if metric['gender_issues']:
            warnings.append(f'Team {number}: gender preference unmet for {", ".join(metric["gender_issues"])}.')
        if metric['mixed_commitment']:
            warnings.append(f'Team {number}: commitment answers differ.')
        if metric['workload_mismatched_pairs']:
            warnings.append(f'Team {number}: workload answers differ in {metric["workload_mismatched_pairs"]} student pair(s).')
        if metric['ethnicity_repeated_pairs']:
            warnings.append(f'Team {number}: {metric["ethnicity_repeated_pairs"]} student pair(s) share an ethnicity category.')
    return warnings
