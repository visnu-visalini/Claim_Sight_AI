import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";

function DamageResults() {
  const { claimId } = useParams();
  const navigate = useNavigate();

  const user = JSON.parse(localStorage.getItem("user"));

  const [images, setImages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchResults = async () => {
      try {
        const response = await fetch(
          `http://127.0.0.1:5000/api/claims/${claimId}/images?user_id=${user.id}`
        );

        const data = await response.json();

        if (!response.ok || !data.success) {
          setError(data.message || "Failed to load results.");
          return;
        }

        setImages(data.images);

      } catch (err) {
        setError("Unable to connect to server. Make sure Flask is running.");
      } finally {
        setLoading(false);
      }
    };

    fetchResults();
  }, [claimId, user.id]);

  const formatConfidence = (value) => {
    if (value === null || value === undefined) return "—";
    return `${(value * 100).toFixed(1)}%`;
  };

  const formatBoundingBox = (raw) => {
    if (!raw) return "—";
    try {
      // Stored as string like "[x1, y1, x2, y2]"
      const coords = JSON.parse(raw.replace(/'/g, '"'));
      return coords.map((v) => Math.round(v)).join(", ");
    } catch {
      return raw;
    }
  };

  return (
    <div className="page-container">

      <header className="dashboard-header">
        <div>
          <h1>ClaimSightAI</h1>
          <p>Claim #{claimId} — AI Damage Results</p>
        </div>
        <button
          className="logout-button"
          onClick={() => navigate("/dashboard")}
        >
          Back to Dashboard
        </button>
      </header>

      <main className="form-main results-main">

        <h2>AI Damage Detection Results</h2>
        <p>Results from YOLO-based vehicle damage analysis.</p>

        {loading && (
          <p className="loading-message">Loading results...</p>
        )}

        {error && (
          <p className="error-message">{error}</p>
        )}

        {!loading && !error && images.length === 0 && (
          <div className="error-box">
            <p>No images found for this claim.</p>
            <button onClick={() => navigate(`/claim/images/${claimId}`)}>
              Upload Images
            </button>
          </div>
        )}

        {!loading && !error && images.length > 0 && (
          <div className="results-grid">
            {images.map((img) => (
              <div key={img.id} className="result-card">

                <div className="result-image-wrapper">
                  <img
                    src={img.image_url}
                    alt={img.filename}
                  />
                </div>

                <div className="result-details">

                  <p className="result-filename">{img.filename}</p>

                  <div className={`damage-badge ${img.damage_detected ? "badge-damage" : "badge-no-damage"}`}>
                    {img.damage_detected ? "Damage Detected" : "No Damage Detected"}
                  </div>

                  {img.damage_detected && (
                    <table className="result-table">
                      <tbody>
                        <tr>
                          <td>Damage Type</td>
                          <td>{img.damage_type || "—"}</td>
                        </tr>
                        <tr>
                          <td>Confidence</td>
                          <td>{formatConfidence(img.confidence)}</td>
                        </tr>
                        <tr>
                          <td>Bounding Box</td>
                          <td>{formatBoundingBox(img.bounding_box)}</td>
                        </tr>
                        <tr>
                          <td>Uploaded</td>
                          <td>
                            {img.uploaded_at
                              ? new Date(img.uploaded_at).toLocaleString()
                              : "—"}
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  )}

                  {!img.damage_detected && (
                    <p className="no-damage-note">
                      The AI model did not detect any damage in this image.
                    </p>
                  )}

                </div>

              </div>
            ))}
          </div>
        )}

        {!loading && !error && images.length > 0 && (
          <div className="results-action-buttons">
            <button
              className="cost-back-button"
              onClick={() => navigate("/dashboard")}
            >
              Back to Dashboard
            </button>
            <button
              className="login-button"
              onClick={() => navigate(`/claim/cost/${claimId}`)}
            >
              Estimate Repair Cost →
            </button>
          </div>
        )}

      </main>

    </div>
  );
}

export default DamageResults;
