from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

from mbqc_ff_evaluator.domain.models import NumericSummary, OnePercArtifact, build_numeric_summary


@dataclass(frozen=True)
class AggregatedArtifacts:
    raw_depth_summary: NumericSummary
    hold_summary: NumericSummary
    meas_summary: NumericSummary


class AggregationService:
    """Aggregate artifact collections into numeric summaries."""

    def aggregate(self, artifacts: Iterable[OnePercArtifact]) -> AggregatedArtifacts:
        materialized = tuple(artifacts)
        if not materialized:
            raise ValueError("artifacts must not be empty")
        hold_values = tuple(
            float(item.required_lifetime_layers)
            for item in materialized
            if item.required_lifetime_layers is not None
        )
        meas_values = tuple(
            float(item.max_measure_delay_layers)
            for item in materialized
            if item.max_measure_delay_layers is not None
        )
        if not hold_values:
            raise ValueError("artifacts must include at least one required_lifetime_layers value")
        if not meas_values:
            raise ValueError("artifacts must include at least one max_measure_delay_layers value")
        return AggregatedArtifacts(
            raw_depth_summary=_summarize(materialized, lambda item: float(item.ff_chain_depth_raw)),
            hold_summary=build_numeric_summary(hold_values),
            meas_summary=build_numeric_summary(meas_values),
        )


def _summarize(
    artifacts: tuple[OnePercArtifact, ...],
    selector: Callable[[OnePercArtifact], float],
) -> NumericSummary:
    return build_numeric_summary(tuple(selector(artifact) for artifact in artifacts))
