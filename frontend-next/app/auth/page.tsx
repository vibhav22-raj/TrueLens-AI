"use client";

import { useEffect, useMemo, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useRouter } from "next/navigation";
import AnimatedBackground from "@/components/AnimatedBackground";
import Navbar from "@/components/Navbar";
import Toast from "@/components/Toast";
import LanguageSelector from "@/components/LanguageSelector";
import {
  apiLogin,
  apiRequestPasswordOtp,
  apiResetPasswordWithOtp,
  apiSignup,
  extractApiError
} from "@/lib/api";
import { setToken } from "@/lib/auth";

const panelVariants = {
  hidden: (direction: number) => ({ opacity: 0, x: direction * 40 }),
  visible: { opacity: 1, x: 0 },
  exit: (direction: number) => ({ opacity: 0, x: direction * -40 })
};

const LOGIN_EMAILS_KEY = "ds_login_emails";

type ForgotStep = "request" | "reset";

function normalizeEmailList(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value
    .filter((item) => typeof item === "string")
    .map((item) => item.trim())
    .filter((item) => item.length > 0)
    .slice(0, 8);
}

export default function AuthPage() {
  const [isLogin, setIsLogin] = useState(true);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [savedEmails, setSavedEmails] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const [showForgot, setShowForgot] = useState(false);
  const [forgotStep, setForgotStep] = useState<ForgotStep>("request");
  const [forgotEmail, setForgotEmail] = useState("");
  const [forgotOtp, setForgotOtp] = useState("");
  const [forgotPassword, setForgotPassword] = useState("");
  const [forgotLoading, setForgotLoading] = useState(false);
  const [forgotDevOtp, setForgotDevOtp] = useState<string | null>(null);

  const router = useRouter();

  useEffect(() => {
    router.prefetch("/dashboard");
  }, [router]);

  useEffect(() => {
    try {
      const raw = window.localStorage.getItem(LOGIN_EMAILS_KEY);
      if (!raw) return;
      setSavedEmails(normalizeEmailList(JSON.parse(raw)));
    } catch {
      setSavedEmails([]);
    }
  }, []);

  const toggleText = useMemo(
    () =>
      isLogin
        ? "New here? Create your shielded account."
        : "Already protected? Log in to continue.",
    [isLogin]
  );

  const rememberEmail = (value: string) => {
    const clean = value.trim();
    if (!clean || !clean.includes("@")) return;
    const merged = [clean, ...savedEmails.filter((item) => item.toLowerCase() !== clean.toLowerCase())].slice(0, 8);
    setSavedEmails(merged);
    try {
      window.localStorage.setItem(LOGIN_EMAILS_KEY, JSON.stringify(merged));
    } catch {
      // no-op
    }
  };

  const resetForgotState = () => {
    setForgotStep("request");
    setForgotOtp("");
    setForgotPassword("");
    setForgotDevOtp(null);
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setMessage("");
    setLoading(true);

    try {
      if (isLogin) {
        const data = await apiLogin({ email, password });
        setToken(data.access_token);
        rememberEmail(data?.user?.email || email);
        router.replace("/dashboard");
        return;
      } else {
        const data = await apiSignup({ email, password, name });
        setToken(data.access_token);
        rememberEmail(data?.user?.email || email);
        router.replace("/dashboard");
        return;
      }
    } catch (err) {
      setMessage(
        extractApiError(
          err,
          isLogin
            ? "Login failed. Please check your credentials."
            : "Signup failed. Try again in a moment."
        )
      );
    } finally {
      setLoading(false);
    }
  };

  const handleForgotRequest = async (event: React.FormEvent) => {
    event.preventDefault();
    setMessage("");
    setForgotLoading(true);
    try {
      const data = await apiRequestPasswordOtp({ email: forgotEmail });
      setForgotStep("reset");
      setForgotDevOtp(data?.debug_otp || null);
      setMessage(data?.message || "OTP sent. Please check your email.");
    } catch (err) {
      setMessage(extractApiError(err, "Could not send OTP. Please try again."));
    } finally {
      setForgotLoading(false);
    }
  };

  const handleForgotReset = async (event: React.FormEvent) => {
    event.preventDefault();
    setMessage("");
    setForgotLoading(true);
    try {
      const data = await apiResetPasswordWithOtp({
        email: forgotEmail,
        otp: forgotOtp,
        new_password: forgotPassword
      });
      setShowForgot(false);
      setIsLogin(true);
      setEmail(forgotEmail);
      setPassword("");
      resetForgotState();
      setMessage(data?.message || "Password changed successfully. Please login again.");
    } catch (err) {
      setMessage(extractApiError(err, "Could not reset password. Check OTP and try again."));
    } finally {
      setForgotLoading(false);
    }
  };

  return (
    <main className="relative min-h-screen overflow-hidden">
      <AnimatedBackground />
      <Navbar variant="auth" />

      <div className="absolute left-6 top-6 z-30">
        <LanguageSelector />
      </div>

      <section className="relative z-10 mx-auto mt-8 grid w-full max-w-6xl items-center gap-10 px-6 pb-16 md:grid-cols-2">
        <div className="glass rounded-[32px] border border-white/10 p-8 md:p-10">
          <p className="text-sm uppercase tracking-[0.3em] text-white/50">DeepShield AI</p>
          <h1 className="mt-4 text-4xl font-semibold leading-tight text-white">
            Welcome to <span className="gradient-text">DeepShield AI</span>
          </h1>
          <p className="mt-4 text-base text-white/70">
            A premium, AI-powered deepfake detection system designed to help you trust every
            image and video you verify.
          </p>
          <div className="mt-8 grid gap-4">
            {[
              "AI-powered deepfake detection system",
              "Trusted by advanced AI models",
              "Protect yourself from digital fraud"
            ].map((item) => (
              <div key={item} className="glass rounded-2xl border border-white/10 px-4 py-3 text-sm text-white/80">
                {item}
              </div>
            ))}
          </div>
        </div>

        <div className="glass rounded-[32px] border border-white/10 p-8 md:p-10">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-semibold text-white">
                {isLogin ? "Secure Login" : "Create Account"}
              </h2>
              <p className="mt-2 text-sm text-white/60">{toggleText}</p>
            </div>
            <div className="flex rounded-full border border-white/15 bg-white/5 p-1">
              <button
                onClick={() => {
                  setIsLogin(true);
                  setMessage("");
                }}
                className={`rounded-full px-4 py-2 text-xs font-semibold transition ${
                  isLogin ? "bg-white text-black" : "text-white/70"
                }`}
              >
                Login
              </button>
              <button
                onClick={() => {
                  setIsLogin(false);
                  setMessage("");
                }}
                className={`rounded-full px-4 py-2 text-xs font-semibold transition ${
                  !isLogin ? "bg-white text-black" : "text-white/70"
                }`}
              >
                Register
              </button>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="mt-8 space-y-5">
            <AnimatePresence mode="wait" initial={false} custom={isLogin ? 1 : -1}>
              <motion.div
                key={isLogin ? "login" : "register"}
                custom={isLogin ? 1 : -1}
                variants={panelVariants}
                initial="hidden"
                animate="visible"
                exit="exit"
                transition={{ duration: 0.35 }}
                className="space-y-5"
              >
                {!isLogin && (
                  <div className="relative">
                    <input
                      type="text"
                      required
                      minLength={2}
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      className="peer w-full rounded-2xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-white outline-none"
                    />
                    <label className="pointer-events-none absolute left-4 top-3 text-sm text-white/60 transition-all peer-focus:-top-3 peer-focus:text-xs peer-focus:text-white peer-valid:-top-3 peer-valid:text-xs">
                      Full Name
                    </label>
                  </div>
                )}

                <div className="relative">
                  <input
                    type="text"
                    list="saved-email-list"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="peer w-full rounded-2xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-white outline-none"
                  />
                  <datalist id="saved-email-list">
                    {savedEmails.map((item) => (
                      <option key={item} value={item} />
                    ))}
                  </datalist>
                  <label className="pointer-events-none absolute left-4 top-3 text-sm text-white/60 transition-all peer-focus:-top-3 peer-focus:text-xs peer-focus:text-white peer-valid:-top-3 peer-valid:text-xs">
                    {isLogin ? "Email or Username" : "Email"}
                  </label>
                </div>

                <div className="relative">
                  <input
                    type="password"
                    required
                    minLength={6}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="peer w-full rounded-2xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-white outline-none"
                  />
                  <label className="pointer-events-none absolute left-4 top-3 text-sm text-white/60 transition-all peer-focus:-top-3 peer-focus:text-xs peer-focus:text-white peer-valid:-top-3 peer-valid:text-xs">
                    Password
                  </label>
                </div>
              </motion.div>
            </AnimatePresence>

            {isLogin && (
              <button
                type="button"
                onClick={() => {
                  setShowForgot(true);
                  setForgotEmail(email);
                  resetForgotState();
                }}
                className="text-xs font-semibold text-rose-200/90 hover:text-rose-100"
              >
                Forgot password?
              </button>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-full bg-gradient-to-r from-rose-500 via-red-600 to-purple-600 px-6 py-3 text-sm font-semibold text-white shadow-[0_0_30px_rgba(190,24,93,0.35)] transition hover:brightness-110"
            >
              {loading ? "Processing..." : isLogin ? "Login" : "Create Account"}
            </button>
          </form>
        </div>
      </section>

      {showForgot && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/60 p-4">
          <div className="glass w-full max-w-md rounded-3xl border border-white/10 p-6">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-white">Reset Password</h3>
              <button
                onClick={() => {
                  setShowForgot(false);
                  resetForgotState();
                }}
                className="text-sm text-white/70 hover:text-white"
              >
                Close
              </button>
            </div>

            {forgotStep === "request" ? (
              <form onSubmit={handleForgotRequest} className="space-y-4">
                <p className="text-sm text-white/70">Enter your account email to receive OTP.</p>
                <input
                  type="email"
                  required
                  value={forgotEmail}
                  onChange={(e) => setForgotEmail(e.target.value)}
                  className="w-full rounded-2xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-white outline-none"
                  placeholder="Email"
                />
                <button
                  type="submit"
                  disabled={forgotLoading}
                  className="w-full rounded-full bg-gradient-to-r from-rose-500 via-red-600 to-purple-600 px-6 py-3 text-sm font-semibold text-white"
                >
                  {forgotLoading ? "Sending OTP..." : "Send OTP"}
                </button>
              </form>
            ) : (
              <form onSubmit={handleForgotReset} className="space-y-4">
                <p className="text-sm text-white/70">Enter OTP sent to your email and set new password.</p>

                {forgotDevOtp && (
                  <div className="rounded-2xl border border-amber-400/30 bg-amber-400/10 p-3 text-xs text-amber-100">
                    Dev OTP (SMTP not configured): <span className="font-semibold">{forgotDevOtp}</span>
                  </div>
                )}

                <input
                  type="text"
                  required
                  value={forgotOtp}
                  onChange={(e) => setForgotOtp(e.target.value)}
                  className="w-full rounded-2xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-white outline-none"
                  placeholder="Enter OTP"
                />

                <input
                  type="password"
                  required
                  minLength={6}
                  value={forgotPassword}
                  onChange={(e) => setForgotPassword(e.target.value)}
                  className="w-full rounded-2xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-white outline-none"
                  placeholder="New Password"
                />

                <button
                  type="submit"
                  disabled={forgotLoading}
                  className="w-full rounded-full bg-gradient-to-r from-rose-500 via-red-600 to-purple-600 px-6 py-3 text-sm font-semibold text-white"
                >
                  {forgotLoading ? "Updating..." : "Reset Password"}
                </button>
              </form>
            )}
          </div>
        </div>
      )}

      {message && <Toast message={message} />}
    </main>
  );
}
