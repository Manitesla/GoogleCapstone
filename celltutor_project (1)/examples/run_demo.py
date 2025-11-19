"""
Demo runner for Agent CellTutor - creates two cell agents and runs a demo session.
Run: python examples/run_demo.py
"""
import textwrap
from celltutor import MockLLM, MockVisualizer, Registry, CellAgentBuilder, CellAgentRuntime

def main():
    llm = MockLLM()
    vis = MockVisualizer()
    reg = Registry()
    builder = CellAgentBuilder(llm, vis, reg)
    runtime = CellAgentRuntime(reg, llm)

    code1 = textwrap.dedent("""
    def factorial(n):
        if n == 0:
            return 1
        res = 1
        for i in range(1, n+1):
            res *= i
        return res
    """).strip()

    code2 = textwrap.dedent("""
    def greet(name):
        return f"Hello, {name}"
    """).strip()

    m1 = builder.build_for_cell(1, code1, title="Factorial cell")
    m2 = builder.build_for_cell(2, code2, title="Greet cell")
    print("Built agents:", m1["id"], m2["id"])

    print("--- Summary for cell 1 ---")
    print(runtime.explain(m1["id"], depth="summary")[:400])

    print("--- Line-by-line for cell 1 ---")
    print(runtime.explain(m1["id"], depth="line")[:800])

    print("--- Visuals for cell 1 ---")
    v = runtime.get_visuals(m1["id"])
    print("Diagram:", v["diagram"])
    print("Animation:", v["animation"])

    print("--- Ask a question ---")
    ans = runtime.ask_question(m1["id"], "What happens when n is 0?")
    print("Agent answer:", ans)

    print("--- Run quiz for cell 1 (mock user answers) ---")
    quiz = reg.get_manifest(m1["id"])["quiz"]
    ua = []
    for i,q in enumerate(quiz):
        ua.append({"q_index": i, "answer": "It returns 1" if i==0 else "Yes"})
    result = runtime.run_quiz(m1["id"], ua)
    print("Quiz result:", result)

if __name__ == "__main__":
    main()
