import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";

function Profile() {
  const navigate = useNavigate();
  const user = JSON.parse(localStorage.getItem("user"));

  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!user?.id) {
      setError("User not found. Please log in again.");
      setLoading(false);
      return;
    }

    const fetchProfile = async () => {
      try {
        const response = await fetch(
          `http://127.0.0.1:5000/api/profile/?user_id=${user.id}`
        );
        const data = await response.json();

        if (!response.ok || !data.success) {
          setError(data.message || "Failed to load profile.");
          return;
        }

        setProfile(data.user);
      } catch {
        setError("Unable to connect to server. Make sure Flask is running.");
      } finally {
        setLoading(false);
      }
    };

    fetchProfile();
  }, [user?.id]);

  return (
    <div className="page-container">

      <header className="dashboard-header">
        <div>
          <h1>ClaimSightAI</h1>
          <p>My Profile</p>
        </div>
        <button className="logout-button" onClick={() => navigate("/dashboard")}>
          Back to Dashboard
        </button>
      </header>

      <main className="myclaims-main">

        <div className="myclaims-header">
          <div>
            <h2>Profile</h2>
            <p>Your account information.</p>
          </div>
        </div>

        {loading && <p className="loading-message">Loading profile...</p>}

        {error && <p className="error-message">{error}</p>}

        {!loading && !error && profile && (
          <div className="form-section" style={{ maxWidth: "500px" }}>
            <h3>Account Details</h3>

            <table className="gen-table">
              <tbody>
                <tr>
                  <td>User ID</td>
                  <td>{profile.id}</td>
                </tr>
                <tr>
                  <td>Name</td>
                  <td>{profile.name}</td>
                </tr>
                <tr>
                  <td>Email</td>
                  <td>{profile.email}</td>
                </tr>
              </tbody>
            </table>
          </div>
        )}

      </main>

    </div>
  );
}

export default Profile;
