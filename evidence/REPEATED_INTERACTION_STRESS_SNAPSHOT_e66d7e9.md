# Repeated-Interaction Stress Snapshot

Candidate SHA: `e66d7e9ffe9312f82a0d5a95b0ce7b0506f6c551`

Candidate branch: `candidate/v0.2-qualified-integrations`

Regression workflow: `37428534048`

Bride qualification workflow: `37428534259`

## Cross-platform consensus

All 9 regression jobs passed across Linux, Windows, and macOS on Python 3.11, 3.12, and 3.13.

All 6 Bride qualification jobs passed across Linux, Windows, and macOS on Python 3.11 and 3.13.

Each qualification artifact contains the donor qualification record, the nine-trial integrated longitudinal record, and the eight-trial repeated-interaction stress record.

The six stress JSON files normalize to the same semantic object.

Normalized stress-result SHA-256:

`54534a007a118178ca7262c7c31ffae3c570856bf488456a2d3c0a984afa1271`

Normalized stress trial-payload SHA-256:

`65831d7d9b6bb4b381c81da24558eb5c86de42d631d75b8206ad9e20d3eef967`

Artifacts:

| Platform | Python | Artifact ID |
| --- | --- | ---: |
| macOS | 3.13 | 11396611419 |
| Windows | 3.11 | 11396518378 |
| Linux | 3.11 | 11396485965 |
| Linux | 3.13 | 11396456875 |
| macOS | 3.11 | 11396427049 |
| Windows | 3.13 | 11395633801 |

## Eight repeated-interaction trials

1. `long-history-replay-restart`: 72 canonical events at 32 turns, projection replay equal, integrity green before and after restart.
2. `plan-multi-restart`: four-step plan survives restart before every step and completes without losing route state.
3. `commitment-retention`: confidentiality remains open after 32 unrelated world events and still changes disclosure policy to `decline`.
4. `private-thought-loop-suppression`: 32 repeated admissions retain one bounded concern, zero memories, and unchanged host truth.
5. `renderer-long-run-drift`: 32 turns preserve identical decisions and semantic projection while surface wording differs.
6. `diagnostic-fork-long-run`: 32 diagnostic turns on a fork leave the primary sequence and projection untouched.
7. `memory-scale-cue-specificity`: at 130 memories the old purple-cassette target remains first for its cue while boiler-specific retrieval remains boiler-specific.
8. `developmental-long-run-divergence`: 16 matched expectation opportunities produce `accept_help` in the confirmed-history life and `keep_distance` in the violated-history life.

All eight trials passed identically on all six qualification jobs.

## Interpretation boundary

This gate demonstrates deterministic functional continuity, bounded causal persistence, replay/restart stability, renderer-neutral semantic continuity under the deterministic renderer pair, diagnostic isolation, cue-specific memory behavior, and developmental path dependence over the frozen stress horizon.

It does not establish phenomenal consciousness, general human equivalence, or invariance across arbitrary live language models. Those remain outside the evidence.

The next phase is release hardening: real v0.1-home upgrade compatibility, backup/restore compatibility, packaging, documentation consistency, and final release-candidate acceptance.
