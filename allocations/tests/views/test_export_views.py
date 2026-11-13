"""Tests of the export view in allocations/views/export_views.py."""

from django.test import TestCase
from django.urls import reverse

from allocations.tests.helpers import create_user, log_in_url_for
from allocations.views.export_views import SAMPLE_DATA


class ExportAllocationViewTestCase(TestCase):
    """Tests of the view that downloads an allocation as a CSV file."""

    def setUp(self):
        self.url = reverse('export_allocation')
        self.user = create_user()
        self.client.force_login(self.user)

    def get_lines(self):
        response = self.client.get(self.url)
        return response.content.decode().splitlines()

    def test_export_url(self):
        self.assertEqual(self.url, '/export_allocation/')

    def test_get_requires_log_in(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, log_in_url_for(self.url))

    def test_normal_user_can_download(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_response_is_csv(self):
        response = self.client.get(self.url)
        self.assertEqual(response['Content-Type'], 'text/csv')

    def test_response_is_a_download(self):
        response = self.client.get(self.url)
        self.assertTrue(response['Content-Disposition'].startswith('attachment'))

    def test_file_starts_with_the_prescribed_header(self):
        self.assertEqual(self.get_lines()[0], 'first_name,last_name,email,team')

    def test_file_has_one_line_per_student(self):
        self.assertEqual(len(self.get_lines()), len(SAMPLE_DATA) + 1)

    def test_every_student_appears_exactly_once(self):
        emails = [line.split(',')[2] for line in self.get_lines()[1:]]
        self.assertEqual(len(emails), len(set(emails)))

    def test_dashboard_links_to_the_export(self):
        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, self.url)
