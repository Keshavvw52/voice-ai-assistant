import { useMemo, useState } from "react";

import bgImage from "../assets/bgm.jpg";
import { clearToken, login, persistToken } from "../services/auth";
import Signup from "./Signup";
import styles from "./Auth.module.css";

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export default function Login({ onLogin }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showSignup, setShowSignup] = useState(false);
  const [errors, setErrors] = useState({});
  const [formError, setFormError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const trimmedEmail = useMemo(() => email.trim(), [email]);

  if (showSignup) {
    return <Signup onSwitchToLogin={() => setShowSignup(false)} />;
  }

  function validateForm() {
    const nextErrors = {};

    if (!trimmedEmail) {
      nextErrors.email = "Email is required.";
    } else if (!EMAIL_PATTERN.test(trimmedEmail)) {
      nextErrors.email = "Enter a valid email address.";
    }

    if (!password.trim()) {
      nextErrors.password = "Password is required.";
    }

    setErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  }

  async function handleLogin(event) {
    event.preventDefault();
    setFormError("");

    if (!validateForm()) {
      clearToken();
      return;
    }

    setIsSubmitting(true);

    try {
      const data = await login({
        email: trimmedEmail,
        password: password.trim(),
      });

      if (!data.access_token) {
        throw new Error("Login response did not include a token.");
      }

      persistToken(data.access_token);
      onLogin();
    } catch (error) {
      clearToken();
      setFormError(error.message || "Login failed.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className={styles.authShell}>
      <div
        className={styles.background}
        style={{ backgroundImage: `url(${bgImage})` }}
      />
      <div className={styles.veil} />

      <section className={styles.panel}>
        <aside className={styles.brand}>
          <div>
            <div className={styles.eyebrow}>Voice AI Workspace</div>
            <h1 className={styles.headline}>
              Talk less to tabs.
              <span className={styles.headlineAccent}> Do more with MAX.</span>
            </h1>
            <p className={styles.copy}>
              Capture ideas, turn speech into action items, and keep your
              dashboard focused on what matters next.
            </p>
          </div>

          <div className={styles.points}>
            <div className={styles.point}>
              <div className={styles.pointTitle}>Fast voice capture</div>
              <div className={styles.pointCopy}>
                Record a thought, get a polished response, and keep moving.
              </div>
            </div>
            <div className={styles.point}>
              <div className={styles.pointTitle}>Task-aware replies</div>
              <div className={styles.pointCopy}>
                MAX turns spoken intent into a clear task list without clutter.
              </div>
            </div>
          </div>
        </aside>

        <div className={styles.formCard}>
          <h2 className={styles.formTitle}>Login</h2>
          <p className={styles.formSubtitle}>
            Use your account to open the dashboard. Empty fields will stay right
            here until they are valid.
          </p>

          <form className={styles.form} onSubmit={handleLogin} noValidate>
            {formError ? <div className={styles.banner}>{formError}</div> : null}

            <div className={styles.field}>
              <label className={styles.label} htmlFor="login-email">
                Email
              </label>
              <input
                id="login-email"
                type="email"
                placeholder="you@example.com"
                autoComplete="email"
                value={email}
                onChange={(event) => {
                  setEmail(event.target.value);
                  if (errors.email || formError) {
                    setErrors((current) => ({ ...current, email: "" }));
                    setFormError("");
                  }
                }}
                className={`${styles.input} ${
                  errors.email ? styles.inputError : ""
                }`}
              />
              <div className={styles.helper}>{errors.email || ""}</div>
            </div>

            <div className={styles.field}>
              <label className={styles.label} htmlFor="login-password">
                Password
              </label>
              <input
                id="login-password"
                type="password"
                placeholder="Enter your password"
                autoComplete="current-password"
                value={password}
                onChange={(event) => {
                  setPassword(event.target.value);
                  if (errors.password || formError) {
                    setErrors((current) => ({ ...current, password: "" }));
                    setFormError("");
                  }
                }}
                className={`${styles.input} ${
                  errors.password ? styles.inputError : ""
                }`}
              />
              <div className={styles.helper}>{errors.password || ""}</div>
            </div>

            <button
              type="submit"
              className={styles.primaryButton}
              disabled={isSubmitting}
            >
              {isSubmitting ? "Signing in..." : "Login Here"}
            </button>
          </form>

          <div className={styles.footer}>
            Need an account?{" "}
            <button
              type="button"
              className={styles.switchButton}
              onClick={() => setShowSignup(true)}
            >
              Create one here
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}
