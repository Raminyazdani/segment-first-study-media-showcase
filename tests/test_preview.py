import json
import subprocess
import sys
import tempfile
import unittest
import wave
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "study_media.py"
EXAMPLES = ROOT / "examples"


class PreviewTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.parent = Path(temp.name)

    def cli(self, *arguments):
        return subprocess.run(
            [sys.executable, "-I", str(SCRIPT), *arguments],
            cwd=self.parent, capture_output=True, text=True, check=False,
        )

    def render(self):
        completed = self.cli()
        self.assertEqual(completed.returncode, 0, completed.stderr)
        summary, directory = completed.stdout.splitlines()
        self.assertEqual(summary, "Rendered 3 mock narration jobs.")
        return Path(directory)

    def test_example_matches_manifest_and_reopens_as_pcm(self):
        directory = self.render()
        jobs = json.loads((directory / "jobs.json").read_text(encoding="utf-8"))
        expected = json.loads((EXAMPLES / "expected-jobs.json").read_text(encoding="utf-8"))
        self.assertEqual(jobs, expected)
        self.assertEqual(len(jobs["jobs"]), 3)
        # Independently counted 27, 29 and 22 words at five pulses per second.
        for job, frames in zip(jobs["jobs"], (43200, 46400, 35200)):
            self.assertEqual(job["audio"]["frames"], frames)
            with wave.open(str(directory / job["audio"]["file"]), "rb") as audio:
                self.assertEqual(audio.getparams()[:4], (1, 1, 8000, frames))
                samples = audio.readframes(frames)
                self.assertEqual(len(samples), frames)
                self.assertGreater(len(set(samples)), 1)

    def test_repeat_creates_separate_identical_artifacts(self):
        first, second = self.render(), self.render()
        self.assertNotEqual(first, second)
        first_files = {item.name: item.read_bytes() for item in first.iterdir()}
        second_files = {item.name: item.read_bytes() for item in second.iterdir()}
        self.assertEqual(first_files, second_files)

    def test_overlap_fails_before_creating_output(self):
        completed = self.cli("--plan", EXAMPLES / "overlap.json")
        self.assertEqual(completed.returncode, 2)
        self.assertIn("segment 2 must start at line 4", completed.stderr)
        self.assertEqual(list(self.parent.iterdir()), [])

    def test_uncovered_last_line_and_boolean_bounds(self):
        plan = self.parent / "plan.json"
        for ranges, message in [
            ([[1, 5]], "lines 6 through 6 uncovered"),
            ([[True, 6]], "requires two integer line numbers"),
        ]:
            with self.subTest(ranges=ranges):
                plan.write_text(json.dumps(ranges), encoding="utf-8")
                completed = self.cli("--plan", plan)
                self.assertEqual(completed.returncode, 2)
                self.assertIn(message, completed.stderr)
                self.assertEqual(list(self.parent.iterdir()), [plan])
