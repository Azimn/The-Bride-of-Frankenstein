from __future__ import annotations

from pathlib import Path
import glob
import json
import tarfile
import zipfile


EXPECTED_VERSION = "0.2.0rc1"


def main() -> None:
    wheels = sorted(glob.glob("dist/*.whl"))
    sdists = sorted(glob.glob("dist/*.tar.gz"))
    assert len(wheels) == 1, wheels
    assert len(sdists) == 1, sdists

    wheel = Path(wheels[0])
    sdist = Path(sdists[0])

    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
        assert "frankenstein/__init__.py" in names
        assert "frankenstein/engine.py" in names
        assert "bride/__init__.py" in names
        assert "bride/cli.py" in names

        metadata_name = next(
            name for name in names
            if name.endswith(".dist-info/METADATA")
        )
        metadata = archive.read(metadata_name).decode("utf-8")
        assert f"Version: {EXPECTED_VERSION}" in metadata

        entry_name = next(
            name for name in names
            if name.endswith(".dist-info/entry_points.txt")
        )
        entry_points = archive.read(entry_name).decode("utf-8")
        assert "frankenstein = frankenstein.cli:main" in entry_points
        assert "bride-qualify = bride.cli:main" in entry_points

        forbidden = [
            name for name in names
            if any(
                marker in name.lower()
                for marker in (
                    ".sqlite",
                    ".tgz",
                    ".env",
                    "__pycache__",
                    ".pytest_cache",
                )
            )
        ]
        assert not forbidden, forbidden

    required_sdist_suffixes = {
        "README.md",
        "CHANGELOG.md",
        "UPGRADING.md",
        "docs/RELEASE_CHECKLIST.md",
        "docs/DONOR_REGISTRY.md",
        "docs/INTEGRATION_LEDGER.md",
        "evidence/REAL_BASELINE_SNAPSHOT_868dd0b.md",
        "evidence/INTEGRATED_LONGITUDINAL_SNAPSHOT_d481153.md",
        "evidence/REPEATED_INTERACTION_STRESS_SNAPSHOT_e66d7e9.md",
        "evidence/V01_TO_V02_UPGRADE_SNAPSHOT_d492f92.md",
    }
    with tarfile.open(sdist, "r:gz") as archive:
        names = set(archive.getnames())
        missing = [
            suffix
            for suffix in sorted(required_sdist_suffixes)
            if not any(name.endswith("/" + suffix) for name in names)
        ]
        assert not missing, missing

    result = {
        "passed": True,
        "version": EXPECTED_VERSION,
        "wheel": wheel.name,
        "sdist": sdist.name,
        "wheel_has_frankenstein": True,
        "wheel_has_bride": True,
        "wheel_cli_entry_points": True,
        "wheel_forbidden_artifacts": [],
        "sdist_required_release_docs": sorted(required_sdist_suffixes),
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
