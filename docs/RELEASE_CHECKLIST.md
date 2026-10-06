# Frankenstein v0.2 Release Checklist

This checklist governs promotion of the Bride v0.2 candidate from release hardening to a public release proposal.

## Required green evidence

- [x] Frozen Frankenstein v0.1 baseline identified by exact commit.
- [x] Real-baseline donor qualification completed on Linux, Windows, and macOS.
- [x] Qualified mechanisms integrated one at a time with ablations preserved.
- [x] Bounded planning integration green.
- [x] Narrow confidentiality commitment pressure integration green.
- [x] Bounded private-cognition concern pressure integration green.
- [x] Involuntary-expression boundary integration green.
- [x] Integrated nine-trial longitudinal gate green cross-platform.
- [x] Repeated-interaction eight-trial stress gate green cross-platform.
- [x] Authentic v0.1 direct-open compatibility green cross-platform.
- [x] Authentic v0.1 backup restore under v0.2 green cross-platform.
- [x] Projection digest made independent of SQLite physical row order.
- [x] v0.2 backup/restore after adding new state green.
- [x] Wheel and source distribution build successfully from the release branch.
- [x] Built wheel installs without editable-source fallback.
- [x] Installed-wheel acceptance harness green on Linux, Windows, and macOS.
- [x] Installed-wheel CLI smoke tests green.
- [x] README current-status, architecture, commands, and roadmap sections reconciled with the actual release candidate.
- [x] Changelog and upgrade guide included in the release tree.
- [x] Technical release-candidate implementation matrix green at exact head `2f86f189c08548807ce8ece2be5837463ffcbb1c`.
- [ ] Final independent acceptance review performed against the final exact head.

## Exact technical evidence

Implementation head:

`2f86f189c08548807ce8ece2be5837463ffcbb1c`

Normal regression workflow:

`37474488230`, 9 of 9 jobs passed.

Release-hardening workflow:

`37474488503`, 12 of 12 jobs passed.

Frozen record:

`evidence/RC1_TECHNICAL_RELEASE_SNAPSHOT_2f86f18.md`

The final documentation-only head containing this checklist and snapshot must also pass the repository workflows before assessor handoff. That final CI verification does not replace the independent acceptance review.

## Human-authority items

- [ ] Repository owner chooses and adds a software license if public reuse or package-index distribution is intended.

Bride does not infer a license. Absence of a license is not treated as permission to redistribute.

## Release boundary

Do not tag `v0.2.0`, create a GitHub Release, publish a package, or merge the candidate into another repository until all technical checklist items are green and the repository owner has made any required licensing or distribution decisions.

A release tag must point to the exact independently reviewed head. If any implementation file changes after final acceptance, rerun the affected gates before tagging.
