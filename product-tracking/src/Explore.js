import React, { useState } from 'react';
import axios from 'axios';
import { Card } from 'react-bootstrap';
import QrScanner from 'react-qr-scanner';
import jsQR from 'jsqr';
import { QRCodeCanvas } from 'qrcode.react';

const Explore = ({ onProductsSelect }) => {
  const [manufacturer, setManufacturer] = useState('');
  const [itemCode, setItemCode] = useState('');
  const [products, setProducts] = useState([]);
  const [message, setMessage] = useState('');

const handleSearchProducts = async () => {
    try {
      const response = await axios.get(`/api/ExploreProducts?manufacturer=${manufacturer}`);

      if (response.status === 200) {
        const data = response.data;
        setProducts(data);
        setMessage('');
        onProductsSelect(manufacturer);
      } else {
        setProducts([]);
        setMessage('No products found for this manufacturer');
      }
    } catch (error) {
      console.error('Errore durante la ricerca:', error);
      setMessage('Error fetching products. Please try again later.');
    }
  };

  return (
    <div className="search-product-container">
      <div className="input-group">
        <input
          type="text"
          className="form-control"
          placeholder="Enter Manufacturer name"
          value={manufacturer}
          onChange={(e) => setManufacturer(e.target.value)}
        />
      </div>

      <button
        className="btn btn-primary w-100 mt-3"
        onClick={handleSearchProducts}
      >
        Search Products
      </button>

      {(products.length > 0 || message) && (
        <div style={{ marginTop: '20px' }}>
          {products.map((product, index) => (
            <div
              key={index}
              style={{
                border: '1px solid #ccc',
                padding: '10px',
                width: '280px',
                borderRadius: '8px',
                boxShadow: '0 2px 6px rgba(0,0,0,0.1)',
                backgroundColor: '#fff',
                margin: '0 auto',
                marginBottom: '20px'
              }}
            >
              <h3>{product.Name}</h3>
              <p><strong>Id:</strong> {product.ID}</p>
              <p><strong>Expiry Date:</strong> {product.ExpiryDate}</p>
              <p><strong>Ingredients:</strong> {product.Ingredients}</p>

              <button
                className="btn btn-sm btn-outline-primary"
                onClick={() => {
                  setItemCode(product.ID);
                  try {
                    document.getElementById("itemCode").value = product.ID;
                  } catch { }
                  window.scrollTo({ top: 0, behavior: 'smooth' });
                }}
              >
                View Details
              </button>
            </div>
          ))}

          {message && products.length === 0 && (
            <p className="text-danger text-center mt-4">{message}</p>
          )}
        </div>
      )}
    </div>
  );
};

export default Explore;