from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from .contracts import DonorRole, Mechanism, PromotionVerdict, QualificationCase, QualificationResult, SubjectAdapter, TrialObservation
from .metrics import causal_effect, consistency, mean_quality, safe_ratio, specificity


@dataclass(frozen=True)
class QualificationPolicy:
    minimum_consistency: float = 0.67
    minimum_specificity: float = 0.15
    maximum_complexity_points: float = 3.0
    require_identity_preservation: bool = True
    require_truth_preservation: bool = True
    require_authority_preservation: bool = True
    require_replay_preservation: bool = True


class QualificationHarness:
    def __init__(self, policy: QualificationPolicy | None = None):
        self.policy = policy or QualificationPolicy()

    def _static_result(self, mechanism: Mechanism, cases: tuple[QualificationCase, ...], verdict: PromotionVerdict, reason: str) -> QualificationResult:
        return QualificationResult(
            mechanism_id=mechanism.spec.mechanism_id,
            verdict=verdict,
            causal_effect=0.0,
            consistency=1.0,
            specificity=1.0,
            baseline_quality=0.0,
            challenger_quality=0.0,
            quality_gain=0.0,
            truth_preserved=True,
            authority_preserved=True,
            replay_preserved=True,
            identity_preserved=True,
            renderer_invariant=None,
            latency_ratio=1.0,
            state_size_ratio=1.0,
            passed_cases=tuple(c.case_id for c in cases),
            failed_cases=(),
            reasons=(reason,),
        )

    def run(self, baseline_subject: SubjectAdapter, mechanism: Mechanism, cases: tuple[QualificationCase, ...], histories: dict[str, tuple[dict, ...]], probes: dict[str, dict]) -> QualificationResult:
        spec = mechanism.spec
        if spec.role in {DonorRole.EVALUATION, DonorRole.PROVENANCE}:
            return self._static_result(mechanism, cases, PromotionVerdict.INFRASTRUCTURE_ONLY, "research infrastructure is not promoted by behavioral superiority")
        if spec.requires_model:
            return self._static_result(mechanism, cases, PromotionVerdict.BLOCKED, "mechanism requires a live compatible model benchmark")

        by_case: dict[str, list[TrialObservation]] = defaultdict(list)
        failed_cases: list[str] = []
        passed_cases: list[str] = []
        reasons: list[str] = []
        all_observations: list[TrialObservation] = []
        baseline_quality_values: list[float] = []
        challenger_quality_values: list[float] = []

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

            case_obs = by_case[case.case_id]
            effect = causal_effect(case_obs, case.expected_channel)
            consistency_score = consistency(case_obs, case.expected_channel)
            baseline_quality = mean_quality(case_obs, case.expected_channel, case.expected_value, "baseline")
            challenger_quality = mean_quality(case_obs, case.expected_channel, case.expected_value, "challenger")
            quality_gain = challenger_quality - baseline_quality
            baseline_quality_values.append(baseline_quality)
            challenger_quality_values.append(challenger_quality)

            case_pass = (
                effect >= case.minimum_effect
                and consistency_score >= self.policy.minimum_consistency
                and challenger_quality >= case.minimum_challenger_quality
                and quality_gain >= case.minimum_quality_gain
            )
            if case_pass:
                passed_cases.append(case.case_id)
            else:
                failed_cases.append(case.case_id)
                reasons.append(
                    f"{case.case_id}: effect={effect:.3f}, consistency={consistency_score:.3f}, "
                    f"baseline_quality={baseline_quality:.3f}, challenger_quality={challenger_quality:.3f}, "
                    f"quality_gain={quality_gain:.3f}"
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
        baseline_quality = sum(baseline_quality_values) / len(baseline_quality_values) if baseline_quality_values else 0.0
        challenger_quality = sum(challenger_quality_values) / len(challenger_quality_values) if challenger_quality_values else 0.0
        quality_gain = challenger_quality - baseline_quality

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

        cost_ok = all(latency_ratio <= c.maximum_latency_ratio and state_size_ratio <= c.maximum_state_size_ratio for c in cases)
        if not cost_ok:
            reasons.append(f"cost regression: latency_ratio={latency_ratio:.3f}, state_size_ratio={state_size_ratio:.3f}")

        invariants_ok = (
            (truth_preserved or not self.policy.require_truth_preservation)
            and (authority_preserved or not self.policy.require_authority_preservation)
            and (identity_preserved or not self.policy.require_identity_preservation)
            and (replay_preserved or not self.policy.require_replay_preservation)
        )
        complexity_ok = spec.complexity_points <= self.policy.maximum_complexity_points

        if not invariants_ok:
            verdict = PromotionVerdict.REJECT
        elif failed_cases:
            verdict = PromotionVerdict.REJECT
        elif not cost_ok or not complexity_ok or spec.role == DonorRole.HISTORICAL:
            verdict = PromotionVerdict.HOLD
            if not complexity_ok:
                reasons.append(f"complexity {spec.complexity_points:.2f} exceeds automatic ceiling {self.policy.maximum_complexity_points:.2f}")
            if spec.role == DonorRole.HISTORICAL:
                reasons.append("historical donor requires a separately justified production need before promotion")
        elif spec.role == DonorRole.DEPLOYMENT:
            verdict = PromotionVerdict.ADAPTER_ONLY
            reasons.append("qualified at a host boundary without becoming subject authority")
        else:
            verdict = PromotionVerdict.PROMOTE
            reasons.append("challenger improved the frozen target and passed truth, authority, replay, identity, and cost gates")

        return QualificationResult(
            mechanism_id=spec.mechanism_id,
            verdict=verdict,
            causal_effect=effect,
            consistency=consistency_score,
            specificity=specificity_score,
            baseline_quality=baseline_quality,
            challenger_quality=challenger_quality,
            quality_gain=quality_gain,
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
