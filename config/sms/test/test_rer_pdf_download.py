from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from sms.test.factories import (
    RiskEvaluationReportFactory,
    StaffUserFactory,
    VoluntaryHazardReportFactory,
)


class TestRERPDFDownload(TestCase):
    def setUp(self):
        self.user = StaffUserFactory(is_staff=True, is_superuser=True)
        self.client.force_login(self.user)
        self.report = VoluntaryHazardReportFactory(
            code='SMS-RVP-2026-001',
            is_processed=True,
        )
        self.rer = RiskEvaluationReportFactory(
            report=self.report,
            analysis_status='REVIEWED',
            reviewed_by=self.user,
            reviewed_at=timezone.now(),
        )
        self.url = reverse('sms:generate_rer_pdf', args=[self.rer.id])

    @patch('sms.views.render_rer_pdf', return_value=b'%PDF-1.7 test')
    def test_reviewed_rer_downloads_as_pdf(self, render_pdf):
        response = self.client.get(self.url)

        assert response.status_code == 200
        assert response['Content-Type'] == 'application/pdf'
        assert response.content.startswith(b'%PDF')
        assert response['Content-Disposition'] == (
            'attachment; filename="rer_sms-rvp-2026-001_'
            f'{self.rer.registration_date:%Y%m%d}.pdf"'
        )
        render_pdf.assert_called_once()
        assert render_pdf.call_args.args[0].id == self.rer.id

    @patch('sms.views.render_rer_pdf')
    def test_unreviewed_rer_is_not_rendered(self, render_pdf):
        self.rer.analysis_status = 'READY_FOR_REVIEW'
        self.rer.save(update_fields=['analysis_status'])

        response = self.client.get(self.url)

        assert response.status_code == 302
        assert response.url == reverse('sms:rer_dashboard')
        render_pdf.assert_not_called()

    @patch('sms.views.render_rer_pdf')
    def test_user_without_sms_permission_cannot_download(self, render_pdf):
        user_without_permission = StaffUserFactory()
        self.client.force_login(user_without_permission)

        response = self.client.get(self.url)

        assert response.status_code == 302
        assert response.url == reverse('sms:rer_dashboard')
        render_pdf.assert_not_called()

    @patch('sms.views.logging.getLogger')
    @patch('sms.views.render_rer_pdf', side_effect=ValueError('Invalid RER'))
    def test_rendering_error_returns_to_dashboard(self, render_pdf, get_logger):
        response = self.client.get(self.url)

        assert response.status_code == 302
        assert response.url == reverse('sms:rer_dashboard')
        render_pdf.assert_called_once()
        get_logger.return_value.exception.assert_called_once()

    def test_completed_dashboard_card_shows_pdf_download(self):
        response = self.client.get(reverse('sms:rer_dashboard'))

        self.assertContains(response, self.url)
        self.assertContains(response, 'Descargar PDF')

    def test_pending_review_card_does_not_show_pdf_download(self):
        self.rer.analysis_status = 'READY_FOR_REVIEW'
        self.rer.save(update_fields=['analysis_status'])

        response = self.client.get(reverse('sms:rer_dashboard'))

        self.assertNotContains(response, self.url)
        self.assertNotContains(response, 'Descargar PDF')
