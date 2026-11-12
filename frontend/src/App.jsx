import { useEffect, useState } from "react";
import { api, setToken, LANGS } from "./api";
import Game from "./Game";
import Challenge from "./Challenge";
import Assistant from "./Assistant";

const LEVELS = [{ n: 1, name: "Easy", min: 10 }, { n: 2, name: "Medium", min: 20 }, { n: 3, name: "Hard", min: 30 }];
const TOPICS = ["Arrays", "Strings", "Loops", "Sorting", "Searching", "Hashing", "Recursion"];

function Auth({ onDone }) {
  const [mode, setMode] = useState("login");
  const [f, setF] = useState({ name: "", email: "", password: "" });
  const [err, setErr] = useState("");
  const submit = async () => {
    try { const r = await api("/auth/" + mode, f); setToken(r.token); onDone(); } catch (e) { setErr(e.message); }
  };
  return (
    <div className="card auth">
      <h2>CodeRush <span className="accent">AI</span></h2>
      {mode === "register" && <input placeholder="Name" value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} />}
      <input placeholder="Email" value={f.email} onChange={(e) => setF({ ...f, email: e.target.value })} />
      <input placeholder="Password" type="password" value={f.password} onChange={(e) => setF({ ...f, password: e.target.value })} />
      {err && <p className="bad">{err}</p>}
      <button className="primary" onClick={submit}>{mode === "login" ? "Log in" : "Register"}</button>
      <button className="ghost" onClick={() => setMode(mode === "login" ? "register" : "login")}>{mode === "login" ? "Create an account" : "I already have an account"}</button>
    </div>
  );
}

export default function App() {
  const [user, setUser] = useState(undefined);
  const [prog, setProg] = useState(null);
  const [view, setView] = useState("home");
  const [cfg, setCfg] = useState({ topic: "Arrays", level: 1, language: "python" });
  const [result, setResult] = useState(null);

  const load = () => api("/progress").then((p) => { setProg(p); setUser(p.user); }).catch(() => setUser(null));
  useEffect(() => { load(); }, []);

  if (user === undefined) return <div className="card">Loading…</div>;
  if (!user) return <Auth onDone={load} />;

  return (
    <div className="app">
      <header>
        <b onClick={() => setView("home")} className="logo">🏃 CodeRush <span className="accent">AI</span></b>
        <nav>
          <button className="ghost" onClick={() => setView("home")}>Home</button>
          <button className="ghost" onClick={() => setView("assistant")}>AI Assistant</button>
          <button className="ghost" onClick={() => { setToken(null); setUser(null); }}>Logout ({user.name})</button>
        </nav>
      </header>

      {view === "home" && (
        <div className="cols">
          <div>
            <h1>Think Fast<br />Code Smart<br /><span className="accent">Win the Level</span></h1>
            <p>Play • Code • Learn • Grow</p>
            <div className="card">
              <label>Topic </label>
              <select value={cfg.topic} onChange={(e) => setCfg({ ...cfg, topic: e.target.value })}>{TOPICS.map((t) => <option key={t}>{t}</option>)}</select>
              <label> Language </label>
              <select value={cfg.language} onChange={(e) => setCfg({ ...cfg, language: e.target.value })}>{Object.entries(LANGS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select>
              <div className="row">
                {LEVELS.map((l) => (
                  <button key={l.n} className={cfg.level === l.n ? "primary" : ""} disabled={l.n > prog.current_level} onClick={() => setCfg({ ...cfg, level: l.n })}>
                    {l.n > prog.current_level ? "🔒 " : ""}{l.name} ({l.min} min)
                  </button>
                ))}
              </div>
              <button className="primary big" onClick={() => setView("challenge")}>▶ Start Game</button>
            </div>
          </div>
          <div>
            <Game progress={0.3} />
            <div className="card">
              <b>Your progress</b>
              <p>Score: {prog.score} pts • Completed: {prog.completed} • Unlocked level: {prog.current_level}</p>
              {prog.history.slice(0, 5).map((h, i) => <div key={i} className="muted">Level {h.level} – {h.result} – {h.score} pts</div>)}
            </div>
          </div>
        </div>
      )}

      {view === "challenge" && <Challenge cfg={cfg} onExit={() => { load(); setView("home"); }} onFinish={(r) => { setResult(r); load(); setView("result"); }} />}
      {view === "assistant" && <Assistant />}

      {view === "result" && result && (
        <div className="card result">
          <h1>{result.completed ? "🏆 You Win!" : result.timed_out ? "⌛ Time Over" : "❌ Not Completed"}</h1>
          <p>Time taken: {Math.floor(result.time_taken / 60)}:{String(result.time_taken % 60).padStart(2, "0")} • Score: {result.score} pts • Level {result.from_level} → {result.new_level} • Tests {result.tests_passed}/{result.tests_total}</p>
          {result.error && <pre className="bad">{result.error}</pre>}
          <div className="card" style={{ whiteSpace: "pre-wrap", textAlign: "left" }}><b>AI Feedback</b>{"\n"}{result.feedback}</div>
          <button className="primary" onClick={() => { setCfg({ ...cfg, level: result.completed ? Math.min(result.from_level + 1, 3) : result.from_level }); setView("challenge"); }}>{result.completed ? "Next Challenge" : "Try Again"}</button>
          <button className="ghost" onClick={() => setView("home")}>Back to Home</button>
        </div>
      )}
    </div>
  );
}
