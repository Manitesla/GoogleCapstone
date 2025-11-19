"""
CellTutor package - core implementation for Agent CellTutor

Contains:
- Registry (SQLite)
- Mock LLM
- Mock Visualizer
- Inspector
- CellAgentBuilder and runtime
- Demo script entrypoints available under examples/run_demo.py
"""

import os
import sqlite3
import uuid
import time
import json
import ast
import textwrap
import logging
from typing import Dict, Any, List, Optional

# Config
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
AGENTS_DIR = os.path.join(BASE_DIR, "agents")
DB_PATH = os.path.join(BASE_DIR, "..", "celltutor.db")
os.makedirs(AGENTS_DIR, exist_ok=True)

logging.basicConfig(
    filename=os.path.join(BASE_DIR, "..", "celltutor_core.log"),
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s'
)
logger = logging.getLogger("celltutor")

def now_ts():
    return time.time()

def gen_id():
    return str(uuid.uuid4())[:8]

class LLMInterface:
    def generate(self, prompt: str, **kwargs) -> str:
        raise NotImplementedError

class MockLLM(LLMInterface):
    def generate(self, prompt: str, **kwargs) -> str:
        p = prompt.lower()
        if "summary:" in p or "summarize" in p:
            s = " ".join(prompt.strip().split())[:200]
            return f"Quick summary: {s}"
        if "explain line" in p or "line-by-line" in p:
            lines = [l.strip() for l in prompt.splitlines() if l.strip()]
            out = []
            for i, ln in enumerate(lines[:10], 1):
                out.append(f"Line {i}: {ln[:80]} -> Explanation: This line ...")
            return "\\n".join(out)
        if "generate quiz" in p or "quiz" in p:
            return json.dumps([
                {"q": "What does the function return?", "type": "short", "answer_hint": "It returns an int"},
                {"q": "Is there a loop in the code?", "type": "mcq", "options": ["Yes", "No"], "answer_hint": "Yes"}
            ])
        if "visualize" in p or "diagram" in p:
            return "visual_instructions: draw a control-flow box for the function and label variables x, y"
        return "MOCK_LLM_REPLY: " + (prompt.strip()[:180])

# Visualizer uses Pillow for placeholder images
try:
    from PIL import Image, ImageDraw
except Exception:
    Image = None

class MockVisualizer:
    def make_diagram(self, cell_id: str, diagram_text: str) -> str:
        path = os.path.join(AGENTS_DIR, f"{cell_id}_diagram.png")
        if Image is None:
            # fallback: write text file
            with open(path + ".txt", "w") as fh:
                fh.write("DIAGRAM PLACEHOLDER\\n" + diagram_text)
            return path + ".txt"
        img = Image.new("RGB", (800, 200), color=(240, 240, 240))
        d = ImageDraw.Draw(img)
        text = "DIAGRAM:\\n" + (diagram_text[:800])
        d.text((10, 10), text, fill=(0,0,0))
        img.save(path)
        return path

    def make_animation(self, cell_id: str, frames_text: List[str]) -> str:
        path = os.path.join(AGENTS_DIR, f"{cell_id}_anim.gif")
        if Image is None:
            with open(path + ".txt", "w") as fh:
                fh.write("ANIM PLACEHOLDER\\n" + "\\n".join(frames_text))
            return path + ".txt"
        frames = []
        for i, t in enumerate(frames_text):
            img = Image.new("RGB", (640, 240), color=(255,255,255))
            d = ImageDraw.Draw(img)
            d.text((10,10), f"Frame {i+1}: {t[:200]}", fill=(0,0,0))
            frames.append(img)
        frames[0].save(path, save_all=True, append_images=frames[1:], duration=800, loop=0)
        return path

