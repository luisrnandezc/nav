from django.core.management.base import BaseCommand

from sms.models import RiskEvaluationReport
from sms.rer_ai import process_rer_analysis


class Command(BaseCommand):
    help = 'Process every RER currently pending SARA residual-risk analysis.'

    def handle(self, *args, **options):
        # Materialize the small queue so status changes made during processing do
        # not alter the command's current iteration.
        pending_ids = list(
            RiskEvaluationReport.objects.filter(
                analysis_status='PENDING',
            ).order_by('created_at', 'pk').values_list('pk', flat=True)
        )

        if not pending_ids:
            self.stdout.write('No pending RER analyses found.')
            return

        completed = 0
        failed = 0

        for rer_id in pending_ids:
            try:
                process_rer_analysis(rer_id)
            except Exception as exc:
                # One failed report must not block the remaining lightweight
                # queue. The workflow records FAILED and its safe error message.
                failed += 1
                self.stderr.write(
                    self.style.ERROR(f'RER {rer_id} failed: {exc}')
                )
            else:
                completed += 1
                self.stdout.write(
                    self.style.SUCCESS(f'RER {rer_id} processed successfully.')
                )

        self.stdout.write(
            f'RER analysis summary: {completed} completed, '
            f'{failed} failed.'
        )
