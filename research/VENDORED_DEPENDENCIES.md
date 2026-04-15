# Vendored Dependencies

This repository vendors third-party research code when it is required for
artifact reproducibility and the upstream license permits redistribution.

## OneAdapt Snapshot

- Path: `OneAdapt_AE 2/`
- Role:
  - source backend for `research/mbqc_ff_evaluator`
  - dependency-graph generation used by the FF evaluator and downstream
    pipeline simulator studies
- Reason for vendoring:
  - the current research artifacts depend on the exact local behavior of the
    OneAdapt codebase
  - keeping a snapshot in-tree makes the FF evaluator and pipeline simulator
    reproducible without requiring an external checkout

## What Should Be Tracked

Track:

- vendored source files under `OneAdapt_AE 2/`
- research source code, tests, docs, and lockfiles
- summary CSVs and figure outputs needed to reproduce report claims
- raw JSON artifacts when they are directly consumed by downstream studies

Do not track:

- `__pycache__/`
- `.pytest_cache/`
- `.mypy_cache/`
- `.cache/`
- `.mplconfig/`
- `*.egg-info/`
- `.DS_Store`

## Update Policy

Treat `OneAdapt_AE 2/` as a versioned snapshot.

If the vendored code is updated:

1. record the reason in the commit message
2. regenerate any affected research artifacts
3. note report-impacting changes in the corresponding docs
