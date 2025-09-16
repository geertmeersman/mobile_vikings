"""Script to extract SemVer labels from commit messages in a pull request.

This script reads commit messages from a file (COMMIT_MESSAGES), determines
the semantic versioning (SemVer) level (major, minor, patch) based on
Conventional Commits, and outputs a JSON object containing the commit types
and the SemVer level. It is designed for use in CI/CD workflows to
automatically label PRs. Dependabot commits are always treated as patch.
"""

import json
import os
import re
import sys


def extract_semver_types(commit_messages):
    """Extract Conventional Commit types from commit messages.

    Args:
        commit_messages (list[str]): List of commit messages.

    Returns:
        list[str]: Unique list of commit types (e.g., ["feat", "fix"]).

    """
    types = []
    pattern = r"^(feat|fix|chore|docs|style|refactor|perf|test)(?:\(.+?\))?!?:\s(.+)$"
    for message in commit_messages:
        match = re.match(pattern, message.strip())
        if match:
            commit_type = match.group(1)
            if commit_type not in types:
                types.append(commit_type)
    return types


def is_dependabot_commit(message):
    """Check if a commit message is from Dependabot.

    Args:
        message (str): Commit message.

    Returns:
        bool: True if the commit is from Dependabot.

    """
    return "dependabot" in message.lower()


def get_semver_level(commit_messages):
    """Determine semantic versioning (SemVer) level from commit messages.

    Dependabot-only commits are always considered patch.

    Args:
        commit_messages (list[str]): List of commit messages.

    Returns:
        str: One of "major", "minor", or "patch".

    """
    # If all commits are Dependabot, force patch
    if all(is_dependabot_commit(msg) for msg in commit_messages):
        return "patch"

    for message in commit_messages:
        msg = message.strip()

        # Major: breaking changes
        if "BREAKING CHANGE:" in msg.upper():
            return "major"
        if re.match(
            r"^(feat|fix|chore|docs|style|refactor|perf|test)(?:\(.+?\))?!:", msg
        ):
            return "major"

    # Minor: features
    for message in commit_messages:
        if is_dependabot_commit(message):
            continue
        if message.strip().startswith("feat"):
            return "minor"

    # Patch: everything else
    return "patch"


def main():
    """Read commit messages, determine SemVer level, and print JSON result.

    The function expects a COMMIT_MESSAGES file in the working directory,
    created by the CI workflow. It parses commit messages to extract commit
    types and determine the appropriate SemVer level, then prints a JSON
    object with both.
    """
    file_path = "COMMIT_MESSAGES"
    if not os.path.exists(file_path):
        sys.exit(f"ERROR: {file_path} does not exist")

    with open(file_path) as file:
        messages = [line.strip() for line in file if line.strip()]

    if not messages:
        sys.exit("ERROR: No commit messages found")

    semver_level = get_semver_level(messages)
    types = extract_semver_types(messages)

    result = {
        "types": types,
        "semver": semver_level,
    }
    print(json.dumps(result))


if __name__ == "__main__":
    main()
