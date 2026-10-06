# Changelog

All notable production changes to the Frankenstein character runtime are recorded here. Research-only donor experiments remain documented in the Bride evidence and promotion ledgers.

## 0.2.0rc1 - 2026-10-06

This release candidate is the first production integration produced by the Bride donor-qualification program. It is derived from the accepted Frankenstein v0.1 baseline and includes only mechanisms that survived controlled real-baseline qualification, architecture-preserving integration, cross-platform regression, longitudinal qualification, repeated-interaction stress, and v0.1 upgrade hardening.

### Added

- Replayable bounded planning with canonical `PLAN_CREATED` and `PLAN_UPDATED` events.
- Plan steps enter the existing `DecisionEngine` as ordinary candidates rather than receiving a second execution path.
- Outcome-driven route switching, bounded alternative routes, restart persistence, completion, and exhaustion behavior.
- Narrow confidentiality commitment pressure for genuine disclosure choices.
- Bounded private-cognition concern admission with telemetry rejection, duplicate suppression, uncertainty labeling, and capped intensity.
- Private-concern pressure that modifies reflection candidate utility while preserving the existing `DecisionEngine` as the sole deliberate selector.
- Separate non-deliberative involuntary-expression channel for high pain or extreme surprise.
- Bride real-baseline donor qualification CLI and machine-readable evidence.
- Integrated longitudinal qualification covering planning persistence, confidentiality, private cognition, involuntary expression, combined pressure competition, renderer-swap semantic invariance, diagnostic fork isolation, cue-specific memory, and developmental divergence.
- Repeated-interaction stress qualification covering replay/restart, multi-restart plans, commitment retention, private-thought loop suppression, renderer drift, fork isolation, scaled memory retrieval, and developmental divergence.
- Authentic v0.1-to-v0.2 compatibility workflow generated from the exact accepted v0.1 commit.

### Changed

- Chat now uses the same unified v0.2 decision gateway as explicit decisions, preventing qualified pressures from being bypassed by the conversational path.
- Projection digests are normalized by semantic row content rather than SQLite `rowid`, making replay-equivalent state hash stable across physical insertion-order changes.
- Package version is now `0.2.0rc1`.
- Package description now reflects the production runtime rather than the donor laboratory.

### Compatibility

- Database schema remains version 1. No destructive migration is required.
- The authentic v0.1 compatibility matrix preserves legacy origin, canonical event IDs, canonical event hashes, semantic projection state, and legacy projected records.
- v0.1 backups restore under v0.2.
- Backups created after adding v0.2 plan and private-cognition state restore correctly under v0.2.
- Existing v0.1 CLI commands remain available.

### Intentional behavioral changes

- An open confidentiality commitment can now influence a later choice when disclosure is actually among the competing actions.
- A bounded private concern explicitly admitted from private cognition can now make reflection more competitive.
- An active plan can contribute its current step to ordinary action competition.
- Involuntary expression is available as a separate transient reflex channel, but it does not create a deliberate action or canonical fact.

Each of these effects has an explicit ablation path in the integration tests.

### Not promoted into the production core

- TinyPersona perception remains an adapter boundary.
- Pretorius selective recall and Digital Subject continuity influence were rejected as redundant in their frozen real-baseline cases.
- Contextual plasticity remains held by the complexity gate.
- Offscreen catch-up remains held by the cost gate.
- Omnicore six-dimensional affect remains a research hold.
- Activation steering and PersonaForge selective dual process remain blocked pending compatible live-model reproduction.

### Known evidence limits

- Renderer invariance has been demonstrated with deterministic renderer substitution and repeated renderer-divergence tests, not arbitrary live language models.
- The stress horizon is bounded and deterministic. It is not evidence of indefinite lifetime stability.
- The project evaluates functional continuity and causal behavior. It does not claim phenomenal consciousness or general human equivalence.

## 0.1.0

Accepted Frankenstein production baseline at `fdaf5be89ccf6991a20eb54649d5318a9adcb6ff`.

The v0.1 baseline established the append-only canonical event ledger, disposable projections, authority boundaries, evidence-backed beliefs, persistent relationships and prospective state, renderer separation, capability gating, replay/restart continuity, backup/restore, and cross-platform acceptance process.
