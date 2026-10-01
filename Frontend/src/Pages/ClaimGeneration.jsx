import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";

function ClaimGeneration() {
  const { claimId } = useParams();
  const navigate = useNavigate();

  const user = JSON.parse(localStorage.getItem("user"));

  const [claim, setClaim] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchClaim = async () => {
      try {
        const response = await fetch(
          `http://127.0.0.1:5000/api/claims/${claimId}/generate?user_id=${user.id}`
        );

        const data = await response.json();

        if (!response.ok || !data.success) {
          setError(data.message || "Failed to generate claim.");
          return;
        }

        setClaim(data.claim);

      } catch (err) {
        setError("Unable to connect to server. Make sure Flask is running.");
      } finally {
        setLoading(false);
      }
    };

    fetchClaim();
  }, [claimId, user.id]);

  const formatINR = (value) => {
    if (value === null || value === undefined) return "—";
    return `₹${value.toLocaleString("en-IN")}`;
  };

  const formatConfidence = (value) => {
    if (value === null || value === undefined) return "—";
    return `${(value * 100).toFixed(1)}%`;
  };

  const formatDate = (iso) => {
    if (!iso) return "—";
    return new Date(iso).toLocaleDateString("en-IN", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  const capitalize = (str) => {
    if (!str) return "—";
    return str.charAt(0).toUpperCase() + str.slice(1);
  };

  return (
    <div className="page-container">

      <header className="dashboard-header">
        <div>
          <h1>ClaimSightAI</h1>
          <p>Claim #{claimId} — Insurance Claim Generation</p>
        </div>
        <button
          className="logout-button"
          onClick={() => navigate("/dashboard")}
        >
          Back to Dashboard
        </button>
      </header>

      <main className="form-main results-main">

        <h2>Generated Insurance Claim</h2>
        <p>Review all claim details before proceeding to submission.</p>

        {loading && (
          <p className="loading-message">Generating claim document...</p>
        )}

        {error && (
          <p className="error-message">{error}</p>
        )}

        {!loading && !error && claim && (
          <>

            {/* ── A. Claim Information ── */}
            <div className="gen-section">
              <h3 className="gen-section-title">A. Claim Information</h3>
              <table className="gen-table">
                <tbody>
                  <tr>
                    <td>Claim ID</td>
                    <td>#{claim.claim_id}</td>
                  </tr>
                  <tr>
                    <td>Status</td>
                    <td>
                      <span className="gen-status-badge">
                        {capitalize(claim.status)}
                      </span>
                    </td>
                  </tr>
                  <tr>
                    <td>Created</td>
                    <td>{formatDate(claim.created_at)}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            {/* ── B. Vehicle Information ── */}
            <div className="gen-section">
              <h3 className="gen-section-title">B. Vehicle Information</h3>
              <table className="gen-table">
                <tbody>
                  <tr>
                    <td>Vehicle Number</td>
                    <td>{claim.vehicle.vehicle_number || "—"}</td>
                  </tr>
                  <tr>
                    <td>Make</td>
                    <td>{claim.vehicle.make || "—"}</td>
                  </tr>
                  <tr>
                    <td>Model</td>
                    <td>{claim.vehicle.model || "—"}</td>
                  </tr>
                  <tr>
                    <td>Year</td>
                    <td>{claim.vehicle.year || "—"}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            {/* ── C. Accident Information ── */}
            <div className="gen-section">
              <h3 className="gen-section-title">C. Accident Information</h3>
              <table className="gen-table">
                <tbody>
                  <tr>
                    <td>Date</td>
                    <td>{formatDate(claim.accident.date)}</td>
                  </tr>
                  <tr>
                    <td>Location</td>
                    <td>{claim.accident.location || "—"}</td>
                  </tr>
                  <tr>
                    <td>Description</td>
                    <td className="gen-description">
                      {claim.accident.description || "—"}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            {/* ── D. AI Damage Assessment ── */}
            <div className="gen-section">
              <h3 className="gen-section-title">D. AI Damage Assessment</h3>

              <div className="gen-damage-summary">
                <span>
                  Total Images: <strong>{claim.damage_assessment.total_images}</strong>
                </span>
                <span>
                  Images with Damage: <strong>{claim.damage_assessment.damaged_images}</strong>
                </span>
              </div>

              {claim.damage_assessment.items.length === 0 ? (
                <p className="no-damage-note">No images uploaded for this claim.</p>
              ) : (
                claim.damage_assessment.items.map((item) => (
                  <div key={item.image_id} className="gen-damage-card">

                    <div className="gen-damage-card-left">
                      <img
                        src={item.image_url}
                        alt={item.filename}
                      />
                    </div>

                    <div className="gen-damage-card-right">
                      <p className="result-filename">{item.filename}</p>

                      <div className={`damage-badge ${item.damage_detected ? "badge-damage" : "badge-no-damage"}`}>
                        {item.damage_detected ? "Damage Detected" : "No Damage Detected"}
                      </div>

                      {item.damage_detected && (
                        <table className="result-table" style={{ marginTop: "12px" }}>
                          <tbody>
                            <tr>
                              <td>Damage Type</td>
                              <td>{capitalize(item.damage_type)}</td>
                            </tr>
                            <tr>
                              <td>Confidence</td>
                              <td>{formatConfidence(item.confidence)}</td>
                            </tr>
                            <tr>
                              <td>Bounding Box</td>
                              <td>{item.bounding_box || "—"}</td>
                            </tr>
                          </tbody>
                        </table>
                      )}
                    </div>

                  </div>
                ))
              )}
            </div>

            {/* ── E. Cost Estimation ── */}
            <div className="gen-section">
              <h3 className="gen-section-title">E. Cost Estimation</h3>

              {!claim.damage_assessment.has_damage ? (
                <p className="no-damage-note">
                  No damage detected — no repair cost applicable.
                </p>
              ) : (
                <>
                  <table className="gen-table">
                    <tbody>
                      <tr>
                        <td>Minimum Estimate</td>
                        <td>{formatINR(claim.cost_estimation.min)}</td>
                      </tr>
                      <tr>
                        <td>Maximum Estimate</td>
                        <td>{formatINR(claim.cost_estimation.max)}</td>
                      </tr>
                      <tr>
                        <td>Average Estimate</td>
                        <td className="gen-cost-highlight">
                          {formatINR(claim.cost_estimation.average)}
                        </td>
                      </tr>
                    </tbody>
                  </table>

                  {claim.cost_estimation.has_unknown_damage && (
                    <div className="cost-unknown-note" style={{ marginTop: "12px" }}>
                      ⚠ One or more damage types could not be estimated.
                      Manual assessment is recommended.
                    </div>
                  )}

                  <div className="cost-disclaimer" style={{ marginTop: "14px" }}>
                    <p>{claim.cost_estimation.estimation_method}</p>
                  </div>
                </>
              )}
            </div>

            {/* ── F. Generated Claim Summary ── */}
            <div className="gen-section">
              <h3 className="gen-section-title">F. Generated Claim Summary</h3>
              <div className="gen-summary-box">
                {claim.summary.split("\n\n").map((para, i) => (
                  <p key={i}>{para}</p>
                ))}
              </div>
            </div>

            {/* ── Navigation ── */}
            <div className="cost-nav-buttons">
              <button
                className="cost-back-button"
                onClick={() => navigate(`/claim/cost/${claimId}`)}
              >
                ← Back to Cost Estimation
              </button>

              <button
                className="login-button"
                onClick={() => navigate(`/claim/review/${claimId}`)}
              >
                Proceed to Claim Review
              </button>
            </div>

          </>
        )}

      </main>

    </div>
  );
}

export default ClaimGeneration;
