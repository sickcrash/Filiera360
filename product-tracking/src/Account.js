import React, { useEffect, useState } from "react";
import { Card, Button , Alert} from "react-bootstrap";
import { Navigate, useNavigate } from "react-router-dom";
import {ManageOperators} from "./components/ManageOperators";
import axios from "axios";

const Account = ({ setIsLoggedIn }) => {
  const navigate = useNavigate();
  const [manufacturer, setManufacturer] = useState('');
  const [email, setEmail] = useState('');
  const [role, setRole] = useState('');
  const [showInput , setShowInput] = useState(false);
  const [name , setName] = useState('');
  const [message , setMessage] = useState(null);

  useEffect(() => {
    setManufacturer(localStorage.getItem("manufacturer"));
    setEmail(localStorage.getItem("email"));
    setRole(localStorage.getItem("role"));
  }, [manufacturer]);

  const toggleInput = () => {
    setShowInput(prev => !showInput);
  }

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
  const changeManufacturer = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem("token");
      const res = await axios.post(
          'api/updateManufacturer',
          name,
          {
            headers: {
              Authorization: `Bearer ${token}`,
              "Content-Type": "application/json",
            }
          }
      )
      if (res.status === 200) {
        setMessage(res.data.message)
        setShowInput(false);
        localStorage.setItem('manufacturer', name)
        setManufacturer(name)

        setName("")
      }
    }catch (error) {

    }
  }
  const handleForgotPassword = () => {
    navigate("/forgot-password");
  };

  return (
    <div className="container mt-5">
      <div className="row justify-content-center">
        <div className="col-md-6">
          {message && <Alert key="success" variant="success">{message}</Alert>}
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
                {role === 'producer' &&
                    <Button onClick={toggleInput} className="btn btn-secondary w-100" >
                      Change Manufacturer Name
                    </Button>
                }
                {
                  showInput &&
                    <form  onSubmit={changeManufacturer} className="card p-3">
                      <div className="mb-3">
                        <label htmlFor="nameInput" className="form-label">New Name</label>
                        <input
                            id="nameInput"
                            type="text"
                            className="form-control"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            placeholder="Insert New Name"
                            required
                        />
                      </div>
                      <button type="submit" className="btn btn-success">Save</button>
                    </form>
                }
                <Button onClick={handleForgotPassword} className="btn btn-secondary my-3 w-100" >
                  Reset password
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
