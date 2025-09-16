"""Script to calculate the next beta version based on PR labels.

- Uses the latest stable release (ignores pre-releases).
- Finds merged PRs since that release into dev-current.
- Chooses the highest SemVer bump from PR labels (major > minor > patch).
- Dependabot-only changes always bump patch.
- If running on dev-current, appends -beta.<commit_count>.
"""

import os
import sys

import requests

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    sys.exit("ERROR: GITHUB_TOKEN is required")

repository = os.environ["GITHUB_REPOSITORY"]
owner, repo = repository.split("/")

headers = {"Authorization": f"token {GITHUB_TOKEN}"}

# --- Helpers -----------------------------------------------------------------


def get_latest_stable_release():
    """Return the latest stable release tag (ignoring pre-releases)."""
    url = f"https://api.github.com/repos/{owner}/{repo}/releases"
    releases = requests.get(url, headers=headers, timeout=10).json()
    for rel in releases:
        if not rel["prerelease"]:
            return rel["tag_name"]
    return "v0.0.0"


def get_commits_since(tag, ref):
    """Return compare info (commits, total_commits) since tag -> ref."""
    url = f"https://api.github.com/repos/{owner}/{repo}/compare/{tag}...{ref}"
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.json()


def get_prs_from_commits(commits):
    """Return list of PRs linked to given commits."""
    prs = []
    for commit in commits:
        sha = commit["sha"]
        url = f"https://api.github.com/repos/{owner}/{repo}/commits/{sha}/pulls"
        resp = requests.get(
            url,
            headers={**headers, "Accept": "application/vnd.github.groot-preview+json"},
            timeout=10,
        )
        if resp.status_code == 200:
            prs.extend(resp.json())
    # Deduplicate by PR number
    unique = {pr["number"]: pr for pr in prs}
    return list(unique.values())


def is_dependabot(pr):
    """Return True if PR was authored by Dependabot."""
    user = pr.get("user", {}).get("login", "").lower()
    return "dependabot" in user


def determine_bump(prs):
    """Determine SemVer bump from PR labels."""
    bump = "patch"
    all_dependabot = all(is_dependabot(pr) for pr in prs) if prs else False

    if all_dependabot:
        return "patch"

    for pr in prs:
        labels = [label["name"].lower() for label in pr.get("labels", [])]
        if "major" in labels:
            return "major"
        if "minor" in labels and bump != "major":
            bump = "minor"
        # patch is default, no need to check
    return bump


# --- Main --------------------------------------------------------------------

ref = os.environ["GITHUB_REF"].split("/")[-1]  # branch or tag name

latest_tag = get_latest_stable_release()
compare_info = get_commits_since(latest_tag, ref)
commits = compare_info["commits"]
commit_count = compare_info["total_commits"]

if commit_count == 0:
    print(latest_tag)
    sys.exit(0)

prs = get_prs_from_commits(commits)
bump = determine_bump(prs)

base = latest_tag.lstrip("v").split("-", 1)[0]
major, minor, patch = map(int, base.split("."))

if bump == "major":
    major += 1
    minor = 0
    patch = 0
elif bump == "minor":
    minor += 1
    patch = 0
else:
    patch += 1

next_version = f"v{major}.{minor}.{patch}"

if ref == "dev-current" and commit_count > 0:
    next_version += f"-beta.{commit_count}"

print(next_version)
