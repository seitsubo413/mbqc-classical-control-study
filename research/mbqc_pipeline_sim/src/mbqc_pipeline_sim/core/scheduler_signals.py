"""Pure helpers for classifying runtime scheduling regimes."""
from __future__ import annotations

import math

from mbqc_pipeline_sim.domain.enums import SchedulerRegime
from mbqc_pipeline_sim.domain.models import PipelineConfig
from mbqc_pipeline_sim.domain.scheduler_models import SchedulerContext, SchedulerSignals

LOW_PRESSURE_THRESHOLD = 0.35
HIGH_PRESSURE_THRESHOLD = 0.75


def build_scheduler_signals(context: SchedulerContext) -> SchedulerSignals:
    ff_pressure_score = _ff_pressure_score(context)
    ff_backpressure_active = _ff_backpressure_active(context)
    is_ff_bottleneck = _is_ff_bottleneck_regime(context)
    is_fully_provisioned = _is_fully_provisioned_regime(context)
    recommended_regime = _recommend_regime(
        ff_pressure_score=ff_pressure_score,
        is_ff_bottleneck=is_ff_bottleneck,
        is_fully_provisioned=is_fully_provisioned,
    )
    return SchedulerSignals(
        ff_pressure_score=ff_pressure_score,
        ff_backpressure_active=ff_backpressure_active,
        is_ff_bottleneck=is_ff_bottleneck,
        is_fully_provisioned=is_fully_provisioned,
        recommended_regime=recommended_regime,
    )


def stall_aware_issue_limit(context: SchedulerContext, signals: SchedulerSignals | None = None) -> int:
    ff_width = context.config.ff_width
    if ff_width is None:
        return context.issue_limit
    active_signals = build_scheduler_signals(context) if signals is None else signals
    if active_signals.ff_backpressure_active:
        return min(context.issue_limit, ff_width)
    return context.issue_limit


def refined_stall_aware_issue_limit(
    context: SchedulerContext,
    signals: SchedulerSignals | None = None,
) -> int:
    ff_width = context.config.ff_width
    if ff_width is None or ff_width >= context.issue_limit:
        return context.issue_limit

    active_signals = build_scheduler_signals(context) if signals is None else signals
    if not active_signals.is_ff_bottleneck:
        return context.issue_limit
    if active_signals.ff_pressure_score <= LOW_PRESSURE_THRESHOLD:
        return context.issue_limit
    if active_signals.ff_pressure_score >= HIGH_PRESSURE_THRESHOLD:
        return ff_width

    score_span = HIGH_PRESSURE_THRESHOLD - LOW_PRESSURE_THRESHOLD
    progress = (active_signals.ff_pressure_score - LOW_PRESSURE_THRESHOLD) / score_span
    width_span = context.issue_limit - ff_width
    scaled_limit = context.issue_limit - math.ceil(progress * width_span)
    return max(ff_width, min(context.issue_limit, scaled_limit))


def _recommend_regime(
    *,
    ff_pressure_score: float,
    is_ff_bottleneck: bool,
    is_fully_provisioned: bool,
) -> SchedulerRegime:
    if is_ff_bottleneck and ff_pressure_score >= HIGH_PRESSURE_THRESHOLD:
        return SchedulerRegime.STALL_AWARE
    if is_fully_provisioned and ff_pressure_score <= LOW_PRESSURE_THRESHOLD:
        return SchedulerRegime.ASAP
    return SchedulerRegime.SHIFTED_CRITICAL


def _ff_backpressure_active(context: SchedulerContext) -> bool:
    ff_width = context.config.ff_width
    if ff_width is None:
        return False
    if context.waiting_ff_count > 0:
        return True
    if context.ff_slots_available == 0:
        return True
    return context.in_flight_meas_count >= ff_width


def _is_fully_provisioned_regime(context: SchedulerContext) -> bool:
    issue_width = context.config.issue_width
    return (
        _effective_meas_width(context.config) >= issue_width
        and _effective_ff_width(context.config) >= issue_width
    )


def _is_ff_bottleneck_regime(context: SchedulerContext) -> bool:
    issue_width = context.config.issue_width
    return _effective_ff_width(context.config) < min(issue_width, _effective_meas_width(context.config))


def _ff_pressure_score(context: SchedulerContext) -> float:
    ff_width = context.config.ff_width
    if ff_width is None:
        return 0.0

    queue_pressure = min(context.waiting_ff_count / ff_width, 1.0)
    meas_pressure = min(context.in_flight_meas_count / ff_width, 1.0)
    slot_pressure = _slot_pressure(context.ff_slots_available, ff_width)
    return round((queue_pressure + meas_pressure + slot_pressure) / 3.0, 6)


def _slot_pressure(slots_available: int | None, width: int) -> float:
    if slots_available is None:
        return 0.0
    clamped = max(0, min(slots_available, width))
    return 1.0 - (clamped / width)


def _effective_meas_width(config: PipelineConfig) -> int:
    return config.meas_width if config.meas_width is not None else config.issue_width


def _effective_ff_width(config: PipelineConfig) -> int:
    return config.ff_width if config.ff_width is not None else config.issue_width
