import { Link, NavLink, Navigate, Route, Routes, useNavigate } from "react-router-dom";
import { session } from "./api";
import { AuthPage, AnalyzePage, DashboardPage } from "./pages";

function Protected({ children }: { children: JSX.Element }) {
  return session.token ? children : <Navigate to="/login" replace />;
}

export default function App() {
  const nav = useNavigate();
  const logged = !!session.token;
  return (
    <>
      <header className="top">
        <Link to="/" className="brand">Fitwell</Link>
        <nav>
          {logged ? (
            <>
              <NavLink to="/analyze">New check</NavLink>
              <NavLink to="/dashboard">My results</NavLink>
              <button className="ghost" onClick={() => { session.clear(); nav("/login"); }}>Log out</button>
            </>
          ) : (<NavLink to="/login">Log in</NavLink>)}
        </nav>
      </header>
      <main>
        <Routes>
          <Route path="/" element={<Navigate to={logged ? "/analyze" : "/login"} replace />} />
          <Route path="/login" element={<AuthPage mode="login" />} />
          <Route path="/register" element={<AuthPage mode="register" />} />
          <Route path="/analyze" element={<Protected><AnalyzePage /></Protected>} />
          <Route path="/dashboard" element={<Protected><DashboardPage /></Protected>} />
          <Route path="*" element={<p>Page not found. <Link to="/">Go home</Link></p>} />
        </Routes>
      </main>
      <footer>Built with React, TypeScript, FastAPI, scikit-learn and SQLite.</footer>
    </>
  );
}
