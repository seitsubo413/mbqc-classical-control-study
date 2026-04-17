"""Derived numeric analyses for the shifted-DAG study."""
from __future__ import annotations

import csv
import math
import statistics
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable


@dataclass(frozen=True)
class SweepObservation:
    dag_variant: str
    algorithm: str
    hardware_size: int
    logical_qubits: int
    dag_seed: int
    policy: str
    release_mode: str
    issue_width: int
    l_meas: int
    l_ff: int
    meas_width: int | None
    ff_width: int | None
    ff_chain_depth: int
    ff_chain_depth_raw: int
    ff_chain_depth_shifted: int | None
    throughput: float
    stall_rate: float
    utilization: float


@dataclass(frozen=True)
class PairingKey:
    algorithm: str
    hardware_size: int
    logical_qubits: int
    dag_seed: int
    policy: str
    release_mode: str
    issue_width: int
    l_meas: int
    l_ff: int
    meas_width: int | None
    ff_width: int | None


@dataclass(frozen=True)
class PairedSeedEffect:
    algorithm: str
    hardware_size: int
    logical_qubits: int
    dag_seed: int
    policy: str
    release_mode: str
    issue_width: int
    l_meas: int
    l_ff: int
    meas_width: int | None
    ff_width: int | None
    raw_ff_chain_depth: int
    shifted_ff_chain_depth: int
    depth_reduction_pct: float
    raw_throughput: float
    shifted_throughput: float
    throughput_delta: float
    throughput_gain_pct: float
    raw_stall_rate: float
    shifted_stall_rate: float
    stall_rate_delta: float
    stall_reduction_pct: float
    raw_utilization: float
    shifted_utilization: float
    utilization_delta: float
    utilization_gain_pct: float
    raw_saturation_ratio: float
    raw_saturation_bucket: str
    raw_stall_bucket: str
    latency_profile: str
    width_profile: str


@dataclass(frozen=True)
class SummaryRow:
    pair_count: int
    unique_seed_count: int
    depth_reduction_pct_median: float
    throughput_gain_pct_median: float
    throughput_gain_pct_q1: float
    throughput_gain_pct_q3: float
    stall_reduction_pct_median: float
    utilization_gain_pct_median: float
    raw_throughput_median: float
    raw_stall_rate_median: float
    throughput_positive_count: int
    throughput_zero_count: int
    throughput_negative_count: int
    throughput_sign_test_pvalue: float


@dataclass(frozen=True)
class ShiftedStudyOutputs:
    paired_seed_effects: tuple[dict[str, object], ...]
    algorithm_summary: tuple[dict[str, object], ...]
    algorithm_hq_summary: tuple[dict[str, object], ...]
    bottleneck_summary: tuple[dict[str, object], ...]
    policy_variant_summary: tuple[dict[str, object], ...]
    policy_win_summary: tuple[dict[str, object], ...]
    policy_vs_asap_summary: tuple[dict[str, object], ...]
    policy_latency_summary: tuple[dict[str, object], ...]
    policy_saturation_summary: tuple[dict[str, object], ...]
    policy_width_summary: tuple[dict[str, object], ...]
    policy_stall_summary: tuple[dict[str, object], ...]
    width_equivalence_cases: tuple[dict[str, object], ...]
    width_equivalence_summary: tuple[dict[str, object], ...]
    stall_regression_cases: tuple[dict[str, object], ...]
    stall_regression_summary: tuple[dict[str, object], ...]
    gain_predictor_summary: tuple[dict[str, object], ...]
    exclusion_summary: tuple[dict[str, object], ...]


def read_sweep_observations(path: Path) -> tuple[SweepObservation, ...]:
    with path.open() as handle:
        rows = list(csv.DictReader(handle))
    return tuple(_parse_sweep_row(row) for row in rows)


def build_paired_seed_effects(
    observations: Iterable[SweepObservation],
) -> tuple[PairedSeedEffect, ...]:
    grouped: dict[PairingKey, dict[str, SweepObservation]] = defaultdict(dict)
    for observation in observations:
        key = PairingKey(
            algorithm=observation.algorithm,
            hardware_size=observation.hardware_size,
            logical_qubits=observation.logical_qubits,
            dag_seed=observation.dag_seed,
            policy=observation.policy,
            release_mode=observation.release_mode,
            issue_width=observation.issue_width,
            l_meas=observation.l_meas,
            l_ff=observation.l_ff,
            meas_width=observation.meas_width,
            ff_width=observation.ff_width,
        )
        grouped[key][observation.dag_variant] = observation

    effects: list[PairedSeedEffect] = []
    for key in sorted(grouped, key=_pairing_key_sort_key):
        variants = grouped[key]
        raw = variants.get("raw")
        shifted = variants.get("shifted")
        if raw is None or shifted is None:
            continue

        raw_saturation_ratio = raw.throughput / raw.issue_width if raw.issue_width > 0 else 0.0
        effects.append(
            PairedSeedEffect(
                algorithm=key.algorithm,
                hardware_size=key.hardware_size,
                logical_qubits=key.logical_qubits,
                dag_seed=key.dag_seed,
                policy=key.policy,
                release_mode=key.release_mode,
                issue_width=key.issue_width,
                l_meas=key.l_meas,
                l_ff=key.l_ff,
                meas_width=key.meas_width,
                ff_width=key.ff_width,
                raw_ff_chain_depth=raw.ff_chain_depth,
                shifted_ff_chain_depth=shifted.ff_chain_depth,
                depth_reduction_pct=_pct_reduction(raw.ff_chain_depth, shifted.ff_chain_depth),
                raw_throughput=raw.throughput,
                shifted_throughput=shifted.throughput,
                throughput_delta=round(shifted.throughput - raw.throughput, 6),
                throughput_gain_pct=_pct_change(raw.throughput, shifted.throughput),
                raw_stall_rate=raw.stall_rate,
                shifted_stall_rate=shifted.stall_rate,
                stall_rate_delta=round(shifted.stall_rate - raw.stall_rate, 6),
                stall_reduction_pct=_pct_reduction(raw.stall_rate, shifted.stall_rate),
                raw_utilization=raw.utilization,
                shifted_utilization=shifted.utilization,
                utilization_delta=round(shifted.utilization - raw.utilization, 6),
                utilization_gain_pct=_pct_change(raw.utilization, shifted.utilization),
                raw_saturation_ratio=round(raw_saturation_ratio, 6),
                raw_saturation_bucket=_raw_saturation_bucket(raw_saturation_ratio),
                raw_stall_bucket=_raw_stall_bucket(raw.stall_rate),
                latency_profile=_latency_profile(raw.l_meas, raw.l_ff),
                width_profile=_width_profile(raw.issue_width, raw.meas_width, raw.ff_width),
            )
        )
    return tuple(effects)


