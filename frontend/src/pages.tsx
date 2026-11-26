import { FormEvent, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, session, Analysis, Stats } from "./api";

export function AuthPage({ mode }: { mode: "login" | "register" }) {
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const isLogin = mode === "login";

  async function submit(e: FormEvent) {
    e.preventDefault(); setError("");
    try {
      const r = await api<{ token: string; email: string }>(`/auth/${mode}`, {
        method: "POST", body: JSON.stringify({ email, password }),
      });
      session.set(r.token, r.email); nav("/analyze");
    } catch (err) { setError((err as Error).message); }
  }

  return (
    <div className="split">
      <section>
        <h1>Know where you stand before you apply.</h1>
        <p className="lead">Paste your resume and a job description. Fitwell shows your match score, the skills you already have, and the ones worth adding.</p>
      </section>
      <form className="card" onSubmit={submit}>
        <h2>{isLogin ? "Welcome back" : "Create your account"}</h2>
        <label htmlFor="email">Email</label>
        <input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        <label htmlFor="pw">Password (6+ characters)</label>
        <input id="pw" type="password" value={password} onChange={(e) => setPassword(e.target.value)} minLength={6} required />
        {error && <p className="error" role="alert">{error}</p>}
        <button className="primary" type="submit">{isLogin ? "Log in" : "Sign up"}</button>
        <p className="small">{isLogin ? <>New here? <Link to="/register">Create an account</Link></> : <>Already registered? <Link to="/login">Log in</Link></>}</p>
      </form>
    </div>
  );
}

function Result({ a }: { a: Analysis }) {
  const tone = a.score >= 75 ? "good" : a.score >= 45 ? "mid" : "low";
  const breakdown = a.breakdown;
  return (
    <section className={`card result ${tone}`} aria-live="polite">
      <div className="score"><b>{Math.round(a.score)}%</b><span>match for {a.job_title}</span></div>
      <p>{a.advice}</p>
      {breakdown && (
        <div className="breakdown">
          <div><b>{breakdown.skill_coverage}%</b><span>skill coverage</span></div>
          <div><b>{breakdown.text_similarity}%</b><span>text similarity</span></div>
          <div><b>{breakdown.confidence}</b><span>{breakdown.skills_considered} skills considered</span></div>
        </div>
      )}
      <h3>Skills you have</h3>
      <div className="chips">{a.matched.length ? a.matched.map((s) => <span key={s} className="chip have" title={a.evidence?.matched[s] || "Explicit keyword match"}>{s}</span>) : <em>None found yet.</em>}</div>
      {a.matched.length > 0 && <details className="evidence"><summary>Review resume evidence</summary>{a.matched.map((skill) => a.evidence?.matched[skill] && <p key={skill}><strong>{skill}: </strong>{a.evidence.matched[skill]}</p>)}</details>}
      <h3>Skills to add</h3>
      <div className="chips">{a.missing.length ? a.missing.map((s) => <span key={s} className="chip need" title={a.evidence?.missing[s] || "Found in job description"}>{s}</span>) : <em>You cover everything listed.</em>}</div>
      {a.missing.length > 0 && <details className="evidence"><summary>Review job requirements</summary>{a.missing.map((skill) => a.evidence?.missing[skill] && <p key={skill}><strong>{skill}: </strong>{a.evidence.missing[skill]}</p>)}</details>}
      <p className="disclaimer">{a.disclaimer}</p>
    </section>
  );
}

export function AnalyzePage() {
  const [job_title, setTitle] = useState("");
  const [job_description, setJd] = useState("");
  const [resume, setResume] = useState("");
  const [result, setResult] = useState<Analysis | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault(); setBusy(true); setError("");
    try {
      setResult(await api<Analysis>("/analyses", { method: "POST", body: JSON.stringify({ job_title, job_description, resume }) }));
    } catch (err) { setError((err as Error).message); } finally { setBusy(false); }
  }

  return (
    <>
      <h1>Check a resume against a job</h1>
      <form className="card" onSubmit={submit}>
        <label htmlFor="t">Job title</label>
        <input id="t" value={job_title} onChange={(e) => setTitle(e.target.value)} placeholder="e.g. Junior Backend Engineer" required />
        <label htmlFor="jd">Job description</label>
        <textarea id="jd" rows={6} value={job_description} onChange={(e) => setJd(e.target.value)} placeholder="Paste the job posting here (at least a few lines)." required />
        <label htmlFor="r">Your resume</label>
        <textarea id="r" rows={8} value={resume} onChange={(e) => setResume(e.target.value)} placeholder="Paste your resume as plain text." required />
        {error && <p className="error" role="alert">{error}</p>}
        <button className="primary" disabled={busy}>{busy ? "Analysing…" : "Check my fit"}</button>
      </form>
      {result && <Result a={result} />}
    </>
  );
}

export function DashboardPage() {
  const [items, setItems] = useState<Analysis[] | null>(null);
  const [stats, setStats] = useState<Stats | null>(null);
  const [error, setError] = useState("");

  const load = () => Promise.all([api<Analysis[]>("/analyses"), api<Stats>("/stats")])
    .then(([a, s]) => { setItems(a); setStats(s); })
    .catch((e) => setError(e.message));
  useEffect(() => { load(); }, []);

  async function remove(id: number) { await api(`/analyses/${id}`, { method: "DELETE" }); load(); }

  if (error) return <p className="error">{error}</p>;
  if (!items || !stats) return <p>Loading your results…</p>;
  return (
    <>
      <h1>My results</h1>
      {items.length === 0 ? (
        <p className="card">Nothing here yet. <Link to="/analyze">Run your first check</Link> and it will appear here.</p>
      ) : (
        <>
          <div className="stats">
            <div><b>{stats.total}</b><span>checks run</span></div>
            <div><b>{stats.average}%</b><span>average match</span></div>
            <div><b>{stats.best}%</b><span>best match</span></div>
          </div>
          <ul className="list">
            {items.map((a) => (
              <li key={a.id} className="card">
                <div className="head"><strong>{a.job_title}</strong><span>{new Date(a.created).toLocaleDateString()}</span></div>
                <div className="track"><div className="fill" style={{ width: `${a.score}%` }} /></div>
                <div className="head"><span>{Math.round(a.score)}% match</span>
                  <span>Missing: {a.missing.slice(0, 4).join(", ") || "nothing"}</span>
                  <button className="ghost danger" onClick={() => remove(a.id)}>Delete</button></div>
              </li>
            ))}
          </ul>
        </>
      )}
    </>
  );
}
