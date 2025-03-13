import React, { useState } from "react";
import { Button, Form } from "react-bootstrap";
import { useNavigate } from "react-router-dom";

const ForgotPassword = () => {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      const response = await fetch("http://localhost:5000/forgot-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      const data = await response.json();
      if (data.message === "Password reset email sent") {
        setMessage("Check your email for the reset link!");
        setTimeout(() => {
          navigate("/login");  // Reindirizza dopo qualche secondo
        }, 3000);
      } else {
        setMessage(data.message);
      }
    } catch (err) {
      setMessage("Error: " + err.message);
    }
  };

  return (
    <div className="container mt-5">
      <h3>Forgot Password</h3>
      <Form onSubmit={handleSubmit}>
        <Form.Group>
          <Form.Label>Email</Form.Label>
          <Form.Control
            type="email"
            placeholder="Enter your email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </Form.Group>
        <Button type="submit" className="mt-3">Send Reset Link</Button>
      </Form>
      {message && <div className="mt-3">{message}</div>}
    </div>
  );
};

export default ForgotPassword;
