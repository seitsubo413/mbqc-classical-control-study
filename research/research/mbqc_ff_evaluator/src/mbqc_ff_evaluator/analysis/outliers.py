from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from statistics import median
from typing import Sequence

from mbqc_ff_evaluator.domain.models import OnePercArtifact, build_numeric_summary


@dataclass(frozen=True)
class MeasurementDelayOutlierRow:
    algorithm: str
    hardware_size: int
    logical_qubits: int
    seed: int
    max_measure_delay_layers: int
    group_median: float
    group_q1: float
    group_q3: float
    iqr: float
    outlier_threshold: float
    ratio_to_group_median: float


@dataclass(frozen=True)
class MeasurementDelayGroupSummaryRow:
    algorithm: str
    hardware_size: int
    logical_qubits: int
    n_seeds: int
    is_coupled: bool
    depth_raw_median: float
    hold_median: float | None
    meas_median: float
    meas_q1: float
    meas_q3: float
    outlier_threshold: float
    outlier_count: int
    max_meas: float
    max_over_median: float
    regime_hint: str


def analyze_measurement_delay_groups(
    artifacts: Sequence[OnePercArtifact],
) -> tuple[list[MeasurementDelayGroupSummaryRow], list[MeasurementDelayOutlierRow]]:
    groups: dict[tuple[str, int, int], list[OnePercArtifact]] = defaultdict(list)
    for artifact in artifacts:
        if artifact.max_measure_delay_layers is None:
            continue
        key = (
            artifact.config.algorithm.value,
            artifact.config.hardware_size,
            artifact.config.logical_qubits,
        )
        groups[key].append(artifact)

    group_rows: list[MeasurementDelayGroupSummaryRow] = []
    outlier_rows: list[MeasurementDelayOutlierRow] = []

    for (algorithm, hardware_size, logical_qubits), group in sorted(groups.items()):
        meas_values = tuple(float(artifact.max_measure_delay_layers) for artifact in group if artifact.max_measure_delay_layers is not None)
        if not meas_values:
            continue
        meas_summary = build_numeric_summary(meas_values)
        depth_summary = build_numeric_summary(tuple(float(artifact.ff_chain_depth_raw) for artifact in group))
        hold_values = tuple(
            float(artifact.required_lifetime_layers)
            for artifact in group
            if artifact.required_lifetime_layers is not None
        )
        hold_summary = build_numeric_summary(hold_values) if hold_values else None

        iqr = meas_summary.q3 - meas_summary.q1
        tukey_threshold = meas_summary.q3 + 1.5 * iqr
        mad = _median_absolute_deviation(meas_values, meas_summary.median)
        if mad > 0.0:
            mad_threshold = meas_summary.median + 3.0 * 1.4826 * mad
            outlier_threshold = min(tukey_threshold, mad_threshold)
        else:
            outlier_threshold = tukey_threshold
        max_meas = meas_summary.maximum
        max_over_median = max_meas / meas_summary.median if meas_summary.median > 0 else float("inf")
        outlier_count = 0

        for artifact in group:
            if artifact.max_measure_delay_layers is None:
                continue
            if float(artifact.max_measure_delay_layers) <= outlier_threshold:
                continue
            outlier_count += 1
            outlier_rows.append(
                MeasurementDelayOutlierRow(
                    algorithm=algorithm,
                    hardware_size=hardware_size,
                    logical_qubits=logical_qubits,
                    seed=artifact.config.seed,
                    max_measure_delay_layers=artifact.max_measure_delay_layers,
                    group_median=meas_summary.median,
                    group_q1=meas_summary.q1,
                    group_q3=meas_summary.q3,
                    iqr=iqr,
                    outlier_threshold=outlier_threshold,
                    ratio_to_group_median=artifact.max_measure_delay_layers / meas_summary.median,
                )
            )

        regime_hint = _classify_regime(
            depth_raw_median=depth_summary.median,
            hold_median=None if hold_summary is None else hold_summary.median,
            meas_median=meas_summary.median,
            outlier_count=outlier_count,
            max_over_median=max_over_median,
        )
        group_rows.append(
            MeasurementDelayGroupSummaryRow(
                algorithm=algorithm,
                hardware_size=hardware_size,
                logical_qubits=logical_qubits,
                n_seeds=len(group),
                is_coupled=logical_qubits == hardware_size * hardware_size,
                depth_raw_median=depth_summary.median,
                hold_median=None if hold_summary is None else hold_summary.median,
                meas_median=meas_summary.median,
                meas_q1=meas_summary.q1,
                meas_q3=meas_summary.q3,
                outlier_threshold=outlier_threshold,
                outlier_count=outlier_count,
                max_meas=max_meas,
                max_over_median=max_over_median,
                regime_hint=regime_hint,
            )
        )

    return group_rows, outlier_rows


def _classify_regime(
    *,
    depth_raw_median: float,
    hold_median: float | None,
    meas_median: float,
    outlier_count: int,
    max_over_median: float,
) -> str:
    baseline = max(depth_raw_median, hold_median or 0.0, 1.0)
    systematic_high = meas_median >= 5.0 * baseline
    seed_sensitive = outlier_count > 0 and max_over_median >= 5.0
    if systematic_high and seed_sensitive:
        return "mixed"
    if systematic_high:
        return "systematic_high"
    if seed_sensitive:
        return "seed_sensitive"
    return "stable"


def _median_absolute_deviation(values: tuple[float, ...], center: float) -> float:
    deviations = tuple(abs(value - center) for value in values)
    return float(median(deviations))
