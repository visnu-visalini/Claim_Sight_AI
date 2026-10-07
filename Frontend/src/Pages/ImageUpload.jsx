import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

// View definitions — order controls display order
const VIEWS = [
  { key: "front", label: "Front View",  required: true  },
  { key: "back",  label: "Back View",   required: true  },
  { key: "left",  label: "Left View",   required: true  },
  { key: "right", label: "Right View",  required: true  },
  { key: "top",   label: "Top View",    required: false },
];

const EMPTY_SLOTS = Object.fromEntries(VIEWS.map((v) => [v.key, null]));

function ImageUpload() {
  const { claimId } = useParams();
  const navigate    = useNavigate();

  const user = JSON.parse(localStorage.getItem("user"));

  // Each slot: null | { file: File, preview: string }
  const [slots, setSlots]     = useState(EMPTY_SLOTS);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState("");
  const [success, setSuccess] = useState("");

  const handleFileChange = (viewKey, e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Revoke previous preview URL if one exists
    setSlots((prev) => {
      if (prev[viewKey]) URL.revokeObjectURL(prev[viewKey].preview);
      return {
        ...prev,
        [viewKey]: { file, preview: URL.createObjectURL(file) },
      };
    });

    // Reset input so the same file can be re-selected after removal
    e.target.value = "";
  };

  const handleRemove = (viewKey) => {
    setSlots((prev) => {
      if (prev[viewKey]) URL.revokeObjectURL(prev[viewKey].preview);
      return { ...prev, [viewKey]: null };
    });
  };

  const requiredFilled = VIEWS
    .filter((v) => v.required)
    .every((v) => slots[v.key] !== null);

  const handleUpload = async () => {
    if (!requiredFilled) {
      setError("Please provide images for all required views: Front, Back, Left, Right.");
      return;
    }

    setError("");
    setSuccess("");
    setLoading(true);

    try {
      const formData = new FormData();
      formData.append("user_id", user.id);

      VIEWS.forEach(({ key }) => {
        if (slots[key]) formData.append(key, slots[key].file);
      });

      const response = await fetch(
        `http://127.0.0.1:5000/api/claims/${claimId}/images`,
        { method: "POST", body: formData }
      );

      const data = await response.json();

      if (!response.ok || !data.success) {
        setError(data.message || "Upload failed.");
        return;
      }

      setSuccess(`${data.images.length} vehicle view image(s) uploaded and analyzed successfully!`);
      setSlots(EMPTY_SLOTS);

      setTimeout(() => navigate(`/claim/results/${claimId}`), 1500);

    } catch {
      setError("Unable to connect to server. Make sure Flask is running.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-container">

      <header className="dashboard-header">
        <div>
          <h1>ClaimSightAI</h1>
          <p>Claim #{claimId} — Upload Vehicle Images</p>
        </div>
        <button className="logout-button" onClick={() => navigate("/dashboard")}>
          Back to Dashboard
        </button>
      </header>

      <main className="form-main">

        <h2>Upload Vehicle Images by View</h2>
        <p>
          Provide a clear photo for each vehicle view.
          Front, Back, Left, and Right are required. Top is optional.
          Accepted formats: JPG, JPEG, PNG (max 10 MB each).
        </p>

        {error   && <p className="error-message">{error}</p>}
        {success && <p className="success-message">{success}</p>}

        <div className="view-upload-grid">
          {VIEWS.map(({ key, label, required }) => (
            <div key={key} className="view-upload-slot">

              <div className="view-upload-slot-header">
                <span className="view-upload-label">{label}</span>
                {required
                  ? <span className="view-required-badge">Required</span>
                  : <span className="view-optional-badge">Optional</span>
                }
              </div>

              {slots[key] ? (
                <div className="view-preview-card">
                  <img src={slots[key].preview} alt={label} />
                  <p className="view-preview-filename">{slots[key].file.name}</p>
                  <button
                    type="button"
                    className="view-remove-button"
                    onClick={() => handleRemove(key)}
                  >
                    Remove
                  </button>
                </div>
              ) : (
                <label className="view-upload-area">
                  <span className="view-upload-icon">+</span>
                  <span>Click to select image</span>
                  <input
                    type="file"
                    accept=".jpg,.jpeg,.png"
                    style={{ display: "none" }}
                    onChange={(e) => handleFileChange(key, e)}
                  />
                </label>
              )}

            </div>
          ))}
        </div>

        <button
          className="login-button"
          style={{ marginTop: "24px" }}
          onClick={handleUpload}
          disabled={loading || !requiredFilled}
        >
          {loading ? "Uploading & Analyzing..." : "Upload & Analyze"}
        </button>

      </main>

    </div>
  );
}

export default ImageUpload;
