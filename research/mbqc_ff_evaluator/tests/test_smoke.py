from __future__ import annotations

from mbqc_ff_evaluator.cli.smoke import build_parser


def test_smoke_parser_accepts_defaults() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "--algorithm",
            "QAOA",
            "--hardware-size",
            "4",
            "--logical-qubits",
            "16",
        ]
    )

    assert args.algorithm == "QAOA"
    assert args.seed == 0
    assert args.refresh_bound == 20
