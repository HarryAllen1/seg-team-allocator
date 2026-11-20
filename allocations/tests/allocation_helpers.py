from decimal import Decimal

from allocations.services.allocation import Student


def students(count=8, **changes):
    result = []
    for index in range(count):
        fields = {
            'first_name': f'Student {index}', 'last_name': 'Example',
            'email': f'student{index:04}@example.org',
            'c_score': Decimal('60'), 'committed': True,
        }
        fields.update(changes)
        result.append(Student(**fields))
    return result
