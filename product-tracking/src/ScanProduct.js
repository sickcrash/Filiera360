// ScanProduct.js
import React, { useEffect, useState } from 'react';
import ProductList from './components/ProductList';
import DataSensors from './components/DataSensors';
import Certifications from './components/Certifications';
import ProductMovements from './components/ProductMovements';
import { useNavigate } from "react-router-dom";

function ScanProduct() {
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [selectedBatch, setSelectedBatch] = useState(null);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token) {
      setIsLoggedIn(true);
    }
  }, []);

  return (
    <div className="container mt-4">
      <ProductList
        onProductSelect={setSelectedProduct}
        onBatchSelect={setSelectedBatch} />
      {/* {selectedProduct && (
        <div className="mt-4" id="customForm">
          <DataSensors productId={selectedProduct} />
          <ProductMovements productId={selectedProduct} />
          <Certifications productId={selectedProduct} />
        </div>
      )} */}
      {!isLoggedIn &&
        <p className="mt-3" style={{ marginBottom: "-2vw", color: "grey" }}>
          👤 Already have an account? {" "}
          <span onClick={() => navigate("/login")} style={{ color: "blue", cursor: "pointer" }}>Login</span>
        </p>
      }
      <br />
      <br />
      {selectedProduct ?
        <p
          onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
          style={{ fontSize: "1vw", textDecoration: "underline", cursor: "pointer" }}
        >
          ☝️ back to top
        </p>
        :
        null
      }
      <br />
      <br />
    </div>
  );
}

export default ScanProduct;
