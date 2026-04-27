import React, { useEffect, useState } from "react";
import PipelineActionsView from "./PipelineActionsView";

const API_BASE = import.meta.env.VITE_API_BASE ?? "/api";

export default function CICDDashboard() {
  const [status, setStatus] = useState("unknown");
  const [message, setMessage] = useState("");
  const [purpose, setPurpose] = useState("testing");
  const [file, setFile] = useState(null);
  const [uploads, setUploads] = useState([]);
  const [pipelineResults, setPipelineResults] = useState(null);
  const [resultsMessage, setResultsMessage] = useState("Loading latest stored results...");

  const authHeaders = () => {
    const token = localStorage.getItem("token");
    return token ? { Authorization: `Bearer ${token}` } : {};
  };

  const fetchStatus = async () => {
    try {
      const res = await fetch(`${API_BASE}/pipeline-status`);
      const data = await res.json();
      if (!res.ok) {
        setStatus("Error");
        return;
      }
      if (data.message === "GitHub not configured" || data.message === "No workflow runs yet") {
        setStatus(data.message === "GitHub not configured" ? "Idle (configure GitHub)" : "Idle");
        return;
      }
      if (data.status === "in_progress" || data.status === "queued") setStatus("Running");
      else if (data.conclusion === "success") setStatus("Success");
      else if (data.conclusion === "failure" || data.conclusion === "cancelled")
        setStatus(data.conclusion === "cancelled" ? "Cancelled" : "Failed");
      else setStatus("Idle");
    } catch {
      setStatus("Offline");
    }
  };

  const loadPipelineResults = async () => {
    try {
      const res = await fetch(`${API_BASE}/pipeline-results`, {
        headers: authHeaders(),
      });
      const data = await res.json();
      if (!res.ok) {
        setPipelineResults(null);
        setResultsMessage(data.error || "Failed to load stored pipeline results");
        return;
      }

      setPipelineResults(data);
      setResultsMessage(data.message || "No stored pipeline results yet");
    } catch {
      setPipelineResults(null);
      setResultsMessage("Unable to load stored pipeline results");
    }
  };

  const loadUploads = async () => {
    try {
      const res = await fetch(`${API_BASE}/uploads`);
      if (!res.ok) return;
      const data = await res.json();
      setUploads(Array.isArray(data) ? data : []);
    } catch {
      setUploads([]);
    }
  };

  const startPipeline = async () => {
    setMessage("");
    try {
      const res = await fetch(`${API_BASE}/run-pipeline`, {
        method: "POST",
        headers: authHeaders(),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        setMessage(data.error || "Start failed");
        return;
      }
      setMessage(data.message || "Triggered");
      fetchStatus();
      loadPipelineResults();
    } catch (e) {
      setMessage(e.message || "Start failed");
    }
  };

  const stopPipeline = async () => {
    setMessage("");
    try {
      const res = await fetch(`${API_BASE}/stop-pipeline`, {
        method: "POST",
        headers: authHeaders(),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        setMessage(data.error || data.message || "Stop failed");
        return;
      }
      setMessage(data.message || "Stopped");
      fetchStatus();
    } catch (e) {
      setMessage(e.message || "Stop failed");
    }
  };

  const submitUpload = async (e) => {
    e.preventDefault();
    setMessage("");
    if (!file) {
      setMessage("Choose a file first");
      return;
    }
    const fd = new FormData();
    fd.append("file", file);
    fd.append("purpose", purpose);
    try {
      const res = await fetch(`${API_BASE}/uploads`, {
        method: "POST",
        headers: authHeaders(),
        body: fd,
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        setMessage(data.error || "Upload failed");
        return;
      }
      setMessage(`Stored: ${data.originalName}`);
      setFile(null);
      e.currentTarget.reset();
      loadUploads();
    } catch (err) {
      setMessage(err.message || "Upload failed");
    }
  };

  useEffect(() => {
    fetchStatus();
    loadUploads();
    loadPipelineResults();
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (status === "Success" || status === "Failed" || status === "Cancelled") {
      loadPipelineResults();
    }
  }, [status]);

  return (
    <div
      style={{
        padding: "40px",
        fontFamily: "system-ui, sans-serif",
        maxWidth: "900px",
        margin: "0 auto",
      }}
    >
      <h2 style={{ marginTop: 0 }}>CI/CD Dashboard</h2>

      <PipelineActionsView />

      <h3 style={{ fontSize: "15px", color: "#57606a" }}>Summary: {status}</h3>

      <div style={{ marginBottom: "16px" }}>
        <button type="button" onClick={startPipeline} style={{ marginRight: "10px" }}>
          Run pipeline
        </button>
        <button type="button" onClick={stopPipeline}>
          Stop pipeline
        </button>
      </div>

      {message ? (
        <p style={{ color: "#333", marginBottom: "16px" }} role="status">
          {message}
        </p>
      ) : null}

      <hr style={{ margin: "24px 0" }} />

      <h3>Test / deployment files (stored in MongoDB)</h3>
      <form onSubmit={submitUpload} style={{ marginBottom: "20px" }}>
        <div style={{ marginBottom: "8px" }}>
          <label htmlFor="purpose">Purpose: </label>
          <select
            id="purpose"
            value={purpose}
            onChange={(e) => setPurpose(e.target.value)}
          >
            <option value="testing">Testing</option>
            <option value="deployment">Deployment</option>
          </select>
        </div>
        <div style={{ marginBottom: "8px" }}>
          <input
            type="file"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
        </div>
        <button type="submit">Upload & store</button>
      </form>

      <h4>Recent uploads</h4>
      <ul style={{ paddingLeft: "20px" }}>
        {uploads.length === 0 ? (
          <li style={{ color: "#666" }}>No files stored yet</li>
        ) : (
          uploads.map((u) => (
            <li key={u._id}>
              {u.originalName} — {u.purpose} — {u.size} bytes —{" "}
              {u.uploadedAt ? new Date(u.uploadedAt).toLocaleString() : ""}
            </li>
          ))
        )}
      </ul>

      <hr style={{ margin: "24px 0" }} />

      <h3>Latest stored CI results</h3>
      <p style={{ color: "#57606a" }}>{resultsMessage}</p>

      {pipelineResults?.summary ? (
        <div style={{ border: "1px solid #d0d7de", borderRadius: "12px", padding: "16px" }}>
          <div style={{ marginBottom: "16px" }}>
            <strong>Status:</strong> {pipelineResults.summary.pipeline_status}
            <span style={{ marginLeft: "16px" }}>
              <strong>Total:</strong> {pipelineResults.summary.total_files}
            </span>
            <span style={{ marginLeft: "16px" }}>
              <strong>Completed:</strong> {pipelineResults.summary.completed}
            </span>
            <span style={{ marginLeft: "16px" }}>
              <strong>Skipped:</strong> {pipelineResults.summary.skipped}
            </span>
          </div>

          {pipelineResults.run ? (
            <p style={{ marginTop: 0 }}>
              Workflow run #{pipelineResults.run.run_number} on branch {pipelineResults.run.head_branch}
            </p>
          ) : null}

          <div style={{ display: "grid", gap: "12px" }}>
            {(pipelineResults.summary.results || []).map((item) => (
              <div
                key={`${item.file_path}-${item.pipeline_status}`}
                style={{
                  border: "1px solid #e5e7eb",
                  borderRadius: "10px",
                  padding: "12px",
                  background: "#f8fafc",
                }}
              >
                <div style={{ fontWeight: 600 }}>{item.file_path}</div>
                <div style={{ marginTop: "4px", color: "#334155" }}>
                  {item.language ? `${item.language} · ` : ""}
                  {item.pipeline_status}
                </div>
                {item.error ? (
                  <div style={{ marginTop: "8px", color: "#b91c1c" }}>{item.error}</div>
                ) : null}
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}
