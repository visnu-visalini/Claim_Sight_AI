import { Navigate } from "react-router-dom";

function AdminRoute({ children }) {
  const isAuthenticated = localStorage.getItem("isAuthenticated");

  if (isAuthenticated !== "true") {
    return <Navigate to="/login" replace />;
  }

  const user = JSON.parse(localStorage.getItem("user"));

  if (user?.role !== "admin") {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
}

export default AdminRoute;
