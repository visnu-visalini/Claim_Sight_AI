import { useState } from "react";
import { useNavigate } from "react-router-dom";

function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

   const handleLogin = async (e) => {
  e.preventDefault();

  try {
    const response = await fetch(
      "http://127.0.0.1:5000/api/auth/login",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email: email,
          password: password,
        }),
      }
    );

    const data = await response.json();

    console.log(data);

    if (data.success) {

  localStorage.setItem(
    "user",
    JSON.stringify(data.user)
  );

  localStorage.setItem(
    "isAuthenticated",
    "true"
  );

  navigate(data.user.role === "admin" ? "/admin/dashboard" : "/dashboard");

} else {

  alert(data.message);

}

  } catch (error) {
    console.error("Login error:", error);
    alert("Unable to connect to server");
  }
};

  return (
    <div className="login-page">
      <div className="login-container">

        <div className="login-left">
          <h1>ClaimSightAI</h1>

          <p className="tagline">
            AI-Powered Vehicle Damage Assessment
            & Insurance Claim Automation
          </p>

          <p className="description">
            Assess vehicle damage, simplify insurance claims,
            and accelerate the claim process using AI.
          </p>
        </div>

        <div className="login-card">

          <h2>Welcome Back</h2>

          <p className="login-subtitle">
            Login to your ClaimSightAI account
          </p>

          <form onSubmit={handleLogin}>

            <div className="form-group">
              <label>Email</label>

              <input
                type="email"
                placeholder="Enter your email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label>Password</label>

              <input
                type="password"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>

            <button type="submit" className="login-button">
              Login
            </button>

          </form>

          <div className="login-footer">
            <p>
              Don't have an account?
              <span className="signup-link" onClick={() => navigate("/signup")}> Create Account</span>
            </p>
          </div>

        </div>

      </div>
    </div>
  );
}

export default Login;