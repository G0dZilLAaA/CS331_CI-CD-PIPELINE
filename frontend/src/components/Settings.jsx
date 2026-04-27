import { useState } from "react";
import { motion } from "framer-motion";
import Navbar from "./Navbar";
import { useTheme } from "../ThemeContext";
import "./Settings.css";

const API_BASE = import.meta.env.VITE_API_BASE ?? "/api";

const containerVariants = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.08 } }
};
const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.35, ease: "easeOut" } }
};

/* ── SVG Icons ─────────────────────────────────────────── */
const IconUser = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
  </svg>
);
const IconLock = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
    <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
  </svg>
);
const IconPalette = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="13.5" cy="6.5" r=".5"/><circle cx="17.5" cy="10.5" r=".5"/>
    <circle cx="8.5" cy="7.5" r=".5"/><circle cx="6.5" cy="12.5" r=".5"/>
    <path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.926 0 1.648-.746 1.648-1.688 0-.437-.18-.835-.437-1.125-.29-.289-.438-.652-.438-1.125a1.64 1.64 0 0 1 1.668-1.668h1.996c3.051 0 5.555-2.503 5.555-5.554C21.965 6.012 17.461 2 12 2z"/>
  </svg>
);
const IconCheck = () => (
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="20 6 9 17 4 12"/>
  </svg>
);
const IconSun = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/>
    <line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
    <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/>
    <line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
    <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
  </svg>
);
const IconMoon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
  </svg>
);

function Settings({ user, onLogout }) {
  const { theme, toggleTheme } = useTheme();

  /* Profile form state */
  const [name, setName] = useState(user?.name || "");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  /* Status */
  const [profileLoading, setProfileLoading] = useState(false);
  const [profileMsg, setProfileMsg] = useState(null); // { type: 'success'|'error', text }

  const initials = user?.name
    ? user.name.split(" ").map((n) => n[0]).join("").toUpperCase().slice(0, 2)
    : "U";

  /* Save profile / password */
  const handleSaveProfile = async (e) => {
    e.preventDefault();
    setProfileMsg(null);

    if (newPassword && newPassword !== confirmPassword) {
      setProfileMsg({ type: "error", text: "Passwords do not match." });
      return;
    }

    setProfileLoading(true);
    try {
      const token = localStorage.getItem("token");
      const body = { name };
      if (newPassword) body.newPassword = newPassword;

      const res = await fetch(`${API_BASE}/settings`, {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
      });

      if (res.ok) {
        setProfileMsg({ type: "success", text: "Profile updated successfully." });
        setNewPassword("");
        setConfirmPassword("");
      } else {
        const data = await res.json().catch(() => ({}));
        setProfileMsg({ type: "error", text: data.error || "Failed to update profile." });
      }
    } catch {
      setProfileMsg({ type: "error", text: "Network error. Please try again." });
    } finally {
      setProfileLoading(false);
    }
  };

  return (
    <div className="settings-page">
      <Navbar user={user} onLogout={onLogout} />

      <div className="settings-body">
        {/* Page header */}
        <motion.div
          className="settings-page-header"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45 }}
        >
          <h2>Settings</h2>
          <p>Manage your profile, security, and display preferences.</p>
        </motion.div>

        <motion.div
          className="settings-grid"
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          {/* ── Profile Card ─────────────────────────────── */}
          <motion.div className="settings-card" variants={itemVariants}>
            <div className="settings-card-header">
              <div className="settings-card-icon"><IconUser /></div>
              <div>
                <div className="settings-card-title">Profile</div>
                <div className="settings-card-subtitle">Update your display name and password</div>
              </div>
            </div>

            {/* Read-only identity */}
            <div className="profile-identity">
              <div className="profile-avatar">{initials}</div>
              <div className="profile-meta">
                <span className="profile-name">{user?.name}</span>
                <span className="profile-role">{user?.position}</span>
              </div>
            </div>

            <div className="info-grid">
              <div className="info-row">
                <span className="info-label">Username</span>
                <span className="info-value">{user?.username}</span>
              </div>
              <div className="info-row">
                <span className="info-label">Employee ID</span>
                <span className="info-value mono">{user?.employeeId || "—"}</span>
              </div>
            </div>

            <div className="settings-divider" />

            <form onSubmit={handleSaveProfile} className="settings-form">
              <div className="input-wrap">
                <label htmlFor="name">Display Name</label>
                <input
                  id="name"
                  className="input-field"
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Your full name"
                  required
                />
              </div>

              <div className="input-wrap">
                <label htmlFor="newPassword">
                  <IconLock /> New Password <span className="optional-tag">(optional)</span>
                </label>
                <input
                  id="newPassword"
                  className="input-field"
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="Leave blank to keep current"
                  autoComplete="new-password"
                />
              </div>

              {newPassword && (
                <motion.div
                  className="input-wrap"
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                >
                  <label htmlFor="confirmPw">Confirm New Password</label>
                  <input
                    id="confirmPw"
                    className={`input-field ${
                      confirmPassword && confirmPassword !== newPassword ? "input-error" : ""
                    }`}
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="Re-enter new password"
                    autoComplete="new-password"
                  />
                  {confirmPassword && confirmPassword !== newPassword && (
                    <span className="field-error">Passwords do not match</span>
                  )}
                </motion.div>
              )}

              {profileMsg && (
                <motion.div
                  className={`settings-alert ${profileMsg.type}`}
                  initial={{ opacity: 0, scale: 0.96 }}
                  animate={{ opacity: 1, scale: 1 }}
                >
                  {profileMsg.type === "success" && <IconCheck />}
                  {profileMsg.text}
                </motion.div>
              )}

              <button
                type="submit"
                className="btn btn-primary btn-full"
                disabled={profileLoading}
              >
                {profileLoading ? (
                  <><span className="spinner" /> Saving…</>
                ) : (
                  "Save Changes"
                )}
              </button>
            </form>
          </motion.div>

          {/* ── Appearance Card ───────────────────────── */}
          <motion.div className="settings-card" variants={itemVariants}>
            <div className="settings-card-header">
              <div className="settings-card-icon"><IconPalette /></div>
              <div>
                <div className="settings-card-title">Appearance</div>
                <div className="settings-card-subtitle">Choose your preferred color scheme</div>
              </div>
            </div>

            <div className="theme-options">
              <button
                className={`theme-option ${theme === "light" ? "active" : ""}`}
                onClick={() => theme !== "light" && toggleTheme()}
                type="button"
              >
                <div className="theme-option-preview light-preview">
                  <div className="preview-bar" />
                  <div className="preview-content">
                    <div className="preview-line" />
                    <div className="preview-line short" />
                  </div>
                </div>
                <div className="theme-option-info">
                  <IconSun />
                  <span>Light Mode</span>
                  {theme === "light" && <span className="theme-active-dot" />}
                </div>
              </button>

              <button
                className={`theme-option ${theme === "dark" ? "active" : ""}`}
                onClick={() => theme !== "dark" && toggleTheme()}
                type="button"
              >
                <div className="theme-option-preview dark-preview">
                  <div className="preview-bar" />
                  <div className="preview-content">
                    <div className="preview-line" />
                    <div className="preview-line short" />
                  </div>
                </div>
                <div className="theme-option-info">
                  <IconMoon />
                  <span>Dark Mode</span>
                  {theme === "dark" && <span className="theme-active-dot" />}
                </div>
              </button>
            </div>

            <div className="current-theme-badge">
              Currently using: <strong>{theme === "dark" ? "Dark" : "Light"} Mode</strong>
            </div>
          </motion.div>
        </motion.div>
      </div>
    </div>
  );
}

export default Settings;