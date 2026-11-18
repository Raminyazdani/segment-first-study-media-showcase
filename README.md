# Segment-first study media

Build a local narration preview for a six-line lesson on the median and mean. An editor groups the lines into three segments. The program validates the whole plan before handing each segment to a mock text-to-speech provider. Its WAV files contain one quiet pulse per word, so you can hear the pace and compare segment lengths. The transcript for each clip travels with its job.

## Quickstart

From the repository root, run this command with Python 3.8 or newer. It uses the standard library and works offline.

```sh
python3 study_media.py
```

The first line reads `Rendered 3 mock narration jobs.` The next line gives the path of a new `study-preview-*` directory in the current directory. Open `jobs.json` to see the provider, line ranges, text and audio metadata. Play the three WAV files in order.

| Clip | Lesson lines | Duration |
| --- | --- | --- |
| `segment-001.wav` | 1–2 | 5.4 seconds |
| `segment-002.wav` | 3–4 | 5.8 seconds |
| `segment-003.wav` | 5–6 | 4.4 seconds |

The [example manifest](examples/expected-jobs.json) contains the complete expected job records for the supplied lesson. Running the command again creates a separate directory with identical file contents.

## Try a different cut

[The lesson](examples/bell-intervals.txt) is plain UTF-8 text. [The plan](examples/line-plan.json) lists inclusive line ranges, starting at 1. Each range must contain text. Together the ranges cover every line in order, exactly once. Blank lines inside a range count toward its line numbers.

For example, save `[[1, 4], [5, 6]]` as `two-clips.json` and run the command below. It combines the introduction and median example in the first clip. Use `--output-parent` to select an existing directory for the preview.

```sh
python3 study_media.py --lesson examples/bell-intervals.txt --plan two-clips.json
```

The [overlapping plan](examples/overlap.json) starts its second segment on a line already used by the first. The command below exits with status 2, reports `segment 2 must start at line 4` and creates zero files.

```sh
python3 study_media.py --plan examples/overlap.json
```

## Tests

```sh
python3 -m unittest discover -s tests -v
```

The tests invoke the CLI, compare its sample manifest, open the WAV files, verify their frame counts and reject incomplete or overlapping plans.
