// ScanProduct.js
import React, { useEffect, useState } from 'react';
import ProductList from '../src/components/ProductList';
import Explore from '../src/Explore';
import DataSensors from '../src/components/DataSensors';
import Certifications from '../src/components/Certifications';
import ProductMovements from '../src/components/ProductMovements';
import { useNavigate } from "react-router-dom";


function ScanProduct() {
  const [selectedManufacturer, setSelectedManufacturer] = useState(null);
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
      {!isLoggedIn &&
        <>
          {/* Logo a sinistra */}
          <div
            style={{
              position: "relative",
            }}
          >
            <img
              src={require("./logo_filiera360.png")}
              style={{
                width: "8vw",
              }}
            />
          </div>
          <p className="mt-3" style={{ marginBottom: "-2vw", color: "grey" }}>
            👤 Already have an account? {" "}
            <span onClick={() => navigate("/login")} style={{ color: "blue", cursor: "pointer" }}>Login</span>
          </p>
        </>
      }

      <div className="col-md-11 mx-auto">


        {/* Scan Batch */}
        <ProductList
          onProductSelect={setSelectedProduct}
          onBatchSelect={setSelectedBatch}
          onProductsSelect={setSelectedManufacturer}
        />







        {selectedProduct ? (
          <p
            onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
            style={{ fontSize: "1vw", textDecoration: "underline", cursor: "pointer" }}
          >
            ☝️ back to top
          </p>
        ) : null}

        <br />
        <br />
      </div>
    </div>
  );
}

export default ScanProduct;
