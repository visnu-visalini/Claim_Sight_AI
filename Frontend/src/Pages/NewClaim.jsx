import { useState } from "react";
import { useNavigate } from "react-router-dom";

function NewClaim() {
  const navigate = useNavigate();

  const user = JSON.parse(localStorage.getItem("user"));
  const currentClaim = JSON.parse(localStorage.getItem("currentClaim"));

  const [vehicleNumber, setVehicleNumber] = useState("");
  const [vehicleMake, setVehicleMake] = useState("");
  const [vehicleModel, setVehicleModel] = useState("");
  const [vehicleYear, setVehicleYear] = useState("");
  const [accidentDate, setAccidentDate] = useState("");
  const [accidentLocation, setAccidentLocation] = useState("");
  const [accidentDescription, setAccidentDescription] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  if (!currentClaim) {
    return (
      <div className="page-container">
        <div className="error-box">
          <p>No active claim found. Please start a new claim from the dashboard.</p>
          <button onClick={() => navigate("/dashboard")}>
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const response = await fetch(
        `http://127.0.0.1:5000/api/claims/${currentClaim.id}`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            user_id: user.id,
            vehicle_number: vehicleNumber,
            vehicle_make: vehicleMake,
            vehicle_model: vehicleModel,
            vehicle_year: parseInt(vehicleYear),
            accident_date: accidentDate,
            accident_location: accidentLocation,
            accident_description: accidentDescription,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok || !data.success) {
        setError(data.message || "Failed to save claim details.");
        return;
      }

      navigate(`/claim/images/${currentClaim.id}`);

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
          <p>New Claim — Vehicle &amp; Accident Details</p>
        </div>
        <button className="logout-button" onClick={() => navigate("/dashboard")}>
          Back to Dashboard
        </button>
      </header>

      <main className="form-main">

        <h2>Claim #{currentClaim.id} — Enter Details</h2>

        {error && <p className="error-message">{error}</p>}

        <form onSubmit={handleSubmit} className="claim-form">

          <section className="form-section">
            <h3>Vehicle Information</h3>

            <div className="form-group">
              <label>Vehicle Number</label>
              <input
                type="text"
                placeholder="e.g. ABC-1234"
                value={vehicleNumber}
                onChange={(e) => setVehicleNumber(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label>Vehicle Make</label>
              <input
                type="text"
                placeholder="e.g. Toyota"
                value={vehicleMake}
                onChange={(e) => setVehicleMake(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label>Vehicle Model</label>
              <input
                type="text"
                placeholder="e.g. Corolla"
                value={vehicleModel}
                onChange={(e) => setVehicleModel(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label>Vehicle Year</label>
              <input
                type="number"
                placeholder="e.g. 2022"
                value={vehicleYear}
                onChange={(e) => setVehicleYear(e.target.value)}
                min="1900"
                max="2100"
                required
              />
            </div>
          </section>

          <section className="form-section">
            <h3>Accident Information</h3>

            <div className="form-group">
              <label>Accident Date</label>
              <input
                type="date"
                value={accidentDate}
                onChange={(e) => setAccidentDate(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label>Accident Location</label>
              <input
                type="text"
                placeholder="e.g. Main Street, Colombo"
                value={accidentLocation}
                onChange={(e) => setAccidentLocation(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label>Accident Description</label>
              <textarea
                placeholder="Describe what happened..."
                value={accidentDescription}
                onChange={(e) => setAccidentDescription(e.target.value)}
                rows={4}
                required
              />
            </div>
          </section>

          <button
            type="submit"
            className="login-button"
            disabled={loading}
          >
            {loading ? "Saving..." : "Save & Continue"}
          </button>

        </form>

      </main>

    </div>
  );
}

export default NewClaim;
