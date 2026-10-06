# Upgrading Frankenstein v0.1 to v0.2

Frankenstein v0.2.0rc1 is designed to open the accepted v0.1 state format directly. The database schema remains version 1. The release-hardening workflow generates a populated character home and backup with the exact accepted v0.1 code at `fdaf5be89ccf6991a20eb54649d5318a9adcb6ff`, then verifies the upgrade under the v0.2 candidate on Linux, Windows, and macOS.

## Before upgrading

Create a v0.1 backup and retain it separately:

```bash
frankenstein verify /path/to/character
frankenstein backup /path/to/character /path/to/pre-v02-backup.tgz
```

Do not delete that backup after the first v0.2 run. It is the correct rollback path if you decide to return to v0.1.

## Install the v0.2 release candidate

From a checked-out release branch:

```bash
python -m pip install .
```

For development or qualification work:

```bash
python -m pip install -e . pytest
```

Confirm the installed version:

```bash
python -c "import frankenstein; print(frankenstein.__version__)"
```

Expected release-candidate version:

```text
0.2.0rc1
```

## Open an existing v0.1 character

No migration command is required:

```bash
frankenstein verify /path/to/character
frankenstein doctor /path/to/character
frankenstein status /path/to/character
```

Opening a v0.1 home under v0.2 does not rewrite its existing canonical events. The release-hardening gate verifies that the original canonical event IDs and event hashes remain unchanged and that the legacy semantic projection survives a rebuild.

## What changes after upgrade

The old state remains valid, but v0.2 can make previously inert state causally active in narrow qualified situations.

An existing confidentiality commitment such as `Keep Project Orchid confidential` can influence a later decision when an actual disclosure action is among the candidates. This is an intentional v0.2 behavior change.

New bounded plan state can be created and will persist through the canonical ledger. Plan steps compete through the existing decision engine.

Private cognition can be admitted only through the bounded private-concern path. Raw private thought remains noncanonical. Admitted private concerns are explicitly labeled as uncertain and do not become world facts or beliefs merely because they were thought.

Involuntary expression is transient and separate from deliberate action authority.

## Rebuild and replay

v0.2 fixes a projection-digest defect found during authentic upgrade testing. Earlier digests could depend on SQLite physical row order even when causal projection state was identical. The v0.2 digest sorts projection rows by semantic content, so replay-equivalent state has a stable digest.

You can verify replay and integrity with:

```bash
frankenstein rebuild /path/to/character
frankenstein verify /path/to/character
frankenstein doctor /path/to/character
```

The digest printed by v0.2 should be treated as the v0.2 semantic projection digest. It is not required to equal a raw v0.1 digest computed by the older row-order-sensitive algorithm.

## Backup compatibility

A v0.1 backup can be restored directly with v0.2:

```bash
frankenstein restore /path/to/pre-v02-backup.tgz /path/to/restored-character
```

A backup created after using v0.2 planning or private-cognition state also restores correctly under v0.2.

## Rollback

Do not run a v0.1 binary against a character home after v0.2-specific canonical plan events have been added. The supported rollback procedure is to restore the pre-upgrade v0.1 backup using the v0.1 runtime.

This preserves a clear authority boundary between old history and new event types rather than attempting an in-place downgrade.

## Verified release evidence

The cross-platform upgrade snapshot is stored at:

`evidence/V01_TO_V02_UPGRADE_SNAPSHOT_d492f92.md`

The authentic upgrade result is identical across all six Linux, Windows, and macOS jobs on Python 3.11 and 3.13.

Normalized result SHA-256:

`69f4be75e46bdecd624aec07a480bf81f064c52caaa9bea44b3debb8a73e513b`
