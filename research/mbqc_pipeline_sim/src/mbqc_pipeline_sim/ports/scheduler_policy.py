from __future__ import annotations

from typing import Callable, Protocol, TYPE_CHECKING

from mbqc_pipeline_sim.domain.enums import SchedulingPolicy
from mbqc_pipeline_sim.domain.scheduler_models import SchedulerContext, SchedulerDecision

if TYPE_CHECKING:
    from mbqc_pipeline_sim.domain.models import PipelineConfig, SimDAG


class SchedulerPolicyPort(Protocol):
    policy_id: SchedulingPolicy

    def select(self, context: SchedulerContext) -> SchedulerDecision:
        ...


SchedulerFactory = Callable[["SimDAG", "PipelineConfig"], SchedulerPolicyPort]
