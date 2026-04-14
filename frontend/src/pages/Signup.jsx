import { useMemo, useState } from "react";

import bgImage from "../assets/bgm.jpg";
import { signup } from "../services/auth";
import styles from "./Auth.module.css";

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export default function Signup({ onSwitchToLogin }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState({});
  const [formError, setFormError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const trimmedEmail = useMemo(() => email.trim(), [email]);

  function validateForm() {
    const nextErrors = {};

    if (!trimmedEmail) {
      nextErrors.email = "Email is required.";
    } else if (!EMAIL_PATTERN.test(trimmedEmail)) {
      nextErrors.email = "Enter a valid email address.";
    }

    if (!password.trim()) {
      nextErrors.password = "Password is required.";
    } else if (password.trim().length < 6) {
      nextErrors.password = "Password must be at least 6 characters.";
    }

    setErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  }

  async function handleSignup(event) {
    event.preventDefault();
    setFormError("");

    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);

    try {
      await signup({
        email: trimmedEmail,
        password: password.trim(),
      });

      onSwitchToLogin();
    } catch (error) {
      setFormError(error.message || "Signup failed.");
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
            <div className={styles.eyebrow}>New Workspace</div>
            <h1 className={styles.headline}>
              Build your voice flow.
              <span className={styles.headlineAccent}> Start in one minute.</span>
            </h1>
            <p className={styles.copy}>
              Create an account to keep voice sessions and task capture inside a
              single, focused workspace.
            </p>
          </div>

          <div className={styles.points}>
            <div className={styles.point}>
              <div className={styles.pointTitle}>Cleaner sessions</div>
              <div className={styles.pointCopy}>
                One login gives you a fresh dashboard and a reliable logout path.
              </div>
            </div>
            <div className={styles.point}>
              <div className={styles.pointTitle}>Simple account setup</div>
              <div className={styles.pointCopy}>
                Email and password only, with inline guidance before submit.
              </div>
            </div>
          </div>
        </aside>

        <div className={styles.formCard}>
          <h2 className={styles.formTitle}>Create Account</h2>
          <p className={styles.formSubtitle}>
            Sign up with a valid email and password, then head straight back to
            login.
          </p>

          <form className={styles.form} onSubmit={handleSignup} noValidate>
            {formError ? <div className={styles.banner}>{formError}</div> : null}

            <div className={styles.field}>
              <label className={styles.label} htmlFor="signup-email">
                Email
              </label>
              <input
                id="signup-email"
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
              <label className={styles.label} htmlFor="signup-password">
                Password
              </label>
              <input
                id="signup-password"
                type="password"
                placeholder="At least 6 characters"
                autoComplete="new-password"
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
              {isSubmitting ? "Creating account..." : "Create Account"}
            </button>
          </form>

          <div className={styles.footer}>
            Already have an account?{" "}
            <button
              type="button"
              className={styles.switchButton}
              onClick={onSwitchToLogin}
            >
              Back to login
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}
