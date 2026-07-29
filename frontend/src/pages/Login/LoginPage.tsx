import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import { useAuth } from "../../context/AuthContext";
import {
  clearRememberedUsername,
  getRememberedUsername,
  setRememberedUsername,
} from "../../services/authStorage";

export default function LoginPage() {
  const navigate = useNavigate();
  const { login, isAuthenticated, isLoading } = useAuth();
  const rememberedUsername = useMemo(() => getRememberedUsername(), []);

  const [usernameOrEmail, setUsernameOrEmail] = useState(rememberedUsername);
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(Boolean(rememberedUsername));
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (isAuthenticated) {
      navigate("/dashboard", { replace: true });
    }
  }, [isAuthenticated, navigate]);

  async function handleLogin(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setLoading(true);
    setErrorMessage(null);

    try {
      await login({
        usernameOrEmail,
        password,
        rememberMe,
      });

      if (rememberMe) {
        setRememberedUsername(usernameOrEmail);
      } else {
        clearRememberedUsername();
      }

      navigate("/dashboard", { replace: true });
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Unable to sign in. Please try again.",
      );
    } finally {
      setLoading(false);
    }
  }

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950 text-white">
        <div className="rounded-3xl border border-white/10 bg-white/5 px-8 py-7 shadow-2xl backdrop-blur">
          <div className="h-10 w-10 animate-spin rounded-full border-2 border-white/20 border-t-emerald-400" />
          <p className="mt-4 text-sm text-white/75">Preparing your session...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="relative min-h-screen overflow-hidden bg-slate-950 text-white">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,_rgba(16,185,129,0.18),_transparent_36%),radial-gradient(circle_at_bottom_right,_rgba(148,163,184,0.15),_transparent_32%),linear-gradient(135deg,_#020617_0%,_#0f172a_45%,_#111827_100%)]" />
      <div className="absolute inset-0 opacity-40 [background-image:linear-gradient(rgba(255,255,255,0.05)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.05)_1px,transparent_1px)] [background-size:48px_48px]" />

      <div className="relative z-10 grid min-h-screen lg:grid-cols-[1.1fr_0.9fr]">
        <section className="flex items-center px-6 py-12 sm:px-10 lg:px-16">
          <div className="max-w-2xl">
            <div className="inline-flex items-center rounded-full border border-emerald-400/20 bg-emerald-400/10 px-4 py-2 text-sm font-medium text-emerald-200">
              JANGID ASSOCIATE CRM
            </div>

            <h1 className="mt-8 text-4xl font-semibold tracking-tight text-white sm:text-5xl lg:text-6xl">
              Secure access for every role in the CRM.
            </h1>

            <p className="mt-6 max-w-xl text-base leading-7 text-slate-300 sm:text-lg">
              Sign in with your username or email, restore your session automatically,
              and keep role-based access ready for the authenticated workspace.
            </p>

            <div className="mt-10 grid gap-4 sm:grid-cols-3">
              {[
                ["JWT sessions", "Stored in localStorage and restored on refresh."],
                ["Auto logout", "401 responses clear the session immediately."],
                ["Role aware", "Navigation hides menus you should not see."],
              ].map(([title, description]) => (
                <div
                  key={title}
                  className="rounded-2xl border border-white/10 bg-white/5 p-4 backdrop-blur"
                >
                  <div className="text-sm font-semibold text-white">{title}</div>
                  <p className="mt-2 text-sm leading-6 text-slate-300">{description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="flex items-center justify-center px-6 py-12 sm:px-10 lg:px-16">
          <div className="w-full max-w-md rounded-3xl border border-white/10 bg-slate-900/75 p-8 shadow-[0_30px_80px_rgba(0,0,0,0.45)] backdrop-blur-xl">
            <div>
              <p className="text-sm uppercase tracking-[0.35em] text-emerald-300/90">
                Welcome back
              </p>
              <h2 className="mt-3 text-3xl font-semibold text-white">Login</h2>
              <p className="mt-2 text-sm leading-6 text-slate-300">
                Use the credentials assigned to your CRM account.
              </p>
            </div>

            <form className="mt-8 space-y-4" onSubmit={handleLogin}>
              <div>
                <label className="mb-2 block text-sm font-medium text-slate-200">
                  Username or Email
                </label>
                <input
                  value={usernameOrEmail}
                  onChange={(event) => setUsernameOrEmail(event.target.value)}
                  autoComplete="username"
                  className="w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-white outline-none transition placeholder:text-slate-500 focus:border-emerald-400/50 focus:ring-2 focus:ring-emerald-400/20"
                  placeholder="Enter your username or email"
                />
              </div>

              <div>
                <label className="mb-2 block text-sm font-medium text-slate-200">
                  Password
                </label>
                <input
                  type="password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  autoComplete="current-password"
                  className="w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-white outline-none transition placeholder:text-slate-500 focus:border-emerald-400/50 focus:ring-2 focus:ring-emerald-400/20"
                  placeholder="Enter your password"
                />
              </div>

              <label className="flex cursor-pointer items-center gap-3 text-sm text-slate-300">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(event) => setRememberMe(event.target.checked)}
                  className="h-4 w-4 rounded border-slate-500 bg-transparent text-emerald-500 focus:ring-emerald-400/30"
                />
                Remember Me
              </label>

              {errorMessage && (
                <div className="rounded-2xl border border-red-400/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
                  {errorMessage}
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="flex w-full items-center justify-center rounded-2xl bg-emerald-500 px-4 py-3.5 text-sm font-semibold text-slate-950 transition hover:bg-emerald-400 disabled:cursor-not-allowed disabled:opacity-70"
              >
                {loading ? "Signing in..." : "Login"}
              </button>
            </form>
          </div>
        </section>
      </div>
    </div>
  );
}