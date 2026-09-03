"""Crash-isolated subprocess entry point for local Whisper transcription."""
import argparse
import json
import sys

from core.ai.faster_whisper_service import FasterWhisperService

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="strict")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", required=True)
    parser.add_argument("--language", default="vi")
    args = parser.parse_args()
    try:
        result = FasterWhisperService.transcribe(args.path, language=args.language)
        json.dump(result, sys.stdout, ensure_ascii=False)
        sys.stdout.flush()
        return 0
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
