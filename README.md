# Agent CellTutor

Agent CellTutor is a multi-agent system that converts notebook code cells into interactive mini-tutors:
- Generates summary and line-by-line explanations
- Produces diagrams and simple animations
- Creates short quizzes and evaluates answers
- Stores per-user attempts and adapts explanations

This repository contains a runnable demo using a Mock LLM and a Mock Visualizer.

## Contents
- `src/celltutor` — core Python package
- `examples/run_demo.py` — demo script that builds and exercises cell agents
- `docs/` — architecture images and diagrams
- `images/` — images used in the writeup
- `celltutor.db` — created at first run (SQLite registry)

## Quick start

1. (Optional) Create a virtual environment and activate it:
```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the demo:
```bash
python examples/run_demo.py
```

## How to use in a notebook
You can import `celltutor` and call the builder/runtime to create per-cell agents and display images inline.

## Extending to real LLMs and visual generators
- Replace `MockLLM` with an adapter to Gemini or OpenAI.
- Replace `MockVisualizer` with real diagram or animation generator.
- Ensure safety: sandbox code execution if you enable runtime traces.

## License
MIT


## CI & LLM Adapter

This repo includes a GitHub Actions CI workflow at `.github/workflows/ci.yml` that runs a smoke test. A `GeminiAdapter` skeleton is provided at `src/celltutor/gemini_adapter.py` to help you plug in a real LLM safely using environment variables.
