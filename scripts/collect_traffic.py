"""Save private GitHub traffic snapshots outside the checkout. Requires authenticated gh.

Run weekly: python scripts/collect_traffic.py
GitHub traffic windows overlap: never sum their unique counts across snapshots.
"""
import argparse
import csv
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def api(endpoint):
    result = subprocess.run(["gh", "api", endpoint], capture_output=True, text=True, encoding="utf-8")
    if result.returncode:
        raise RuntimeError(f"GitHub API request failed for {endpoint}: {result.stderr.strip()}")
    return json.loads(result.stdout)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", default="kishormorol/cli-faq-shortcuts")
    ap.add_argument("--output-dir", type=Path,
                    default=Path.home() / ".local/share/cli-faq-shortcuts/traffic")
    args = ap.parse_args()
    output = args.output_dir.expanduser().resolve()
    checkout = Path(__file__).resolve().parent.parent
    if output == checkout or checkout in output.parents:
        ap.error("Save private analytics outside the repository")
    now = datetime.now(timezone.utc)
    prefix = f"repos/{args.repo}"
    try:
        repo = api(prefix)
        snapshot = {"captured_at": now.isoformat(), "repository": args.repo,
                    "stars": repo["stargazers_count"], "forks": repo["forks_count"]}
        for name, endpoint in [("views", "views"), ("clones", "clones"),
                               ("referrers", "popular/referrers"), ("paths", "popular/paths")]:
            snapshot[name] = api(f"{prefix}/traffic/{endpoint}")
    except (RuntimeError, OSError, ValueError) as exc:
        ap.exit(1, f"{exc}\n")
    output.mkdir(parents=True, exist_ok=True)
    dest = output / (now.strftime("%Y-%m-%dT%H%M%S%fZ") + ".json")
    dest.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    series = output / "summary.csv"
    new_file = not series.exists()
    with series.open("a", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        if new_file:
            writer.writerow(["captured_at", "repository", "stars", "forks", "views", "unique_visitors",
                             "clones", "unique_cloners", "window_start", "window_end"])
        days = snapshot["views"]["views"]
        writer.writerow([snapshot["captured_at"], args.repo, snapshot["stars"], snapshot["forks"],
                         snapshot["views"]["count"], snapshot["views"]["uniques"],
                         snapshot["clones"]["count"], snapshot["clones"]["uniques"],
                         days[0]["timestamp"] if days else "", days[-1]["timestamp"] if days else ""])
    print(f"Saved private snapshot: {dest}")
    print(f"Stars: {snapshot['stars']}; unique visitors: {snapshot['views']['uniques']}; "
          f"unique cloners: {snapshot['clones']['uniques']}")
    print("Traffic totals cover the API's returned window, not the time since the previous snapshot.")


if __name__ == "__main__":
    main()
