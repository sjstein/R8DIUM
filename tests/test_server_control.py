from concurrent.futures import ThreadPoolExecutor
import subprocess
import sys
import threading
import time
import unittest
from unittest import mock

import serverControl


def psutil_mock():
    module = mock.Mock()
    module.NoSuchProcess = type('NoSuchProcess', (Exception,), {})
    module.AccessDenied = type('AccessDenied', (Exception,), {})
    module.ZombieProcess = type('ZombieProcess', (Exception,), {})
    return module


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

    @mock.patch.object(serverControl.os, 'name', 'nt')
    @mock.patch('serverControl._matching_windows_processes')
    def test_windows_stop_terminates_and_waits_for_every_matching_process(
            self, matching_processes):
        first = mock.Mock(info={'pid': 101, 'name': serverControl.RUN8_EXECUTABLE})
        second = mock.Mock(info={'pid': 202, 'name': serverControl.RUN8_EXECUTABLE})
        matching_processes.side_effect = [([first, second], []), ([], [])]
        psutil = psutil_mock()
        psutil.wait_procs.return_value = ([first, second], [])

        with mock.patch.dict(sys.modules, {'psutil': psutil}):
            result = serverControl._stop_windows_server('HGR8', r'C:\Run8')

        self.assertTrue(result.success)
        first.terminate.assert_called_once_with()
        second.terminate.assert_called_once_with()
        psutil.wait_procs.assert_called_once_with(
            [first, second],
            timeout=serverControl.STOP_TIMEOUT_SECONDS,
        )
        self.assertIn('101, 202', result.message)

    @mock.patch.object(serverControl.os, 'name', 'nt')
    @mock.patch('serverControl._matching_windows_processes')
    def test_windows_stop_fails_closed_when_a_process_cannot_be_inspected(
            self, matching_processes):
        matching_processes.return_value = ([], ['PID 101: access denied'])
        psutil = psutil_mock()

        with mock.patch.dict(sys.modules, {'psutil': psutil}):
            result = serverControl._stop_windows_server('HGR8', r'C:\Run8')

        self.assertFalse(result.success)
        self.assertIn('Unable to inspect all Run8 processes', result.message)

    @mock.patch.object(serverControl.os, 'name', 'nt')
    @mock.patch('serverControl._matching_windows_processes')
    def test_windows_stop_force_kills_a_process_that_does_not_exit(self, matching_processes):
        process = mock.Mock(info={'pid': 101, 'name': serverControl.RUN8_EXECUTABLE})
        matching_processes.side_effect = [([process], []), ([], [])]
        psutil = psutil_mock()
        psutil.wait_procs.side_effect = [([], [process]), ([process], [])]

        with mock.patch.dict(sys.modules, {'psutil': psutil}):
            result = serverControl._stop_windows_server('HGR8', r'C:\Run8')

        self.assertTrue(result.success)
        process.terminate.assert_called_once_with()
        process.kill.assert_called_once_with()
        self.assertEqual(psutil.wait_procs.call_count, 2)

    @mock.patch('serverControl._start_windows_server')
    @mock.patch('serverControl._stop_windows_server')
    def test_restart_does_not_start_after_stop_failure(self, stop_server, start_server):
        stop_server.return_value = serverControl.ControlResult(
            False,
            'Unable to terminate all Run8 processes for HGR8: PID 101: access denied',
        )

        result = serverControl.control_server('restart', 'HGR8', r'C:\Run8')

        self.assertFalse(result.success)
        start_server.assert_not_called()

    def test_lifecycle_operations_for_one_server_are_serialized(self):
        first_entered = threading.Event()
        release_first = threading.Event()
        calls = []

        def controlled_call(action, *_args):
            calls.append(action)
            if action == 'first':
                first_entered.set()
                release_first.wait(timeout=1)
            return serverControl.ControlResult(True, action)

        with mock.patch('serverControl._control_server_unlocked', side_effect=controlled_call):
            with ThreadPoolExecutor(max_workers=2) as executor:
                first = executor.submit(serverControl.control_server, 'first', 'HGR8', r'C:\Run8')
                self.assertTrue(first_entered.wait(timeout=1))
                second = executor.submit(serverControl.control_server, 'second', 'HGR8', r'C:\Run8')
                time.sleep(0.05)
                self.assertEqual(calls, ['first'])
                release_first.set()
                self.assertTrue(first.result(timeout=1).success)
                self.assertTrue(second.result(timeout=1).success)

        self.assertEqual(calls, ['first', 'second'])


if __name__ == '__main__':
    unittest.main()
