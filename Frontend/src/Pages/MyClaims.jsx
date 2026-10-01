import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";

function MyClaims() {
  const navigate = useNavigate();

  const user = JSON.parse(localStorage.getItem("user"));

  const [claims, setClaims] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!user?.id) {
      setError("User not found. Please log in again.");
      setLoading(false);
      return;
    }

    const fetchClaims = async () => {
      try {
        const response = await fetch(
          `http://127.0.0.1:5000/api/claims/my?user_id=${user.id}`
        );

        const data = await response.json();

        if (!response.ok || !data.success) {
          setError(data.message || "Failed to load claims.");
          return;
        }

        setClaims(data.claims);

      } catch (err) {
        setError("Unable to connect to server. Make sure Flask is running.");
      } finally {
        setLoading(false);
      }
    };

    fetchClaims();
  }, [user?.id]);

  // ── Helpers ──────────────────────────────────────────────────────────────

  const formatINR = (value) => {
    if (value === null || value === undefined) return "—";
    return `₹${value.toLocaleString("en-IN")}`;
  };

  const formatDate = (iso) => {
    if (!iso) return "—";
    return new Date(iso).toLocaleDateString("en-IN", {
      year: "numeric", month: "short", day: "numeric",
    });
  };

  const capitalize = (str) => {
    if (!str) return "—";
    return str.charAt(0).toUpperCase() + str.slice(1);
  };

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <div className="page-container">

      <header className="dashboard-header">
        <div>
          <h1>ClaimSightAI</h1>
          <p>My Claims</p>
        </div>
        <button
          className="logout-button"
          onClick={() => navigate("/dashboard")}
        >
          Back to Dashboard
        </button>
      </header>

      <main className="myclaims-main">

        <div className="myclaims-header">
          <div>
            <h2>My Claims</h2>
            <p>View and track your insurance claims.</p>
          </div>

          <button
            className="login-button myclaims-new-btn"
            onClick={() => navigate("/claim/new")}
          >
            + New Claim
          </button>
        </div>

        {/* Loading */}
        {loading && (
          <p className="loading-message">Loading your claims...</p>
        )}

        {/* Error */}
        {error && (
          <p className="error-message">{error}</p>
        )}

        {/* Empty state */}
        {!loading && !error && claims.length === 0 && (
          <div className="myclaims-empty">
            <div className="myclaims-empty-icon">📋</div>
            <h3>No Claims Yet</h3>
            <p>You haven't created any insurance claims yet.</p>
            <button
              className="login-button"
              style={{ marginTop: "20px" }}
              onClick={() => navigate("/claim/new")}
            >
              Create New Claim
            </button>
          </div>
        )}

        {/* Claims list */}
        {!loading && !error && claims.length > 0 && (
          <>
            <p className="myclaims-count">
              {claims.length} claim{claims.length !== 1 ? "s" : ""} found
            </p>

            <div className="myclaims-list">
              {claims.map((claim) => (
                <div key={claim.claim_id} className="myclaim-card">

                  {/* Card header — ID + status */}
                  <div className="myclaim-card-header">
                    <span className="myclaim-id">Claim #{claim.claim_id}</span>
                    <span className={`myclaim-status-badge myclaim-status-${claim.status}`}>
                      {claim.status.toUpperCase()}
                    </span>
                  </div>

                  {/* Vehicle */}
                  <div className="myclaim-vehicle">
                    <span className="myclaim-vehicle-name">
                      {claim.vehicle.make && claim.vehicle.model
                        ? `${claim.vehicle.make} ${claim.vehicle.model}`
                        : "Vehicle details not entered"}
                      {claim.vehicle.year ? ` (${claim.vehicle.year})` : ""}
                    </span>
                    {claim.vehicle.vehicle_number && (
                      <span className="myclaim-vehicle-number">
                        {claim.vehicle.vehicle_number}
                      </span>
                    )}
                  </div>

                  <div className="myclaim-grid">

                    {/* Accident */}
                    <div className="myclaim-field">
                      <span className="myclaim-label">Accident Date</span>
                      <span className="myclaim-value">
                        {formatDate(claim.accident.date)}
                      </span>
                    </div>

                    <div className="myclaim-field">
                      <span className="myclaim-label">Location</span>
                      <span className="myclaim-value">
                        {claim.accident.location || "—"}
                      </span>
                    </div>

                    {/* Damage */}
                    <div className="myclaim-field">
                      <span className="myclaim-label">Damage</span>
                      <span className="myclaim-value">
                        {claim.damage.has_damage
                          ? claim.damage.damage_types.map(capitalize).join(", ")
                          : "No damage detected"}
                      </span>
                    </div>

                    <div className="myclaim-field">
                      <span className="myclaim-label">Images</span>
                      <span className="myclaim-value">
                        {claim.damage.image_count} uploaded
                      </span>
                    </div>

                    {/* Cost */}
                    <div className="myclaim-field">
                      <span className="myclaim-label">Estimated Cost</span>
                      <span className="myclaim-value myclaim-cost">
                        {claim.damage.has_damage
                          ? `${formatINR(claim.cost_estimate.min)} – ${formatINR(claim.cost_estimate.max)}`
                          : "—"}
                      </span>
                    </div>

                    {/* Dates */}
                    <div className="myclaim-field">
                      <span className="myclaim-label">Created</span>
                      <span className="myclaim-value">
                        {formatDate(claim.created_at)}
                      </span>
                    </div>

                    {claim.submitted_at && (
                      <div className="myclaim-field">
                        <span className="myclaim-label">Submitted</span>
                        <span className="myclaim-value">
                          {formatDate(claim.submitted_at)}
                        </span>
                      </div>
                    )}

                  </div>

                  {/* Action */}
                  <div className="myclaim-actions">
                    <button
                      className="myclaim-view-btn"
                      onClick={() => navigate(`/claim/review/${claim.claim_id}`)}
                    >
                      View Claim →
                    </button>
                  </div>

                </div>
              ))}
            </div>
          </>
        )}

      </main>

    </div>
  );
}

export default MyClaims;
