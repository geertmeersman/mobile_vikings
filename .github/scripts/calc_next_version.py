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

repository = os.environ.get("GITHUB_REPOSITORY")
if not repository:
    sys.exit("ERROR: GITHUB_REPOSITORY is required")
owner, repo = repository.split("/", 1)

session = requests.Session()
session.headers.update(
    {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "User-Agent": f"{owner}-{repo}-semver-script",
    }
)

# --- Helpers -----------------------------------------------------------------


def get_latest_stable_release():
    """Return the latest stable release tag (ignores pre-releases and drafts)."""
    try:
        latest_url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
        resp = session.get(latest_url, timeout=10)
        if resp.status_code == 404:
            return "v0.0.0"
        resp.raise_for_status()
        data = resp.json()
        if not data.get("prerelease") and not data.get("draft"):
            return data["tag_name"]
        # Fallback: scan list for first non-prerelease, non-draft
        url = f"https://api.github.com/repos/{owner}/{repo}/releases?per_page=100"
        r = session.get(url, timeout=10)
        r.raise_for_status()
        for rel in r.json():
            if not rel.get("prerelease") and not rel.get("draft"):
                return rel["tag_name"]
        return "v0.0.0"
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to resolve latest stable release: {e}") from e


def get_commits_since(tag, ref):
    """Return compare info (commits, total_commits) since tag -> ref."""
    url = f"https://api.github.com/repos/{owner}/{repo}/compare/{tag}...{ref}"
    resp = session.get(url, timeout=10)
    if resp.status_code == 404 or tag == "v0.0.0":
        # Fallback: no base tag -> approximate using recent commits on ref
        commits_url = f"https://api.github.com/repos/{owner}/{repo}/commits?sha={ref}&per_page=100"
        c_resp = session.get(commits_url, timeout=10)
        c_resp.raise_for_status()
        commits = c_resp.json()
        return {"commits": commits, "total_commits": len(commits)}
    resp.raise_for_status()
    return resp.json()


def get_prs_from_commits(commits):
    """Return list of PR issue objects (with labels) linked to given commits."""
    pr_numbers = set()
    for commit in commits:
        sha = commit["sha"]
        url = f"https://api.github.com/repos/{owner}/{repo}/commits/{sha}/pulls"
        resp = session.get(url, timeout=10)
        if resp.status_code == 200:
            pr_numbers.update(pr["number"] for pr in resp.json())
        elif resp.status_code == 404:
            # No PRs linked to this commit; continue
            continue
        else:
            resp.raise_for_status()
    # Fetch issue objects to get labels
    enriched = []
    for num in pr_numbers:
        issue_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{num}"
        i_resp = session.get(issue_url, timeout=10)
        i_resp.raise_for_status()
        enriched.append(i_resp.json())
    return enriched


def is_dependabot(pr):
    """Return True if PR was authored by Dependabot."""
    user = pr.get("user", {}) or {}
    login = (user.get("login") or "").lower()
    utype = user.get("type")
    return utype == "Bot" and (
        login == "dependabot[bot]" or login.startswith("dependabot")
    )


def determine_bump(prs):
    """Determine SemVer bump from PR labels."""
    bump = "patch"
    all_dependabot = all(is_dependabot(pr) for pr in prs) if prs else False

    if all_dependabot:
        return "patch"

    for pr in prs:
        labels = [label["name"].lower() for label in pr.get("labels", [])]
        print(labels)
        if "major" in labels:
            return "major"
        if "minor" in labels and bump != "major":
            bump = "minor"
        # patch is default, no need to check
    return bump


# --- Main --------------------------------------------------------------------

ref = (
    os.environ.get("TARGET_REF")
    or os.environ.get("REF")
    or os.environ.get("GITHUB_REF_NAME")
    or os.environ["GITHUB_REF"].split("/")[-1]
)  # branch or tag name

latest_tag = get_latest_stable_release()
compare_info = get_commits_since(latest_tag, ref)
commits = compare_info["commits"]
commit_count = compare_info["total_commits"]
if commit_count > len(commits):
    print(
        f"Error: compare API truncated commits ({len(commits)}/{commit_count}); refusing to compute an unsafe SemVer.",
        file=sys.stderr,
    )
    sys.exit(2)

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
