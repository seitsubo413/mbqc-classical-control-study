"""Cycle-accurate MBQC pipeline simulator — core loop."""
from __future__ import annotations

from mbqc_pipeline_sim.domain.enums import NodeState, ReleaseMode
from mbqc_pipeline_sim.domain.errors import SimulationDeadlockError
from mbqc_pipeline_sim.domain.models import CycleRecord, PipelineConfig, SimDAG, SimResult
from mbqc_pipeline_sim.core.pipeline_stage import LatencyPipeline
from mbqc_pipeline_sim.core.scheduler_features import build_scheduler_context
from mbqc_pipeline_sim.core.scheduler import build_scheduler


class MbqcPipelineSimulator:
    """Simulate measurement scheduling on a dependency DAG.

    Pipeline model::

        Ready Queue ─(issue W/cyc)─> MeasUnit ─(L_meas)─> FFProc ─(L_ff)─> done
                 ^                                                        │
                 └──────────── dependency resolution ─────────────────────┘
    """

    def run(self, dag: SimDAG, config: PipelineConfig) -> SimResult:
        node_ids = {n.node_id for n in dag.nodes}

        # --- state tracking ---
        state: dict[int, NodeState] = {nid: NodeState.PENDING for nid in node_ids}
        remaining_indeg: dict[int, int] = dict(dag.indegree)

        ready: list[int] = sorted(
            nid for nid, d in remaining_indeg.items() if d == 0
        )
        for nid in ready:
            state[nid] = NodeState.READY

        meas_pipe = LatencyPipeline(config.l_meas, width=config.meas_width)
        ff_pipe = LatencyPipeline(config.l_ff, width=config.ff_width)
        scheduler = build_scheduler(config.policy, dag, config=config)

        cycle = 0
        done_count = 0
        stall_cycles = 0
        total_issued = 0
        records: list[CycleRecord] = []
        deferred_ready: list[int] = []
        ff_waiting: list[int] = []

        while done_count < len(node_ids):
            if deferred_ready:
                ready.extend(deferred_ready)
                deferred_ready = []

            # ── Phase 1: Resolve FF completions → update dependents ──
            completed_ff = ff_pipe.advance()
            for nid in completed_ff:
                state[nid] = NodeState.DONE
                done_count += 1
                for succ in dag.adjacency.get(nid, []):
                    remaining_indeg[succ] -= 1
                    if remaining_indeg[succ] == 0 and state[succ] == NodeState.PENDING:
                        state[succ] = NodeState.READY
                        if config.release_mode == ReleaseMode.SAME_CYCLE:
                            ready.append(succ)
                        else:
                            deferred_ready.append(succ)

            # ── Phase 2: Advance measurement pipeline → feed into FF ──
            completed_meas = meas_pipe.advance()
            for nid in completed_meas:
                state[nid] = NodeState.WAITING_FF
                ff_waiting.append(nid)
            admitted_ff = ff_pipe.enqueue_many(ff_waiting)
            if admitted_ff:
                admitted_set = set(admitted_ff)
                ff_waiting = [nid for nid in ff_waiting if nid not in admitted_set]
                for nid in admitted_ff:
                    state[nid] = NodeState.IN_FLIGHT_FF

            # ── Phase 3: Issue from ready queue ──
            meas_slots = meas_pipe.available_input_slots
            issue_limit = config.issue_width if meas_slots is None else min(config.issue_width, meas_slots)
            context = build_scheduler_context(
                dag=dag,
                config=config,
                cycle=cycle,
                ready=tuple(ready),
                issue_limit=issue_limit,
                remaining_indegree=remaining_indeg,
                waiting_ff_count=len(ff_waiting),
                in_flight_meas_count=meas_pipe.occupancy,
                in_flight_ff_count=ff_pipe.occupancy,
                meas_slots_available=meas_slots,
                ff_slots_available=ff_pipe.available_input_slots,
            )
            decision = scheduler.select(context)
            to_issue = list(decision.selected_node_ids)
            if to_issue:
                issued_set = set(to_issue)
                ready[:] = [nid for nid in ready if nid not in issued_set]
                for nid in to_issue:
                    state[nid] = NodeState.IN_FLIGHT_MEAS
            admitted_meas = meas_pipe.enqueue_many(to_issue)
            if len(admitted_meas) != len(to_issue):
                raise SimulationDeadlockError(
                    "Measurement stage refused issued nodes; issue gating is inconsistent"
                )
            total_issued += len(admitted_meas)

            is_stall = len(to_issue) == 0 and done_count < len(node_ids)
            if is_stall:
                stall_cycles += 1

            if (
                not completed_ff
                and not completed_meas
                and not to_issue
                and not ready
                and not deferred_ready
                and not ff_waiting
                and meas_pipe.occupancy == 0
                and ff_pipe.occupancy == 0
                and done_count < len(node_ids)
            ):
                raise SimulationDeadlockError(
                    f"Simulation deadlocked on {dag.algorithm}_H{dag.hardware_size}_Q{dag.logical_qubits}_s{dag.dag_seed}"
                )

            records.append(
                CycleRecord(
                    cycle=cycle,
                    issued=len(to_issue),
                    ready_queue_size=len(ready),
                    waiting_ff_queue_size=len(ff_waiting),
                    in_flight_meas=meas_pipe.occupancy,
                    in_flight_ff=ff_pipe.occupancy,
                    completed_this_cycle=len(completed_ff),
                    total_done=done_count,
                )
            )
            cycle += 1

        total_cycles = cycle
        throughput = len(node_ids) / total_cycles if total_cycles > 0 else 0.0
        max_possible = config.issue_width * total_cycles
        utilization = total_issued / max_possible if max_possible > 0 else 0.0

        label = (
            f"{dag.algorithm}_H{dag.hardware_size}_Q{dag.logical_qubits}"
            f"_s{dag.dag_seed}_{dag.dag_variant.value}"
        )

        return SimResult(
            dag_label=label,
            config=config,
            total_nodes=len(node_ids),
            total_cycles=total_cycles,
            throughput=throughput,
            stall_cycles=stall_cycles,
            stall_rate=stall_cycles / total_cycles if total_cycles > 0 else 0.0,
            utilization=utilization,
            dag_variant=dag.dag_variant,
            ff_chain_depth=dag.ff_chain_depth,
            ff_chain_depth_raw=dag.ff_chain_depth_raw,
            ff_chain_depth_shifted=dag.ff_chain_depth_shifted,
            algorithm=dag.algorithm,
            hardware_size=dag.hardware_size,
            logical_qubits=dag.logical_qubits,
            dag_seed=dag.dag_seed,
            cycle_records=tuple(records),
        )
