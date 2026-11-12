import { useEffect, useRef, useState } from "react";
import Editor from "@monaco-editor/react";
import { api, LANGS } from "./api";
import Game from "./Game";

const EXT = { python: "py", javascript: "js", java: "java", cpp: "cpp" };
const fmt = (s) => `${String(Math.max(0, Math.floor(s / 60))).padStart(2, "0")}:${String(Math.max(0, s % 60)).padStart(2, "0")}`;

export default function Challenge({ cfg, onFinish, onExit }) {
  const [ch, setCh] = useState(null);
  const [err, setErr] = useState("");
  const [lang, setLang] = useState(cfg.language || "python");
  const [codes, setCodes] = useState({});          // one buffer per language, so switching never loses code
  const [problems, setProblems] = useState([]);    // live syntax errors / warnings
  const [left, setLeft] = useState(0);
  const [out, setOut] = useState(null);
  const [hints, setHints] = useState([]);
  const [busy, setBusy] = useState(false);
  const [finished, setFinished] = useState(false);
  const done = useRef(false), ed = useRef(null), mo = useRef(null), seq = useRef(0);
  const code = codes[lang] ?? "";

  useEffect(() => {
    api("/challenge/start", cfg)
      .then((d) => {
        setCh(d); setLeft(d.seconds_left); setCodes(d.question.starters);
        if (!d.question.starters[lang]) setLang("python"); // question not available in the chosen language
      })
      .catch((e) => setErr(e.message));
  }, []);

  useEffect(() => {
    if (!ch) return;
    const t = setInterval(() => setLeft((s) => s - 1), 1000);
    return () => clearInterval(t);
  }, [ch]);

  useEffect(() => { if (ch && left <= 0 && !done.current) submit(); }, [left, ch]);

  // ---- live error checking while typing (debounced). JavaScript is checked by Monaco itself.
  useEffect(() => {
    if (!ch || lang === "javascript") return;
    const id = ++seq.current;
    const t = setTimeout(async () => {
      try {
        const r = await api(`/challenge/${ch.attempt_id}/check`, { code, language: lang });
        if (id === seq.current) setProblems(r.markers);
      } catch { /* ignore network hiccups while typing */ }
    }, 700);
    return () => clearTimeout(t);
  }, [code, lang, ch]);

  // ---- draw the red/yellow squiggles in the editor
  useEffect(() => {
    const m = mo.current, e = ed.current;
    if (!m || !e || lang === "javascript") return;
    const model = e.getModel();
    if (!model) return;
    m.editor.setModelMarkers(model, "coderush", problems.map((p) => {
      const line = Math.min(Math.max(p.line, 1), model.getLineCount());
      const end = Math.min(p.endCol || p.col + 1, model.getLineMaxColumn(line));
      return {
        startLineNumber: line, endLineNumber: line, startColumn: Math.min(p.col, end), endColumn: Math.max(end, p.col + 1),
        message: p.message, severity: p.severity === "error" ? m.MarkerSeverity.Error : m.MarkerSeverity.Warning,
      };
    }));
  }, [problems, lang]);

  const switchLang = (l) => { setLang(l); setProblems([]); setOut(null); };
  const jump = (p) => { const e = ed.current; if (!e) return; e.revealLineInCenter(p.line); e.setPosition({ lineNumber: p.line, column: p.col }); e.focus(); };

  async function run() {
    setBusy(true);
    try { setOut(await api(`/challenge/${ch.attempt_id}/run`, { code, language: lang })); } catch (e) { setOut({ error: e.message }); }
    setBusy(false);
  }
  async function hint() {
    const r = await api(`/challenge/${ch.attempt_id}/hint`, { code, language: lang });
    setHints((h) => [...h, r.hint]);
  }
  async function submit() {
    if (done.current) return;
    done.current = true; setBusy(true);
    try {
      const r = await api(`/challenge/${ch.attempt_id}/submit`, { code, language: lang });
      if (r.completed) { setFinished(true); await new Promise((ok) => setTimeout(ok, 2600)); } // runner reaches the flag
      onFinish(r);
    } catch (e) { setErr(e.message); done.current = false; }
    setBusy(false);
  }

  if (err) return <div className="card">{err}<br /><button onClick={onExit}>Back</button></div>;
  if (!ch) return <div className="card">Generating your challenge with AI…</div>;

  const passed = out?.results ? out.results.filter((r) => r.passed).length : 0;
  const total = out?.results ? out.results.length : 1;
  const errors = problems.filter((p) => p.severity === "error");

  return (
    <div className="challenge">
      <div className="topbar">
        <span className="badge">Level {ch.level}</span><span className="badge">{ch.difficulty}</span>
        <span className={"timer " + (left < 60 ? "danger" : "")}>⏱ {fmt(left)}</span>
        <button className="ghost" onClick={onExit}>Quit</button>
      </div>
      <div className="cols">
        <div>
          <Game progress={finished ? 1 : out?.results ? 0.5 * passed / total : 0} />
          <div className="card">
            <h3>{ch.question.title}</h3>
            <div className={ch.question.source === "ai" ? "good" : "bad"}>{ch.question.source === "ai" ? "✨ AI-generated" : "⚠ " + ch.question.note}</div>
            <p style={{ whiteSpace: "pre-wrap" }}>{ch.question.statement}</p>
            {ch.question.examples.map((e, i) => <pre key={i}>Input: {e.input}{"\n"}Output: {e.output}</pre>)}
            {hints.map((h, i) => <div className="hint" key={i}>💡 Hint {i + 1}: {h}</div>)}
          </div>
        </div>
        <div>
          <div className="row" style={{ alignItems: "center" }}>
            <select value={lang} onChange={(e) => switchLang(e.target.value)}>
              {Object.keys(ch.question.starters).map((k) => <option key={k} value={k}>{LANGS[k]}</option>)}
            </select>
            <span className={errors.length ? "bad" : "good"}>{errors.length ? `✘ ${errors.length} error${errors.length > 1 ? "s" : ""}` : "✔ No errors"}</span>
          </div>
          <Editor
            height="320px" theme="vs-dark" path={`solution.${EXT[lang]}`} language={lang} value={code}
            onChange={(v) => setCodes((c) => ({ ...c, [lang]: v || "" }))}
            onMount={(e, m) => { ed.current = e; mo.current = m; }}
            onValidate={(ms) => { if (lang === "javascript") setProblems(ms.map((m) => ({ line: m.startLineNumber, col: m.startColumn, endCol: m.endColumn, message: m.message, severity: m.severity >= 8 ? "error" : "warning" }))); }}
            options={{
              fontSize: 14, minimap: { enabled: false }, scrollBeyondLastLine: false,
              tabSize: lang === "javascript" ? 2 : 4, insertSpaces: true, detectIndentation: false,   // 4 spaces, never tabs
              autoIndent: "full", formatOnType: true, formatOnPaste: true,                          // Enter after "if x:" indents
              renderWhitespace: "boundary", guides: { indentation: true, highlightActiveIndentation: true },
              bracketPairColorization: { enabled: true }, autoClosingBrackets: "always", autoClosingQuotes: "always",
            }}
          />
          <div className="probs">
            {problems.slice(0, 5).map((p, i) => (
              <div key={i} className={"prob " + (p.severity === "error" ? "bad" : "warn")} onClick={() => jump(p)}>
                {p.severity === "error" ? "✘" : "⚠"} Line {p.line}: {p.message}
              </div>
            ))}
          </div>
          <div className="row">
            <button onClick={run} disabled={busy}>▷ Run Code</button>
            <button onClick={hint} disabled={busy || hints.length >= 3}>💡 Hint ({3 - hints.length} left)</button>
            <button className="primary" onClick={submit} disabled={busy}>Submit</button>
          </div>
          <div className="card output">
            <b>Execution Output</b>
            {!out && <p className="muted">Run your code to see results.</p>}
            {out?.error && <pre className="bad">{out.error}</pre>}
            {out?.results?.map((r, i) => (
              <pre key={i} className={r.passed ? "good" : "bad"}>
                {r.passed ? "✔ Passed" : "✘ Failed"} | Output: {JSON.stringify(r.output)} | Expected: {JSON.stringify(r.expected)} | {r.time}s{r.error ? "\n" + r.error : ""}
              </pre>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
