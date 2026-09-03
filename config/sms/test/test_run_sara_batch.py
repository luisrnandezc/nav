from unittest.mock import Mock, call, patch

from django.test import SimpleTestCase

from sms.scripts import run_sara_batch


class TestRunSARABatch(SimpleTestCase):
    @patch('sms.scripts.run_sara_batch.call_command')
    @patch('sms.scripts.run_sara_batch.process_pending_reports')
    def test_batch_processes_vhr_and_rer_queues(
        self,
        process_pending_reports,
        call_command,
    ):
        queue_calls = Mock()
        queue_calls.attach_mock(process_pending_reports, 'process_vhr')
        queue_calls.attach_mock(call_command, 'process_rer')

        with patch('builtins.print'):
            run_sara_batch.main()

        assert queue_calls.mock_calls == [
            call.process_vhr(),
            call.process_rer('process_pending_rer_analyses'),
        ]