class Registry:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute(\"\"\"
            CREATE TABLE IF NOT EXISTS cell_agents (
                id TEXT PRIMARY KEY,
                cell_index INTEGER,
                manifest TEXT,
                created_at REAL
            )
        \"\"\")
        cur.execute(\"\"\"
            CREATE TABLE IF NOT EXISTS attempts (
                id TEXT PRIMARY KEY,
                cell_id TEXT,
                ts REAL,
                quiz_result_json TEXT
            )
        \"\"\")
        conn.commit()
        conn.close()

    def register(self, cell_index: int, manifest: Dict[str, Any]) -> str:
        cid = manifest.get("id") or gen_id()
        manifest["id"] = cid
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("INSERT INTO cell_agents (id,cell_index,manifest,created_at) VALUES (?,?,?,?)",
                    (cid, cell_index, json.dumps(manifest), now_ts()))
        conn.commit()
        conn.close()
        logger.info(f"Registered cell agent {cid} for cell {cell_index}")
        return cid

    def get_manifest(self, cell_id: str) -> Optional[Dict[str,Any]]:
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT manifest FROM cell_agents WHERE id=?", (cell_id,))
        r = cur.fetchone()
        conn.close()
        if not r: return None
        return json.loads(r[0])

    def store_attempt(self, cell_id: str, result: Dict[str,Any]) -> str:
        aid = gen_id()
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("INSERT INTO attempts (id,cell_id,ts,quiz_result_json) VALUES (?,?,?,?)",
                    (aid, cell_id, now_ts(), json.dumps(result)))
        conn.commit()
        conn.close()
        logger.info(f"Stored attempt {aid} for cell {cell_id}")
        return aid

class Inspector:
    @staticmethod
    def extract_summary(code: str) -> Dict[str,Any]:
        try:
            tree = ast.parse(code)
        except Exception as e:
            return {"error": "not python or parse error", "raw_code": code[:200]}
        funcs = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
        loops = any(isinstance(n, (ast.For, ast.While)) for n in ast.walk(tree))
        imports = [n.names[0].name for n in ast.walk(tree) if isinstance(n, ast.Import)]
        imports += [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module]
        return {
            "functions": funcs,
            "has_loop": loops,
            "imports": list(set([i for i in imports if i])),
            "lines": [ln for ln in code.splitlines() if ln.strip()]
        }

class CellAgentBuilder:
    def __init__(self, llm: LLMInterface, visualizer: MockVisualizer, registry: Registry):
        self.llm = llm
        self.visualizer = visualizer
        self.registry = registry

    def build_for_cell(self, cell_index: int, code: str, title: Optional[str]=None) -> Dict[str,Any]:
        inspect = Inspector.extract_summary(code)
        name = title or f"CellAgent_{cell_index}"
        summary_prompt = f"Summary:\\nCode:\\n{code}\\n\\nProvide a concise summary."
        summary = self.llm.generate(summary_prompt)
        line_prompt = "Line-by-line explanation:\\n" + "\\n".join(inspect.get("lines", [])[:20])
        line_by_line = self.llm.generate(line_prompt)
        vis_prompt = "Visualize the following code:\\n\\n" + code + "\\n\\nSuggest a diagram and steps."
        vis_instructions = self.llm.generate(vis_prompt)
        diagram_path = self.visualizer.make_diagram(gen_id(), vis_instructions)
        frames = [f"State {i+1}: explain variable changes" for i in range(3)]
        anim_path = self.visualizer.make_animation(gen_id(), frames)
        quiz_prompt = "Generate a 1-3 question quiz based on this code. Return JSON list of questions."
        quiz_json = self.llm.generate(quiz_prompt)
        try:
            quiz = json.loads(quiz_json)
        except Exception:
            quiz = [{"q": "What does the code do?", "type": "short", "answer_hint": "describe"}]
        manifest = {
            "name": name,
            "cell_index": cell_index,
            "code_sample": code,
            "inspection": inspect,
            "summary": summary,
            "line_by_line": line_by_line,
            "diagram": diagram_path,
            "animation": anim_path,
            "quiz": quiz,
            "created_at": now_ts()
        }
        cid = self.registry.register(cell_index, manifest)
        manifest["id"] = cid
        return manifest

class CellAgentRuntime:
    def __init__(self, registry: Registry, llm: LLMInterface):
        self.registry = registry
        self.llm = llm

    def explain(self, cell_id: str, depth: str="summary") -> str:
        manifest = self.registry.get_manifest(cell_id)
        if not manifest:
            raise ValueError("Cell agent not found")
        if depth == "summary":
            return manifest["summary"]
        if depth == "line":
            return manifest["line_by_line"]
        return manifest.get("summary")

    def get_visuals(self, cell_id: str) -> Dict[str,str]:
        m = self.registry.get_manifest(cell_id)
        return {"diagram": m.get("diagram"), "animation": m.get("animation")}

    def ask_question(self, cell_id: str, user_question: str) -> str:
        m = self.registry.get_manifest(cell_id)
        context = m["code_sample"][:2000]
        prompt = f"User question: {user_question}\\nContext:\\n{context}\\nProvide a clear, concise answer."
        return self.llm.generate(prompt)

    def run_quiz(self, cell_id: str, user_answers: List[Dict[str,Any]]) -> Dict[str,Any]:
        manifest = self.registry.get_manifest(cell_id)
        quiz = manifest.get("quiz", [])
        results = []
        for ans in user_answers:
            idx = ans["q_index"]
            user_ans = ans["answer"]
            expected_hint = quiz[idx].get("answer_hint","").lower() if idx < len(quiz) else ""
            correct = expected_hint in user_ans.lower() if expected_hint else True
            results.append({"index": idx, "user_answer": user_ans, "correct": correct})
        summary = {"score": sum(1 for r in results if r["correct"]), "total": len(results), "details": results}
        self.registry.store_attempt(cell_id, summary)
        return summary
