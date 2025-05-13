import React, { useEffect, useState } from 'react';
import axios from 'axios';

const MyProducts = ({ onProductsSelect }) => {
  const [manufacturer, setManufacturer] = useState('');
  const [products, setProducts] = useState([]);
  const [message, setMessage] = useState('');

  // ✅ Recupera manufacturer da localStorage o altro metodo
  useEffect(() => {
    const storedManufacturer = localStorage.getItem('manufacturer'); // o sessionStorage, o dal JWT decodificato, ecc.
    if (storedManufacturer) {
      setManufacturer(storedManufacturer);
    } else {
      setMessage('Manufacturer not found');
    }
  }, []);

  // ✅ Chiama l’API quando manufacturer è disponibile
  useEffect(() => {
    if (manufacturer) {
      handleSearchProduct();
    }
  }, [manufacturer]);

  const handleSearchProduct = async () => {
    try {
      const response = await axios.get(`/api/getProductsByManufacturer?manufacturer=${manufacturer}`);
      if (response.status === 200) {
        setProducts(response.data);
        setMessage('');
        if (onProductsSelect) onProductsSelect(manufacturer);
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
          {product.CustomObject && Object.entries(product.CustomObject).map(([key, value]) => (
            <div key={key} style={{ textAlign: "center" }}>
              <p><strong>{key}</strong>: {value}</p>
            </div>
          ))}
        </div>
      ))}

      {message && <p className="mt-3 text-danger">{message}</p>}
    </div>
  );
};

export default MyProducts;
