"""Build a local mock narration preview from a lesson and its line plan."""

import argparse
import json
import shutil
import sys
import tempfile
import wave
from pathlib import Path

EXAMPLES = Path(__file__).resolve().parent / "examples"
SAMPLE_RATE = 8000
# A quiet 500 Hz pulse and a rest make each whitespace-delimited word audible.
CYCLE = bytes([128, 134, 139, 143, 144, 143, 139, 134,
               128, 122, 117, 113, 112, 113, 117, 122])
WORD_AUDIO = CYCLE * 20 + bytes([128]) * 1280


def segment_lesson(text, plan):
    """Resolve consecutive, inclusive, one-based ranges against the lesson."""
    lines = text.splitlines()
    if not lines or not text.strip():
        raise ValueError("lesson must contain text")
    if not isinstance(plan, list) or not plan:
        raise ValueError("plan must be a nonempty list of line ranges")

    next_line = 1
    segments = []
    for number, pair in enumerate(plan, start=1):
        if (not isinstance(pair, list) or len(pair) != 2
                or any(type(value) is not int for value in pair)):
            raise ValueError(f"segment {number} requires two integer line numbers")
        first, last = pair
        if first != next_line:
            raise ValueError(f"segment {number} must start at line {next_line}")
        if not first <= last <= len(lines):
            raise ValueError(f"segment {number} must end between lines {first} and {len(lines)}")
        transcript = "\n".join(lines[first - 1:last])
        if not transcript.strip():
            raise ValueError(f"segment {number} contains only whitespace")
        segments.append({
            "id": f"segment-{number:03}",
            "lines": [first, last],
            "text": transcript,
        })
        next_line = last + 1
    if next_line != len(lines) + 1:
        raise ValueError(f"plan leaves lines {next_line} through {len(lines)} uncovered")
    return segments


def render_mock(job, directory):
    audio_name = job["id"] + ".wav"
    word_count = len(job["text"].split())
    with wave.open(str(directory / audio_name), "wb") as audio:
        audio.setparams((1, 1, SAMPLE_RATE, 0, "NONE", "PCM"))
        for _ in range(word_count):
            audio.writeframesraw(WORD_AUDIO)
    return {"file": audio_name, "frames": len(WORD_AUDIO) * word_count}


def build(lesson_path, plan_path, parent):
    text = lesson_path.read_text(encoding="utf-8")
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    segments = segment_lesson(text, plan)
    directory = Path(tempfile.mkdtemp(prefix="study-preview-", dir=parent))
    try:
        for job in segments:
            job["audio"] = render_mock(job, directory)
        manifest = {"provider": "mock-pulse", "sample_rate_hz": SAMPLE_RATE, "jobs": segments}
        (directory / "jobs.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    except BaseException:
        shutil.rmtree(directory)
        raise
    return directory, len(segments)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lesson", type=Path, default=EXAMPLES / "bell-intervals.txt")
    parser.add_argument("--plan", type=Path, default=EXAMPLES / "line-plan.json")
    parser.add_argument("--output-parent", type=Path, default=Path.cwd(),
                        help="existing directory in which to create a new preview")
    args = parser.parse_args()
    try:
        directory, count = build(args.lesson, args.plan, args.output_parent)
    except (OSError, ValueError) as error:
        parser.exit(2, f"Preview failed: {error}\n")
    print(f"Rendered {count} mock narration jobs.")
    print(directory.resolve())


if __name__ == "__main__":
    sys.exit(main())
