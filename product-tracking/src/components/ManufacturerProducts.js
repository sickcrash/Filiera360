import React, { useEffect, useState } from 'react';
import axios from 'axios';

function ManufacturerProducts() {
  const [products, setProducts] = useState([]);
  const [manufacturer, setManufacturer] = useState(''); // da aggiornare con il produttore attuale
  const [error, setError] = useState('');

  useEffect(() => {
    // Esempio: recupera il nome del produttore dall'utente loggato (da localStorage, token, ecc.)
    const userManufacturer = localStorage.getItem('manufacturer') || 'Company A';
    setManufacturer(userManufacturer);

    axios
      .get(`http://localhost:5000/getProductsByManufacturer?manufacturer=${userManufacturer}`)
      .then((response) => {
        setProducts(response.data);
      })
      .catch((err) => {
        console.error('Errore nel recupero dei prodotti:', err);
        setError('Errore durante il recupero dei prodotti.');
      });
  }, []);

  return (
    <div className="p-6">
      <h2 className="text-xl font-bold mb-4">Prodotti del produttore: {manufacturer}</h2>
      {error && <p className="text-red-500">{error}</p>}
      {products.length === 0 ? (
        <p>Nessun prodotto trovato.</p>
      ) : (
        <ul className="space-y-4">
          {products.map((product, index) => (
            <li key={index} className="border rounded-xl p-4 shadow">
              <p><strong>ID:</strong> {product.ID}</p>
              <p><strong>Nome:</strong> {product.Name}</p>
              <p><strong>Data Produzione:</strong> {product.ProductionDate}</p>
              <p><strong>Data Scadenza:</strong> {product.ExpirationDate}</p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default ManufacturerProducts;
