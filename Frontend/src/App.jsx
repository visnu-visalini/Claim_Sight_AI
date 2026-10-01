import { BrowserRouter, Routes, Route } from "react-router-dom";

import Login from "./Pages/Login";
import Signup from "./Pages/signup";
import Dashboard from "./Pages/Dashboard";
import NewClaim from "./Pages/NewClaim";
import ImageUpload from "./Pages/ImageUpload";
import DamageResults from "./Pages/DamageResults";
import CostEstimation from "./Pages/CostEstimation";
import ClaimGeneration from "./Pages/ClaimGeneration";
import ClaimReview from "./Pages/ClaimReview";
import MyClaims from "./Pages/MyClaims";
import Profile from "./Pages/Profile";
import AdminDashboard from "./Pages/AdminDashboard";
import ProtectedRoute from "./Components/ProtectedRoute";
import AdminRoute from "./Components/AdminRoute";


function App() {

  return (
    <BrowserRouter>

      <Routes>

        {/* Login */}
        <Route
          path="/"
          element={<Login />}
        />

        <Route
          path="/login"
          element={<Login />}
        />

        {/* Signup */}
        <Route
          path="/signup"
          element={<Signup />}
        />

        {/* Dashboard */}
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />

        {/* New Claim — Vehicle Details */}
        <Route
          path="/claim/new"
          element={
            <ProtectedRoute>
              <NewClaim />
            </ProtectedRoute>
          }
        />

        {/* Image Upload */}
        <Route
          path="/claim/images/:claimId"
          element={
            <ProtectedRoute>
              <ImageUpload />
            </ProtectedRoute>
          }
        />

        {/* Damage Results */}
        <Route
          path="/claim/results/:claimId"
          element={
            <ProtectedRoute>
              <DamageResults />
            </ProtectedRoute>
          }
        />

        {/* Cost Estimation */}
        <Route
          path="/claim/cost/:claimId"
          element={
            <ProtectedRoute>
              <CostEstimation />
            </ProtectedRoute>
          }
        />

        {/* Claim Generation */}
        <Route
          path="/claim/generate/:claimId"
          element={
            <ProtectedRoute>
              <ClaimGeneration />
            </ProtectedRoute>
          }
        />

        {/* Claim Review */}
        <Route
          path="/claim/review/:claimId"
          element={
            <ProtectedRoute>
              <ClaimReview />
            </ProtectedRoute>
          }
        />

        {/* My Claims */}
        <Route
          path="/claims"
          element={
            <ProtectedRoute>
              <MyClaims />
            </ProtectedRoute>
          }
        />

        {/* Profile */}
        <Route
          path="/profile"
          element={
            <ProtectedRoute>
              <Profile />
            </ProtectedRoute>
          }
        />

        {/* Admin Dashboard */}
        <Route
          path="/admin/dashboard"
          element={
            <AdminRoute>
              <AdminDashboard />
            </AdminRoute>
          }
        />

      </Routes>

    </BrowserRouter>
  );
}

export default App;