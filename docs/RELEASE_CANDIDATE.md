# Frankenstein v0.2.0rc1 Release Candidate

Status: **RC ACCEPTANCE PENDING RELEASE-BRANCH CI**

Release branch: `release/v0.2-rc1`

Pre-RC hardening source head: `31f727afe6918e05b1deb508d09fd99cb042e36d`

Package version: `0.2.0rc1`

## Accepted qualified core

RC1 contains exactly four new production mechanisms over the Frankenstein v0.1 baseline:

1. bounded replayable planning,
2. narrow confidentiality commitment pressure,
3. bounded private-cognition concern pressure,
4. a separate involuntary-expression channel.

TinyPersona perception remains adapter-only. Held, rejected, blocked, and infrastructure-only donors remain outside the production core.

## Evidence chain

Real-baseline donor qualification is frozen at `868dd0be6f1b332e826f0da399073d59baae6763`.

The four integration slices and their cross-platform runs are recorded in `docs/INTEGRATION_LEDGER.md`.

Integrated longitudinal evidence is frozen at `d481153628cad95ca4348e5f6a799b0472c808cb` with regression run `37427624732` and qualification run `37427624706`.

Repeated-interaction stress is frozen at `e66d7e9ffe9312f82a0d5a95b0ce7b0506f6c551` with regression run `37428534048` and qualification run `37428534259`. All six stress artifacts normalize to the same result.

Release hardening is green at `31f727afe6918e05b1deb508d09fd99cb042e36d` with regression run `37516915821` and qualification run `37516915930`.

## Compatibility contract

Database schema version remains 1. RC1 introduces no mandatory migration for Frankenstein v0.1 homes.

The legacy `projection_digest()` remains available with its original order-sensitive semantics. RC1 adds `semantic_projection_digest()` as the portable semantic replay and backup digest.

New backups include both the legacy projection digest and the semantic projection digest. Restore verifies the semantic digest when present. Legacy backup manifests without the semantic field remain supported.

## Final RC gate

The release branch must independently pass:

- the 9-job regression matrix,
- the 6-job Bride qualification matrix,
- the 15-probe Frankenstein acceptance harness,
- the nine integrated longitudinal trials,
- the eight 32-turn repeated-interaction stress trials,
- the v0.1 compatibility and backup/restore suite.

RC1 is not accepted until those release-branch checks are green.