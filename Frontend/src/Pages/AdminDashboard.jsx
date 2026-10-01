import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";

const VALID_STATUSES = ["draft", "submitted", "approved", "rejected"];

const formatINR = (v) =>
  v == null ? "—" : `₹${v.toLocaleString("en-IN")}`;

const formatDate = (iso) =>
  iso
    ? new Date(iso).toLocaleDateString("en-IN", {
        year: "numeric",
        month: "short",
        day: "numeric",
      })
    : "—";

const capitalize = (s) =>
  s ? s.charAt(0).toUpperCase() + s.slice(1) : "—";

function AdminDashboard() {
  const navigate = useNavigate();
  const admin = JSON.parse(localStorage.getItem("user"));

  const [stats, setStats]       = useState(null);
  const [claims, setClaims]     = useState([]);
  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState("");

  const [search, setSearch]     = useState("");
  const [filter, setFilter]     = useState("all");

  // Per-card state: expanded detail panel + status update
  const [expanded, setExpanded]         = useState({});
  const [pendingStatus, setPendingStatus] = useState({});
  const [updating, setUpdating]         = useState({});
  const [updateMsg, setUpdateMsg]       = useState({});
  const [downloading, setDownloading]   = useState({});
  const [downloadErr, setDownloadErr]   = useState({});

  const handleLogout = () => {
    localStorage.removeItem("user");
    localStorage.removeItem("isAuthenticated");
    navigate("/login");
  };

  // ── Fetch stats + claims on mount ────────────────────────────────────────

  useEffect(() => {
    if (!admin?.id) {
      setError("Admin session not found. Please log in again.");
      setLoading(false);
      return;
    }

    const fetchAll = async () => {
      try {
        const [statsRes, claimsRes] = await Promise.all([
          fetch(`http://127.0.0.1:5000/api/admin/stats?user_id=${admin.id}`),
          fetch(`http://127.0.0.1:5000/api/admin/claims?user_id=${admin.id}`),
        ]);

        const statsData  = await statsRes.json();
        const claimsData = await claimsRes.json();

        if (!statsRes.ok || !statsData.success) {
          setError(statsData.message || "Failed to load stats.");
          return;
        }
        if (!claimsRes.ok || !claimsData.success) {
          setError(claimsData.message || "Failed to load claims.");
          return;
        }

        setStats(statsData.stats);
        setClaims(claimsData.claims);

        // Seed pendingStatus with each claim's current status
        const initial = {};
        claimsData.claims.forEach((c) => {
          initial[c.claim_id] = c.status;
        });
        setPendingStatus(initial);

      } catch {
        setError("Unable to connect to server. Make sure Flask is running.");
      } finally {
        setLoading(false);
      }
    };

    fetchAll();
  }, [admin?.id]);

  // ── Status update ─────────────────────────────────────────────────────────

  const handleStatusUpdate = async (claimId) => {
    const newStatus = pendingStatus[claimId];
    setUpdating((p) => ({ ...p, [claimId]: true }));
    setUpdateMsg((p) => ({ ...p, [claimId]: "" }));

    try {
      const res = await fetch(
        `http://127.0.0.1:5000/api/admin/claims/${claimId}/status`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ user_id: admin.id, status: newStatus }),
        }
      );
      const data = await res.json();

      if (!res.ok || !data.success) {
        setUpdateMsg((p) => ({
          ...p,
          [claimId]: data.message || "Update failed.",
        }));
        return;
      }

      // Reflect the change locally without a full refetch
      setClaims((prev) =>
        prev.map((c) =>
          c.claim_id === claimId ? { ...c, status: newStatus } : c
        )
      );
      setStats((prev) => {
        if (!prev) return prev;
        // Rebuild counts from updated claims list
        const updated = claims.map((c) =>
          c.claim_id === claimId ? { ...c, status: newStatus } : c
        );
        return {
          total_claims:     updated.length,
          draft_claims:     updated.filter((c) => c.status === "draft").length,
          submitted_claims: updated.filter((c) => c.status === "submitted").length,
          approved_claims:  updated.filter((c) => c.status === "approved").length,
          rejected_claims:  updated.filter((c) => c.status === "rejected").length,
        };
      });
      setUpdateMsg((p) => ({ ...p, [claimId]: "✓ Updated" }));
    } catch {
      setUpdateMsg((p) => ({ ...p, [claimId]: "Connection error." }));
    } finally {
      setUpdating((p) => ({ ...p, [claimId]: false }));
    }
  };

  // ── PDF download ──────────────────────────────────────────────────────────

  const handleDownload = async (claimId) => {
    setDownloading((p) => ({ ...p, [claimId]: true }));
    setDownloadErr((p) => ({ ...p, [claimId]: "" }));
    try {
      const res = await fetch(
        `http://127.0.0.1:5000/api/claims/${claimId}/report?user_id=${admin.id}`
      );
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setDownloadErr((p) => ({ ...p, [claimId]: err.message || "Failed to generate report." }));
        return;
      }
      const blob = await res.blob();
      const url  = URL.createObjectURL(blob);
      const a    = document.createElement("a");
      a.href     = url;
      a.download = `ClaimSightAI_${claimId}_Report.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch {
      setDownloadErr((p) => ({ ...p, [claimId]: "Unable to connect to server." }));
    } finally {
      setDownloading((p) => ({ ...p, [claimId]: false }));
    }
  };

  // ── Filter + search ───────────────────────────────────────────────────────

  const visible = claims.filter((c) => {
    const matchStatus = filter === "all" || c.status === filter;
    if (!matchStatus) return false;

    if (!search.trim()) return true;
    const q = search.toLowerCase();
    return (
      String(c.claim_id).includes(q) ||
      c.claimant.name.toLowerCase().includes(q) ||
      c.claimant.email.toLowerCase().includes(q) ||
      (c.vehicle.vehicle_number || "").toLowerCase().includes(q)
    );
  });

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <div className="page-container">

      <header className="dashboard-header">
        <div>
          <h1>ClaimSightAI</h1>
          <p>Admin Dashboard — {admin?.name}</p>
        </div>
        <button className="logout-button" onClick={handleLogout}>
          Logout
        </button>
      </header>

      <main className="admin-main">

        {/* ── Loading / Error ── */}
        {loading && <p className="loading-message">Loading dashboard...</p>}
        {error   && <p className="error-message">{error}</p>}

        {!loading && !error && (
          <>
            {/* ── Stats ── */}
            {stats && (
              <div className="admin-stats-grid">
                <StatCard label="Total Claims"     value={stats.total_claims} />
                <StatCard label="Draft"            value={stats.draft_claims} />
                <StatCard label="Submitted"        value={stats.submitted_claims} />
                <StatCard label="Approved"         value={stats.approved_claims} />
                <StatCard label="Rejected"         value={stats.rejected_claims} />
              </div>
            )}

            {/* ── Controls ── */}
            <div className="admin-controls">
              <input
                className="admin-search-input"
                placeholder="Search by Claim ID, name, email, vehicle number…"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
              <select
                className="admin-filter-select"
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
              >
                <option value="all">All Statuses</option>
                {VALID_STATUSES.map((s) => (
                  <option key={s} value={s}>{capitalize(s)}</option>
                ))}
              </select>
            </div>

            <p className="admin-claims-count">
              {visible.length} claim{visible.length !== 1 ? "s" : ""} shown
            </p>

            {/* ── Empty state ── */}
            {visible.length === 0 && (
              <div className="admin-empty">
                <div className="admin-empty-icon">📋</div>
                <h3>No Claims Found</h3>
                <p>No claims match the current search or filter.</p>
              </div>
            )}

            {/* ── Claims list ── */}
            <div className="admin-claims-list">
              {visible.map((claim) => {
                const isExpanded = !!expanded[claim.claim_id];
                const msg        = updateMsg[claim.claim_id] || "";

                return (
                  <div key={claim.claim_id} className="admin-claim-card">

                    {/* Header row */}
                    <div className="admin-claim-header">
                      <span className="admin-claim-id">
                        Claim #{claim.claim_id}
                      </span>
                      <div className="admin-claim-meta">
                        <span
                          className={`admin-status-badge admin-status-${claim.status}`}
                        >
                          {claim.status.toUpperCase()}
                        </span>
                        <span className="myclaim-label">
                          {formatDate(claim.created_at)}
                        </span>
                      </div>
                    </div>

                    {/* Claimant */}
                    <p className="admin-claimant">
                      {claim.claimant.name}{" "}
                      <span>({claim.claimant.email})</span>
                    </p>

                    {/* Summary grid */}
                    <div className="admin-claim-grid">
                      <Field
                        label="Vehicle"
                        value={
                          claim.vehicle.make && claim.vehicle.model
                            ? `${claim.vehicle.make} ${claim.vehicle.model}${
                                claim.vehicle.year
                                  ? ` (${claim.vehicle.year})`
                                  : ""
                              }`
                            : "—"
                        }
                      />
                      <Field
                        label="Reg. Number"
                        value={claim.vehicle.vehicle_number || "—"}
                      />
                      <Field
                        label="Accident Date"
                        value={formatDate(claim.accident.date)}
                      />
                      <Field
                        label="Location"
                        value={claim.accident.location || "—"}
                      />
                      <Field
                        label="Damage"
                        value={
                          claim.damage.has_damage
                            ? claim.damage.damage_types
                                .map(capitalize)
                                .join(", ") || "Detected"
                            : "None detected"
                        }
                      />
                      <Field
                        label="Est. Cost"
                        value={
                          claim.damage.has_damage
                            ? `${formatINR(
                                claim.cost_estimate.min
                              )} – ${formatINR(claim.cost_estimate.max)}`
                            : "—"
                        }
                        highlight
                      />
                      {claim.submitted_at && (
                        <Field
                          label="Submitted"
                          value={formatDate(claim.submitted_at)}
                        />
                      )}
                    </div>

                    {/* Actions row */}
                    <div className="admin-claim-actions">

                      {/* Status update */}
                      <div className="admin-status-form">
                        <select
                          className="admin-status-select"
                          value={pendingStatus[claim.claim_id] ?? claim.status}
                          onChange={(e) =>
                            setPendingStatus((p) => ({
                              ...p,
                              [claim.claim_id]: e.target.value,
                            }))
                          }
                        >
                          {VALID_STATUSES.map((s) => (
                            <option key={s} value={s}>
                              {capitalize(s)}
                            </option>
                          ))}
                        </select>
                        <button
                          className="admin-update-btn"
                          disabled={
                            updating[claim.claim_id] ||
                            pendingStatus[claim.claim_id] === claim.status
                          }
                          onClick={() => handleStatusUpdate(claim.claim_id)}
                        >
                          {updating[claim.claim_id] ? "Saving…" : "Update Status"}
                        </button>
                        {msg && (
                          <span
                            style={{
                              fontSize: "13px",
                              color: msg.startsWith("✓")
                                ? "#16a34a"
                                : "#dc2626",
                            }}
                          >
                            {msg}
                          </span>
                        )}
                      </div>

                      {/* Expand / collapse */}
                      <button
                        className="admin-expand-btn"
                        onClick={() =>
                          setExpanded((p) => ({
                            ...p,
                            [claim.claim_id]: !p[claim.claim_id],
                          }))
                        }
                      >
                        {isExpanded ? "Hide Details ▲" : "View Details ▼"}
                      </button>
                    </div>

                    {/* Expanded detail panel */}
                    {isExpanded && (
                      <div className="admin-detail-panel">

                        <div className="admin-detail-section">
                          <p className="admin-detail-title">Accident Details</p>
                          <div className="admin-detail-grid">
                            <Field
                              label="Date"
                              value={formatDate(claim.accident.date)}
                            />
                            <Field
                              label="Location"
                              value={claim.accident.location || "—"}
                            />
                            <Field
                              label="Description"
                              value={claim.accident.description || "—"}
                            />
                          </div>
                        </div>

                        <div className="admin-detail-section">
                          <p className="admin-detail-title">Damage & Cost</p>
                          <div className="admin-detail-grid">
                            <Field
                              label="Images Uploaded"
                              value={claim.damage.image_count}
                            />
                            <Field
                              label="Damage Types"
                              value={
                                claim.damage.has_damage
                                  ? claim.damage.damage_types
                                      .map(capitalize)
                                      .join(", ") || "Detected"
                                  : "None"
                              }
                            />
                            <Field
                              label="Min Estimate"
                              value={formatINR(claim.cost_estimate.min)}
                            />
                            <Field
                              label="Max Estimate"
                              value={formatINR(claim.cost_estimate.max)}
                            />
                            <Field
                              label="Avg Estimate"
                              value={formatINR(claim.cost_estimate.average)}
                              highlight
                            />
                          </div>
                        </div>

                        <div className="admin-detail-section">
                          <p className="admin-detail-title">Claimant</p>
                          <div className="admin-detail-grid">
                            <Field label="User ID" value={claim.claimant.id} />
                            <Field label="Name"    value={claim.claimant.name} />
                            <Field label="Email"   value={claim.claimant.email} />
                          </div>
                        </div>

                        <div style={{ marginTop: "14px" }}>
                          <button
                            className="admin-expand-btn"
                            disabled={!!downloading[claim.claim_id]}
                            onClick={() => handleDownload(claim.claim_id)}
                          >
                            {downloading[claim.claim_id] ? "Generating PDF…" : "⬇ Download Report"}
                          </button>
                          {downloadErr[claim.claim_id] && (
                            <p className="error-message" style={{ marginTop: "8px" }}>
                              {downloadErr[claim.claim_id]}
                            </p>
                          )}
                        </div>

                      </div>
                    )}

                  </div>
                );
              })}
            </div>
          </>
        )}

      </main>
    </div>
  );
}

// ── Small reusable field ──────────────────────────────────────────────────

function StatCard({ label, value }) {
  return (
    <div className="admin-stat-card">
      <div className="admin-stat-number">{value}</div>
      <div className="admin-stat-label">{label}</div>
    </div>
  );
}

function Field({ label, value, highlight }) {
  return (
    <div className="myclaim-field">
      <span className="myclaim-label">{label}</span>
      <span
        className="myclaim-value"
        style={highlight ? { fontWeight: 700, color: "#2563eb" } : {}}
      >
        {value}
      </span>
    </div>
  );
}

export default AdminDashboard;
