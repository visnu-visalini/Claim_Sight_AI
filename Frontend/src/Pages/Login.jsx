import { useState } from "react";

function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleLogin = (e) => {
    e.preventDefault();

    console.log("Email:", email);
    console.log("Password:", password);
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
              <span className="signup-link"> Create Account</span>
            </p>
          </div>

        </div>

      </div>
    </div>
  );
}

export default Login;