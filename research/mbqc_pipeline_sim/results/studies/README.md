# Study Namespaces

`results/summary` と `results/figures` は既存 pipeline study の baseline です。

新しい比較実験は `results/studies/<study_id>/<experiment_id>/...` 配下に出力し、既存 CSV / figure と混ぜない方針を取ります。

shifted DAG dynamic study の既定 namespace:

- `13_shifted_dag_dynamic/raw_vs_shifted_next_cycle_width_matched/`

throughput コスト（ASAP vs ff_rate_matched、shifted のみ）:

- `17_throughput_cost/summary/sweep.csv`

L_ff 感度分析（ASAP vs ff_rate_matched、raw + shifted、QAOA/VQE H8/Q64）:

- `18_lff_sensitivity/summary/sweep.csv`

L_meas 感度分析（ASAP vs ff_rate_matched、raw + shifted、QAOA/VQE H6/H8）:

- `19_lmeas_sensitivity/summary/sweep_all.csv`
