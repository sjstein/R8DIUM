import subprocess
import unittest
from unittest import mock

import serverControl


class ServerControlTests(unittest.TestCase):
    @mock.patch('serverControl.subprocess.run')
    def test_configured_command_runs_without_a_shell(self, run):
        run.return_value = subprocess.CompletedProcess([], 0, stdout='stopped\n', stderr='')

        result = serverControl.control_server(
            'stop',
            'HGR8',
            '/run8',
            stop_command='/usr/local/bin/run8-control stop HGR8',
        )

        self.assertTrue(result.success)
        self.assertEqual(result.message, 'stopped')
        run.assert_called_once_with(
            ['/usr/local/bin/run8-control', 'stop', 'HGR8'],
            cwd='/run8',
            capture_output=True,
            text=True,
            timeout=serverControl.CONTROL_TIMEOUT_SECONDS,
            check=False,
        )

    @mock.patch('serverControl.subprocess.run')
    def test_nonzero_command_is_reported(self, run):
        run.return_value = subprocess.CompletedProcess([], 4, stdout='', stderr='not running\n')

        result = serverControl.control_server(
            'restart',
            'HGR8',
            '/run8',
            restart_command='/usr/local/bin/run8-control restart HGR8',
        )

        self.assertFalse(result.success)
        self.assertIn('status 4', result.message)
        self.assertIn('not running', result.message)

    @mock.patch('serverControl._run_command')
    def test_restart_falls_back_to_stop_then_start_commands(self, run_command):
        run_command.side_effect = [
            serverControl.ControlResult(True, 'stopped'),
            serverControl.ControlResult(True, 'started'),
        ]

        result = serverControl.control_server(
            'restart',
            'HGR8',
            '/run8',
            start_command='/control start',
            stop_command='/control stop',
        )

        self.assertTrue(result.success)
        self.assertEqual(result.message, 'stopped\nstarted')
        self.assertEqual(
            run_command.call_args_list,
            [mock.call('/control stop', '/run8'), mock.call('/control start', '/run8')],
        )

    @mock.patch.object(serverControl.os, 'name', 'posix')
    def test_linux_requires_a_configured_stop_command(self):
        result = serverControl.control_server('stop', 'HGR8', '/run8')

        self.assertFalse(result.success)
        self.assertIn('No stop_command is configured', result.message)

    def test_unknown_action_is_rejected(self):
        result = serverControl.control_server('explode', 'HGR8', '/run8')

        self.assertFalse(result.success)
        self.assertIn('Unknown lifecycle action', result.message)


if __name__ == '__main__':
    unittest.main()
