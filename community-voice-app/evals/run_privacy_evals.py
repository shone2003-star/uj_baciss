"""Score the privacy filter on fictional reports with planted personal details.

uv run python -m evals.run_privacy_evals                 run (needs Ollama running)
Options: --limit N (quick try), --save-baseline (accept these scores as the baseline).
Runs on this computer only: nothing is uploaded.
"""

import argparse
import json
import sys

from community_voice.core.config import PROJECT_ROOT
from community_voice.privacy.redact import redact
from evals import privacy_scoring
from evals.scoring import regressions

LABELS = PROJECT_ROOT / "data" / "evals" / "pii_reports.json"
BASELINE = PROJECT_ROOT / "evals" / "privacy_baseline.json"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int)
    parser.add_argument("--save-baseline", action="store_true")
    args = parser.parse_args()

    reports = json.loads(LABELS.read_text(encoding="utf-8"))[: args.limit]
    per_report = []
    for report in reports:
        redacted = redact(report["text"]).text
        scores = privacy_scoring.score_report(redacted, report["pii"], report["area"])
        per_report.append(scores)
        for key, values in scores.items():
            if 0.0 in values:
                print(f"  {report['id']} {key}: {redacted}")

    summary = privacy_scoring.summarize(per_report)
    print(f"\nScored {len(reports)} reports")
    for key, value in summary.items():
        print(f"  {key:20} {value:.2f}")

    if args.save_baseline:
        BASELINE.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        print(f"Baseline saved to {BASELINE.relative_to(PROJECT_ROOT)}")
    elif args.limit:
        print("Quick try: no baseline check.")
    elif not BASELINE.exists():
        print("No baseline yet. Run again with --save-baseline.")
    elif problems := regressions(summary, json.loads(BASELINE.read_text())):
        print("REGRESSION:\n  " + "\n  ".join(problems))
        sys.exit(1)
    else:
        print("No regression against the baseline.")


if __name__ == "__main__":
    main()
