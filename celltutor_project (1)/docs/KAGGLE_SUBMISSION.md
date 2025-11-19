# Agent CellTutor — Capstone Project Writeup

**Title:** Agent CellTutor — Per-Cell Teaching & Evaluation Agents  
**Track:** Agents for Good / Enterprise (education-focused)  
**Author:** Your Name

## Project Overview
Agent CellTutor converts notebook code cells into interactive, multimodal mini-tutors. Each cell agent generates explanations (summary & line-by-line), produces visuals and animations, accepts follow-up questions, and quizzes the learner in real-time. The system stores attempts to personalize future explanations.

## Problem Statement
(Describe the problem — copy from README or expand.)

## Solution Statement
(Describe solution — copy from README or expand.)

## Architecture
(Include the two architecture images and a description.)

## Implementation
- Language: Python 3.10
- Core components: CellAgentBuilder, CellAgentRuntime, Registry, Inspector, Visualizer
- LLM: pluggable via LLMInterface (MockLLM provided; GeminiAdapter skeleton included)
- Visuals: MockVisualizer (Pillow) — replaceable with production generators

## How to run
1. Create virtualenv and install requirements:
```
pip install -r requirements.txt
```
2. Run demo:
```
python examples/run_demo.py
```

## Evaluation
- Per-cell quizzes measure pass rate.
- Logs and registry store attempts for analysis.
- Suggested metrics: average attempts per cell, time to pass, pass rate per lesson.

## Safety & Ethics
- No arbitrary remote code execution enabled by default.
- All LLM adapters must be provided API keys via env vars.
- Do not commit secrets.

## Files & Reproducibility
- `src/celltutor` — core code
- `examples/run_demo.py` — demonstration
- `docs/ARCHITECTURE.md` — diagrams
- `images/architecture1.png` and `images/architecture2.png` — visuals

## Future Work
- Runtime tracing with sandboxed execution
- Better visual generators & animation tooling
- Integration with real LLMs & vector DB for memory

