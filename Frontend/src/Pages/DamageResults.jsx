import { useState, useEffect, useRef } from "react";
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
                  <DamageImageWithBox
                    imageUrl={img.image_url}
                    filename={img.filename}
                    boundingBox={img.bounding_box}
                    damageType={img.damage_type}
                    confidence={img.confidence}
                    damageDetected={img.damage_detected}
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
                          <td>Location</td>
                          <td>{img.bounding_box ? "See image overlay" : "—"}</td>
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

                  <OpenAIPanel img={img} />

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

// ── OpenAI Second Opinion panel ─────────────────────────────────────────

function OpenAIPanel({ img }) {
  if (!img.openai_available) {
    return (
      <div className="openai-panel openai-unavailable">
        <span className="openai-label">GPT-4o Vision</span>
        <span className="openai-na">Unavailable</span>
      </div>
    );
  }

  const agreesBadge = img.openai_agrees_with_yolo === true
    ? <span className="openai-agree">✓ Agrees with YOLO</span>
    : img.openai_agrees_with_yolo === false
    ? <span className="openai-disagree">✗ Disagrees with YOLO</span>
    : null;

  return (
    <div className="openai-panel">
      <div className="openai-panel-header">
        <span className="openai-label">GPT-4o Vision — Second Opinion</span>
        {agreesBadge}
      </div>
      <table className="result-table" style={{ marginTop: "8px" }}>
        <tbody>
          <tr>
            <td>Damage Present</td>
            <td>{img.openai_damage_present ? "Yes" : "No"}</td>
          </tr>
          {img.openai_damage_present && (
            <>
              <tr>
                <td>Damage Type</td>
                <td>{img.openai_damage_type || "—"}</td>
              </tr>
              <tr>
                <td>Affected Part</td>
                <td>{img.openai_affected_part || "—"}</td>
              </tr>
              <tr>
                <td>Severity</td>
                <td>
                  <span className={`openai-severity openai-severity-${(img.openai_severity || "").toLowerCase()}`}>
                    {img.openai_severity || "—"}
                  </span>
                </td>
              </tr>
              <tr>
                <td>Confidence</td>
                <td>
                  {img.openai_confidence != null
                    ? `${(img.openai_confidence * 100).toFixed(1)}%`
                    : "—"}
                </td>
              </tr>
            </>
          )}
          {img.openai_assessment && (
            <tr>
              <td>Assessment</td>
              <td style={{ fontStyle: "italic", color: "#475569" }}>
                {img.openai_assessment}
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

// ── Bounding-box overlay component ──────────────────────────────────────

function parseBoundingBox(raw) {
  if (!raw) return null;
  try {
    const coords = JSON.parse(raw);
    if (
      !Array.isArray(coords) ||
      coords.length !== 4 ||
      coords.some((v) => typeof v !== "number" || isNaN(v))
    ) return null;
    return coords; // [x1, y1, x2, y2]
  } catch {
    return null;
  }
}

function DamageImageWithBox({
  imageUrl,
  filename,
  boundingBox,
  damageType,
  confidence,
  damageDetected,
}) {
  const imgRef = useRef(null);
  const [naturalSize, setNaturalSize] = useState(null);

  const coords = damageDetected ? parseBoundingBox(boundingBox) : null;

  const handleLoad = (e) => {
    setNaturalSize({
      w: e.target.naturalWidth,
      h: e.target.naturalHeight,
    });
  };

  const label =
    damageType && confidence != null
      ? `${damageType} ${(confidence * 100).toFixed(1)}%`
      : damageType || null;

  return (
    <div style={{ position: "relative", width: "100%", lineHeight: 0 }}>
      <img
        ref={imgRef}
        src={imageUrl}
        alt={filename}
        onLoad={handleLoad}
        style={{ width: "100%", height: "100%", display: "block", objectFit: "cover" }}
      />

      {/* SVG overlay — only rendered once natural dimensions are known and
          we have a valid 4-coordinate bounding box */}
      {coords && naturalSize && (
        <svg
          viewBox={`0 0 ${naturalSize.w} ${naturalSize.h}`}
          preserveAspectRatio="xMidYMid meet"
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            width: "100%",
            height: "100%",
            pointerEvents: "none",
          }}
        >
          {/* Box */}
          <rect
            x={coords[0]}
            y={coords[1]}
            width={coords[2] - coords[0]}
            height={coords[3] - coords[1]}
            fill="none"
            stroke="#ef4444"
            strokeWidth={Math.max(2, naturalSize.w * 0.003)}
            strokeLinejoin="round"
          />

          {/* Label background */}
          {label && (
            <>
              <rect
                x={coords[0]}
                y={Math.max(0, coords[1] - naturalSize.h * 0.045)}
                width={label.length * naturalSize.w * 0.013}
                height={naturalSize.h * 0.042}
                fill="#ef4444"
                rx={naturalSize.w * 0.004}
              />
              <text
                x={coords[0] + naturalSize.w * 0.006}
                y={Math.max(naturalSize.h * 0.035, coords[1] - naturalSize.h * 0.01)}
                fill="white"
                fontSize={naturalSize.h * 0.035}
                fontFamily="Arial, sans-serif"
                fontWeight="bold"
              >
                {label}
              </text>
            </>
          )}
        </svg>
      )}
    </div>
  );
}

export default DamageResults;
