import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";

function ClaimReview() {
  const { claimId } = useParams();
  const navigate = useNavigate();

  const user = JSON.parse(localStorage.getItem("user"));

  const [claim, setClaim] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [submittedAt, setSubmittedAt] = useState(null);

  const [showConfirm, setShowConfirm] = useState(false);

  const [downloading, setDownloading]     = useState(false);
  const [downloadError, setDownloadError] = useState("");

  const handleDownload = async () => {
    setDownloading(true);
    setDownloadError("");
    try {
      const res = await fetch(
        `http://127.0.0.1:5000/api/claims/${claimId}/report?user_id=${user.id}`
      );
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setDownloadError(err.message || "Failed to generate report.");
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
      setDownloadError("Unable to connect to server. Make sure Flask is running.");
    } finally {
      setDownloading(false);
    }
  };

  useEffect(() => {
    const fetchReview = async () => {
      try {
        const response = await fetch(
          `http://127.0.0.1:5000/api/claims/${claimId}/review?user_id=${user.id}`
        );

        const data = await response.json();

        if (!response.ok || !data.success) {
          setError(data.message || "Failed to load claim for review.");
          return;
        }

        setClaim(data.claim);

        // If already submitted, reflect that immediately
        if (data.claim.status === "submitted") {
          setSubmitted(true);
          setSubmittedAt(data.claim.submitted_at);
        }

      } catch (err) {
        setError("Unable to connect to server. Make sure Flask is running.");
      } finally {
        setLoading(false);
      }
    };

    fetchReview();
  }, [claimId, user.id]);

  const handleSubmit = async () => {
    setShowConfirm(false);
    setSubmitError("");
    setSubmitting(true);

    try {
      const response = await fetch(
        `http://127.0.0.1:5000/api/claims/${claimId}/submit`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ user_id: user.id }),
        }
      );

      const data = await response.json();

      if (!response.ok || !data.success) {
        setSubmitError(data.message || "Submission failed.");
        return;
      }

      setSubmitted(true);
      setSubmittedAt(data.submitted_at);
      setClaim((prev) => ({ ...prev, status: "submitted" }));

    } catch (err) {
      setSubmitError("Unable to connect to server. Make sure Flask is running.");
    } finally {
      setSubmitting(false);
    }
  };

  // ── Helpers ──────────────────────────────────────────────────────────────

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
      year: "numeric", month: "long", day: "numeric",
    });
  };

  const formatDateTime = (iso) => {
    if (!iso) return "—";
    return new Date(iso).toLocaleString("en-IN");
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
          <p>Claim #{claimId} — Review &amp; Submit</p>
        </div>
        <button
          className="logout-button"
          onClick={() => navigate("/dashboard")}
        >
          Back to Dashboard
        </button>
      </header>

      <main className="form-main results-main">

        <h2>Claim Review</h2>
        <p>Review all details carefully before submitting your insurance claim.</p>

        {loading && <p className="loading-message">Loading claim for review...</p>}
        {error   && <p className="error-message">{error}</p>}

        {/* ── Submission success banner ── */}
        {submitted && (
          <div className="review-success-banner">
            <div className="review-success-icon">✓</div>
            <div>
              <h3>Claim Submitted Successfully</h3>
              <p>
                Your insurance claim #{claimId} has been submitted.
                {submittedAt && (
                  <> Submitted on {formatDateTime(submittedAt)}.</>
                )}
              </p>
            </div>
          </div>
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
                      <span className={`review-status-badge review-status-${claim.status}`}>
                        {capitalize(claim.status)}
                      </span>
                    </td>
                  </tr>
                  <tr>
                    <td>Created</td>
                    <td>{formatDate(claim.created_at)}</td>
                  </tr>
                  {claim.submitted_at && (
                    <tr>
                      <td>Submitted</td>
                      <td>{formatDateTime(claim.submitted_at)}</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            {/* ── B. Vehicle Details ── */}
            <div className="gen-section">
              <h3 className="gen-section-title">B. Vehicle Details</h3>
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

            {/* ── C. Accident Details ── */}
            <div className="gen-section">
              <h3 className="gen-section-title">C. Accident Details</h3>
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

            {/* ── D. Damage Assessment ── */}
            <div className="gen-section">
              <h3 className="gen-section-title">D. Damage Assessment</h3>

              <div className="gen-damage-summary">
                <span>Total Images: <strong>{claim.damage_assessment.total_images}</strong></span>
                <span>Images with Damage: <strong>{claim.damage_assessment.damaged_images}</strong></span>
              </div>

              {claim.damage_assessment.items.length === 0 ? (
                <p className="no-damage-note">No images uploaded for this claim.</p>
              ) : (
                claim.damage_assessment.items.map((item) => (
                  <div key={item.image_id} className="gen-damage-card">

                    <div className="gen-damage-card-left">
                      <img src={item.image_url} alt={item.filename} />
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

                      {/* OpenAI second opinion */}
                      {item.openai_available && (
                        <div className="openai-panel" style={{ marginTop: "14px" }}>
                          <div className="openai-panel-header">
                            <span className="openai-label">GPT-4o Vision — Second Opinion</span>
                            {item.openai_agrees_with_yolo === true && (
                              <span className="openai-agree">✓ Agrees with YOLO</span>
                            )}
                            {item.openai_agrees_with_yolo === false && (
                              <span className="openai-disagree">✗ Disagrees with YOLO</span>
                            )}
                          </div>
                          <table className="result-table" style={{ marginTop: "8px" }}>
                            <tbody>
                              <tr>
                                <td>Damage Present</td>
                                <td>{item.openai_damage_present ? "Yes" : "No"}</td>
                              </tr>
                              {item.openai_damage_present && (
                                <>
                                  <tr>
                                    <td>Damage Type</td>
                                    <td>{item.openai_damage_type || "—"}</td>
                                  </tr>
                                  <tr>
                                    <td>Affected Part</td>
                                    <td>{item.openai_affected_part || "—"}</td>
                                  </tr>
                                  <tr>
                                    <td>Severity</td>
                                    <td>
                                      <span className={`openai-severity openai-severity-${(item.openai_severity || "").toLowerCase()}`}>
                                        {item.openai_severity || "—"}
                                      </span>
                                    </td>
                                  </tr>
                                  <tr>
                                    <td>Confidence</td>
                                    <td>
                                      {item.openai_confidence != null
                                        ? `${(item.openai_confidence * 100).toFixed(1)}%`
                                        : "—"}
                                    </td>
                                  </tr>
                                </>
                              )}
                              {item.openai_assessment && (
                                <tr>
                                  <td>Assessment</td>
                                  <td style={{ fontStyle: "italic", color: "#475569" }}>
                                    {item.openai_assessment}
                                  </td>
                                </tr>
                              )}
                            </tbody>
                          </table>
                        </div>
                      )}
                      {item.openai_available === false && (
                        <div className="openai-panel openai-unavailable" style={{ marginTop: "14px" }}>
                          <span className="openai-label">GPT-4o Vision</span>
                          <span className="openai-na">Unavailable</span>
                        </div>
                      )}
                    </div>

                  </div>
                ))
              )}
            </div>

            {/* ── E. Cost Estimate ── */}
            <div className="gen-section">
              <h3 className="gen-section-title">E. Cost Estimate</h3>

              {!claim.damage_assessment.has_damage ? (
                <p className="no-damage-note">
                  No damage detected — no repair cost applicable.
                </p>
              ) : (
                <>
                  <table className="gen-table">
                    <tbody>
                      <tr>
                        <td>Minimum</td>
                        <td>{formatINR(claim.cost_estimation.min)}</td>
                      </tr>
                      <tr>
                        <td>Maximum</td>
                        <td>{formatINR(claim.cost_estimation.max)}</td>
                      </tr>
                      <tr>
                        <td>Average</td>
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

            {/* ── F. Insurance Claim Summary ── */}
            <div className="gen-section">
              <h3 className="gen-section-title">F. Insurance Claim Summary</h3>
              <div className="gen-summary-box">
                {claim.summary.split("\n\n").map((para, i) => (
                  <p key={i}>{para}</p>
                ))}
              </div>
            </div>

            {/* ── Submit error ── */}
            {submitError && (
              <p className="error-message">{submitError}</p>
            )}

            {/* ── Download error ── */}
            {downloadError && (
              <p className="error-message">{downloadError}</p>
            )}

            {/* ── Confirmation dialog ── */}
            {showConfirm && (
              <div className="review-confirm-overlay">
                <div className="review-confirm-box">
                  <h3>Confirm Submission</h3>
                  <p>
                    Are you sure you want to submit this insurance claim?
                    This action cannot be undone.
                  </p>
                  <div className="review-confirm-buttons">
                    <button
                      className="cost-back-button"
                      onClick={() => setShowConfirm(false)}
                    >
                      Cancel
                    </button>
                    <button
                      className="review-submit-button"
                      onClick={handleSubmit}
                    >
                      Yes, Submit Claim
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* ── Bottom navigation ── */}
            <div className="cost-nav-buttons" style={{ marginTop: "20px" }}>

              <button
                className="cost-back-button"
                onClick={() => navigate(`/claim/generate/${claimId}`)}
                disabled={submitting}
              >
                ← Back to Claim Generation
              </button>

              <button
                className="cost-back-button"
                onClick={handleDownload}
                disabled={downloading}
              >
                {downloading ? "Generating PDF…" : "⬇ Download Report"}
              </button>

              {!submitted ? (
                <button
                  className="review-submit-button"
                  onClick={() => setShowConfirm(true)}
                  disabled={submitting}
                >
                  {submitting ? "Submitting..." : "Submit Claim"}
                </button>
              ) : (
                <button
                  className="login-button"
                  onClick={() => navigate("/dashboard")}
                >
                  Back to Dashboard
                </button>
              )}

            </div>

          </>
        )}

      </main>

    </div>
  );
}

export default ClaimReview;
