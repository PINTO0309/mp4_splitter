import csv
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse


def cut_video(task, safe_mode=False):
    """Cut video segments with ffmpeg (safe mode re-encodes to prevent artifacts)."""
    src_path, start, end, output_path = task

    if safe_mode:
        # Precise frame-level trimming + re-encode
        cmd = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel", "error",
            "-nostdin",
            "-y",
            "-i", str(src_path),
            "-ss", start,
            "-to", end,
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "18",
            "-c:a", "aac",
            "-movflags", "+faststart",
            str(output_path),
        ]
    else:
        # Fast mode (may introduce artifacts)
        cmd = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel", "error",
            "-nostdin",
            "-y",
            "-ss", start,
            "-to", end,
            "-i", str(src_path),
            "-c", "copy",
            "-avoid_negative_ts", "1",
            str(output_path),
        ]

    try:
        subprocess.run(cmd, check=True, stdin=subprocess.DEVNULL)
        return f"✅ Done: {output_path.name}"
    except subprocess.CalledProcessError:
        return f"❌ Failed: {src_path.name} ({start} to {end})"


def load_tasks(input_dir: Path, csv_path: Path, output_dir: Path, allowed_files: set[str] | None = None):
    """Build trimming tasks from the CSV."""
    tasks = []
    with open(csv_path, newline='', encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=1):
            filename = row["filename"].strip()
            if allowed_files is not None and filename not in allowed_files:
                allowed_list = ", ".join(sorted(allowed_files))
                print(f"⚠️ {filename} ignored because --input targets: {allowed_list}.")
                continue
            start = row["start"].strip()
            end = row["end"].strip()
            src_path = input_dir / filename
            if not src_path.exists():
                print(f"⚠️ {src_path} not found. Skipping.")
                continue

            stem = src_path.stem
            ext = src_path.suffix
            out_name = f"{stem}_cut_{i:03d}{ext}"
            output_path = output_dir / out_name
            tasks.append((src_path, start, end, output_path))
    return tasks


def main():
    parser = argparse.ArgumentParser(
        description="Split videos in bulk using the provided segment list."
    )
    parser.add_argument("-i", "--input", required=True, help="Directory of input videos or a single MP4 file")
    parser.add_argument("-o", "--output", required=True, help="Path to the output folder")
    parser.add_argument("-c", "--csv", required=True, help="Path to the CSV describing segments")
    parser.add_argument("-t", "--threads", type=int, default=4, help="Number of parallel threads (default: 4)")
    parser.add_argument("-s", "--safe", action="store_true", help="Enable artifact-reduction mode (re-encode)")

    args = parser.parse_args()

    input_path = Path(args.input)
    allowed_files = None
    if input_path.is_file():
        allowed_files = {input_path.name}
        input_dir = input_path.parent
    elif input_path.is_dir():
        input_dir = input_path
    else:
        parser.error(f"--input path {input_path} does not exist.")

    output_dir = Path(args.output)
    csv_path = Path(args.csv)
    output_dir.mkdir(parents=True, exist_ok=True)

    tasks = load_tasks(input_dir, csv_path, output_dir, allowed_files)
    print(f"🎬 Generating {len(tasks)} clips (threads: {args.threads})")
    if args.safe:
        print("🛡️ Safe mode: re-encoding to reduce artifacts.\n")
    else:
        print("⚡ Fast mode: no re-encode (artifacts may appear in the first frames).\n")

    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        futures = {executor.submit(cut_video, t, args.safe): t for t in tasks}
        for future in as_completed(futures):
            print(future.result())

    print("\n✅ All tasks completed.")


if __name__ == "__main__":
    main()
