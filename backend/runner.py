"""Code Runner + live syntax checker for Python, JavaScript, Java and C++.
USE_DOCKER=true  -> every compile/run happens in a throw-away container (no network, memory/CPU/process limits)
USE_DOCKER=false -> local subprocess with timeout (development only; NOT a security boundary)
Local mode needs: python, node, javac+java, g++ installed."""
import ast, io, json, os, re, secrets, subprocess, sys, tempfile, tokenize
import langs

HARNESS_PY = r'''
import json, sys, time, os, io, traceback, contextlib
d = sys.argv[1]
tests = json.load(open(os.path.join(d, "tests.json")))
real = sys.stdout
ns = {}
try:
    with contextlib.redirect_stdout(io.StringIO()):
        exec(compile(open(os.path.join(d, "user_code.py")).read(), "user_code", "exec"), ns)
    fn = ns["solution"]
except BaseException:
    real.write(json.dumps({"error": traceback.format_exc(limit=3)})); sys.exit(0)
results = []
for t in tests:
    s = time.perf_counter()
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            out = fn(*t["input"])
        results.append({"passed": json.dumps(out, sort_keys=True, default=str) == json.dumps(t["expected"], sort_keys=True),
                        "output": out, "expected": t["expected"], "time": round(time.perf_counter() - s, 4)})
    except BaseException:
        results.append({"passed": False, "output": None, "expected": t["expected"],
                        "error": traceback.format_exc(limit=2).strip().splitlines()[-1],
                        "time": round(time.perf_counter() - s, 4)})
real.write(json.dumps({"results": results}, default=str))
'''

HARNESS_JS = r'''
const fs = require("fs"), vm = require("vm"), path = require("path");
const d = process.argv[2];
const tests = JSON.parse(fs.readFileSync(path.join(d, "tests.json"), "utf8"));
const write = process.stdout.write.bind(process.stdout);
console.log = console.info = console.warn = console.error = () => {};
try {
  vm.runInThisContext(fs.readFileSync(path.join(d, "user_code.js"), "utf8"), { filename: "solution.js" });
  if (typeof solution !== "function") throw new Error("Function solution is not defined");
} catch (e) {
  write(JSON.stringify({ error: String(e && e.stack ? e.stack.split("\n").slice(0, 4).join(" | ") : e) })); process.exit(0);
}
const results = [];
for (const t of tests) {
  const s = process.hrtime.bigint();
  const el = () => Number(process.hrtime.bigint() - s) / 1e9;
  try { let o = solution(...JSON.parse(JSON.stringify(t.input))); if (o === undefined) o = null; results.push({ output: o, time: el() }); }
  catch (e) { results.push({ output: null, error: String(e).split("\n")[0], time: el() }); }
}
write(JSON.stringify({ results }));
'''

IMAGES = {"python": "python:3.11-slim", "javascript": "node:20-slim", "java": "eclipse-temurin:21-jdk", "cpp": "gcc:13"}
CPP_HEAD = "#include <bits/stdc++.h>\nusing namespace std;\n#line 1\n"   # '#line 1' keeps user line numbers correct
JAVA_HEAD = "import java.util.*; "                                        # same line as user code -> line numbers unchanged

class ToolMissing(Exception):
    pass

def _docker():
    return os.getenv("USE_DOCKER", "false").lower() == "true"

def _eq(a, b):
    return json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)

def _exec(cmd, d, timeout, language, stdin_name=None):
    """Run cmd inside dir d (locally or in a container). Returns (CompletedProcess | None, timed_out)."""
    docker = _docker()
    name = "cr-" + secrets.token_hex(6)
    if docker:
        full = ["docker", "run", "--rm", "-i", "--name", name, "--network", "none", "--memory", "256m", "--cpus", "1",
                "--pids-limit", "128", "-v", f"{d}:/code", "-w", "/code", IMAGES[language]] + cmd
        limit = timeout + 25  # container start-up time
    else:
        full, limit = cmd, timeout
    stdin = open(os.path.join(d, stdin_name), "rb") if stdin_name else subprocess.DEVNULL
    try:
        return subprocess.run(full, cwd=d, stdin=stdin, capture_output=True, text=True, errors="replace", timeout=limit), False
    except subprocess.TimeoutExpired:
        if docker:
            subprocess.run(["docker", "rm", "-f", name], capture_output=True)
        return None, True
    except FileNotFoundError as e:
        raise ToolMissing(f"'{full[0]}' is not installed on the server" + (" (is Docker running?)" if docker else ""))
    finally:
        if stdin_name:
            stdin.close()

