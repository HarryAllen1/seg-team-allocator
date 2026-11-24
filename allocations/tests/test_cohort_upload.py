from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from allocations.models import User

PASSWORD = 'Allocation123'
GOOD_FILE = (
    b'first_name,last_name,email,gender,ethnicity,c-score,programme\n'
    b'Ann,Lee,ann@x.ac.uk,1,4,70,Maths\n'
    b'Bob,Ng,bob@x.ac.uk,2,1,55,CS\n'
)
BAD_FILE = (
    b'first_name,last_name,email,gender,ethnicity,c-score\nAnn,Lee,ann@x.ac.uk,9,4,170\nBob,Ng,ann@x.ac.uk,2,1,55\n'
)


class UploadCohortViewTests(TestCase):
    """Tests for uploading a cohort CSV file, which creates and updates students (users)."""

    def setUp(self):
        self.user = User.objects.create_user(
            'johndoe', password=PASSWORD, first_name='John', last_name='Doe', email='john@x.ac.uk'
        )
        self.url = reverse('upload_cohort')
        self.client.login(username='johndoe', password=PASSWORD)

    def upload(self, content, name='cohort.csv'):
        return self.client.post(self.url, {'file': SimpleUploadedFile(name, content)}, follow=True)

    def test_requires_log_in(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, f'{reverse("log_in")}?next={self.url}', fetch_redirect_response=False)

    def test_get_shows_upload_form(self):
        self.assertContains(self.client.get(self.url), 'Upload and validate')

    def test_valid_file_creates_students(self):
        response = self.upload(GOOD_FILE)
        self.assertContains(response, 'Imported 2 students: 2 new, 0 updated.')
        ann = User.objects.get(email='ann@x.ac.uk')
        self.assertEqual((ann.first_name, ann.gender, ann.ethnicity, ann.c_score), ('Ann', 1, 4, Decimal(70)))
        self.assertEqual(ann.username, 'ann@x.ac.uk')
        self.assertFalse(ann.has_usable_password())
        self.assertFalse(ann.is_staff)
        self.assertEqual(User.objects.get(email='bob@x.ac.uk').c_score, Decimal(55))

    def test_unstored_extra_columns_are_reported(self):
        self.assertContains(self.upload(GOOD_FILE), 'programme were accepted but are not stored yet')

    def test_existing_student_is_updated_not_duplicated(self):
        User.objects.create_user('ann', first_name='Old', last_name='Name', email='Ann@X.ac.uk')
        response = self.upload(GOOD_FILE)
        self.assertContains(response, '1 new, 1 updated')
        self.assertEqual(User.objects.filter(email__iexact='ann@x.ac.uk').count(), 1)
        ann = User.objects.get(username='ann')
        self.assertEqual((ann.first_name, ann.email, ann.c_score), ('Ann', 'ann@x.ac.uk', Decimal(70)))

    def test_users_missing_from_the_file_are_left_alone(self):
        User.objects.create_user('zed', first_name='Zed', last_name='Z', email='zed@x.ac.uk')
        self.upload(GOOD_FILE)
        self.assertTrue(User.objects.filter(username='zed').exists())

    def test_staff_email_in_file_is_an_error_and_nothing_is_saved(self):
        # johndoe is not staff here, so make a superuser whose email appears in the file.
        User.objects.create_superuser('boss', first_name='Bo', last_name='Ss', email='bob@x.ac.uk', password=PASSWORD)
        response = self.upload(GOOD_FILE)
        self.assertContains(response, 'belongs to a staff account')
        self.assertFalse(User.objects.filter(email='ann@x.ac.uk').exists())
        self.assertEqual(User.objects.get(username='boss').first_name, 'Bo')

    def test_username_clash_is_an_error(self):
        User.objects.create_user('ann@x.ac.uk', first_name='Other', last_name='Person', email='other@x.ac.uk')
        response = self.upload(GOOD_FILE)
        self.assertContains(response, 'already used by another account')
        self.assertFalse(User.objects.filter(email='ann@x.ac.uk').exists())

    def test_invalid_file_imports_nothing_and_lists_problems(self):
        before = User.objects.count()
        response = self.upload(BAD_FILE)
        self.assertContains(response, 'The file was not imported.')
        self.assertContains(response, 'Duplicate email')
        self.assertContains(response, 'not a valid gender code')
        self.assertEqual(User.objects.count(), before)

    def test_file_without_csv_extension_is_rejected(self):
        response = self.upload(GOOD_FILE, name='cohort.xlsx')
        self.assertContains(response, '.csv extension')
        self.assertEqual(User.objects.count(), 1)

    def test_warnings_are_shown_after_a_successful_import(self):
        response = self.upload(b'first_name,last_name,email\nAnn,Lee,ann@x.ac.uk\n')
        self.assertContains(response, 'Imported 1 student: 1 new, 0 updated.')
        self.assertContains(response, 'No &#x27;gender&#x27; column')
        self.assertContains(response, 'alert-warning')
