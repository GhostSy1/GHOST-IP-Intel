import unittest
import os
import json

class TestCoreEngine(unittest.TestCase):
    def test_db_exists(self):
        db_path = os.path.join(os.path.dirname(__file__), '../db/vulnerabilities.json')
        self.assertTrue(os.path.exists(db_path))
        with open(db_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.assertIn("entries", data)

if __name__ == "__main__":
    unittest.main()
