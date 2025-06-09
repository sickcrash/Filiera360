import React, { useEffect, useState } from "react";
import {
  BrowserRouter as Router,
  Route,
  Routes,
  Navigate,
} from "react-router-dom";
import Login from "./components/Login";
import SignUp from "./components/SignUp";
import Account from "./Account";
import AddProduct from "./AddProduct";
import ScanProduct from "./ScanProduct";
import Navbar from "./components/Navbar";
import ForgotPassword from "./components/ForgotPassword";
import About from "./components/About";
import ResetPassword from "./components/ResetPassword";
import AccessDenied from "./components/AccessDenied";
import ProtectedRoute from "./components/ProtectedRoute";
import ChangePassword from "./components/ChangePassword";

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token) {
      setIsLoggedIn(true);
    }
  }, []);

  return (
    <Router>
      <Navbar />

      <Routes>
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/about" element={<About />} />
        <Route path="/reset-password/:token" element={<ResetPassword />} />
        <Route
          path="/login"
          element={
            isLoggedIn ? (
              <Navigate to="/add-product" />
            ) : (
              <Login setIsLoggedIn={setIsLoggedIn} />
            )
          }
        />
        <Route
          path="/signup"
          element={isLoggedIn ? <Navigate to="/add-product" /> : <SignUp />}
        />
        <Route
          path="/add-product"
          element={
            isLoggedIn ? (
              <ProtectedRoute allowedRoles={["producer", "operator"]}>
                <AddProduct />
              </ProtectedRoute>
            ) : (
              <Navigate to="/login" />
            )
          }
        />
        <Route path="/scan-product" element={<ScanProduct />} />
        <Route path="/scan-product/:id" element={<ScanProduct />} />
        <Route
          path="/account"
          element={
            isLoggedIn ? (
              <Account setIsLoggedIn={setIsLoggedIn} />
            ) : (
              <Navigate to="/login" />
            )
          }
        />
        <Route
          path="/"
          element={<Navigate to={isLoggedIn ? "/add-product" : "/login"} />}
        />
        <Route path="/access-denied" element={<AccessDenied />} />
        <Route path="/change-password" element={<ChangePassword />} />
      </Routes>
    </Router>
  );
}

export default App;
