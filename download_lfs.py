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
import sys
from pathlib import Path

REPOS = [
    "https://gitlab.com/CalyxOS/lfs_prebuilts_calyx_chromium_arm64.git",
    "https://gitlab.com/CalyxOS/lfs_prebuilts_calyx_microg.git",
    "https://gitlab.com/CalyxOS/lfs_prebuilts_calyx_lupin.git",
]

FILES_TO_COPY = [
    "git/lfs_prebuilts_calyx_chromium_arm64/universal.apk",
    "git/lfs_prebuilts_calyx_chromium_arm64/TrichromeLibrary6432.apk",
    "git/lfs_prebuilts_calyx_chromium_arm64/TrichromeWebView6432.apk",
    "git/lfs_prebuilts_calyx_microg/GmsCore/play-services-core-mapbox-default-release.apk",
    "git/lfs_prebuilts_calyx_microg/GmsCore/vending-app-default-release-unsigned.apk",
    "git/lfs_prebuilts_calyx_lupin/updater/updater-release.apk",
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


def sign_file(file_path: Path, cert_path: Path, key_path: Path) -> None:
    """Sign the given APK file using apksigner."""
    print(f"Signing {file_path} with cert '{cert_path}' and key '{key_path}'")
    subprocess.run(["apksigner", "sign", "--v4-signing-enabled=false",
                    "--key", key_path, "--cert", cert_path, str(file_path)], check=True)


def main() -> None:
    GIT_DIR.mkdir(parents=True, exist_ok=True)

    for url in REPOS:
        clone_repo(url)

    copy_files(FILES_TO_COPY, OUTPUT_DIR)

    for file in FILES_TO_COPY:
        if "chromium" in file:
            sign_file(OUTPUT_DIR / Path(file).name, Path("keys/chromium.x509.pem"), Path("keys/chromium.pk8"))
        elif "microg" in file:
            sign_file(OUTPUT_DIR / Path(file).name, Path("keys/microg.x509.pem"), Path("keys/microg.pk8"))
        elif "lupin/updater" in file:
            sign_file(OUTPUT_DIR / Path(file).name, Path("keys/org.calyxos.lupin.updater.x509.pem"), Path("keys/org.calyxos.lupin.updater.pk8"))
        else:
            print(f"Error: no signing keys specified for {file}, skipping signing.")
            sys.exit(1)

    print("Done.")


if __name__ == "__main__":
    main()
