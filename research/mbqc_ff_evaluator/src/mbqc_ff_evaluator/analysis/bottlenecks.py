from __future__ import annotations

from mbqc_ff_evaluator.domain.enums import ConstraintKind


def dominant_constraint(
    *,
    dependency_ns: float,
    hold_ns: float | None,
    measurement_ns: float | None,
) -> ConstraintKind | None:
    candidates: list[tuple[ConstraintKind, float]] = [
        (ConstraintKind.DEPENDENCY, dependency_ns),
    ]
    if hold_ns is not None:
        candidates.append((ConstraintKind.HOLD, hold_ns))
    if measurement_ns is not None:
        candidates.append((ConstraintKind.MEASUREMENT, measurement_ns))
    if not candidates:
        return None
    return min(candidates, key=lambda item: item[1])[0]
