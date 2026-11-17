# Group Allocation system by Team Kangaroo

A group allocation system developed for the Small Group Project assignment of the Software Engineering Group Project module at King's College London.

## Team members

The members of the team are, in alphabetical order:

- Acelya Oksuz
- Harry Allen
- Maylin Kottarathil
- Ssuhaan Jaiin
- Vivash Pitroda

## Deployment

The system has been deployed at [_insert url here_](*url*)

## Getting started

```
python3.12 -m venv venv
source venv/bin/activate          # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed             # Adds sample users
python manage.py runserver
```

Then open <http://127.0.0.1:8000/> and log in as `janedoe` (a superuser) or
`johndoe` (a normal user). Both have the password `Allocation123`.

Run `python manage.py unseed` to delete all users again.

## Tests

Run all tests with `python manage.py test`. You can also run a part of them,
for example `python manage.py test allocations.tests.views`.

[Coverage.py](https://coverage.readthedocs.io/) measures which parts of the
code the tests run. Its settings are in `.coveragerc`.

```
coverage run manage.py test       # Run the tests while measuring coverage
coverage report                   # Show the coverage of each file
coverage html                     # Write a detailed report to htmlcov/
```

Open `htmlcov/index.html` in a browser to see exactly which lines and
branches are not tested. The report leaves out code that is not ours or that
is not worth testing, such as the virtual environment, migrations, settings
and the tests themselves.

# Algorithm allocation
Worked on the design, core allocator and respective tests.

## How it works

The allocator takes Student records and AllocationOptions, checks the inputs in memory and returns teams, measurements, warnings and search-limit status. It checks duplicate identifiers and the values needed based on the criteria.

Default team size is 4-5, and commitment is matched. Team size can be set from 1–10. Commitment can be hard matching, soft matching or ignored. Gender, attainment, workload and ethnicity can all be toggled.

The allocator asks which team arrangement would be better overall for gender and C-score, and chooses the result. If they are equally as good, then the allocator asks which one is better for workload and ethnicity, and then that one will be chosen. There is no strict ordering between gender and C-score or workload and ethnicity as well.


## Tests

Wrote tests on 
- Checking team size 
- Checking the matching of commitment 
- Checking the handling of missing/invalid values
