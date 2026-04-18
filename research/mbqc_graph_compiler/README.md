# MBQC Graph Compiler

JCZ ゲートモデルによる MBQC グラフ状態コンパイラ。

`OneAdapt_AE 2/OnePerc/` から必要な部分のみを抽出・整理したパッケージ。
`pyzx` / `qiskit` / `sys.path` ハックへの依存を除去してある。

## 提供する機能

| モジュール | 関数 | 説明 |
|-----------|------|------|
| `jcz_circuit` | `JCZCircuit`, `JGate`, `CZGate` | JCZ ゲートモデルの回路クラス |
| `circuit_constructors` | `construct_qaoa/qft/vqe/...` | 標準アルゴリズムの JCZ 回路生成 |
| `graph_state` | `generate_graph_state` | JCZ 回路 → MBQC グラフ状態 |
| `dependency` | `determine_dependency`, `signal_shift` | X/Z 依存グラフ抽出・signal shift 最適化 |
| `reduce_degree` | `reduce_degree` | グラフノード次数を ≤ 4 に制限 |
| `map_route` | `map_route`, `Empty` | N×N グリッドへのマッピング・ルーティング |

## インストール

```bash
pip install -e research/mbqc_graph_compiler
```

## 使い方

```python
from mbqc_graph_compiler import (
    construct_qaoa,
    generate_graph_state,
    determine_dependency,
    signal_shift,
)

# QAOA 回路を JCZ ゲートに変換
gates, n_qubits = construct_qaoa(nqubit=16, average_gate_num=0.5)

# グラフ状態を生成
graph_state = generate_graph_state(gates, n_qubits)

# FF 依存グラフを抽出
dgraph_raw, gs = determine_dependency(graph_state)

# signal shift で D_ff を圧縮
dgraph_shifted, _ = signal_shift(dgraph_raw.copy(), gs.copy())
```

## 依存

- `networkx >= 3.0`
- `numpy >= 1.24`
- `matplotlib >= 3.7`（`map_route` の可視化関数のみ）
