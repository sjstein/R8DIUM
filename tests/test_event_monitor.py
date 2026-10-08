import json
from pathlib import Path
import tempfile
import unittest

from run8EventMonitor import (
    EventCursor,
    format_manual_restart,
    format_supervisor_event,
    format_unexpected_exit,
)


class EventCursorTests(unittest.TestCase):
    def test_events_are_delivered_once_after_commit(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            event_path = root / 'events.jsonl'
            state_path = root / 'events.offset'
            event_path.write_text(
                json.dumps({'event': 'unexpected_exit', 'exit_status': 2}) + '\n',
                encoding='utf-8',
            )
            cursor = EventCursor(event_path, state_path)

            pending = cursor.read_pending()
            cursor.commit(pending[0][1])

            self.assertEqual(pending[0][0]['exit_status'], 2)
            self.assertEqual(cursor.read_pending(), [])
            self.assertGreater(int(state_path.read_text(encoding='ascii')), 0)

    def test_partial_event_is_not_consumed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            event_path = root / 'events.jsonl'
            event_path.write_text('{"event": "unexpected_exit"}', encoding='utf-8')

            cursor = EventCursor(event_path, root / 'events.offset')

            self.assertEqual(cursor.read_pending(), [])

    def test_truncated_event_file_resets_cursor(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            event_path = root / 'events.jsonl'
            state_path = root / 'events.offset'
            state_path.write_text('9999\n', encoding='ascii')
            event_path.write_text('{"event": "unexpected_exit"}\n', encoding='utf-8')

            pending = EventCursor(event_path, state_path).read_pending()

            self.assertEqual(pending[0][0]['event'], 'unexpected_exit')

    def test_alert_contains_diagnostic_context(self):
        message = format_unexpected_exit({
            'timestamp_utc': '2026-10-08T11:13:39Z',
            'exit_status': 2,
            'memory_available': '6000000 kB',
            'cgroup_oom_kill': '0',
            'diagnostic_file': '/run8-control/diagnostics/example.txt',
        })

        self.assertIn('unexpected exit', message)
        self.assertIn('automatically after a crash', message)
        self.assertIn('exit status: `2`', message)
        self.assertIn('OOM kills: `0`', message)
        self.assertIn('separate notification', message)

    def test_otto_success_event_has_readiness_message(self):
        message = format_supervisor_event({
            'event': 'otto_engaged',
            'timestamp_utc': '2026-10-08T15:13:44Z',
            'attempt': 1,
        })

        self.assertIn('startup complete', message)
        self.assertIn('all signaled routes', message)
        self.assertIn('attempt: `1`', message)

    def test_otto_failure_event_requests_attention(self):
        message = format_supervisor_event({
            'event': 'otto_activation_failed',
            'error': 'success marker missing',
            'diagnostic_file': '/run8-control/diagnostics/otto.png',
        })

        self.assertIn('requires attention', message)
        self.assertIn('success marker missing', message)
        self.assertIn('otto.png', message)

    def test_unknown_event_is_ignored(self):
        self.assertIsNone(format_supervisor_event({'event': 'future_event'}))

    def test_manual_restart_identifies_actor_and_cause(self):
        message = format_manual_restart(
            'High Green',
            '<@1234> (Dispatcher)',
            'Run8 stopped. Run8 start initiated.',
        )

        self.assertIn('Discord administrator', message)
        self.assertIn('High Green', message)
        self.assertIn('<@1234> (Dispatcher)', message)
        self.assertIn('/restart_server', message)
        self.assertIn('separate notification', message)


if __name__ == '__main__':
    unittest.main()
