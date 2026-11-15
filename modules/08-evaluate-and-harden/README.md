# 08 · Evaluate, measure, threat-model

**Goal:** measure before optimizing; learn where your controls are weak.

## Lab
1. `python scripts/eval_gateway.py` for a baseline pass rate. Add 5 cases to `eval/golden.jsonl`.
2. `python scripts/benchmark.py -n 20` vs `--unique`. Record p50/p95 and explain the gap.
3. Open `app/tests/test_guard_bypasses.py`: four strict xfails document bypasses. Pick one, design a better control, make it pass, and say what still gets through.
4. Install monitoring (Module 05) and graph `gateway_chat_seconds`.
5. Write a 5-line threat model: assets, actors, top 3 abuses, controls, residual risk.

## Checkpoint
`make verify-08`

## Stretch
Compare two models on your eval set: quality vs latency vs memory.
