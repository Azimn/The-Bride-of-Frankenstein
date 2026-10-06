# Frankenstein v0.2.0rc1 Technical Release Snapshot

Implementation head: `2f86f189c08548807ce8ece2be5837463ffcbb1c`

Release branch: `release/v0.2-rc1-hardening`

Package version: `0.2.0rc1`

Normal regression workflow: `37474488230`

Release-hardening workflow: `37474488503`

## Exact-head result

The implementation head passed every mechanical release gate executed for the release candidate.

Normal regression matrix:

- 9 of 9 jobs passed.
- Linux, Windows, and macOS passed on Python 3.11, 3.12, and 3.13.

Release-hardening matrix:

- 12 of 12 jobs passed.
- 6 authentic v0.1 upgrade jobs passed on Linux, Windows, and macOS on Python 3.11 and 3.13.
- 6 built-package smoke jobs passed on Linux, Windows, and macOS on Python 3.11 and 3.13.

## Built-package gates

Every package-smoke job:

- built one wheel and one source distribution from the release tree,
- ran the deterministic distribution-content verifier,
- installed the built wheel rather than an editable checkout,
- passed `pip check`,
- reported package and runtime version `0.2.0rc1`,
- passed `python -m frankenstein eval`,
- executed the `frankenstein` console entry point,
- executed the `bride-qualify` console entry point.

The distribution-content gate verifies:

- the wheel contains both `frankenstein` and `bride`,
- both console entry points are present,
- SQLite state, backups, environment files, and cache artifacts are absent,
- the source distribution contains README, changelog, upgrade guide, release checklist, donor and integration records, and the frozen evidence snapshots required for the research record.

An earlier package run exposed that the source distribution omitted release documentation. `MANIFEST.in` and `scripts/verify_distribution.py` were added before this exact-head run. The corrected distribution passed on all six package-smoke jobs.

## Authentic v0.1 compatibility

Each release-hardening upgrade job checked out the exact accepted Frankenstein v0.1 source:

`Azimn/Frankenstein@fdaf5be89ccf6991a20eb54649d5318a9adcb6ff`

The v0.1 code generated a populated home and backup. The installed v0.2 release candidate then verified direct-open compatibility, replay, integrity, legacy event identity, legacy semantic state, v0.1 backup restore, use of the four v0.2 qualified mechanisms, and v0.2 backup/restore after new state was added.

The detailed compatibility consensus remains frozen in:

`evidence/V01_TO_V02_UPGRADE_SNAPSHOT_d492f92.md`

## Release-hardening artifacts

| Artifact | ID | GitHub artifact digest |
| --- | ---: | --- |
| release-package-Windows-py3.11 | 11418916131 | `sha256:d582e4d42fa43cf8e43e4ee16adbcebd30a84aa486cbd998e63f3b0dde0ef886` |
| release-hardening-Linux-py3.11 | 11418746223 | `sha256:4e7c4bf73dc4bb794d59e7d98459a0c8b8316a14f096e40f285491cea609616f` |
| release-package-Linux-py3.13 | 11418736151 | `sha256:50f570c5ca62e6be2a03d5de867c6873bb272a4813f4531cef779ab2b833d612` |
| release-package-Linux-py3.11 | 11418576262 | `sha256:6489abe16b143218b2173d5e0fe6c27de44d3ab5f7c8ef1cc1dc5aa93bf9ecce` |
| release-package-Windows-py3.13 | 11418416644 | `sha256:38460a4c96ce4f72d6413b8cec7acc5de89240f195aebd43cb13631cd47a6dbc` |
| release-hardening-Linux-py3.13 | 11418267260 | `sha256:a2169433c5d3d2b9092e221ce66c29a2f7263c292af1ae12a98d57cab705e995` |
| release-package-macOS-py3.13 | 11418087960 | `sha256:f4b05bd967bc2c22ea5c328b4b8fec3770cbdb2a4eb2b4e3f75509f40c88c30a` |
| release-hardening-macOS-py3.13 | 11417804292 | `sha256:467f2efb507f2940b4d2e2d0dcf56f354688c5e79bcb9a24748a665270cae29d` |
| release-hardening-macOS-py3.11 | 11417764435 | `sha256:44df98ad45eafd57101f16442dc1dd26d2bd0098c24d6d15ece9e51b42ff9a08` |
| release-hardening-Windows-py3.13 | 11417744803 | `sha256:62da2d517f1bb190070963416f5ca5894c2ef48c3d871127e468f24ca1a1fad6` |
| release-hardening-Windows-py3.11 | 11417709548 | `sha256:a6ce9a29f82c634c734d1b170d9c47b01aeced54ecee19681bafeffcbda0ef34` |
| release-package-macOS-py3.11 | 11417524270 | `sha256:cad93f2f5d7b9cdc639ebde9dcd878a85ab4a0fcd07e3f80b5aa232fdeae6f54` |

## Evidence chain

The technical release decision rests on the full accumulated chain, not this packaging run alone:

- frozen real-baseline donor qualification,
- one-at-a-time production integration with ablations,
- cross-platform integration regressions,
- nine-trial integrated longitudinal qualification,
- eight-trial repeated-interaction stress qualification,
- authentic v0.1 direct-open and backup compatibility,
- projection-digest replay hardening,
- built wheel and source distribution validation.

## Current release boundary

This snapshot establishes technical release-candidate readiness for the implementation head above. It is not a public-release authorization.

No `v0.2.0` tag, GitHub Release, package-index publication, merge into another repository, or software license is created by this record.

A final documentation-only head containing this snapshot must pass the repository workflows before it is presented as the final assessor head. A separate independent assessor review remains an explicit release gate.

The repository owner must also choose a software license before distribution that requires an explicit grant of reuse rights.
