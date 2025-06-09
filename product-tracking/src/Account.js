import React, { useEffect, useState } from "react";
import { Card, Button } from "react-bootstrap";
import { Navigate, useNavigate } from "react-router-dom";
import {ManageOperators} from "./components/ManageOperators";

const Account = ({ setIsLoggedIn }) => {
  const navigate = useNavigate();
  const [manufacturer, setManufacturer] = useState('');
  const [email, setEmail] = useState('');
  const [role, setRole] = useState('');

  useEffect(() => {
    setManufacturer(localStorage.getItem("manufacturer"));
    setEmail(localStorage.getItem("email"));
    setRole(localStorage.getItem("role"));
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("token");
      localStorage.removeItem("manufacturer");
      localStorage.removeItem("email");
      // Store user ID for liked products
      localStorage.removeItem("userId");
      localStorage.removeItem("role");

    setIsLoggedIn(false);
    navigate("/login");
  };

  const handleChangePassword = () => {
  navigate("/change-password");
};

  return (
    <div className="container mt-5">
      <div className="row justify-content-center">
        <div className="col-md-6">
          <div className="card shadow">
            <div className="card-body">
              <Card.Header style={{ textAlign: "center" }}>
                <h4>Account 👤</h4>
              </Card.Header>
              <br />
              <div className="form-group">
                <h4 style={{ textAlign: "center", fontWeight: "lighter" }}>
                  Manufacturer: <b>{manufacturer}</b>
                </h4>
                <h4 style={{ textAlign: "center", fontWeight: "lighter" }}>
                  email: <b>{email}</b>
                </h4>
                <h4 style={{ textAlign: "center", fontWeight: "lighter" }}>
                  role: <b>{role}</b>
                </h4>
                <hr/>
                <Button onClick={handleChangePassword} className="btn btn-secondary w-100" >
                  Change password
                </Button>
                <Button onClick={handleLogout} className="btn btn-primary my-3 w-100">
                  Logout
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>


      {role === 'producer'&& <div className="row justify-content-center">
        <div className="col-md-6">
          <ManageOperators />
        </div>
      </div>}

    </div>
  );
};

export default Account;
