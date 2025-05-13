import React, { useEffect, useState } from 'react';
import axios from 'axios';

const MyProducts = ({ onProductsSelect }) => {
  const [manufacturer, setManufacturer] = useState('');
  const [itemCode, setItemCode] = useState('');
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

      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          justifyContent: 'center', // centro orizzontale
          alignItems: 'flex-start',     // centro verticale
          width: '100%',       // altezza minima per centrare verticalmente
          gap: '20px',
          padding: '20px'
        }}
      >
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
              margin: '0 auto'
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
      </div>


      {message && <p className="mt-3 text-danger">{message}</p>}
    </div>
  );
};

export default MyProducts;
