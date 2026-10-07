import csv
import importlib.util
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest import mock


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class DatabaseWriteTests(unittest.TestCase):
    def _load_module(self):
        fake_config = types.SimpleNamespace(SECURITY_FILE=[], DB_FILENAME='unused.csv')
        fake_xmltodict = types.SimpleNamespace()
        spec = importlib.util.spec_from_file_location(
            'r8dium_test_db_access',
            REPOSITORY_ROOT / 'dbAccess.py',
        )
        module = importlib.util.module_from_spec(spec)
        with mock.patch.dict(
                sys.modules,
                {'r8diumInclude': fake_config, 'xmltodict': fake_xmltodict}):
            spec.loader.exec_module(module)
        return module

    def test_save_db_atomically_replaces_csv_with_same_schema(self):
        db_access = self._load_module()
        record = {field: '' for field in db_access.db_field_list}
        record[db_access.sid] = '1'
        record[db_access.discord_name] = 'Test User'

        with tempfile.TemporaryDirectory() as temp_dir:
            database = Path(temp_dir) / 'state' / 'r8diumDb.csv'
            database.parent.mkdir()
            database.write_text('old data', encoding='utf-8')

            saved = db_access.save_db(str(database), [record])

            self.assertEqual(saved, 1)
            with database.open(newline='') as csv_file:
                rows = list(csv.DictReader(csv_file))
            self.assertEqual(rows, [record])
            self.assertEqual(list(database.parent.glob('.r8diumDb.csv.*')), [])


if __name__ == '__main__':
    unittest.main()
