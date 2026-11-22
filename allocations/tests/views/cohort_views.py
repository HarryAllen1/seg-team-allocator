"""Views for importing the cohort of students to allocate."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from allocations.forms import CohortUploadForm
from allocations.services.cohort_store import save_students
from allocations.services.csv_import import parse_cohort_csv

# Show at most this many problems on screen. The total is always shown.
MAX_ISSUES_SHOWN = 100


@login_required
def upload_cohort(request):
    """Let a user upload a cohort CSV file, validate it and import its students."""
    result = None
    if request.method == 'POST':
        form = CohortUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # Parsing and validating do not touch the database, so no transaction is open while they run.
            result = parse_cohort_csv(form.cleaned_data['file'].read())
            counts = save_students(result) if result.is_valid else None
            if counts is not None:
                created, updated = counts
                noun = 'student' if created + updated == 1 else 'students'
                messages.success(request, f'Imported {created + updated} {noun}: {created} new, {updated} updated.')
                for warning in result.warnings:
                    messages.warning(request, warning.message)
                if result.extra_columns:
                    columns = ', '.join(result.extra_columns)
                    messages.warning(request, f'The columns {columns} were accepted but are not stored yet.')
                return redirect('upload_cohort')
    else:
        form = CohortUploadForm()
    context = {'form': form, 'result': result, 'max_shown': MAX_ISSUES_SHOWN}
    return render(request, 'upload_cohort.html', context)
