import { useState } from "react";
import { api, LANGS } from "./api";

export default function Assistant() {
  const [tab, setTab] = useState("question");
  const [f, setF] = useState({ level: "Medium", topic: "Arrays", language: "python" });
  const [q, setQ] = useState(null);
  const [problem, setProblem] = useState("");
  const [code, setCode] = useState("");
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);

  const go = async (fn) => { setBusy(true); try { await fn(); } catch (e) { setText(e.message); } setBusy(false); };

  return (
    <div className="card">
      <h2>🤖 AI Assistant</h2>
      <div className="row">
        {[["question", "Generate Question"], ["hint", "Get Hint"], ["feedback", "Code Feedback"]].map(([k, l]) =>
          <button key={k} className={tab === k ? "primary" : ""} onClick={() => { setTab(k); setText(""); }}>{l}</button>)}
      </div>
      {tab === "question" && (<>
        <div className="row">
          <select value={f.level} onChange={(e) => setF({ ...f, level: e.target.value })}><option>Easy</option><option>Medium</option><option>Hard</option></select>
          <select value={f.topic} onChange={(e) => setF({ ...f, topic: e.target.value })}>{["Arrays", "Strings", "Loops", "Sorting", "Searching", "Hashing", "Recursion"].map((t) => <option key={t}>{t}</option>)}</select>
          <select value={f.language} onChange={(e) => setF({ ...f, language: e.target.value })}>{Object.entries(LANGS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select>
          <button className="primary" disabled={busy} onClick={() => go(async () => setQ(await api("/assistant/question", f)))}>{busy ? "Generating…" : "Generate Question"}</button>
        </div>
        {q && <div className="card"><h3>{q.title}</h3><div className={q.source === "ai" ? "good" : "bad"}>{q.source === "ai" ? "✨ AI-generated" : "⚠ " + q.note}</div><p style={{ whiteSpace: "pre-wrap" }}>{q.statement}</p>{q.examples.map((e, i) => <pre key={i}>Input: {e.input}{"\n"}Output: {e.output}</pre>)}</div>}
      </>)}
      {tab !== "question" && (<>
        <textarea rows={4} placeholder="Paste the problem statement" value={problem} onChange={(e) => setProblem(e.target.value)} />
        <textarea rows={8} placeholder="Paste your code" value={code} onChange={(e) => setCode(e.target.value)} />
        <button className="primary" disabled={busy} onClick={() => go(async () => {
          const r = tab === "hint" ? await api("/assistant/hint", { problem, code, language: f.language }) : await api("/assistant/feedback", { problem, code, language: f.language });
          setText(r.hint || r.feedback);
        })}>{busy ? "Thinking…" : tab === "hint" ? "Get Hint" : "Get Feedback"}</button>
        {text && <div className="card" style={{ whiteSpace: "pre-wrap" }}>{text}</div>}
      </>)}
    </div>
  );
}
