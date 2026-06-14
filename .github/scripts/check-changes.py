"""Check if gh-pages-deploy content differs from the published gh-pages branch."""

import json
import os
import subprocess
from pathlib import Path


def main():
    deploy_dir = Path("gh-pages-deploy")
    has_gh_pages = os.environ.get("HAVE_GH_PAGES", "false") == "true"

    def git_blob(path: str):
        proc = subprocess.run(
            ["git", "show", f"gh-pages:{path}"],
            capture_output=True,
            text=False,
        )
        return proc.stdout if proc.returncode == 0 else None

    def normalized_bytes(name: str, payload: bytes) -> bytes:
        # Ignore metadata-only churn in JSON files.
        if name in {"history.json", "upcoming_sessions.json"}:
            try:
                data = json.loads(payload.decode("utf-8"))
                if isinstance(data, dict):
                    data.pop("last_updated", None)
                return (
                    json.dumps(data, sort_keys=True, separators=(",", ":")) + "\n"
                ).encode("utf-8")
            except Exception:
                return payload
        return payload

    changed = False

    if has_gh_pages:
        # Compare complete file sets (including deletions).
        old_files_proc = subprocess.run(
            ["git", "ls-tree", "-r", "--name-only", "gh-pages"],
            capture_output=True,
            text=True,
            check=False,
        )
        old_files = {
            line.strip() for line in old_files_proc.stdout.splitlines() if line.strip()
        }
        new_files = {p.name for p in deploy_dir.iterdir() if p.is_file()}

        if old_files != new_files:
            changed = True
            added = sorted(new_files - old_files)
            removed = sorted(old_files - new_files)
            if added:
                print(f'New files: {", ".join(added)}')
            if removed:
                print(f'Removed files: {", ".join(removed)}')
        else:
            for name in sorted(new_files):
                old_raw = git_blob(name)
                new_raw = (deploy_dir / name).read_bytes()
                if old_raw is None or normalized_bytes(
                    name, old_raw
                ) != normalized_bytes(name, new_raw):
                    changed = True
                    print(f"File changed: {name}")
                    break
    else:
        changed = True
        print("gh-pages branch doesn't exist yet, will deploy")

    if changed:
        print("Changes detected, will deploy")
    else:
        print(
            "No changes detected, skipping deployment to avoid unnecessary Pages build"
        )

    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a", encoding="utf-8") as fh:
            fh.write(f"changed={'true' if changed else 'false'}\n")


if __name__ == "__main__":
    main()
