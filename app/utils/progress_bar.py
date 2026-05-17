import sys
import time


def show_progress_steps(steps: list[str], delay: float = 0.3) -> None:
    for i, step in enumerate(steps, 1):
        sys.stdout.write(f"\r[{i}/{len(steps)}] {step}...")
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write("\r" + " " * 60 + "\r")
    sys.stdout.flush()
