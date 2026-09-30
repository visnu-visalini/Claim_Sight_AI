import { useNavigate } from "react-router-dom";

function Dashboard() {
  const navigate = useNavigate();

  const user = JSON.parse(
    localStorage.getItem("user")
  );

  const handleLogout = () => {
    localStorage.removeItem("user");
    localStorage.removeItem("isAuthenticated");

    navigate("/login");
  };

  const handleCreateClaim = async () => {
    try {
      if (!user?.id) {
        alert("User information not found. Please login again.");
        navigate("/login");
        return;
      }

      const response = await fetch(
        "http://127.0.0.1:5000/api/claims/",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            user_id: user.id,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        alert(data.message || "Failed to create claim");
        return;
      }

      // Store the newly created claim
      localStorage.setItem(
        "currentClaim",
        JSON.stringify(data.claim)
      );

      // Go to the new claim page
      navigate("/claim/new");

    } catch (error) {
      console.error("Create claim error:", error);

      alert(
        "Unable to connect to the backend. Make sure Flask is running."
      );
    }
  };

  return (
    <div className="dashboard-page">

      <header className="dashboard-header">

        <div>
          <h1>ClaimSightAI</h1>
          <p>AI-Powered Insurance Claims</p>
        </div>

        <button
          className="logout-button"
          onClick={handleLogout}
        >
          Logout
        </button>

      </header>

      <main className="dashboard-content">

        <div className="welcome-section">

          <h2>
            Welcome, {user?.name || "User"}!
          </h2>

          <p>
            Manage your vehicle insurance claims
            from one place.
          </p>

        </div>

        <div className="dashboard-cards">

          <div className="dashboard-card">

            <h3>New Claim</h3>

            <p>
              Start a new vehicle insurance claim
              with AI-powered damage assessment.
            </p>

            <button onClick={handleCreateClaim}>
              Create Claim
            </button>

          </div>

          <div className="dashboard-card">

            <h3>My Claims</h3>

            <p>
              View your existing claims and
              track their current status.
            </p>

            <button
              onClick={() => navigate("/claims")}
            >
              View Claims
            </button>

          </div>

          <div className="dashboard-card">

            <h3>Profile</h3>

            <p>
              View and manage your account
              information.
            </p>

            <button
              onClick={() => navigate("/profile")}
            >
              View Profile
            </button>

          </div>

        </div>

      </main>

    </div>
  );
}

export default Dashboard;