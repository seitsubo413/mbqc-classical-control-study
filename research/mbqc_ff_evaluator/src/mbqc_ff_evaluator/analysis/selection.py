from __future__ import annotations

from mbqc_ff_evaluator.analysis.models import BudgetRow, BudgetSelection
from mbqc_ff_evaluator.domain.enums import BudgetSelectionMode


def is_coupled_configuration(hardware_size: int, logical_qubits: int) -> bool:
    return logical_qubits == hardware_size * hardware_size


def filter_budget_rows(
    rows: list[BudgetRow],
    selection: BudgetSelection,
    *,
    algorithm: str | None = None,
) -> list[BudgetRow]:
    filtered: list[BudgetRow] = []
    for row in rows:
        if abs(row.tau_ph_us - selection.tau_ph_us) > 0.01:
            continue
        if algorithm is not None and row.algorithm != algorithm:
            continue
        if selection.mode is BudgetSelectionMode.ALL:
            filtered.append(row)
            continue
        if selection.mode is BudgetSelectionMode.COUPLED_ONLY:
            if row.is_coupled:
                filtered.append(row)
            continue
        if selection.mode is BudgetSelectionMode.FIXED_H:
            if selection.hardware_size is None:
                raise ValueError("hardware_size is required for FIXED_H selection")
            if row.hardware_size == selection.hardware_size:
                filtered.append(row)
            continue
        if selection.mode is BudgetSelectionMode.FIXED_Q:
            if selection.logical_qubits is None:
                raise ValueError("logical_qubits is required for FIXED_Q selection")
            if row.logical_qubits == selection.logical_qubits:
                filtered.append(row)
            continue
        raise ValueError(f"unsupported selection mode: {selection.mode.value}")
    return filtered


def selection_label(selection: BudgetSelection) -> str:
    if selection.mode is BudgetSelectionMode.ALL:
        return "all configurations"
    if selection.mode is BudgetSelectionMode.COUPLED_ONLY:
        return "coupled configurations (Q = H²)"
    if selection.mode is BudgetSelectionMode.FIXED_H:
        if selection.hardware_size is None:
            raise ValueError("hardware_size is required for FIXED_H selection")
        return f"fixed H = {selection.hardware_size}"
    if selection.logical_qubits is None:
        raise ValueError("logical_qubits is required for FIXED_Q selection")
    return f"fixed Q = {selection.logical_qubits}"
