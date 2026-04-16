from __future__ import annotations

from mbqc_pipeline_sim.domain.enums import SchedulingPolicy
from mbqc_pipeline_sim.domain.models import PipelineConfig, SimDAG
from mbqc_pipeline_sim.ports.scheduler_policy import SchedulerFactory, SchedulerPolicyPort


class SchedulerRegistry:
    def __init__(self) -> None:
        self._factories: dict[SchedulingPolicy, SchedulerFactory] = {}

    def register(self, policy: SchedulingPolicy, factory: SchedulerFactory) -> None:
        self._factories[policy] = factory

    def build(
        self,
        policy: SchedulingPolicy,
        dag: SimDAG,
        config: PipelineConfig,
    ) -> SchedulerPolicyPort:
        try:
            factory = self._factories[policy]
        except KeyError as exc:
            raise ValueError(f"Unknown policy: {policy}") from exc
        return factory(dag, config)
