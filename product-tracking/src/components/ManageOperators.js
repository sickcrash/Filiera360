import React, { useEffect, useState } from "react";
import axios from "axios";
import { Card, Button } from "react-bootstrap";

export const ManageOperators = () => {
  const [operators, setOperators] = useState([]);
    const [newOperator, setNewOperator] = useState("");
    const [errorMessage, setErrorMessage] = useState("");

  const handleDeleteOperator = async (operator) => {
    try {
<<<<<<< HEAD
      const response = await axios.post(`/api/operators/delete`, {
=======
      const response = await axios.post(`http://127.0.0.1:5000/operators/delete`, {
>>>>>>> ded673831a52c69239e34cebddc68e8c3e8417c7
        email: operator
      },{
          headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`,
              'Content-Type': 'application/json'
          }}
      );
      console.log(response);
      setOperators(operators.filter((o) => o !== operator));
    } catch (error) {
    setErrorMessage("Error deleting operator: " + error.toString());
      console.error(error);
    }
  };

  const handleCreateOperator = async () => {
    console.log(newOperator);

    if (!newOperator || newOperator.trim() === "") {
      setErrorMessage("Operator name cannot be empty");
      return;
    }

    try {
<<<<<<< HEAD
        const response = await axios.post(`/api/operators/add`, {
=======
        const response = await axios.post(`http://127.0.0.1:5000/operators/add`, {
>>>>>>> ded673831a52c69239e34cebddc68e8c3e8417c7
            email: newOperator
        }, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`,
                'Content-Type': 'application/json'
            }}
        );
        if (response.status !== 201) {
            setErrorMessage("Error creating operator");
            return;
        }

        setOperators([...operators, newOperator]);
        setNewOperator("");
    } catch (error) {
        setErrorMessage("Error creating operator: "+ error.toString());
      console.error(error);
    }
  };

  useEffect(() => {
    const fetchOperators = async () => {
      try {
<<<<<<< HEAD
        const response = await axios.get(`/api/operators`, {
=======
        const response = await axios.get(`http://127.0.0.1:5000/operators`, {
>>>>>>> ded673831a52c69239e34cebddc68e8c3e8417c7
          headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`,
            "Content-Type": "application/json",
          },
        });
        setOperators(response.data.operators);
      } catch (error) {
        console.error(error);
      }
    };
    fetchOperators();
  }, []);

  return (
    <div className="row justify-content-center my-4">
      <div className="col">
        <div className="card shadow">
          <div className="card-body">
            <Card.Header style={{ textAlign: "center" }}>
              <h4>Operators 👷</h4>
            </Card.Header>
            <br />
            <div
                className="card shadow flex flex-row justify-content-between align-items-center p-3 bg-white rounded"
              >
                <div className="input-group mr-2">
                    <input
                        type="text"
                        className="form-control"
                        placeholder="Add new operator"
                        value={newOperator}
                        onChange={(e) => setNewOperator(e.target.value)}
                    />
                </div>
                <Button
                  variant="success"
                  onClick={() => handleCreateOperator()}
                >
                +
                </Button>
              </div>
              {errorMessage && (
                <div className="text text-danger" style={{ textAlign: "center" }}>
                  {errorMessage}
                </div>
              )}
              <hr />
            {operators?.map((operator, index) => (
              <div
                key={index}
                className="card shadow flex flex-row justify-content-between align-items-center p-3 mb-2 bg-white rounded"
              >
                <div>{operator}</div>
                <Button
                  variant="danger"
                  onClick={() => handleDeleteOperator(operator)}
                >
                  🗑️
                </Button>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
