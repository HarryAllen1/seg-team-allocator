"""Views for exporting the csv."""

from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from allocations.csv_processing import write_csv

# Temporary stand in data and will be replaced with a database query once operational.
SAMPLE_DATA = [
    ('Rahul', 'Khan', 'rahul.khan@students.example', 'Alpaca'),
    ('Rami', 'Fahmy', 'rami.fahmy@students.example', 'Alpaca'),
    ('Victoria', 'Thomas', 'victoria.thomas@students.example', 'Alpaca'),
    ('Hadi', 'Abbas', 'hadi.abbas@students.example', 'Alpaca'),
    ('Alice', 'Walker', 'alice.walker@students.example', 'Alpaca'),
    ('Daniel', 'Patel', 'daniel.patel@students.example', 'Alpaca'),
    ('Aisha', 'Malik', 'aisha.malik@students.example', 'Alpaca'),
    ('Ethan', 'Clarke', 'ethan.clarke@students.example', 'Alpaca'),
    ('Mahmoud', 'Rahim', 'mahmoud.rahim@students.example', 'Llama'),
    ('Zoya', 'Banerjee', 'zoya.banerjee@students.example', 'Llama'),
    ('Rina', 'Islam', 'rina.islam@students.example', 'Llama'),
    ('Zara', 'Chen', 'zara.chen@students.example', 'Llama'),
    ('Oscar', 'Cooper', 'oscar.cooper@students.example', 'Llama'),
    ('Maya', 'Sharma', 'maya.sharma@students.example', 'Llama'),
    ('Adam', 'Wilson', 'adam.wilson@students.example', 'Llama'),
    ('Sara', 'Hussain', 'sara.hussain@students.example', 'Llama'),
    ('Soojin', 'Ahmed', 'soojin.ahmed@students.example', 'Shark'),
    ('Luca', 'Green-Ahmed', 'luca.green.ahmed@students.example', 'Shark'),
    ('Jun', 'Bhat', 'jun.bhat@students.example', 'Shark'),
    ('Shreya', 'Chandra', 'shreya.chandra@students.example', 'Shark'),
    ('Noah', 'Brown', 'noah.brown@students.example', 'Shark'),
    ('Ananya', 'Mehta', 'ananya.mehta@students.example', 'Shark'),
    ('Leo', 'Martin', 'leo.martin@students.example', 'Shark'),
    ('Fatima', 'Ali', 'fatima.ali@students.example', 'Shark'),
    ('Arjun', 'Kapoor', 'arjun.kapoor@students.example', 'Alpaca'),
    ('Emily', 'Scott', 'emily.scott@students.example', 'Llama'),
    ('Yusuf', 'Khan', 'yusuf.khan@students.example', 'Shark'),
    ('Priya', 'Verma', 'priya.verma@students.example', 'Alpaca'),
    ('Oliver', 'James', 'oliver.james@students.example', 'Llama'),
    ('Nadia', 'Farooq', 'nadia.farooq@students.example', 'Shark'),
]


@login_required
def export_allocation(request):
    """Download the exported csv."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="output.csv"'
    write_csv(response,SAMPLE_DATA)
    return response