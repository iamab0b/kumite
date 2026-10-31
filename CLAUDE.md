# Kumite — instructions for coding agents

Kumite is an offline Tekken 8 sparring and coaching agent: a reflex layer, a decision model (Laya) and a numeric head choosing at decision points, a per-frame imitation transformer executing, an opponent model, and an LLM planner and coach. One developer (Sahil). Claude Code is the orchestrator; every other agent reviews or works on its own branch and never writes to `main`. The v2 build plan is in the Claude project as `plan/kumite-v2-build-plan.md`; task ids such as 6.3 refer to it.

## Layout
- `game/` hot loop, memory reader, reflex layer, sequencer and virtual pad, recorder, brain API on :8765. Runs on Windows host Python only.
- `tactical/` the decision harness (task 6.3): Decider protocol, decision-point domain, traces, replay and fork.
- `models/` training code per model; checkpoints and weights are never committed.
- `knowledge/` per-character bundles, menus, stage geometry, frame-data validator. `characters/` is legacy input until the Kazuya bundle reproduces it.
- `replay/` service on :8766 and `analytics/` service on :8767, both FastAPI. `app/` Electron + React + Vite desktop app and overlay.
- `contracts/` JSON Schemas, `api.md`, `recording.md`, `validate.py`. `data/` runtime data; only `data/samples/` is committed. `tools/` scripts, mocks and hooks. `docs/` explanations. `prep/` local only, never committed.

## Rules
1. No comments and no docstrings in any code file. Names carry meaning; explanations live in `docs/<package>.md`, in the contracts and in commit messages. A hook rejects edits that add them.
2. Contract first. Every record that crosses a boundary has a schema in `contracts/` and a validated sample in `data/samples/`. Run `python contracts/validate.py` after touching either. A breaking change bumps `schema_version` and keeps a reader for the previous version.
3. Version by game build. Anything derived from the game carries `game_version` and `pe_timestamp`.
4. Offline only, read only. `ReadProcessMemory` on `Polaris-Win64-Shipping.exe` plus a virtual pad. Never write game memory, inject, attach a debugger, or drive the pad unless the offline interlock is satisfied. Online modes are never played, logged or touched.
5. Never commit `prep/`, anything under `data/` outside `data/samples/`, keys, `.env` files, weights or checkpoints. `prep/memory-facts.md` is never published anywhere.
6. Two kinds of work. Game-machine work is anything that touches the Tekken process or its machine and runs only on Sahil's laptop. Everything else ships with a fixture (a sample, a mock in `tools/mock/`, or a generator) and must build and test without the game.
7. Work on a branch; `main` moves by merge after review. A hook refuses `git push` from `main`.
8. Every service reads `DATA_DIR` and exposes `GET /health`.
9. End every task with the exact command to run and what to expect.

## Agents
- `second-opinion` runs Cursor (`agent -p`) and Antigravity (`agy -p`) on a diff, read only, and returns disagreements.
- `repo-reader` answers long-context questions about the whole repository.
- `spark` runs training, evaluation and sync jobs on the DGX Spark over SSH inside tmux and returns the log tail.
External agents never run with `--force`, `--yolo` or `--dangerously-skip-permissions` and never write to the tree directly.
