import { useState } from "react";
import { useNavigate } from "react-router-dom";

function Signup() {

  const navigate = useNavigate();

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleSignup = async (e) => {

    e.preventDefault();

    try {

      const response = await fetch(
        "http://127.0.0.1:5000/api/auth/signup",
        {
          method: "POST",

          headers: {
            "Content-Type": "application/json",
          },

          body: JSON.stringify({
            name,
            email,
            password,
          }),
        }
      );

      const data = await response.json();

      if (data.success) {

        alert("Account created successfully!");

        navigate("/login");

      } else {

        alert(data.message);

      }

    } catch (error) {

      console.error("Signup error:", error);

      alert("Unable to connect to server");

    }
  };

  return (
    <div className="login-page">

      <div className="login-card">

        <h2>Create Account</h2>

        <p className="login-subtitle">
          Create your ClaimSightAI account
        </p>

        <form onSubmit={handleSignup}>

          <div className="form-group">

            <label>Full Name</label>

            <input
              type="text"
              placeholder="Enter your name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />

          </div>

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
              placeholder="Create a password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />

          </div>

          <button
            type="submit"
            className="login-button"
          >
            Create Account
          </button>

        </form>

        <div className="login-footer">

          <p>
            Already have an account?

            <span
              className="signup-link"
              onClick={() => navigate("/login")}
            >
              {" "}Login
            </span>

          </p>

        </div>

      </div>

    </div>
  );
}

export default Signup;