def build_shifted_study_outputs(
    observations: Iterable[SweepObservation],
) -> ShiftedStudyOutputs:
    observation_tuple = tuple(observations)
    effects = build_paired_seed_effects(observation_tuple)

    return ShiftedStudyOutputs(
        paired_seed_effects=tuple(_paired_effect_to_row(effect) for effect in effects),
        algorithm_summary=_summaries_to_rows(
            effects,
            lambda effect: {"algorithm": effect.algorithm},
        ),
        algorithm_hq_summary=_summaries_to_rows(
            effects,
            lambda effect: {
                "algorithm": effect.algorithm,
                "hardware_size": effect.hardware_size,
                "logical_qubits": effect.logical_qubits,
            },
        ),
        bottleneck_summary=_build_bottleneck_summary_rows(effects),
        policy_variant_summary=_build_policy_variant_summary_rows(observation_tuple),
        policy_win_summary=_build_policy_win_summary_rows(observation_tuple),
        policy_vs_asap_summary=_build_policy_vs_asap_summary_rows(observation_tuple),
        policy_latency_summary=_summaries_to_rows(
            effects,
            lambda effect: {
                "algorithm": effect.algorithm,
                "policy": effect.policy,
                "latency_profile": effect.latency_profile,
            },
        ),
        policy_saturation_summary=_summaries_to_rows(
            effects,
            lambda effect: {
                "algorithm": effect.algorithm,
                "policy": effect.policy,
                "raw_saturation_bucket": effect.raw_saturation_bucket,
            },
        ),
        policy_width_summary=_summaries_to_rows(
            effects,
            lambda effect: {
                "algorithm": effect.algorithm,
                "policy": effect.policy,
                "width_profile": effect.width_profile,
            },
        ),
        policy_stall_summary=_summaries_to_rows(
            effects,
            lambda effect: {
                "algorithm": effect.algorithm,
                "policy": effect.policy,
                "raw_stall_bucket": effect.raw_stall_bucket,
            },
        ),
        width_equivalence_cases=_build_width_equivalence_case_rows(effects),
        width_equivalence_summary=_build_width_equivalence_summary_rows(effects),
        stall_regression_cases=_build_stall_regression_case_rows(effects),
        stall_regression_summary=_build_stall_regression_summary_rows(effects),
        gain_predictor_summary=_build_gain_predictor_summary_rows(effects),
        exclusion_summary=_build_exclusion_summary_rows(observation_tuple),
    )


