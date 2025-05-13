import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Card, Table, Row, Col } from 'react-bootstrap';
import { QRCodeCanvas } from 'qrcode.react';
import QrScanner from 'react-qr-scanner';
import jsQR from 'jsqr';


const Explore = ({ onProductsSelect }) => {
  const [manufacturer, setManufacturer] = useState('');
  const [itemCode, setItemCode] = useState('');
  const [products, setProducts] = useState([]);
  const [message, setMessage] = useState('');
  const [product, setProduct] = useState([]);

  const handleSearchProduct = async () => {


    try {
      // Esegui la richiesta alla tua API
      const response = await axios.get(`/api/getProductsByManufacturer?manufacturer=${manufacturer}`);

      // Verifica la risposta
      if (response.status === 200) {
        setMessage('ciaooooo');
        const data = response.data;

        // Controlla se la risposta è un array, se no la trasforma in un array
        setProducts(data);
        setMessage('');
        onProductsSelect(manufacturer); // Cancella eventuali messaggi di errore
      } else {
        setMessage('No products found for this manufacturer');
        setProducts([]); // Resetta la lista dei prodotti
      }
    } catch (error) {
      console.error('Errore durante la ricerca:', error);
      setMessage('Error fetching products. Please try again later.');
    }
  };

  return (
    <div className="search-product-container">
      <h3>Search Product</h3>
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
        onClick={handleSearchProduct}
      >
        Search Products
      </button>


      {products.map((product, index) => (
        <div key={index} style={{ border: '1px solid #ccc', marginBottom: '10px', padding: '10px' }}>
          <h3>{product.Name}</h3>
          <p><strong>Id:</strong> {product.ID}</p>
          <p><strong>Expiry Date:</strong> {product.ExpiryDate}</p>
          <p><strong>Ingredients:</strong> {product.Ingredients}</p>
          <p><strong>Allergens:</strong> {product.Allergens}</p>
          <p><strong>Nutritional Information:</strong> {product.Nutritional_information}</p>
          <p><strong>Harvest Date:</strong> {product.HarvestDate}</p>
          <p><strong>Pesticide Use:</strong> {product.PesticideUse}</p>
          <p><strong>Fertilizer Use:</strong> {product.FertilizerUse}</p>
          <p><strong>Country of Origin:</strong> {product.CountryOfOrigin}</p>

          {/* Custom fields rendering */}
          {product.CustomObject && product.CustomObject && Object.entries(product.CustomObject).map(([key, value]) => (
          <div style={{ textAlign: "center" }}>
          <p> <strong>{key}</strong>: {value}</p> 
          </div>
          ))}

        </div>
      ))}



      {/* Messaggio di errore o successo */}
      {message && <p className="mt-3 text-danger">{message}</p>}

      
    </div>
  );
}

export default Explore;
