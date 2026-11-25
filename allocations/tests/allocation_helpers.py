from decimal import Decimal

from allocations.models import User


def students(count=8, **changes):
    result = []
    for index in range(count):
        fields = {
            'first_name': f'Student {index}', 'last_name': 'Example',
            'username': f'student{index:04}',
            'email': f'student{index:04}@example.org',
            'c_score': Decimal(60),
        }
        fields.update(changes)
        result.append(User(**fields))
    return result
