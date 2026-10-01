import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

function ImageUpload() {
  const { claimId } = useParams();
  const navigate = useNavigate();

  const user = JSON.parse(localStorage.getItem("user"));

  const [selectedFiles, setSelectedFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const handleFileChange = (e) => {
    const newFiles = Array.from(e.target.files);

    const withPreviews = newFiles.map((file) => ({
      file,
      preview: URL.createObjectURL(file),
      id: `${file.name}-${Date.now()}-${Math.random()}`,
    }));

    setSelectedFiles((prev) => [...prev, ...withPreviews]);
    // Reset input so same file can be re-added if removed
    e.target.value = "";
  };

  const handleRemove = (id) => {
    setSelectedFiles((prev) => {
      const removed = prev.find((f) => f.id === id);
      if (removed) URL.revokeObjectURL(removed.preview);
      return prev.filter((f) => f.id !== id);
    });
  };

  const handleUpload = async () => {
    if (selectedFiles.length === 0) {
      setError("Please select at least one image.");
      return;
    }

    setError("");
    setSuccess("");
    setLoading(true);

    try {
      const formData = new FormData();
      formData.append("user_id", user.id);
      selectedFiles.forEach((item) => formData.append("images", item.file));

      const response = await fetch(
        `http://127.0.0.1:5000/api/claims/${claimId}/images`,
        {
          method: "POST",
          body: formData,
        }
      );

      const data = await response.json();

      if (!response.ok || !data.success) {
        setError(data.message || "Upload failed.");
        return;
      }

      setSuccess(`${data.images.length} image(s) uploaded and analyzed successfully!`);
      setSelectedFiles([]);

      // Navigate to damage results after a short delay so user sees the message
      setTimeout(() => {
        navigate(`/claim/results/${claimId}`);
      }, 1500);

    } catch (err) {
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
          <p>Claim #{claimId} — Upload Accident Images</p>
        </div>
        <button
          className="logout-button"
          onClick={() => navigate("/dashboard")}
        >
          Back to Dashboard
        </button>
      </header>

      <main className="form-main">

        <h2>Upload Vehicle Accident Images</h2>
        <p>Select clear photos of the vehicle damage. Accepted: JPG, JPEG, PNG.</p>

        {error && <p className="error-message">{error}</p>}
        {success && <p className="success-message">{success}</p>}

        <div className="form-group">
          <label>Select Images</label>
          <input
            type="file"
            accept=".jpg,.jpeg,.png"
            multiple
            onChange={handleFileChange}
          />
        </div>

        {selectedFiles.length > 0 && (
          <div className="image-preview-section">
            <p>{selectedFiles.length} image(s) selected</p>

            <div className="image-preview-grid">
              {selectedFiles.map((item) => (
                <div key={item.id} className="image-preview-card">
                  <img
                    src={item.preview}
                    alt={item.file.name}
                  />
                  <p>{item.file.name}</p>
                  <button
                    type="button"
                    onClick={() => handleRemove(item.id)}
                  >
                    Remove
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        <button
          className="login-button"
          onClick={handleUpload}
          disabled={loading || selectedFiles.length === 0}
        >
          {loading ? "Uploading..." : "Upload Images"}
        </button>

      </main>

    </div>
  );
}

export default ImageUpload;
