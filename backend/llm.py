"""AI module: question generation, hints, feedback. Falls back to a built-in question if no API key."""
import json, os, re
import runner, langs
try:
    from dotenv import load_dotenv; load_dotenv()
except ImportError:
    pass
try:
    import anthropic
    client = anthropic.Anthropic() if os.getenv("ANTHROPIC_API_KEY") else None
except ImportError:
    client = None

MODEL = os.getenv("LLM_MODEL", "claude-sonnet-5-5")

FALLBACK = {
    "title": "Two Sum",
    "statement": "Given a list of integers nums and an integer target, return the indices of the two numbers that add up to target. Exactly one solution exists and you may not use the same element twice. Return the indices as [smaller, larger].",
    "examples": [{"input": "nums = [2,7,11,15], target = 9", "output": "[0, 1]"}],
    "starter_code": "def solution(nums, target):\n    # Write your code here\n    pass\n",
    "test_cases": [
        {"input": [[2, 7, 11, 15], 9], "expected": [0, 1]},
        {"input": [[3, 2, 4], 6], "expected": [1, 2]},
        {"input": [[3, 3], 6], "expected": [0, 1]},
        {"input": [[1, 5, 8, 3], 11], "expected": [2, 3]},
        {"input": [[-1, -2, -3, -4, -5], -8], "expected": [2, 4]},
    ],
    "reference_solution": "def solution(nums, target):\n    seen = {}\n    for i, n in enumerate(nums):\n        if target - n in seen:\n            return [seen[target - n], i]\n        seen[n] = i\n",
}

def _ask(system, prompt, max_tokens=2000):
    r = client.messages.create(model=MODEL, max_tokens=max_tokens, system=system,
                               messages=[{"role": "user", "content": prompt}])
    return "".join(b.text for b in r.content if b.type == "text")

def _json(text):
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    return json.loads(text)

def _validate(q):
    """Reject AI questions whose tests are wrong: the AI's own reference solution must pass every test."""
    need = ["title", "statement", "examples", "starter_code", "test_cases", "reference_solution"]
    if not all(k in q for k in need) or len(q["test_cases"]) < 5:
        return None
    if not all(isinstance(t.get("input"), list) and "expected" in t for t in q["test_cases"]):
        return None
    res = runner.run_python(q["reference_solution"], q["test_cases"])
    if "results" not in res or not all(r["passed"] for r in res["results"]):
        return None
    return q

import fallbacks

def generate_question(topic, level, language, minutes):
    prompt = f"""Create one coding problem on the topic "{topic}" at {level} difficulty, solvable in Python within {minutes} minutes.
The problem MUST be about {topic}. Return ONLY JSON with keys:
title, statement (full problem text incl. input/output description), examples (list of {{input, output}} strings),
starter_code (Python defining `def solution(...)` with a comment and `pass`),
test_cases (at least 6 items: {{"input": [positional args as JSON list], "expected": JSON value}}),
reference_solution (complete correct Python defining `solution`).
Rules: the answer must be unique and deterministic (no problems with several valid outputs). Arguments and results may ONLY be: int (32-bit), bool, string (no newlines), list of ints, or list of lists of ints, so the problem can also be solved in Java and C++."""
    reason = "no ANTHROPIC_API_KEY set" if not client else "AI output failed validation 3 times"
    if client:
        for _ in range(3):
            try:
                q = _validate(_json(_ask("You are a programming-contest problem setter. Output JSON only.", prompt, 4000)))
                if q:
                    return {**q, "source": "ai", "note": ""}
                print("LLM question rejected by validation")
            except Exception as e:
                reason = f"AI call failed: {type(e).__name__}: {str(e)[:120]}"
                print("LLM question error:", e)
    fb = fallbacks.get(topic, level) or FALLBACK
    return {**fb, "source": "fallback", "note": f"Built-in sample question ({reason})."}

def public(q):
    d = {k: q.get(k, "") for k in ("title", "statement", "examples", "starter_code", "source", "note")}
    d["starters"] = langs.starters(q)   # starter code for every language this question supports
    return d

def hint(problem, code, n, language="python"):
    if not client:
        return f"Hint {n}: break the problem into small steps and think about which data structure avoids repeated work."
    levels = {1: "a very small conceptual clue", 2: "a bigger clue naming the approach or data structure", 3: "a detailed step-by-step outline in words"}
    return _ask("You are a coding tutor. NEVER write the full solution or any complete code.",
                f"Problem:\n{problem}\n\nStudent code ({language}):\n{code}\n\nGive {levels.get(n, levels[3])}. Max 3 sentences.", 400)

def feedback(problem, code, results, completed, language="python"):
    if not client:
        return "AI feedback is unavailable (no API key set). Tests passed." if completed else "AI feedback is unavailable (no API key set). Some tests failed - re-check your logic and edge cases."
    return _ask("You are a friendly coding mentor. Be concise and use simple words.",
                f"Problem:\n{problem}\n\nStudent code ({language}):\n{code}\n\nTest results (JSON):\n{json.dumps(results)[:1500]}\n\n"
                "Explain: 1) is the logic correct, 2) mistakes/errors, 3) time and space complexity, 4) one improvement tip. Do not give the full corrected code.", 700)
