import { Eye, EyeOff, LockKeyhole, Mail, ShieldCheck } from "lucide-react";
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
  const remembered = useMemo(() => getRememberedUsername(), []);
  const [usernameOrEmail, setUsernameOrEmail] = useState(remembered);
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(Boolean(remembered));
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [sessionMessage] = useState(()=>{const value=window.sessionStorage.getItem("session-ended-message");window.sessionStorage.removeItem("session-ended-message");return value});

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
      await login({ usernameOrEmail, password, rememberMe });
      if (rememberMe) {
        setRememberedUsername(usernameOrEmail);
      } else {
        clearRememberedUsername();
      }
      navigate("/dashboard", { replace: true });
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : "Unable to sign in. Please try again.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="relative grid min-h-screen overflow-hidden bg-[#0F172A] lg:grid-cols-[1.08fr_.92fr]">
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_12%_18%,rgba(249,115,22,.22),transparent_26%),radial-gradient(circle_at_70%_88%,rgba(59,130,246,.13),transparent_30%)]"
      />

      <section className="relative hidden min-h-screen flex-col justify-between px-12 py-10 text-white lg:flex xl:px-16 xl:py-12">
        <div>
          <div className="flex items-center gap-4">
            <span className="grid h-16 w-16 place-items-center rounded-2xl border border-white/15 bg-white/10 shadow-lg shadow-slate-950/20">
              <img
                src="/branding/ja-logo.png"
                alt="Jangid Associate CRM"
                className="h-16 w-16 object-contain"
              />
            </span>
            <div>
              <p className="font-bold tracking-[.12em]">Jangid Associate CRM</p>
              <p className="mt-1 text-xs font-medium tracking-[.14em] text-orange-300">
                CUSTOMER RELATIONSHIP MANAGEMENT
              </p>
            </div>
          </div>

          <div className="mt-24 max-w-2xl xl:mt-32">
            <p className="text-xs font-semibold uppercase tracking-[.28em] text-orange-300">
              Business, organised
            </p>
            <h1 className="mt-6 text-4xl font-bold leading-[1.12] tracking-tight xl:text-5xl">
              Every customer relationship, handled with confidence.
            </h1>
            <p className="mt-6 max-w-xl text-base leading-8 text-slate-300 xl:text-lg">
              A focused workspace for your team to track cases, follow-ups, and outcomes.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 text-sm font-medium text-slate-300">
          <span className="grid h-9 w-9 place-items-center rounded-xl bg-orange-500/15 text-orange-300">
            <ShieldCheck size={19} aria-hidden="true" />
          </span>
          Secure, role-aware workspace
        </div>
      </section>

      <section
        aria-labelledby="login-heading"
        className="relative flex min-h-screen items-center justify-center bg-slate-50/95 px-5 py-10 dark:bg-slate-950/95 sm:px-8"
      >
        <div className="w-full max-w-md">
          <div className="mb-8 flex items-center justify-center gap-3 lg:hidden">
            <span className="grid h-16 w-16 place-items-center rounded-2xl bg-slate-900 shadow-lg shadow-slate-900/20 dark:bg-white">
              <img
                src="/branding/ja-logo.png"
                alt="Jangid Associate CRM"
                className="h-16 w-16 object-contain"
              />
            </span>
            <div>
              <p className="text-sm font-bold tracking-[.14em] text-slate-900 dark:text-white">
                Jangid Associate CRM
              </p>
            </div>
          </div>

          <div className="rounded-3xl border border-slate-200/80 bg-white p-7 shadow-2xl shadow-slate-950/10 dark:border-slate-800 dark:bg-slate-900 dark:shadow-black/30 sm:p-9">
            <p className="text-xs font-semibold uppercase tracking-[.22em] text-orange-600 dark:text-orange-400">
              Welcome back
            </p>
            <h2
              id="login-heading"
              className="mt-3 text-3xl font-bold tracking-tight text-slate-950 dark:text-white"
            >
              Sign in to your CRM
            </h2>
            <p className="mt-3 text-sm leading-6 text-slate-500 dark:text-slate-400">
              Continue to the Jangid Associate CRM customer workspace.
            </p>

            {sessionMessage&&<p className="mt-5 whitespace-pre-line rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">{sessionMessage}</p>}
            <form className="mt-8 space-y-5" onSubmit={handleLogin}>
              <label className="block text-sm font-semibold text-slate-700 dark:text-slate-200">
                Username or email
                <span className="relative mt-2 block">
                  <Mail
                    aria-hidden="true"
                    className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400"
                    size={18}
                  />
                  <input
                    required
                    value={usernameOrEmail}
                    onChange={(event) => setUsernameOrEmail(event.target.value)}
                    autoComplete="username"
                    placeholder="Enter username or email"
                    className="w-full rounded-xl border border-slate-200 bg-slate-50 py-3 pl-11 pr-4 text-slate-900 shadow-sm transition placeholder:text-slate-400 hover:border-slate-300 focus:border-orange-500 focus:bg-white focus:outline-none dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:hover:border-slate-600 dark:focus:border-orange-500"
                  />
                </span>
              </label>

              <label className="block text-sm font-semibold text-slate-700 dark:text-slate-200">
                Password
                <span className="relative mt-2 block">
                  <LockKeyhole
                    aria-hidden="true"
                    className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400"
                    size={18}
                  />
                  <input
                    required
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    autoComplete="current-password"
                    placeholder="Enter password"
                    className="w-full rounded-xl border border-slate-200 bg-slate-50 py-3 pl-11 pr-12 text-slate-900 shadow-sm transition placeholder:text-slate-400 hover:border-slate-300 focus:border-orange-500 focus:bg-white focus:outline-none dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:hover:border-slate-600 dark:focus:border-orange-500"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword((value) => !value)}
                    aria-label={showPassword ? "Hide password" : "Show password"}
                    aria-pressed={showPassword}
                    className="absolute right-2.5 top-1/2 -translate-y-1/2 rounded-lg p-1.5 text-slate-400 transition hover:bg-slate-200/70 hover:text-slate-700 dark:hover:bg-slate-800 dark:hover:text-slate-200"
                  >
                    {showPassword ? (
                      <EyeOff size={18} aria-hidden="true" />
                    ) : (
                      <Eye size={18} aria-hidden="true" />
                    )}
                  </button>
                </span>
              </label>

              <label className="flex cursor-pointer items-center gap-3 text-sm text-slate-600 dark:text-slate-300">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(event) => setRememberMe(event.target.checked)}
                  className="h-4 w-4 rounded border-slate-300 accent-orange-500"
                />
                Remember me on this device
              </label>

              {errorMessage && (
                <div
                  role="alert"
                  aria-live="polite"
                  className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900/70 dark:bg-red-950/40 dark:text-red-300"
                >
                  {errorMessage}
                </div>
              )}

              <button
                type="submit"
                disabled={loading || isLoading}
                className="flex w-full items-center justify-center rounded-xl bg-orange-500 px-4 py-3.5 text-sm font-semibold text-white shadow-lg shadow-orange-500/25 transition hover:bg-orange-600 hover:shadow-orange-500/35 active:bg-orange-700 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {loading ? "Signing in…" : "Sign in securely"}
              </button>
            </form>

            <p className="mt-8 text-center text-xs text-slate-400 dark:text-slate-500">
              © {new Date().getFullYear()} Jangid Associate CRM. All rights reserved.
            </p>
          </div>
        </div>
      </section>
    </main>
  );
}