def _cmds(language, d, docker, check=False):
    py = "python" if docker else sys.executable
    exe = ("/code" if docker else d) + "/main"
    if check:
        return {"java": ["javac", "-proc:none", "-Xmaxerrs", "10", "Main.java"],
                "cpp": ["g++", "-fsyntax-only", "-std=c++17", "main.cpp"]}[language]
    return {"python": (None, [py, "harness.py", "."]),
            "javascript": (None, ["node", "harness.js", "."]),
            "java": (["javac", "-proc:none", "Main.java"], ["java", "-Xmx128m", "-cp", ".", "Main"]),
            "cpp": (["g++", "-O1", "-std=c++17", "-o", "main", "main.cpp"], [exe])}[language]

def _prepare(d, language, code, tests, types, with_tests=True):
    def w(name, text):
        with open(os.path.join(d, name), "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
    if language == "python":
        w("user_code.py", code); w("tests.json", json.dumps(tests)); w("harness.py", HARNESS_PY)
    elif language == "javascript":
        w("user_code.js", code); w("tests.json", json.dumps(tests)); w("harness.js", HARNESS_JS)
    elif language == "java":
        w("Main.java", JAVA_HEAD + code + "\n" + (langs.java_harness(types) if types else ""))
        if with_tests and types: w("input.txt", langs.encode_input(types, tests))
    else:
        w("main.cpp", CPP_HEAD + code + "\n" + (langs.cpp_harness(types) if types else ""))
        if with_tests and types: w("input.txt", langs.encode_input(types, tests))

def _clean(text, d):
    return text.replace(JAVA_HEAD, "").replace(d + os.sep, "").replace("/code/", "").strip()

def run_code(language, code, tests, timeout=5, type_tests=None):
    """-> {"results": [{passed, output, expected, time, error?}]} or {"error": "..."}"""
    if language not in langs.LANGS:
        return {"error": f"Unsupported language: {language}"}
    types = None
    if language in ("java", "cpp"):
        types = langs.infer_types(type_tests or tests)
        if not types:
            return {"error": f"This question uses data types that {langs.LANGS[language]} is not set up for yet. Please switch to Python or JavaScript."}
    try:
        with tempfile.TemporaryDirectory() as d:
            _prepare(d, language, code, tests, types)
            compile_cmd, run_cmd = _cmds(language, d, _docker())
            if compile_cmd:
                p, late = _exec(compile_cmd, d, 90, language)
                if late:
                    return {"error": "Compilation timed out"}
                if p.returncode != 0:
                    return {"error": "Compilation error:\n" + _clean(p.stderr or p.stdout, d)[:1500]}
            stdin = "input.txt" if language in ("java", "cpp") else None
            p, late = _exec(run_cmd, d, timeout, language, stdin)
            if late:
                return {"error": f"Time Limit Exceeded (>{timeout}s). Check for infinite loops."}
            if language in ("python", "javascript"):
                try:
                    res = json.loads(p.stdout)
                except Exception:
                    return {"error": (p.stderr or "Runner failed")[-500:]}
                if language == "javascript" and "results" in res:
                    for r, t in zip(res["results"], tests):
                        r["expected"] = t["expected"]
                        r["passed"] = "error" not in r and _eq(r["output"], t["expected"])
                return res
            rp = os.path.join(d, "results.txt")
            lines = open(rp, encoding="utf-8", errors="replace").read().splitlines() if os.path.exists(rp) else []
            if not lines and p.returncode != 0:
                return {"error": "Runtime Error: " + (_clean(p.stderr, d)[-500:] or "the program crashed (for example a segmentation fault or out-of-range access)")}
            results = []
            for i, t in enumerate(tests):
                if i < len(lines):
                    parts = lines[i].split(" ", 2)
                    sec = int(parts[1]) / 1e6 if len(parts) > 1 and parts[1].isdigit() else 0
                    if parts[0] == "OK":
                        try:
                            out = json.loads(parts[2])
                            results.append({"passed": _eq(out, t["expected"]), "output": out, "expected": t["expected"], "time": round(sec, 4)})
                            continue
                        except Exception:
                            pass
                    results.append({"passed": False, "output": None, "expected": t["expected"], "time": round(sec, 4),
                                    "error": (parts[2] if len(parts) > 2 else "error")[:200]})
                else:
                    results.append({"passed": False, "output": None, "expected": t["expected"], "time": 0,
                                    "error": "Runtime Error: program crashed or stopped early (check array bounds / recursion)"})
            return {"results": results}
    except ToolMissing as e:
        return {"error": str(e)}

def run_python(code, tests, timeout=5):
    return run_code("python", code, tests, timeout)

# ------------------------------------------------------------------ live syntax checking
def _marker(line, col, msg, sev, n_user):
    if line > n_user:  # error inside the generated test harness => almost always a signature mismatch
        return {"line": n_user, "col": 1, "endCol": 2, "severity": sev, "message": "Check that solution(...) matches the starter signature. " + msg}
    return {"line": line, "col": col, "endCol": col + 1, "severity": sev, "message": msg}

def _check_python(code):
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        col = e.offset or 1
        end = getattr(e, "end_offset", None) if getattr(e, "end_lineno", e.lineno) == e.lineno else None
        return [{"line": e.lineno or 1, "col": col, "endCol": end or col + 1, "severity": "error",
                 "message": f"{type(e).__name__}: {e.msg}"}]
    except Exception as e:
        return [{"line": 1, "col": 1, "endCol": 2, "severity": "error", "message": f"SyntaxError: {e}"}]
    m = []
    if not any(isinstance(n, ast.FunctionDef) and n.name == "solution" for n in tree.body):
        m.append({"line": 1, "col": 1, "endCol": 2, "severity": "warning", "message": "Define a function named solution(...)"})
    try:  # indentation style: 4 spaces per level, no tabs
        for tok in tokenize.generate_tokens(io.StringIO(code).readline):
            if tok.type == tokenize.INDENT and ("\t" in tok.string or len(tok.string) % 4):
                m.append({"line": tok.start[0], "col": 1, "endCol": len(tok.string) + 1, "severity": "warning",
                          "message": "Use 4 spaces for each indentation level (no tabs)"})
    except Exception:
        pass
    return m

def check_syntax(language, code, tests=None):
    """-> list of {line, col, endCol, severity, message}. JavaScript is checked in the browser by Monaco itself."""
    if language == "python":
        return _check_python(code)
    if language not in ("java", "cpp"):
        return []
    types = langs.infer_types(tests) if tests else None
    n_user = code.count("\n") + 1
    try:
        with tempfile.TemporaryDirectory() as d:
            _prepare(d, language, code, [], types, with_tests=False)
            p, late = _exec(_cmds(language, d, _docker(), check=True), d, 60, language)
            if late or p is None:
                return []
            out = (p.stderr or "") + (p.stdout or "")
    except ToolMissing as e:
        return [{"line": 1, "col": 1, "endCol": 2, "severity": "warning", "message": f"Live checking unavailable: {e}"}]
    lines, ms, seen = out.splitlines(), [], set()
    for i, ln in enumerate(lines):
        if language == "java":
            m = re.search(r"Main\.java:(\d+): (error|warning): (.*)$", ln)
            if not m: continue
            line, sev, msg, col = int(m.group(1)), m.group(2), m.group(3), 1
            if i + 2 < len(lines) and "^" in lines[i + 2]:
                col = lines[i + 2].index("^") + 1
            if line == 1: col = max(1, col - len(JAVA_HEAD))
        else:
            m = re.search(r"main\.cpp:(\d+):(\d+): (fatal error|error|warning): (.*)$", ln)
            if not m: continue
            line, col, sev, msg = int(m.group(1)), int(m.group(2)), m.group(3), m.group(4)
            sev = "error" if "error" in sev else "warning"
        mk = _marker(line, col, msg, sev, n_user)
        key = (mk["line"], mk["message"])
        if key not in seen:
            seen.add(key); ms.append(mk)
    return ms[:10]
