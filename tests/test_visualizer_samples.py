from pathlib import Path
import unittest

from visualizer.app import app


class VisualizerSampleTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_visualizer_has_no_interactive_sample_loader(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b"Load Sample", response.data)
        self.assertNotIn(b"Load a sample", response.data)
        self.assertNotIn(b"Loop / Sample", response.data)
        self.assertNotIn("sample-program", response.get_data(as_text=True))
        self.assertNotIn(
            "/api/samples/<sample_id>",
            {str(rule) for rule in app.url_map.iter_rules()},
        )

    def test_compiler_sample_programs_remain_available_as_test_fixtures(self):
        tests_directory = Path(__file__).resolve().parent
        for filename in (
            "arithmetic.minix",
            "condition.minix",
            "error.minix",
            "sample.minix",
            "types.minix",
        ):
            with self.subTest(filename=filename):
                source = (tests_directory / filename).read_text(encoding="utf-8")
                self.assertTrue(source.strip())


if __name__ == "__main__":
    unittest.main()
