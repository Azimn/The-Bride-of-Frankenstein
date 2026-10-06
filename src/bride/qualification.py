from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from .contracts import (
    DonorRole,
    Mechanism,
    PromotionVerdict,
    QualificationCase,
    QualificationResult,
    SubjectAdapter,
    TrialObservation,
)
from .metrics import causal_effect, consistency, safe_ratio, specificity


@dataclass(frozen=True)
class QualificationPolicy:
    minimum_consistency: float = 0.67
    minimum_specificity: float = 0.15
    require_identity_preservation: bool = True
    require_truth_preservation: bool = True
    require_authority_preservation: bool = True
    require_replay_preservation: bool = True


class QualificationHarness:
    def __init__(self, policy: QualificationPolicy | None = None):
        self.policy = policy or QualificationPolicy()

    def run(
        self,
        baseline_subject: SubjectAdapter,
        mechanism: Mechanism,
        cases: tuple[QualificationCase, ...],
        histories: dict[str, tuple[dict[str, Any], ...]],
        probes: dict[str, dict[str, Any]],
    ) -> QualificationResult:
        spec = mechanism.spec
        if spec.role in {DonorRole.EVALUATION, DonorRole.PROVENANCE}:
            return QualificationResult(
                mechanism_id=spec.mechanism_id,
                verdict=PromotionVerdict.INFRASTRUCTURE_ONLY,
                causal_effect=0.0,
                consistency=1.0,
                specificity=1.0,
                truth_preserved=True,
                authority_preserved=True,
                replay_preserved=True,
                identity_preserved=True,
                renderer_invariant=None,
                latency_ratio=1.0,
                state_size_ratio=1.0,
                passed_cases=tuple(c.case_id for c in cases),
                failed_cases=(),
                reasons=("research infrastructure is not promoted by behavioral superiority",),
            )

        by_case: dict[str, list[TrialObservation]] = defaultdict(list)
        failed_cases: list[str] = []
        passed_cases: list[str] = []
        reasons: list[str] = []
        all_observations: list[TrialObservation] = []

        for case in cases:
            history = histories.get(case.case_id, ())
            probe = probes.get(case.case_id, {})
            for replicate in range(case.minimum_replicates):
                root = baseline_subject.fork()
                root.apply_history(history)
                baseline = root.fork()
                challenger = root.fork()
                challenger.intervene(spec.mechanism_id, mechanism.intervention_payload(case, replicate))
                baseline_result = baseline.probe(probe)
                challenger_result = challenger.probe(probe)
                obs = TrialObservation(
                    baseline=baseline_result,
                    challenger=challenger_result,
                    baseline_snapshot=baseline.snapshot(),
                    challenger_snapshot=challenger.snapshot(),
                    intervention_label=case.intervention_label,
                    replicate=replicate,
                )
                by_case[case.case_id].append(obs)
                all_observations.append(obs)

            effect = causal_effect(by_case[case.case_id], case.expected_channel)
            consistency_score = consistency(by_case[case.case_id], case.expected_channel)
            if effect >= case.minimum_effect and consistency_score >= self.policy.minimum_consistency:
                passed_cases.append(case.case_id)
            else:
                failed_cases.append(case.case_id)
                reasons.append(
                    f"{case.case_id}: effect={effect:.3f}, consistency={consistency_score:.3f} "
                    f"did not meet effect>={case.minimum_effect:.3f} and consistency>={self.policy.minimum_consistency:.3f}"
                )

        truth_preserved = all(o.baseline_snapshot.historical_truth_digest == o.challenger_snapshot.historical_truth_digest for o in all_observations)
        authority_preserved = all(o.baseline_snapshot.authority_digest == o.challenger_snapshot.authority_digest for o in all_observations)
        identity_preserved = all(o.baseline_snapshot.identity_digest == o.challenger_snapshot.identity_digest for o in all_observations)
        replay_preserved = all(bool(o.challenger_snapshot.replay_digest) for o in all_observations)

        latency_ratios = [safe_ratio(o.challenger.latency_ms, o.baseline.latency_ms) for o in all_observations]
        state_ratios = [safe_ratio(float(o.challenger.state_size_bytes), float(o.baseline.state_size_bytes)) for o in all_observations]
        latency_ratio = sum(latency_ratios) / len(latency_ratios) if latency_ratios else 1.0
        state_size_ratio = sum(state_ratios) / len(state_ratios) if state_ratios else 1.0

        effect_values = [causal_effect(by_case[c.case_id], c.expected_channel) for c in cases]
        consistency_values = [consistency(by_case[c.case_id], c.expected_channel) for c in cases]
        specificity_values = [specificity(by_case[c.case_id], c.expected_channel) for c in cases]
        effect = sum(effect_values) / len(effect_values) if effect_values else 0.0
        consistency_score = sum(consistency_values) / len(consistency_values) if consistency_values else 0.0
        specificity_score = sum(specificity_values) / len(specificity_values) if specificity_values else 0.0

        if not truth_preserved:
            reasons.append("historical truth digest changed under the donor intervention")
        if not authority_preserved:
            reasons.append("architectural authority digest changed under the donor intervention")
        if not identity_preserved:
            reasons.append("identity digest changed under the donor intervention")
        if not replay_preserved:
            reasons.append("challenger state did not expose a valid replay digest")
        if specificity_score < self.policy.minimum_specificity:
            reasons.append(f"specificity {specificity_score:.3f} was below {self.policy.minimum_specificity:.3f}")

        cost_ok = all(
            latency_ratio <= case.maximum_latency_ratio and state_size_ratio <= case.maximum_state_size_ratio
            for case in cases
        )
        if not cost_ok:
            reasons.append(f"cost regression: latency_ratio={latency_ratio:.3f}, state_size_ratio={state_size_ratio:.3f}")

        invariants_ok = (
            (truth_preserved or not self.policy.require_truth_preservation)
            and (authority_preserved or not self.policy.require_authority_preservation)
            and (identity_preserved or not self.policy.require_identity_preservation)
            and (replay_preserved or not self.policy.require_replay_preservation)
        )

        if invariants_ok and cost_ok and not failed_cases and specificity_score >= self.policy.minimum_specificity:
            verdict = PromotionVerdict.PROMOTE
            reasons.append("all causal, longitudinal, authority, truth, replay, identity, and cost gates passed")
        elif not invariants_ok:
            verdict = PromotionVerdict.REJECT
        elif failed_cases:
            verdict = PromotionVerdict.REJECT
        else:
            verdict = PromotionVerdict.HOLD

        return QualificationResult(
            mechanism_id=spec.mechanism_id,
            verdict=verdict,
            causal_effect=effect,
            consistency=consistency_score,
            specificity=specificity_score,
            truth_preserved=truth_preserved,
            authority_preserved=authority_preserved,
            replay_preserved=replay_preserved,
            identity_preserved=identity_preserved,
            renderer_invariant=None,
            latency_ratio=latency_ratio,
            state_size_ratio=state_size_ratio,
            passed_cases=tuple(passed_cases),
            failed_cases=tuple(failed_cases),
            reasons=tuple(reasons),
        )
