# CodeRush AI – Gamified and AI-Enhanced Coding Practice Platform

Stack (as in the report): React + Monaco + HTML5 Canvas · FastAPI · Code Runner (Docker) · LLM API · database.
Database: SQLite for development (zero setup). Moving to PostgreSQL later only means changing `db.py`.

## Run the backend
```bash
cd backend
python -m venv venv && source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                  # put your ANTHROPIC_API_KEY in .env
uvicorn main:app --reload --port 8000
```
Without an API key the app still works using a built-in "Two Sum" question and simple hints.

## Run the frontend
```bash
cd frontend
npm install
npm run dev        # open http://localhost:5173
```

## Languages (Python, JavaScript, Java, C++)
Choose the language on the home screen or switch inside the challenge (each language keeps its own code).
Every question gets starter code in every language it supports; Java/C++ signatures are generated from the test data
(types: int, bool, string, list of ints, list of lists of ints). Questions the AI makes with other types fall back to Python/JavaScript.
- **Live errors while typing:** Python (compiler + 4-space indentation warnings), Java (`javac`) and C++ (`g++ -fsyntax-only`) are checked by
  the backend 0.7 s after you stop typing and shown as squiggles + a list under the editor (click an item to jump to the line).
  JavaScript is checked by the editor itself.
- **Python indentation:** 4 spaces, Tab/Shift+Tab indent/unindent, Enter after `if x:` indents, indent guides, tabs flagged.
- Local mode (`USE_DOCKER=false`) needs `python`, `node`, a JDK (`javac`, `java`) and `g++` installed.
- Docker mode pulls these images once: `python:3.11-slim`, `node:20-slim`, `eclipse-temurin:21-jdk`, `gcc:13`.

## Safe code execution
Set `USE_DOCKER=true` in `backend/.env` (Docker must be installed; `docker pull python:3.11-slim` once).
Containers run with no network, 128 MB RAM, 0.5 CPU and a process limit.
`USE_DOCKER=false` runs code in a plain subprocess: fine on your own laptop, NOT safe for real users.

## Features mapped to the report
| Report feature | Where |
|---|---|
| Easy 10 / Medium 20 / Hard 30 min timers | `main.py` MINUTES (timer also enforced server-side), `Challenge.jsx` |
| Running game moves with test progress | `Game.jsx` |
| AI question generation (topic/level/language) | `llm.generate_question`, Assistant page |
| Step-by-step hints (3 levels, never full code) | `llm.hint`, `/challenge/{id}/hint` |
| AI feedback: logic, errors, complexity | `llm.feedback` |
| Run on test cases, output + expected + time | `runner.py` |
| Score, level unlock, saved progress | `/challenge/{id}/submit`, `progress` table |

## Design decisions worth explaining in your viva
- **AI test cases are verified**: the LLM also writes a reference solution; the question is used only if that solution passes all its own tests (otherwise retried, then falls back).
- **Hidden tests**: Run Code shows 2 sample tests; Submit runs all of them.
- **Server-side timer**: start time is stored on the server, so editing the browser timer cannot cheat.
- **Score** = level base points − 10 per hint + time bonus.

## Next steps (from your Future Enhancements)
Java/C/C++ runners (new harness per language), leaderboard (`SELECT ... ORDER BY score`), daily challenges/streaks, weak-topic personalisation from the `attempts` table.

## Deploy (free demo: Render + Vercel)
1. Push to GitHub (`.gitignore` already excludes `.env` and the database).
2. Render -> New -> Blueprint -> pick the repo (uses `render.yaml`). Set `ANTHROPIC_API_KEY`; leave `FRONTEND_ORIGIN` for step 4.
3. Vercel -> Import repo, root directory `frontend`, env var `VITE_API_URL` = your Render URL (no trailing slash).
4. Put the Vercel URL into Render's `FRONTEND_ORIGIN` and redeploy.
Note: free Render disk resets on restart (users/progress lost), and `USE_DOCKER=false` is not safe for public users.
