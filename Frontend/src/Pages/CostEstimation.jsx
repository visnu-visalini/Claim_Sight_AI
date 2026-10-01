import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";

function CostEstimation() {
  const { claimId } = useParams();
  const navigate = useNavigate();

  const user = JSON.parse(localStorage.getItem("user"));

  const [estimate, setEstimate] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchEstimate = async () => {
      try {
        const response = await fetch(
          `http://127.0.0.1:5000/api/claims/${claimId}/cost?user_id=${user.id}`
        );

        const data = await response.json();

        if (!response.ok || !data.success) {
          setError(data.message || "Failed to load cost estimate.");
          return;
        }

        setEstimate(data.estimate);

      } catch (err) {
        setError("Unable to connect to server. Make sure Flask is running.");
      } finally {
        setLoading(false);
      }
    };

    fetchEstimate();
  }, [claimId, user.id]);

  const formatINR = (value) => {
    if (value === null || value === undefined) return "—";
    return `₹${value.toLocaleString("en-IN")}`;
  };

  const formatConfidence = (value) => {
    if (value === null || value === undefined) return "—";
    return `${(value * 100).toFixed(1)}%`;
  };

  return (
    <div className="page-container">

      <header className="dashboard-header">
        <div>
          <h1>ClaimSightAI</h1>
          <p>Claim #{claimId} — Repair Cost Estimation</p>
        </div>
        <button
          className="logout-button"
          onClick={() => navigate("/dashboard")}
        >
          Back to Dashboard
        </button>
      </header>

      <main className="form-main results-main">

        <h2>Estimated Repair Cost</h2>
        <p>Based on AI-detected damage from uploaded images.</p>

        {loading && (
          <p className="loading-message">Calculating estimate...</p>
        )}

        {error && (
          <p className="error-message">{error}</p>
        )}

        {/* No damage detected */}
        {!loading && !error && estimate && !estimate.has_damage && (
          <div className="cost-no-damage-box">
            <div className="cost-no-damage-icon">✓</div>
            <h3>No Damage Detected</h3>
            <p>
              The AI model did not detect any damage in the uploaded images
              for this claim. No repair cost estimate is required.
            </p>
            <button
              className="login-button"
              style={{ marginTop: "20px" }}
              onClick={() => navigate(`/claim/results/${claimId}`)}
            >
              View Damage Results
            </button>
          </div>
        )}

        {/* Damage detected — show breakdown */}
        {!loading && !error && estimate && estimate.has_damage && (
          <>
            {/* Per-damage breakdown */}
            <div className="cost-section">
              <h3>Damage Breakdown</h3>

              {estimate.damage_items.map((item, index) => (
                <div key={index} className="cost-item-card">

                  <div className="cost-item-header">
                    <span className="cost-item-type">
                      {item.damage_type
                        ? item.damage_type.charAt(0).toUpperCase() +
                          item.damage_type.slice(1)
                        : "Unknown"}
                    </span>
                    <span className="cost-confidence-badge">
                      AI Confidence: {formatConfidence(item.confidence)}
                    </span>
                  </div>

                  <p className="cost-item-filename">{item.filename}</p>

                  {item.status === "estimated" ? (
                    <div className="cost-item-values">
                      <div className="cost-value-block">
                        <span className="cost-label">Estimated Range</span>
                        <span className="cost-range">
                          {formatINR(item.estimated_min)} – {formatINR(item.estimated_max)}
                        </span>
                      </div>
                      <div className="cost-value-block">
                        <span className="cost-label">Estimated Average</span>
                        <span className="cost-average">
                          {formatINR(item.estimated_average)}
                        </span>
                      </div>
                    </div>
                  ) : (
                    <div className="cost-unknown-note">
                      <span>⚠</span> {item.note}
                    </div>
                  )}

                </div>
              ))}
            </div>

            {/* Total summary */}
            <div className="cost-total-card">
              <h3>Total Estimated Repair Cost</h3>

              <div className="cost-total-row">
                <span>Minimum</span>
                <span className="cost-total-value">
                  {formatINR(estimate.total_estimated_min)}
                </span>
              </div>

              <div className="cost-total-row">
                <span>Maximum</span>
                <span className="cost-total-value">
                  {formatINR(estimate.total_estimated_max)}
                </span>
              </div>

              <div className="cost-total-row cost-total-highlight">
                <span>Estimated Average</span>
                <span className="cost-total-value">
                  {formatINR(estimate.total_estimated_average)}
                </span>
              </div>

              {estimate.has_unknown_damage && (
                <p className="cost-unknown-warning">
                  ⚠ One or more damage types could not be estimated.
                  The total above excludes those items.
                  Manual assessment is recommended.
                </p>
              )}
            </div>

            {/* Disclaimer */}
            <div className="cost-disclaimer">
              <p>
                <strong>Disclaimer:</strong> {estimate.estimation_method}
              </p>
            </div>

            {/* Navigation */}
            <div className="cost-nav-buttons">
              <button
                className="cost-back-button"
                onClick={() => navigate(`/claim/results/${claimId}`)}
              >
                ← Back to Damage Results
              </button>

              <button
                className="login-button"
                onClick={() => navigate(`/claim/generate/${claimId}`)}
              >
                Generate Insurance Claim →
              </button>
            </div>
          </>
        )}

      </main>

    </div>
  );
}

export default CostEstimation;
