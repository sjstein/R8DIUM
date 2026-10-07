import importlib.util
import os
from pathlib import Path
import tempfile
import textwrap
import unittest
from unittest import mock


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class ConfigTests(unittest.TestCase):
    def _load_config(self, config_text, environment=None, token_file_content=None):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / 'test.cfg'
            config_file.write_text(textwrap.dedent(config_text), encoding='utf-8')
            spec = importlib.util.spec_from_file_location(
                'r8dium_test_config',
                REPOSITORY_ROOT / 'r8diumInclude.py',
            )
            module = importlib.util.module_from_spec(spec)
            variables = {
                'R8DIUM_CONFIG_FILE': str(config_file),
                'R8DIUM_BOT_TOKEN': '',
                'R8DIUM_BOT_TOKEN_FILE': '',
            }
            variables.update(environment or {})
            if token_file_content is not None:
                token_file = Path(temp_dir) / 'bot-token'
                token_file.write_text(token_file_content, encoding='utf-8')
                variables['R8DIUM_BOT_TOKEN_FILE'] = str(token_file)
            with mock.patch.dict(os.environ, variables, clear=False):
                spec.loader.exec_module(module)
            return module

    def test_legacy_config_defaults_lifecycle_commands_to_blank(self):
        config = self._load_config(
            '''
            [local]
            db_name = users
            log_file = bot

            [discord]
            bot_token = config-token
            bot_status = Run8
            ch_admin = staff
            ch_log = none
            ban_scan_time = 60
            log_scan_time = 300
            expire_scan_time = 60
            inactive_days_threshold = 90
            UID_purge_timer = 0

            [server_1]
            name = HGR8
            launch_path = /run8
            security_file = /run8/Content/HostSecurity.xml
            log_file = /run8/Run8.log
            industry_file = /run8/Config.ind
            world_file = /run8/Auto Save World.xml
            traffic_file = /run8/Traffic.r8
            hump_file = /run8/Hump.r8
            r8server_addr = run8.example.test
            r8server_port = 15197
            ''',
        )

        self.assertEqual(config.R8SERVER_NAME, ['HGR8'])
        self.assertEqual(config.R8SERVER_START_COMMAND, [''])
        self.assertEqual(config.R8SERVER_STOP_COMMAND, [''])
        self.assertEqual(config.R8SERVER_RESTART_COMMAND, [''])

    def test_environment_token_overrides_config_token(self):
        config = self._load_config(
            '''
            [local]
            db_name = users
            log_file = bot

            [discord]
            bot_status = Run8
            ch_admin = staff
            ch_log = none
            ban_scan_time = 60
            log_scan_time = 300
            expire_scan_time = 60
            inactive_days_threshold = 90
            UID_purge_timer = 0

            [server_1]
            name = HGR8
            launch_path = /run8
            security_file = /run8/Content/HostSecurity.xml
            log_file = /run8/Run8.log
            industry_file = /run8/Config.ind
            world_file = /run8/Auto Save World.xml
            traffic_file = /run8/Traffic.r8
            hump_file = /run8/Hump.r8
            r8server_addr = run8.example.test
            r8server_port = 15197
            start_command = /control start
            stop_command = /control stop
            restart_command = /control restart
            ''',
            {'R8DIUM_BOT_TOKEN': 'environment-token'},
        )

        self.assertEqual(config.TOKEN, 'environment-token')
        self.assertEqual(config.R8SERVER_RESTART_COMMAND, ['/control restart'])

    def test_token_can_be_read_from_a_secret_file(self):
        config = self._load_config(
            '''
            [local]
            db_name = users
            log_file = bot

            [discord]
            bot_status = Run8
            ch_admin = staff
            ch_log = none
            ban_scan_time = 60
            log_scan_time = 300
            expire_scan_time = 60
            inactive_days_threshold = 90
            UID_purge_timer = 0

            [server_1]
            name = HGR8
            launch_path = /run8
            security_file = /run8/Content/HostSecurity.xml
            log_file = /run8/Run8.log
            industry_file = /run8/Config.ind
            world_file = /run8/Auto Save World.xml
            traffic_file = /run8/Traffic.r8
            hump_file = /run8/Hump.r8
            r8server_addr = run8.example.test
            r8server_port = 15197
            ''',
            token_file_content='secret-file-token\n',
        )

        self.assertEqual(config.TOKEN, 'secret-file-token')


if __name__ == '__main__':
    unittest.main()
