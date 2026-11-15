# 01 · Design (before you build)

**Goal:** describe the system as small independent *concepts* and prove the design with a simulation. Mirrors the "Design" phase of an AI-engineering course: decide what the system must do **and refuse to do** before writing a service.

## Ideas
- A **concept** has one purpose, its own state, a few actions, and an operational principle (a sentence that says why it is useful).
- Concepts never call each other. A composition (here `Gateway.handle`) wires them, and its **order** is a design decision.
- Write down what the system must refuse to do.

## Lab
1. Read `sim/concepts.py`, then run `python modules/01-design/sim/simulate.py`.
2. Run `python -m pytest modules/01-design/sim -q` and read each test as a requirement.
3. Add a new concept, `ModelBudget` (max total model calls per window). Decide where it goes in the order, and write tests first.
4. Fill in your own rows in `docs/design/traceability.md`.

## Checkpoint
`make verify-01`

## Stretch
Add a `Moderation` concept for responses. What invariant should hold?
