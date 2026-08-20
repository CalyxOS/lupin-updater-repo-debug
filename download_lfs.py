#!/usr/bin/env python3
"""
Clone a set of Git repositories (pulling their Git LFS objects) into a local
`git/` folder, then copy a curated list of files out of those repos into
`fdroid/repo/`.

Requirements:
    - git must be installed and available on PATH
    - git-lfs must be installed and available on PATH
      (Debian/Ubuntu: sudo apt install git-lfs)

Usage:
    python3 clone_and_collect.py
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

REPOS = [
    "https://gitlab.com/CalyxOS/lfs_prebuilts_calyx_chromium_arm64.git",
    "https://gitlab.com/CalyxOS/lfs_prebuilts_calyx_microg.git",
]

FILES_TO_COPY = [
    "git/lfs_prebuilts_calyx_chromium_arm64/universal.apk",
    "git/lfs_prebuilts_calyx_chromium_arm64/TrichromeLibrary6432.apk",
    "git/lfs_prebuilts_calyx_chromium_arm64/TrichromeWebView6432.apk",
    "git/lfs_prebuilts_calyx_microg/GmsCore/play-services-core-mapbox-default-release.apk",
    "git/lfs_prebuilts_calyx_microg/GmsCore/vending-app-default-release-unsigned.apk",
]

GIT_DIR = Path("git")
OUTPUT_DIR = Path("fdroid/repo")


def clone_repo(url: str) -> None:
    print(f"Cloning {url}")
    # A normal `git clone` already fetches/smudges LFS objects automatically
    # as long as git-lfs is installed and has run `git lfs install` once.
    # We pass GIT_LFS_SKIP_SMUDGE=0 explicitly to guarantee LFS content (not just pointer files) is checked out.
    env = os.environ | {"GIT_LFS_SKIP_SMUDGE": "0"}
    subprocess.run(
        ["git", "clone", "--depth", "1", url],
        check=True,
        env=env,
        cwd=GIT_DIR,
    )


def copy_files(paths: list[str], output_dir: Path) -> None:
    """Copy each listed file into output_dir, preserving just the filename."""
    output_dir.mkdir(parents=True, exist_ok=True)

    for path_str in paths:
        src = Path(path_str)
        if not src.is_file():
            print(f"Warning: source file not found, skipping: {src}")
            continue

        dest = output_dir / src.name
        shutil.copy2(src, dest)
        print(f"Copied {src} -> {dest}")


def main() -> None:
    GIT_DIR.mkdir(parents=True, exist_ok=True)

    for url in REPOS:
        clone_repo(url)

    copy_files(FILES_TO_COPY, OUTPUT_DIR)

    print("Done.")


if __name__ == "__main__":
    main()
