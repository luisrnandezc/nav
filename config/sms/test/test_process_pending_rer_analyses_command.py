from io import StringIO
from unittest.mock import call, patch

from django.core.management import call_command
from django.test import TestCase

from sms.services.rer_openai_analysis import RERAnalysisServiceError
from sms.test.factories import RiskEvaluationReportFactory


WORKFLOW_PATH = (
    'sms.management.commands.process_pending_rer_analyses.'
    'process_pending_rer_analysis'
)


class TestProcessPendingRERAnalysesCommand(TestCase):
    @patch(WORKFLOW_PATH)
    def test_processes_pending_rers_in_creation_order(self, process_analysis):
        first = RiskEvaluationReportFactory(analysis_status='PENDING')
        second = RiskEvaluationReportFactory(analysis_status='PENDING')
        stdout = StringIO()

        call_command('process_pending_rer_analyses', stdout=stdout)

        assert process_analysis.call_args_list == [call(first.pk), call(second.pk)]
        assert '2 completed, 0 failed, 0 skipped' in stdout.getvalue()

    @patch(WORKFLOW_PATH)
    def test_ignores_rers_that_are_not_pending(self, process_analysis):
        RiskEvaluationReportFactory(analysis_status='DRAFT')
        RiskEvaluationReportFactory(analysis_status='PROCESSING')
        RiskEvaluationReportFactory(analysis_status='READY_FOR_REVIEW')
        stdout = StringIO()

        call_command('process_pending_rer_analyses', stdout=stdout)

        process_analysis.assert_not_called()
        assert 'No pending RER analyses found.' in stdout.getvalue()

    @patch(WORKFLOW_PATH)
    def test_one_failure_does_not_block_the_next_pending_rer(
        self,
        process_analysis,
    ):
        first = RiskEvaluationReportFactory(analysis_status='PENDING')
        second = RiskEvaluationReportFactory(analysis_status='PENDING')
        process_analysis.side_effect = [
            RERAnalysisServiceError('SARA is unavailable.'),
            None,
        ]
        stdout = StringIO()
        stderr = StringIO()

        call_command(
            'process_pending_rer_analyses',
            stdout=stdout,
            stderr=stderr,
        )

        assert process_analysis.call_args_list == [call(first.pk), call(second.pk)]
        assert f'RER {first.pk} failed' in stderr.getvalue()
        assert f'RER {second.pk} processed successfully' in stdout.getvalue()
        assert '1 completed, 1 failed, 0 skipped' in stdout.getvalue()
