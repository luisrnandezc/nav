from django.contrib import admin
from django.test import SimpleTestCase

from fms.models import FlightReport


class FlightReportAdminTests(SimpleTestCase):
    def test_change_form_uses_only_existing_model_fields(self):
        model_admin = admin.site._registry[FlightReport]

        form = model_admin.get_form(request=None)

        self.assertNotIn('aura_processed', form.base_fields)
        self.assertIn('comments', form.base_fields)
