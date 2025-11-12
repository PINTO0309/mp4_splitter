# mp4_splitter

Command-line utility for splitting MP4 files into multiple clips based on a CSV segment list.

## Requirements

- Python 3.12
- [`ffmpeg`](https://ffmpeg.org/) available on your `PATH`

## Installation

```bash
pip install mp4sp
# or, inside this repository
uv sync
uv run mp4sp --help
```

## Preparing the segment list

Create a UTF-8 CSV file with the columns `filename`, `start`, and `end`. Timestamps can be in `HH:MM:SS[.mmm]` format.

```csv
filename,start,end
test.mp4,00:00:01.000,00:00:05.167
test.mp4,00:00:05.168,00:00:10.000
test.mp4,00:00:10.001,00:01:03.000
another.mp4,12,24
```

- `filename` is resolved relative to the input directory you pass via `--input`.
- Each row produces an output file named `<original>_cut_<index>.mp4`.
- Pure numbers in `start`/`end` are treated as seconds, so `another.mp4,12,24` means “take another.mp4 from 12s to 24s,” yielding a 12-second clip.
- If you pass a single file to `--input`, ensure the `filename` column matches that file name; all other rows are skipped automatically.

## Usage

1. Place the source videos under an input folder (or point directly at a single `.mp4` file), e.g. `videos/`.
2. Create the CSV file as described above, e.g. `split_list.csv`.
3. Run the CLI:

```bash
mp4sp \
--input videos \
--output clips \
--csv split_list.csv \
--threads 8 \
--safe
```

### Options

- `--input / -i`: Directory containing the source MP4 files (required). You may also pass a single `.mp4` file path, in which case rows for other files are ignored and only that file is processed.
- `--output / -o`: Directory in which the clips will be written (required; created if missing).
- `--csv / -c`: Path to the CSV file with segment definitions (required).
- `--threads / -t`: Number of parallel splits to run. Defaults to 4.
- `--safe / -s`: Re-encode each clip to avoid artifacts (slower but frame-accurate).

Set `--safe` when you need artifact-free cuts or when cutting from formats where keyframes are sparse. Omit it for the fastest stream-copy mode.

## Example from source checkout

```bash
uv run mp4sp \
-i samples/input \
-o samples/output \
-c split_list.csv \
-t 4 \
-s
```

Upon completion the tool logs progress for each clip and finishes with `All tasks completed.`. The resulting files reside in the output directory.
