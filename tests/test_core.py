import os
import unittest

class TestCoreEngine(unittest.TestCase):
    def test_main_presence(self):
        self.assertTrue(os.path.exists("main.py"))

if __name__ == "__main__":
    unittest.main()
