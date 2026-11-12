import hashlib, secrets, time, json, os
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import db, llm, runner, langs

app = FastAPI(title="CodeRush AI")
app.add_middleware(CORSMiddleware, allow_origins=[o.strip() for o in os.getenv("FRONTEND_ORIGIN", "http://localhost:5173").split(",")], allow_methods=["*"], allow_headers=["*"])
db.init()

LEVEL_NAMES = {1: "Easy", 2: "Medium", 3: "Hard"}
MINUTES = {1: 10, 2: 20, 3: 30}
POINTS = {1: 100, 2: 200, 3: 300}
SAMPLE_COUNT = 2  # tests shown in detail on "Run Code"; the rest are hidden until Submit

# ---------- auth ----------
class AuthIn(BaseModel):
    email: str
    password: str
    name: str = ""

def hash_pw(pw, salt=None):
    salt = salt or secrets.token_hex(8)
    return salt + "$" + hashlib.pbkdf2_hmac("sha256", pw.encode(), salt.encode(), 100_000).hex()

def new_session(uid):
    t = secrets.token_hex(24)
    db.execute("INSERT INTO sessions(token,user_id) VALUES(?,?)", (t, uid))
    return {"token": t}

@app.post("/api/auth/register")
def register(b: AuthIn):
    if len(b.password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")
    if db.one("SELECT id FROM users WHERE email=?", (b.email,)):
        raise HTTPException(400, "Email already registered")
    uid = db.execute("INSERT INTO users(name,email,password) VALUES(?,?,?)", (b.name or b.email.split("@")[0], b.email, hash_pw(b.password)))
    db.execute("INSERT INTO progress(user_id) VALUES(?)", (uid,))
    return new_session(uid)

@app.post("/api/auth/login")
def login(b: AuthIn):
    u = db.one("SELECT * FROM users WHERE email=?", (b.email,))
    if not u or not secrets.compare_digest(hash_pw(b.password, u["password"].split("$")[0]), u["password"]):
        raise HTTPException(401, "Wrong email or password")
    return new_session(u["id"])

def current_user(authorization: str = Header(default="")):
    u = db.one("SELECT u.* FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token=?", (authorization.replace("Bearer ", ""),))
    if not u:
        raise HTTPException(401, "Not logged in")
    return u

@app.get("/api/progress")
def progress(u=Depends(current_user)):
    p = db.one("SELECT * FROM progress WHERE user_id=?", (u["id"],))
    hist = db.many("SELECT level,result,time_taken,score,created FROM attempts WHERE user_id=? AND result!='in_progress' ORDER BY id DESC LIMIT 10", (u["id"],))
    return {"user": {"name": u["name"], "email": u["email"]}, **p, "history": hist}

# ---------- challenge ----------
class StartIn(BaseModel):
    topic: str = "Arrays"
    level: int = 1
    language: str = "python"

class CodeIn(BaseModel):
    code: str
    language: str = "python"

def load_attempt(aid, u):
    a = db.one("SELECT * FROM attempts WHERE id=? AND user_id=?", (aid, u["id"]))
    if not a:
        raise HTTPException(404, "Attempt not found")
    if a["result"] != "in_progress":
        raise HTTPException(400, "Challenge already finished")
    q = json.loads(db.one("SELECT data FROM questions WHERE id=?", (a["question_id"],))["data"])
    return a, q

@app.post("/api/challenge/start")
def start(b: StartIn, u=Depends(current_user)):
    prog = db.one("SELECT * FROM progress WHERE user_id=?", (u["id"],))
    if b.level not in LEVEL_NAMES or b.level > prog["current_level"]:
        raise HTTPException(403, "Level locked - complete the previous level first")
    if b.language not in langs.LANGS:
        raise HTTPException(400, "Unsupported language")
    q = llm.generate_question(b.topic, LEVEL_NAMES[b.level], b.language, MINUTES[b.level])
    qid = db.execute("INSERT INTO questions(topic,level,language,data) VALUES(?,?,?,?)", (b.topic, LEVEL_NAMES[b.level], b.language, json.dumps(q)))
    aid = db.execute("INSERT INTO attempts(user_id,question_id,level,started_at,result) VALUES(?,?,?,?,'in_progress')", (u["id"], qid, b.level, time.time()))
    return {"attempt_id": aid, "level": b.level, "difficulty": LEVEL_NAMES[b.level], "seconds_left": MINUTES[b.level] * 60, "question": llm.public(q)}

@app.post("/api/challenge/{aid}/run")
def run(aid: int, b: CodeIn, u=Depends(current_user)):
    a, q = load_attempt(aid, u)
    return runner.run_code(b.language, b.code, q["test_cases"][:SAMPLE_COUNT], type_tests=q["test_cases"])

@app.post("/api/challenge/{aid}/check")
def check(aid: int, b: CodeIn, u=Depends(current_user)):
    """Live syntax check while the student types (squiggles in the editor). Does not run the code."""
    a, q = load_attempt(aid, u)
    return {"markers": runner.check_syntax(b.language, b.code, q["test_cases"])}

@app.post("/api/challenge/{aid}/hint")
def hint(aid: int, b: CodeIn, u=Depends(current_user)):
    a, q = load_attempt(aid, u)
    if a["hints_used"] >= 3:
        return {"hint": "No more hints for this challenge.", "hints_used": 3}
    n = a["hints_used"] + 1
    db.execute("UPDATE attempts SET hints_used=? WHERE id=?", (n, aid))
    return {"hint": llm.hint(q["statement"], b.code, n, b.language), "hints_used": n}

@app.post("/api/challenge/{aid}/submit")
def submit(aid: int, b: CodeIn, u=Depends(current_user)):
    a, q = load_attempt(aid, u)
    limit = MINUTES[a["level"]] * 60
    elapsed = time.time() - a["started_at"]
    too_late = elapsed > limit + 5  # small grace for network delay
    res = runner.run_code(b.language, b.code, q["test_cases"])
    rs = res.get("results", [])
    all_pass = bool(rs) and all(r["passed"] for r in rs) and "error" not in res
    completed = all_pass and not too_late
    score = 0
    if completed:
        score = max(10, POINTS[a["level"]] - 10 * a["hints_used"] + int(50 * (1 - elapsed / limit)))
    result = "completed" if completed else ("timeout" if too_late else "failed")
    db.execute("UPDATE attempts SET time_taken=?, result=?, score=? WHERE id=?", (elapsed, result, score, aid))
    if completed:
        db.execute("UPDATE progress SET completed=completed+1, score=score+?, current_level=MAX(current_level, ?) WHERE user_id=?",
                   (score, min(a["level"] + 1, 3), u["id"]))
    fb = llm.feedback(q["statement"], b.code, rs if rs else res, completed, b.language)
    db.execute("INSERT INTO feedback(attempt_id,text) VALUES(?,?)", (aid, fb))
    prog = db.one("SELECT * FROM progress WHERE user_id=?", (u["id"],))
    shown = [r if i < SAMPLE_COUNT else {"passed": r["passed"], "hidden": True} for i, r in enumerate(rs)]
    return {"completed": completed, "timed_out": too_late, "time_taken": round(elapsed), "score": score,
            "from_level": a["level"], "new_level": prog["current_level"], "tests_passed": sum(r["passed"] for r in rs),
            "tests_total": len(rs), "error": res.get("error"), "results": shown, "feedback": fb}

# ---------- AI assistant page ----------
class GenIn(BaseModel):
    topic: str = "Arrays"
    level: str = "Medium"
    language: str = "python"

class AssistIn(BaseModel):
    problem: str
    code: str = ""
    hint_level: int = 1
    language: str = "python"

@app.post("/api/assistant/question")
def a_question(b: GenIn, u=Depends(current_user)):
    mins = {"Easy": 10, "Medium": 20, "Hard": 30}.get(b.level, 20)
    return llm.public(llm.generate_question(b.topic, b.level, b.language, mins))

@app.post("/api/assistant/hint")
def a_hint(b: AssistIn, u=Depends(current_user)):
    return {"hint": llm.hint(b.problem, b.code, b.hint_level, b.language)}

@app.post("/api/assistant/feedback")
def a_feedback(b: AssistIn, u=Depends(current_user)):
    return {"feedback": llm.feedback(b.problem, b.code, "not executed", False, b.language)}
