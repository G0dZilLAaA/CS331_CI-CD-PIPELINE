import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Navbar from "./Navbar";
import AITester from "./AITester";
import CITrigger from "./CITrigger";
import "./Dashboard.css";

const containerVariants = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.1 } }
};

const itemVariants = {
  hidden: { opacity: 0, y: 24 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: "easeOut" } }
};

const IconGrid = () => (
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/>
    <rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/>
  </svg>
);
const IconCpu = () => (
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/>
    <line x1="9" y1="1" x2="9" y2="4"/><line x1="15" y1="1" x2="15" y2="4"/>
    <line x1="9" y1="20" x2="9" y2="23"/><line x1="15" y1="20" x2="15" y2="23"/>
    <line x1="20" y1="9" x2="23" y2="9"/><line x1="20" y1="14" x2="23" y2="14"/>
    <line x1="1" y1="9" x2="4" y2="9"/><line x1="1" y1="14" x2="4" y2="14"/>
  </svg>
);
const IconZap = () => (
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
  </svg>
);
const IconCheck = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="20 6 9 17 4 12"/>
  </svg>
);
const IconShield = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
  </svg>
);

const TABS = [
  { id: "overview",   label: "Overview",  Icon: IconGrid },
  { id: "ai-tester",  label: "AI Tester", Icon: IconCpu },
  { id: "ci-trigger", label: "Run CI",    Icon: IconZap },
];

const STAT_CARDS = [
  { Icon: IconZap,   label: "CI Runs",   value: "∞", color: "#7c5cfc" },
  { Icon: IconCpu,   label: "AI Tests",  value: "—", color: "#06c7e1" },
  { Icon: IconCheck, label: "Pass Rate", value: "—", color: "#22d3a0" },
  { Icon: IconShield,label: "Coverage",  value: "—", color: "#f59e0b" },
];

const FEATURES = [
  {
    Icon: IconCpu,
    title: "AI Test Generation",
    desc: "Upload your code and let the AI generate comprehensive test cases using hybrid search algorithms.",
    tab: "ai-tester",
  },
  {
    Icon: IconZap,
    title: "Trigger CI Pipeline",
    desc: "Manually trigger your GitHub Actions CI/CD workflow and monitor live pipeline status.",
    tab: "ci-trigger",
  },
];

function Dashboard({ user, onLogout }) {
  const [activeTab, setActiveTab] = useState("overview");

  return (
    <div className="dashboard-page">
      <Navbar user={user} onLogout={onLogout} />

      <div className="dashboard-body">
        {/* Welcome */}
        <motion.div
          className="welcome-banner"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <h2>
            Welcome back,{" "}
            <span className="text-gradient">{user?.name || "User"}</span>
          </h2>
          <p>Here&apos;s what&apos;s happening in your CI/CD pipeline.</p>
        </motion.div>

        {/* Stat Cards */}
        <motion.div
          className="stats-row"
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          {STAT_CARDS.map((s) => (
            <motion.div key={s.label} className="stat-card" variants={itemVariants}>
              <div className="stat-card-icon" style={{ color: s.color }}><s.Icon /></div>
              <div className="stat-card-value" style={{ color: s.color }}>{s.value}</div>
              <div className="stat-card-label">{s.label}</div>
            </motion.div>
          ))}
        </motion.div>

        {/* Tabs */}
        <motion.div
          className="tab-row"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
        >
          {TABS.map((tab) => (
            <button
              key={tab.id}
              className={`tab-btn ${activeTab === tab.id ? "active" : ""}`}
              onClick={() => setActiveTab(tab.id)}
            >
              <tab.Icon />
              <span>{tab.label}</span>
            </button>
          ))}
        </motion.div>

        {/* Tab Content */}
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            className="tab-content-panel"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.25, ease: "easeInOut" }}
          >
            {activeTab === "overview" && (
              <motion.div
                className="feature-grid"
                variants={containerVariants}
                initial="hidden"
                animate="visible"
              >
                {FEATURES.map((f) => (
                  <motion.div
                    key={f.title}
                    className="feature-card"
                    variants={itemVariants}
                    onClick={() => setActiveTab(f.tab)}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.99 }}
                  >
                    <div className="feature-card-icon"><f.Icon /></div>
                    <div className="feature-card-title">{f.title}</div>
                    <div className="feature-card-desc">{f.desc}</div>
                    <div>
                      <span className="btn btn-primary btn-sm">Open →</span>
                    </div>
                  </motion.div>
                ))}
              </motion.div>
            )}
            {activeTab === "ai-tester"  && <AITester user={user} />}
            {activeTab === "ci-trigger" && <CITrigger user={user} />}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
}

export default Dashboard;