def write_shifted_study_outputs(outputs: ShiftedStudyOutputs, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(output_dir / "paired_seed_effects.csv", outputs.paired_seed_effects)
    _write_csv(output_dir / "algorithm_summary.csv", outputs.algorithm_summary)
    _write_csv(output_dir / "algorithm_hq_summary.csv", outputs.algorithm_hq_summary)
    _write_csv(output_dir / "bottleneck_summary.csv", outputs.bottleneck_summary)
    _write_csv(output_dir / "policy_variant_summary.csv", outputs.policy_variant_summary)
    _write_csv(output_dir / "policy_win_summary.csv", outputs.policy_win_summary)
    _write_csv(output_dir / "policy_vs_asap_summary.csv", outputs.policy_vs_asap_summary)
    _write_csv(output_dir / "policy_latency_summary.csv", outputs.policy_latency_summary)
    _write_csv(output_dir / "policy_saturation_summary.csv", outputs.policy_saturation_summary)
    _write_csv(output_dir / "policy_width_summary.csv", outputs.policy_width_summary)
    _write_csv(output_dir / "policy_stall_summary.csv", outputs.policy_stall_summary)
    _write_csv(output_dir / "width_equivalence_cases.csv", outputs.width_equivalence_cases)
    _write_csv(output_dir / "width_equivalence_summary.csv", outputs.width_equivalence_summary)
    _write_csv(output_dir / "stall_regression_cases.csv", outputs.stall_regression_cases)
    _write_csv(output_dir / "stall_regression_summary.csv", outputs.stall_regression_summary)
    _write_csv(output_dir / "gain_predictor_summary.csv", outputs.gain_predictor_summary)
    _write_csv(output_dir / "exclusion_summary.csv", outputs.exclusion_summary)


def _parse_sweep_row(row: dict[str, str]) -> SweepObservation:
    return SweepObservation(
        dag_variant=row["dag_variant"],
        algorithm=row["algorithm"],
        hardware_size=int(row["hardware_size"]),
        logical_qubits=int(row["logical_qubits"]),
        dag_seed=int(row["dag_seed"]),
        policy=row["policy"],
        release_mode=row.get("release_mode", "same_cycle"),
        issue_width=int(row["issue_width"]),
        l_meas=int(row["l_meas"]),
        l_ff=int(row["l_ff"]),
        meas_width=_optional_int(row.get("meas_width", "")),
        ff_width=_optional_int(row.get("ff_width", "")),
        ff_chain_depth=int(row["ff_chain_depth"]),
        ff_chain_depth_raw=int(row["ff_chain_depth_raw"]),
        ff_chain_depth_shifted=_optional_int(row.get("ff_chain_depth_shifted", "")),
        throughput=float(row["throughput"]),
        stall_rate=float(row["stall_rate"]),
        utilization=float(row["utilization"]),
    )


def _summaries_to_rows(
    effects: Iterable[PairedSeedEffect],
    key_fn: Callable[[PairedSeedEffect], dict[str, object]],
) -> tuple[dict[str, object], ...]:
    grouped: dict[tuple[tuple[str, object], ...], list[PairedSeedEffect]] = defaultdict(list)
    key_payloads: dict[tuple[tuple[str, object], ...], dict[str, object]] = {}
    for effect in effects:
        payload = key_fn(effect)
        key = tuple(sorted(payload.items()))
        grouped[key].append(effect)
        key_payloads[key] = payload

    rows: list[dict[str, object]] = []
    for key in sorted(grouped):
        summary = _summarize_effect_group(grouped[key])
        row = dict(key_payloads[key])
        row.update(_summary_row_to_mapping(summary))
        rows.append(row)
    return tuple(rows)


def _build_bottleneck_summary_rows(
    effects: Iterable[PairedSeedEffect],
) -> tuple[dict[str, object], ...]:
    grouped: dict[tuple[str, str, str], list[PairedSeedEffect]] = defaultdict(list)
    for effect in effects:
        grouped[(effect.algorithm, "raw_stall_bucket", effect.raw_stall_bucket)].append(effect)
        grouped[(effect.algorithm, "raw_saturation_bucket", effect.raw_saturation_bucket)].append(effect)
        grouped[(effect.algorithm, "latency_profile", effect.latency_profile)].append(effect)
        grouped[(effect.algorithm, "width_profile", effect.width_profile)].append(effect)
        grouped[(effect.algorithm, "policy", effect.policy)].append(effect)

    rows: list[dict[str, object]] = []
    for key in sorted(grouped):
        algorithm, group_type, group_value = key
        summary = _summarize_effect_group(grouped[key])
        row = {
            "algorithm": algorithm,
            "group_type": group_type,
            "group_value": group_value,
        }
        row.update(_summary_row_to_mapping(summary))
        rows.append(row)
    return tuple(rows)


def _build_policy_variant_summary_rows(
    observations: Iterable[SweepObservation],
) -> tuple[dict[str, object], ...]:
    grouped: dict[tuple[str, str, str, str, str], list[SweepObservation]] = defaultdict(list)
    for observation in observations:
        grouped[
            (
                observation.dag_variant,
                observation.algorithm,
                observation.policy,
                _latency_profile(observation.l_meas, observation.l_ff),
                _width_profile(
                    observation.issue_width,
                    observation.meas_width,
                    observation.ff_width,
                ),
            )
        ].append(observation)

    rows: list[dict[str, object]] = []
    for key in sorted(grouped):
        dag_variant, algorithm, policy, latency_profile, width_profile = key
        group = grouped[key]
        rows.append(
            {
                "dag_variant": dag_variant,
                "algorithm": algorithm,
                "policy": policy,
                "latency_profile": latency_profile,
                "width_profile": width_profile,
                "observation_count": len(group),
                "unique_seed_count": len({item.dag_seed for item in group}),
                "throughput_median": _round(_median(item.throughput for item in group)),
                "stall_rate_median": _round(_median(item.stall_rate for item in group)),
                "utilization_median": _round(_median(item.utilization for item in group)),
            }
        )
    return tuple(rows)


def _build_policy_win_summary_rows(
    observations: Iterable[SweepObservation],
) -> tuple[dict[str, object], ...]:
    grouped: dict[tuple[object, ...], list[SweepObservation]] = defaultdict(list)
    for observation in observations:
        grouped[
            (
                observation.dag_variant,
                observation.algorithm,
                observation.hardware_size,
                observation.logical_qubits,
                observation.dag_seed,
                observation.release_mode,
                observation.issue_width,
                observation.l_meas,
                observation.l_ff,
                observation.meas_width,
                observation.ff_width,
            )
        ].append(observation)

    summary: dict[tuple[str, str, str, str], dict[str, int]] = defaultdict(
        lambda: {
            "scenario_count": 0,
            "throughput_win_count": 0,
            "stall_win_count": 0,
            "joint_win_count": 0,
        }
    )
    for scenario in grouped.values():
        best_throughput = max(item.throughput for item in scenario)
        best_stall = min(item.stall_rate for item in scenario)
        for item in scenario:
            key = (
                item.dag_variant,
                item.algorithm,
                item.policy,
                _width_profile(item.issue_width, item.meas_width, item.ff_width),
            )
            summary[key]["scenario_count"] += 1
            throughput_winner = math.isclose(item.throughput, best_throughput)
            stall_winner = math.isclose(item.stall_rate, best_stall)
            if throughput_winner:
                summary[key]["throughput_win_count"] += 1
            if stall_winner:
                summary[key]["stall_win_count"] += 1
            if throughput_winner and stall_winner:
                summary[key]["joint_win_count"] += 1

    rows: list[dict[str, object]] = []
    for key in sorted(summary):
        dag_variant, algorithm, policy, width_profile = key
        counts = summary[key]
        scenario_count = counts["scenario_count"]
        rows.append(
            {
                "dag_variant": dag_variant,
                "algorithm": algorithm,
                "policy": policy,
                "width_profile": width_profile,
                "scenario_count": scenario_count,
                "throughput_win_count": counts["throughput_win_count"],
                "throughput_win_rate": _round(counts["throughput_win_count"] / scenario_count),
                "stall_win_count": counts["stall_win_count"],
                "stall_win_rate": _round(counts["stall_win_count"] / scenario_count),
                "joint_win_count": counts["joint_win_count"],
                "joint_win_rate": _round(counts["joint_win_count"] / scenario_count),
            }
        )
    return tuple(rows)


def _build_policy_vs_asap_summary_rows(
    observations: Iterable[SweepObservation],
) -> tuple[dict[str, object], ...]:
    grouped: dict[tuple[object, ...], dict[str, SweepObservation]] = defaultdict(dict)
    for observation in observations:
        grouped[
            (
                observation.dag_variant,
                observation.algorithm,
                observation.hardware_size,
                observation.logical_qubits,
                observation.dag_seed,
                observation.release_mode,
                observation.issue_width,
                observation.l_meas,
                observation.l_ff,
                observation.meas_width,
                observation.ff_width,
            )
        ][observation.policy] = observation

    summary: dict[tuple[str, str, str, str], list[dict[str, float]]] = defaultdict(list)
    for scenario in grouped.values():
        asap = scenario.get("asap")
        if asap is None:
            continue
        width_profile = _width_profile(asap.issue_width, asap.meas_width, asap.ff_width)
        for policy, observation in scenario.items():
            summary[(asap.dag_variant, asap.algorithm, policy, width_profile)].append(
                {
                    "throughput_delta_pct": _pct_change(asap.throughput, observation.throughput),
                    "stall_delta_pct": _pct_change(asap.stall_rate, observation.stall_rate),
                    "utilization_delta_pct": _pct_change(asap.utilization, observation.utilization),
                    "throughput_better": 1.0 if observation.throughput > asap.throughput else 0.0,
                    "stall_better": 1.0 if observation.stall_rate < asap.stall_rate else 0.0,
                    "joint_better": 1.0
                    if observation.throughput > asap.throughput and observation.stall_rate < asap.stall_rate
                    else 0.0,
                }
            )

    rows: list[dict[str, object]] = []
    for key in sorted(summary):
        dag_variant, algorithm, policy, width_profile = key
        group = summary[key]
        pair_count = len(group)
        rows.append(
            {
                "dag_variant": dag_variant,
                "algorithm": algorithm,
                "policy": policy,
                "width_profile": width_profile,
                "pair_count": pair_count,
                "throughput_delta_pct_median_vs_asap": _round(
                    _median(item["throughput_delta_pct"] for item in group)
                ),
                "stall_delta_pct_median_vs_asap": _round(
                    _median(item["stall_delta_pct"] for item in group)
                ),
                "utilization_delta_pct_median_vs_asap": _round(
                    _median(item["utilization_delta_pct"] for item in group)
                ),
                "throughput_better_count_vs_asap": int(sum(item["throughput_better"] for item in group)),
                "stall_better_count_vs_asap": int(sum(item["stall_better"] for item in group)),
                "joint_better_count_vs_asap": int(sum(item["joint_better"] for item in group)),
            }
        )
    return tuple(rows)


def _build_exclusion_summary_rows(
    observations: Iterable[SweepObservation],
) -> tuple[dict[str, object], ...]:
    grouped: dict[tuple[str, int, int], dict[str, set[int]]] = defaultdict(
        lambda: {"raw": set(), "shifted": set()}
    )
    all_raw: set[tuple[str, int, int, int]] = set()
    all_shifted: set[tuple[str, int, int, int]] = set()
    for observation in observations:
        group = grouped[(observation.algorithm, observation.hardware_size, observation.logical_qubits)]
        group[observation.dag_variant].add(observation.dag_seed)
        token = (
            observation.algorithm,
            observation.hardware_size,
            observation.logical_qubits,
            observation.dag_seed,
        )
        if observation.dag_variant == "raw":
            all_raw.add(token)
        elif observation.dag_variant == "shifted":
            all_shifted.add(token)

    rows: list[dict[str, object]] = []
    overall_missing = len(all_raw - all_shifted)
    rows.append(
        {
            "scope": "overall",
            "algorithm": "ALL",
            "hardware_size": "",
            "logical_qubits": "",
            "raw_seed_count": len(all_raw),
            "shifted_seed_count": len(all_shifted),
            "missing_shifted_seed_count": overall_missing,
            "paired_seed_count": len(all_raw & all_shifted),
            "is_complete_pair_set": "yes" if overall_missing == 0 else "no",
        }
    )

    for key in sorted(grouped):
        algorithm, hardware_size, logical_qubits = key
        raw_seeds = grouped[key]["raw"]
        shifted_seeds = grouped[key]["shifted"]
        missing = len(raw_seeds - shifted_seeds)
        rows.append(
            {
                "scope": "algorithm_hq",
                "algorithm": algorithm,
                "hardware_size": hardware_size,
                "logical_qubits": logical_qubits,
                "raw_seed_count": len(raw_seeds),
                "shifted_seed_count": len(shifted_seeds),
                "missing_shifted_seed_count": missing,
                "paired_seed_count": len(raw_seeds & shifted_seeds),
                "is_complete_pair_set": "yes" if missing == 0 else "no",
            }
        )
    return tuple(rows)


def _build_width_equivalence_case_rows(
    effects: Iterable[PairedSeedEffect],
) -> tuple[dict[str, object], ...]:
    grouped: dict[tuple[object, ...], list[PairedSeedEffect]] = defaultdict(list)
    for effect in effects:
        key = (
            effect.algorithm,
            effect.hardware_size,
            effect.logical_qubits,
            effect.dag_seed,
            effect.policy,
            effect.release_mode,
            effect.issue_width,
            effect.l_meas,
            effect.l_ff,
        )
        grouped[key].append(effect)

    rows: list[dict[str, object]] = []
    for key in sorted(grouped):
        group = grouped[key]
        width_profiles = sorted(effect.width_profile for effect in group)
        signatures: dict[tuple[float, ...], list[str]] = defaultdict(list)
        for effect in group:
            signatures[_width_outcome_signature(effect)].append(effect.width_profile)
        equivalent_groups = [
            "|".join(sorted(set(profiles)))
            for _signature, profiles in sorted(signatures.items(), key=lambda item: item[0])
        ]
        rows.append(
            {
                "algorithm": key[0],
                "hardware_size": key[1],
                "logical_qubits": key[2],
                "dag_seed": key[3],
                "policy": key[4],
                "release_mode": key[5],
                "issue_width": key[6],
                "l_meas": key[7],
                "l_ff": key[8],
                "width_profile_count": len(width_profiles),
                "unique_outcome_count": len(signatures),
                "is_width_inactive": "yes" if len(signatures) == 1 else "no",
                "width_profiles": ",".join(width_profiles),
                "equivalent_profile_groups": ";".join(equivalent_groups),
            }
        )
    return tuple(rows)


def _build_width_equivalence_summary_rows(
    effects: Iterable[PairedSeedEffect],
) -> tuple[dict[str, object], ...]:
    case_rows = _build_width_equivalence_case_rows(effects)
    grouped: dict[tuple[str, int, str], list[dict[str, object]]] = defaultdict(list)
    for row in case_rows:
        grouped[(str(row["algorithm"]), int(row["issue_width"]), str(row["policy"]))].append(row)

    rows: list[dict[str, object]] = []
    for key in sorted(grouped):
        algorithm, issue_width, policy = key
        group = grouped[key]
        inactive_count = sum(1 for row in group if row["is_width_inactive"] == "yes")
        rows.append(
            {
                "algorithm": algorithm,
                "issue_width": issue_width,
                "policy": policy,
                "case_count": len(group),
                "inactive_case_count": inactive_count,
                "inactive_case_rate": _round(inactive_count / len(group)),
                "max_width_profile_count": max(int(row["width_profile_count"]) for row in group),
            }
        )
    return tuple(rows)


def _build_stall_regression_case_rows(
    effects: Iterable[PairedSeedEffect],
) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    for effect in effects:
        if effect.stall_reduction_pct >= 0.0:
            continue
        rows.append(
            {
                **_paired_effect_to_row(effect),
                "throughput_direction": _throughput_direction(effect.throughput_delta),
                "stall_direction": "worse",
            }
        )
    return tuple(rows)


def _build_stall_regression_summary_rows(
    effects: Iterable[PairedSeedEffect],
) -> tuple[dict[str, object], ...]:
    regressions = [effect for effect in effects if effect.stall_reduction_pct < 0.0]
    grouped: dict[tuple[str, str, str, str], list[PairedSeedEffect]] = defaultdict(list)
    for effect in regressions:
        grouped[(effect.algorithm, effect.policy, effect.latency_profile, effect.width_profile)].append(effect)

    rows: list[dict[str, object]] = []
    for key in sorted(grouped):
        algorithm, policy, latency_profile, width_profile = key
        group = grouped[key]
        throughput_directions = [_throughput_direction(effect.throughput_delta) for effect in group]
        rows.append(
            {
                "algorithm": algorithm,
                "policy": policy,
                "latency_profile": latency_profile,
                "width_profile": width_profile,
                "case_count": len(group),
                "throughput_improved_count": sum(1 for item in throughput_directions if item == "improved"),
                "throughput_equal_count": sum(1 for item in throughput_directions if item == "equal"),
                "throughput_worse_count": sum(1 for item in throughput_directions if item == "worse"),
                "stall_reduction_pct_median": _round(_median(effect.stall_reduction_pct for effect in group)),
                "throughput_gain_pct_median": _round(_median(effect.throughput_gain_pct for effect in group)),
            }
        )
    return tuple(rows)


def _build_gain_predictor_summary_rows(
    effects: Iterable[PairedSeedEffect],
) -> tuple[dict[str, object], ...]:
    grouped: dict[tuple[str, str, str, str, str, str], list[PairedSeedEffect]] = defaultdict(list)
    for effect in effects:
        grouped[
            (
                effect.algorithm,
                effect.policy,
                effect.raw_stall_bucket,
                effect.raw_saturation_bucket,
                effect.latency_profile,
                effect.width_profile,
            )
        ].append(effect)

    rows: list[dict[str, object]] = []
    for key in sorted(grouped):
        algorithm, policy, raw_stall_bucket, raw_saturation_bucket, latency_profile, width_profile = key
        group = grouped[key]
        gain_positive_count = sum(1 for effect in group if effect.throughput_gain_pct > 0.0)
        gain_ge_5_count = sum(1 for effect in group if effect.throughput_gain_pct >= 5.0)
        gain_ge_20_count = sum(1 for effect in group if effect.throughput_gain_pct >= 20.0)
        gain_positive_rate = gain_positive_count / len(group)
        gain_ge_5_rate = gain_ge_5_count / len(group)
        gain_ge_20_rate = gain_ge_20_count / len(group)
        rows.append(
            {
                "algorithm": algorithm,
                "policy": policy,
                "raw_stall_bucket": raw_stall_bucket,
                "raw_saturation_bucket": raw_saturation_bucket,
                "latency_profile": latency_profile,
                "width_profile": width_profile,
                "pair_count": len(group),
                "throughput_gain_pct_median": _round(_median(effect.throughput_gain_pct for effect in group)),
                "gain_positive_count": gain_positive_count,
                "gain_positive_rate": _round(gain_positive_rate),
                "gain_ge_5_count": gain_ge_5_count,
                "gain_ge_5_rate": _round(gain_ge_5_rate),
                "gain_ge_20_count": gain_ge_20_count,
                "gain_ge_20_rate": _round(gain_ge_20_rate),
                "predicted_gain_band": _predicted_gain_band(gain_positive_rate, gain_ge_5_rate, gain_ge_20_rate),
            }
        )
    return tuple(rows)


def _paired_effect_to_row(effect: PairedSeedEffect) -> dict[str, object]:
    return {
        "algorithm": effect.algorithm,
        "hardware_size": effect.hardware_size,
        "logical_qubits": effect.logical_qubits,
        "dag_seed": effect.dag_seed,
        "policy": effect.policy,
        "release_mode": effect.release_mode,
        "issue_width": effect.issue_width,
        "l_meas": effect.l_meas,
        "l_ff": effect.l_ff,
        "meas_width": effect.meas_width if effect.meas_width is not None else "",
        "ff_width": effect.ff_width if effect.ff_width is not None else "",
        "raw_ff_chain_depth": effect.raw_ff_chain_depth,
        "shifted_ff_chain_depth": effect.shifted_ff_chain_depth,
        "depth_reduction_pct": effect.depth_reduction_pct,
        "raw_throughput": effect.raw_throughput,
        "shifted_throughput": effect.shifted_throughput,
        "throughput_delta": effect.throughput_delta,
        "throughput_gain_pct": effect.throughput_gain_pct,
        "raw_stall_rate": effect.raw_stall_rate,
        "shifted_stall_rate": effect.shifted_stall_rate,
        "stall_rate_delta": effect.stall_rate_delta,
        "stall_reduction_pct": effect.stall_reduction_pct,
        "raw_utilization": effect.raw_utilization,
        "shifted_utilization": effect.shifted_utilization,
        "utilization_delta": effect.utilization_delta,
        "utilization_gain_pct": effect.utilization_gain_pct,
        "raw_saturation_ratio": effect.raw_saturation_ratio,
        "raw_saturation_bucket": effect.raw_saturation_bucket,
        "raw_stall_bucket": effect.raw_stall_bucket,
        "latency_profile": effect.latency_profile,
        "width_profile": effect.width_profile,
    }


def _summarize_effect_group(group: list[PairedSeedEffect]) -> SummaryRow:
    throughput_values = sorted(effect.throughput_gain_pct for effect in group)
    throughput_positive_count = sum(1 for value in throughput_values if value > 0.0)
    throughput_zero_count = sum(1 for value in throughput_values if value == 0.0)
    throughput_negative_count = sum(1 for value in throughput_values if value < 0.0)

    return SummaryRow(
        pair_count=len(group),
        unique_seed_count=len({effect.dag_seed for effect in group}),
        depth_reduction_pct_median=_round(_median(effect.depth_reduction_pct for effect in group)),
        throughput_gain_pct_median=_round(_median(throughput_values)),
        throughput_gain_pct_q1=_round(_q1(throughput_values)),
        throughput_gain_pct_q3=_round(_q3(throughput_values)),
        stall_reduction_pct_median=_round(_median(effect.stall_reduction_pct for effect in group)),
        utilization_gain_pct_median=_round(_median(effect.utilization_gain_pct for effect in group)),
        raw_throughput_median=_round(_median(effect.raw_throughput for effect in group)),
        raw_stall_rate_median=_round(_median(effect.raw_stall_rate for effect in group)),
        throughput_positive_count=throughput_positive_count,
        throughput_zero_count=throughput_zero_count,
        throughput_negative_count=throughput_negative_count,
        throughput_sign_test_pvalue=_round(
            _two_sided_sign_test_pvalue(
                throughput_positive_count,
                throughput_negative_count,
            )
        ),
    )


def _summary_row_to_mapping(summary: SummaryRow) -> dict[str, object]:
    return {
        "pair_count": summary.pair_count,
        "unique_seed_count": summary.unique_seed_count,
        "depth_reduction_pct_median": summary.depth_reduction_pct_median,
        "throughput_gain_pct_median": summary.throughput_gain_pct_median,
        "throughput_gain_pct_q1": summary.throughput_gain_pct_q1,
        "throughput_gain_pct_q3": summary.throughput_gain_pct_q3,
        "stall_reduction_pct_median": summary.stall_reduction_pct_median,
        "utilization_gain_pct_median": summary.utilization_gain_pct_median,
        "raw_throughput_median": summary.raw_throughput_median,
        "raw_stall_rate_median": summary.raw_stall_rate_median,
        "throughput_positive_count": summary.throughput_positive_count,
        "throughput_zero_count": summary.throughput_zero_count,
        "throughput_negative_count": summary.throughput_negative_count,
        "throughput_sign_test_pvalue": summary.throughput_sign_test_pvalue,
    }


def _width_outcome_signature(effect: PairedSeedEffect) -> tuple[float, ...]:
    return (
        effect.raw_throughput,
        effect.shifted_throughput,
        effect.raw_stall_rate,
        effect.shifted_stall_rate,
        effect.raw_utilization,
        effect.shifted_utilization,
    )


def _pairing_key_sort_key(key: PairingKey) -> tuple[object, ...]:
    return (
        key.algorithm,
        key.hardware_size,
        key.logical_qubits,
        key.dag_seed,
        key.policy,
        key.release_mode,
        key.issue_width,
        key.l_meas,
        key.l_ff,
        key.meas_width if key.meas_width is not None else -1,
        key.ff_width if key.ff_width is not None else -1,
    )


def _write_csv(path: Path, rows: tuple[dict[str, object], ...]) -> None:
    if not rows:
        return
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _optional_int(value: str | None) -> int | None:
    if value is None or value == "":
        return None
    return int(value)


def _round(value: float) -> float:
    return round(value, 6)


def _median(values: Iterable[float]) -> float:
    return statistics.median(list(values))


def _q1(values: list[float]) -> float:
    if not values:
        return 0.0
    midpoint = len(values) // 2
    sample = values[:midpoint] if len(values) > 1 else values
    return statistics.median(sample)


def _q3(values: list[float]) -> float:
    if not values:
        return 0.0
    midpoint = (len(values) + 1) // 2
    sample = values[midpoint:] if len(values) > 1 else values
    return statistics.median(sample)


def _pct_change(base: float, new: float) -> float:
    if math.isclose(base, 0.0):
        return 0.0 if math.isclose(new, 0.0) else 100.0
    return round(((new - base) / base) * 100.0, 6)


def _pct_reduction(base: float, reduced: float) -> float:
    if math.isclose(base, 0.0):
        return 0.0 if math.isclose(reduced, 0.0) else -100.0
    return round(((base - reduced) / base) * 100.0, 6)


def _raw_stall_bucket(value: float) -> str:
    if math.isclose(value, 0.0):
        return "stall_free"
    if value <= 0.05:
        return "stall_low"
    if value <= 0.15:
        return "stall_medium"
    return "stall_high"


def _raw_saturation_bucket(value: float) -> str:
    if value < 0.5:
        return "underutilized"
    if value < 0.8:
        return "active"
    if value < 0.95:
        return "near_saturation"
    return "saturated"


def _latency_profile(l_meas: int, l_ff: int) -> str:
    if l_meas == 1 and l_ff == 1:
        return "l1_l1"
    if l_meas == 2 and l_ff == 2:
        return "l2_l2"
    return "mixed"


def _width_profile(issue_width: int, meas_width: int | None, ff_width: int | None) -> str:
    meas_token = "unbounded" if meas_width is None else str(meas_width)
    ff_token = "unbounded" if ff_width is None else str(ff_width)
    return f"W{issue_width}_M{meas_token}_F{ff_token}"


def _two_sided_sign_test_pvalue(wins: int, losses: int) -> float:
    trials = wins + losses
    if trials == 0:
        return 1.0
    tail = min(wins, losses)
    probability = sum(math.comb(trials, k) for k in range(tail + 1)) / (2**trials)
    return min(1.0, 2.0 * probability)


def _throughput_direction(delta: float) -> str:
    if delta > 0.0:
        return "improved"
    if delta < 0.0:
        return "worse"
    return "equal"


def _predicted_gain_band(gain_positive_rate: float, gain_ge_5_rate: float, gain_ge_20_rate: float) -> str:
    if gain_ge_20_rate >= 0.8:
        return "strong"
    if gain_ge_5_rate >= 0.8:
        return "moderate"
    if gain_positive_rate >= 0.8:
        return "weak"
    return "unlikely"


# ---------------------------------------------------------------------------
# D_ff correlation analysis (Option 3)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DffPolicyCase:
    """Per-seed, per-scenario policy vs ASAP comparison with D_ff."""

    dag_variant: str
    algorithm: str
    hardware_size: int
    logical_qubits: int
    dag_seed: int
    policy: str
    l_meas: int
    l_ff: int
    meas_width: int | None
    ff_width: int | None
    ff_chain_depth: int
    ff_chain_depth_raw: int
    ff_chain_depth_shifted: int | None
    throughput_asap: float
    throughput_policy: float
    throughput_vs_asap_pct: float
    stall_asap: float
    stall_policy: float
    stall_vs_asap_pct: float  # positive = stall increased (worse), negative = improved


@dataclass(frozen=True)
class DffCorrelationBin:
    """Median policy vs ASAP metrics, grouped by D_ff bin."""

    dag_variant: str
    policy: str
    ff_chain_depth_bin: str
    ff_chain_depth_bin_min: int
    ff_chain_depth_bin_max: int
    case_count: int
    throughput_vs_asap_pct_median: float
    stall_vs_asap_pct_median: float
    throughput_positive_rate: float
    stall_positive_rate: float  # fraction where stall improved vs asap


def build_dff_policy_cases(
    observations: Iterable[SweepObservation],
) -> tuple[DffPolicyCase, ...]:
    """For each scenario, compare every policy vs ASAP on the same dag_variant."""
    # Group by (dag_variant, alg, H, Q, seed, l_meas, l_ff, meas_width, ff_width)
    ScenarioKey = tuple[str, str, int, int, int, int, int, int | None, int | None]
    grouped: dict[ScenarioKey, dict[str, SweepObservation]] = defaultdict(dict)
    for obs in observations:
        key: ScenarioKey = (
            obs.dag_variant,
            obs.algorithm,
            obs.hardware_size,
            obs.logical_qubits,
            obs.dag_seed,
            obs.l_meas,
            obs.l_ff,
            obs.meas_width,
            obs.ff_width,
        )
        grouped[key][obs.policy] = obs

    cases: list[DffPolicyCase] = []
    for key in sorted(grouped):
        scenario = grouped[key]
        asap = scenario.get("asap")
        if asap is None:
            continue
        dag_variant, algorithm, hardware_size, logical_qubits, dag_seed, l_meas, l_ff, meas_width, ff_width = key
        for policy, obs in sorted(scenario.items()):
            cases.append(
                DffPolicyCase(
                    dag_variant=dag_variant,
                    algorithm=algorithm,
                    hardware_size=hardware_size,
                    logical_qubits=logical_qubits,
                    dag_seed=dag_seed,
                    policy=policy,
                    l_meas=l_meas,
                    l_ff=l_ff,
                    meas_width=meas_width,
                    ff_width=ff_width,
                    ff_chain_depth=obs.ff_chain_depth,
                    ff_chain_depth_raw=obs.ff_chain_depth_raw,
                    ff_chain_depth_shifted=obs.ff_chain_depth_shifted,
                    throughput_asap=asap.throughput,
                    throughput_policy=obs.throughput,
                    throughput_vs_asap_pct=_pct_change(asap.throughput, obs.throughput),
                    stall_asap=asap.stall_rate,
                    stall_policy=obs.stall_rate,
                    stall_vs_asap_pct=_pct_change(asap.stall_rate, obs.stall_rate),
                )
            )
    return tuple(cases)


def build_dff_correlation_bins(
    cases: Iterable[DffPolicyCase],
    bins: tuple[tuple[int, int], ...] = ((1, 2), (3, 5), (6, 15), (16, 40), (41, 100), (101, 400)),
) -> tuple[DffCorrelationBin, ...]:
    """Aggregate DffPolicyCase into D_ff bins for summary."""
    def _bin_label(lo: int, hi: int) -> str:
        return f"{lo}-{hi}"

    grouped: dict[tuple[str, str, str], list[DffPolicyCase]] = defaultdict(list)
    bin_bounds: dict[str, tuple[int, int]] = {}
    for case in cases:
        for lo, hi in bins:
            if lo <= case.ff_chain_depth <= hi:
                label = _bin_label(lo, hi)
                bin_bounds[label] = (lo, hi)
                grouped[(case.dag_variant, case.policy, label)].append(case)
                break

    rows: list[DffCorrelationBin] = []
    for key in sorted(grouped):
        dag_variant, policy, label = key
        group = grouped[key]
        lo, hi = bin_bounds[label]
        rows.append(
            DffCorrelationBin(
                dag_variant=dag_variant,
                policy=policy,
                ff_chain_depth_bin=label,
                ff_chain_depth_bin_min=lo,
                ff_chain_depth_bin_max=hi,
                case_count=len(group),
                throughput_vs_asap_pct_median=_round(_median(c.throughput_vs_asap_pct for c in group)),
                stall_vs_asap_pct_median=_round(_median(c.stall_vs_asap_pct for c in group)),
                throughput_positive_rate=_round(
                    sum(1 for c in group if c.throughput_vs_asap_pct > 0.0) / len(group)
                ),
                stall_positive_rate=_round(
                    sum(1 for c in group if c.stall_vs_asap_pct < 0.0) / len(group)
                ),
            )
        )
    return tuple(rows)


def _dff_case_to_row(case: DffPolicyCase) -> dict[str, object]:
    return {
        "dag_variant": case.dag_variant,
        "algorithm": case.algorithm,
        "hardware_size": case.hardware_size,
        "logical_qubits": case.logical_qubits,
        "dag_seed": case.dag_seed,
        "policy": case.policy,
        "l_meas": case.l_meas,
        "l_ff": case.l_ff,
        "meas_width": case.meas_width if case.meas_width is not None else "",
        "ff_width": case.ff_width if case.ff_width is not None else "",
        "ff_chain_depth": case.ff_chain_depth,
        "ff_chain_depth_raw": case.ff_chain_depth_raw,
        "ff_chain_depth_shifted": case.ff_chain_depth_shifted if case.ff_chain_depth_shifted is not None else "",
        "throughput_asap": case.throughput_asap,
        "throughput_policy": case.throughput_policy,
        "throughput_vs_asap_pct": case.throughput_vs_asap_pct,
        "stall_asap": case.stall_asap,
        "stall_policy": case.stall_policy,
        "stall_vs_asap_pct": case.stall_vs_asap_pct,
    }


def _dff_bin_to_row(bin_: DffCorrelationBin) -> dict[str, object]:
    return {
        "dag_variant": bin_.dag_variant,
        "policy": bin_.policy,
        "ff_chain_depth_bin": bin_.ff_chain_depth_bin,
        "ff_chain_depth_bin_min": bin_.ff_chain_depth_bin_min,
        "ff_chain_depth_bin_max": bin_.ff_chain_depth_bin_max,
        "case_count": bin_.case_count,
        "throughput_vs_asap_pct_median": bin_.throughput_vs_asap_pct_median,
        "stall_vs_asap_pct_median": bin_.stall_vs_asap_pct_median,
        "throughput_positive_rate": bin_.throughput_positive_rate,
        "stall_positive_rate": bin_.stall_positive_rate,
    }


def write_dff_correlation_outputs(
    cases: tuple[DffPolicyCase, ...],
    bins: tuple[DffCorrelationBin, ...],
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(output_dir / "dff_policy_cases.csv", tuple(_dff_case_to_row(c) for c in cases))
    _write_csv(output_dir / "dff_correlation_bins.csv", tuple(_dff_bin_to_row(b) for b in bins))
