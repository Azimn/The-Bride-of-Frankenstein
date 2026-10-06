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
- [ ] Wheel and source distribution build successfully from the release branch.
- [ ] Built wheel installs without editable-source fallback.
- [ ] Installed-wheel acceptance harness green on Linux, Windows, and macOS.
- [ ] Installed-wheel CLI smoke tests green.
- [ ] README current-status, architecture, commands, and roadmap sections reconciled with the actual release candidate.
- [ ] Changelog and upgrade guide included in the release tree.
- [ ] Final release-candidate matrix green at one exact head.
- [ ] Final independent acceptance review performed against that exact head.

## Human-authority items

- [ ] Repository owner chooses and adds a software license if public reuse or package-index distribution is intended.

Bride does not infer a license. Absence of a license is not treated as permission to redistribute.

## Release boundary

Do not tag `v0.2.0`, create a GitHub Release, publish a package, or merge the candidate into another repository until all technical checklist items are green and the repository owner has made any required licensing/distribution decisions.

A release tag must point to the exact reviewed head. If any file changes after final acceptance, rerun the affected gates before tagging.
