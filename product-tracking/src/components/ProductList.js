import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Card, Table, Row, Col } from 'react-bootstrap';
import UpdateProduct from './update_prod/UpdateProduct';
import UpdateBatch from './update_prod/UpdateBatch';
import { QRCodeCanvas } from 'qrcode.react';
import QrScanner from 'react-qr-scanner';
import jsQR from 'jsqr';
import Viewer3D from './Viewer3D';
import DataSensors from './DataSensors';

const ProductList = ({ onProductSelect, onBatchSelect }) => {
  const isProducer = localStorage.getItem("role") === "producer";
  const isOperator = localStorage.getItem("role") === "operator";
  const isUser = localStorage.getItem("role") === "user";

  const [itemCode, setItemCode] = useState('');
  const [message, setMessage] = useState('');
  const [product, setProduct] = useState(null);
  const [batchProduct, setbatchProduct] = useState(null);
  const [productHistory, setProductHistory] = useState([]);
  const [status, setStatus] = useState('');
  const [showCamera, setShowCamera] = useState('false');
  const [scan, setScan] = useState(0);
  const [glbFile, setGlbFile] = useState(null);
  const [batch, setBatch] = useState(null);
  const [batchHistory, setBatchHistory] = useState([]);
  const [itemCodeBatch, setItemCodeBatch] = useState('');
  const [messageBatch, setMessageBatch] = useState('');
  const [scanBatch, setScanBatch] = useState(0);



  // variabili useState per la gestione dei prodotti preferiti
  const [liked, setLiked] = useState(false); // controllo se il prodotto é stato preferito o meno 
  const [likedProducts, setLikedProducts] = useState(() => {
    // Load liked products from localStorage when component mounts
    const savedProducts = localStorage.getItem('likedProducts');
    return savedProducts ? JSON.parse(savedProducts) : [];
  });

  // Nuovo stato per la cronologia dei prodotti scansionati
  const [recentlyScanned, setRecentlyScanned] = useState(() => {
    // Load recently scanned products from localStorage
    const savedScanned = localStorage.getItem('recentlyScannedProducts');
    return savedScanned ? JSON.parse(savedScanned) : [];
  });

  // Handle scanning the product and fetching its details
  const handleScan = async (e) => {
    e?.preventDefault();
    setScanBatch(0) // evita conflitti

    // controllo il prodotto scannerizzato è gia stato preferito
    setLiked(likedProducts.some(p => p.ID === itemCode)); // Check if product is already liked

    try {
      console.log("Scanning for Item Code: " + itemCode);

      // Fetch product details from the server
      const token = localStorage.getItem('token');
      const response = await axios.get(`/api/getProduct?productId=${itemCode}`);
      const historyResponse = await axios.get(`/api/getProductHistory?productId=${itemCode}`);

      if (response.status === 200) {
        const productData = response.data;
        setProduct(productData); // Set product details in state
        setbatchProduct(); // EVITA DI AVERE DUE PRODOTTI DIVERSI IN CONTEMPORANEA
        setBatch(); // EVITA DI AVERE PRODOTTO E BATCH INCOERENTI
        setMessage(`Product ${itemCode} found!`);
        console.log(`Product ${itemCode} found!`);
        onProductSelect(itemCode);
        setProductHistory(historyResponse.data || "");

        // Aggiungi il prodotto alla cronologia dei prodotti scansionati
        addToRecentlyScanned(productData);
        window.scrollTo({ top: 0, behavior: 'smooth' })
      } else {
        setMessage('Product not found.');
        setProduct(null);
        onProductSelect(null);
      }
    } catch (error) {
      setMessage('Failed to fetch product details.');
      setProduct(null);
      onProductSelect(null);
    }

    // Fetch the GLB model using the itemCode from the product
    try {
      const modelResponse = await axios.get(`/api/getModel?productId=${itemCode}`);

      if (modelResponse.status === 200) {
        const base64Model = modelResponse.data.ModelBase64;

        const byteCharacters = atob(base64Model.split(',')[1]);
        const byteArray = new Uint8Array(byteCharacters.length);

        for (let i = 0; i < byteCharacters.length; i++) {
          byteArray[i] = byteCharacters.charCodeAt(i);
        }

        const glbBlob = new Blob([byteArray], { type: 'application/octet-stream' });
        setGlbFile(glbBlob);

        console.log('GLB model loaded successfully!');
      } else {
        console.log('Failed to fetch GLB model.');
        setGlbFile(null);
      }
    } catch (error) {
      console.error("Error fetching model: ", error);
      setGlbFile(null);
    }

    // Retrieve product movements
    // try {
    //   const movementsResponse = await axios.get(`/api/getAllMovements?productId=${itemCode}`);
    //   if (movementsResponse.status === 200) {
    //     const movementsFound = movementsResponse.data;
    //     setStatus(movementsFound[movementsFound.length - 1]?.Status || "");
    //   } else {
    //     setStatus("");
    //   }
    // } catch (error) {
    //   setStatus("");
    // }
  };

  const handleScanBatch = async (e) => {
    e?.preventDefault();
    setScan(0) // evita conflitti

    try {
      console.log("Scanning for Item Code: " + itemCodeBatch);

      // Fetch batch details from the server
      const responseBatch = await axios.get(`/api/getBatch?batchId=${itemCodeBatch}`);
      console.log("responseBatch", responseBatch);
      const historyResponseBatch = await axios.get(`/api/getBatchHistory?batchId=${itemCodeBatch}`);
      console.log(historyResponseBatch);

      //Se la chiamata alla getBatch mi ritorna 200 stato OK
      if (responseBatch.status === 200) {
        console.log(responseBatch.data);
        //Salvo l'id del prodotto nella variabile idproduct
        const idproduct = responseBatch.data.ProductId;

        setBatch(responseBatch.data); // Set batch details in state
        addToRecentlyScanned(responseBatch.data);
        window.scrollTo({ top: 0, behavior: 'smooth' })
        //Chiamo il backend per ottenere i dettagli del prodotto
        const responseProduct = await axios.get(`/api/getProduct?productId=${idproduct}`);
        //Se la chiamata alla getProduct mi ritorna 200 stato OK
        if (responseProduct.status === 200) {
          //Salvo i dettagli del prodotto nella variabile BatchProduct
          setbatchProduct(responseProduct.data);
          setProduct() // EVITA DI AVERE DUE PRODOTTI DIVERSI IN CONTEMPORANEA
          // Fetch the GLB model using the itemCode from the product
          try {
            const modelResponse = await axios.get(`/api/getModel?productId=${idproduct}`);

            if (modelResponse.status === 200) {
              const base64Model = modelResponse.data.ModelBase64;

              const byteCharacters = atob(base64Model.split(',')[1]);
              const byteArray = new Uint8Array(byteCharacters.length);

              for (let i = 0; i < byteCharacters.length; i++) {
                byteArray[i] = byteCharacters.charCodeAt(i);
              }

              const glbBlob = new Blob([byteArray], { type: 'application/octet-stream' });
              setGlbFile(glbBlob);

              console.log('GLB model loaded successfully!');
            } else {
              console.log('Failed to fetch GLB model.');
              setGlbFile(null);
            }
          } catch (error) {
            console.error("Error fetching model: ", error);
            setGlbFile(null);
          }
        }
        else {
          alert('Product not found');
          setbatchProduct(null);
          onProductSelect(null);
        }
        setMessageBatch(`Batch ${itemCodeBatch} found!`);
        console.log(`Batch ${itemCodeBatch} found!`);
        onBatchSelect(itemCodeBatch);
        setBatchHistory(historyResponseBatch.data || "");
      } else {
        setMessageBatch('Batch not found.');
        setBatch(null);
        onBatchSelect(null);
      }
    } catch (error) {
      setMessageBatch('Failed to fetch batch details.');
      setBatch(null);
      onBatchSelect(null);
    }
  };

  const getLastUpdate = () => {
    if (productHistory.length > 0) {
      const lastUpdate = productHistory[productHistory.length - 1].Timestamp;
      const date = new Date(lastUpdate.seconds * 1000 + lastUpdate.nanos / 1000000);
      return date.toLocaleString();
    }
    return null;
  };

  const getLastUpdateBatch = () => {
    if (batchHistory.length > 0) {
      const lastUpdateBatch = batchHistory[batchHistory.length - 1].Timestamp;
      const date = new Date(lastUpdateBatch.seconds * 1000 + lastUpdateBatch.nanos / 1000000);
      return date.toLocaleString();
    }
    return null;
  };

  const getFirstUpdate = () => {
    if (productHistory.length > 0) {
      const firstUpdate = productHistory[0].Timestamp;
      const date = new Date(firstUpdate.seconds * 1000 + firstUpdate.nanos / 1000000);
      return date.toLocaleString();
    }
    return null;
  };

  const getFirstUpdateBatch = () => {
    if (batchHistory.length > 0) {
      const firstUpdateBatch = batchHistory[0].Timestamp;
      const date = new Date(firstUpdateBatch.seconds * 1000 + firstUpdateBatch.nanos / 1000000);
      return date.toLocaleString();
    }
    return null;
  };

  // Scarica un file di testo contenente la cronologia del prodotto
  const handleDownloadHistoryLog = () => {
    const history = productHistory;
    let logContent = `Product History for ID: ${itemCode}\n\n`;

    history.forEach((item, index) => {
      const date = new Date(item.Timestamp.seconds * 1000).toLocaleString();
      const valueData = JSON.parse(item.Value);

      logContent += `Transaction ${index + 1}\n`;
      logContent += `Date and Time: ${date}\n`;
      logContent += `ID: ${valueData.ID}\n`;
      logContent += `Name: ${valueData.Name}\n`;
      logContent += `Manufacturer: ${valueData.Manufacturer}\n`;
      logContent += `Expiry Date: ${valueData.ExpiryDate}\n`;
      logContent += `Ingredients: ${valueData.Ingredients}\n`;
      logContent += `Nutritional Information: ${valueData.Nutritional_information || 'N/A'}\n`;
      logContent += `Allergens: ${valueData.Allergens || 'N/A'}\n`;
      logContent += `Harvest Date: ${valueData.HarvestDate}\n`;
      logContent += `Pesticide Use: ${valueData.PesticideUse || 'N/A'}\n`;
      logContent += `Fertilizer Use: ${valueData.FertilizerUse || 'N/A'}\n`;
      logContent += `Country Of Origin: ${valueData.CountryOfOrigin || 'N/A'}\n`;

      if (valueData.SensorData && Object.keys(valueData.SensorData).length > 0) {
        logContent += `Sensor Data:\n`;
        Object.entries(valueData.SensorData).forEach(([key, value]) => {
          logContent += `${key}: ${value}\n`;
        });
      } else {
        logContent += `Sensor Data: N/A\n`; // Se non ci sono sensor data, mostriamo N/A
      }

      if (valueData.Certifications && Object.keys(valueData.Certifications).length > 0) {
        logContent += `Certifications:\n`;
        Object.entries(valueData.Certifications).forEach(([key, value]) => {
          logContent += `${key}: ${value}\n`;
        });
      } else {
        logContent += `Custom Fields: N/A\n`; // Se non ci sono certifications, mostriamo N/A
      }

      if (valueData.CustomObject && Object.keys(valueData.CustomObject).length > 0) {
        logContent += `Custom Fields:\n`;
        Object.entries(valueData.CustomObject).forEach(([key, value]) => {
          logContent += `${key}: ${value}\n`;
        });
      } else {
        logContent += `Custom Fields: N/A\n`; // Se non ci sono custom fields, mostriamo N/A
      }
    });

    const blob = new Blob([logContent], { type: 'text/plain' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `${itemCode}_product_history.txt`;

    link.click();
  };

  const handleDownloadHistoryLogBatch = () => {
    const history = batchHistory;
    let logContent = `Batch History for ID: ${itemCode}\n\n`;

    history.forEach((item, index) => {
      const date = new Date(item.Timestamp.seconds * 1000).toLocaleString();
      const valueData = JSON.parse(item.Value);

      logContent += `Transaction ${index + 1}\n`;
      logContent += `Date and Time: ${date}\n`;
      logContent += `ID: ${valueData.ID}\n`;
      logContent += `Product ID: ${valueData.ProductId}\n`;
      logContent += `Operator: ${valueData.Operator}\n`;
      logContent += `Batch number: ${valueData.BatchNumber}\n`;
      logContent += `Quantity: ${valueData.Quantity}\n`;
      logContent += `Production date: ${valueData.Production_date || 'N/A'}\n`;
      logContent += `State: ${valueData.State || 'N/A'}\n`;

      if (valueData.CustomObject && Object.keys(valueData.CustomObject).length > 0) {
        logContent += `Custom Batch Fields:\n`;
        Object.entries(valueData.CustomObject).forEach(([key, value]) => {
          logContent += `${key}: ${value}\n`;
        });
      } else {
        logContent += `Custom Batch Fields: N/A\n`; // Se non ci sono custom fields, mostriamo N/A
      }
    });

    const blob = new Blob([logContent], { type: 'text/plain' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `${itemCodeBatch}_batch_history.txt`;

    link.click();
  };

  // Funzione per decodificare immagini caricate
  const handleImageUpload = (event) => {
    console.log("starting QR code processing...");
    const file = event.target.files[0];
    console.log(file);
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        const img = new Image();
        img.src = e.target.result;
        img.onload = () => {
          const canvas = document.createElement('canvas');
          canvas.width = img.width;
          canvas.height = img.height;
          const ctx = canvas.getContext('2d');
          ctx.drawImage(img, 0, 0, img.width, img.height);
          const imageData = ctx.getImageData(0, 0, img.width, img.height);
          const code = jsQR(imageData.data, img.width, img.height);
          if (code) {
            console.log(code.data);
            document.getElementById("itemCode").value = code.data;
            setItemCode(code.data);
            setScan(scan + 1); // trigger scan
          } else {
            console.log('No QR code found in uploaded image.');
            setMessageBatch('No QR code found in uploaded image.');
          }
        };
      };
      reader.readAsDataURL(file);
      setShowCamera(false);
      document.getElementById("uploader").value = "";
    }
  };

  // Funzione per decodificare immagini caricate
  const handleImageUploadBatch = (event) => {
    console.log("starting QR code processing...");
    const file = event.target.files[0];
    console.log(file);
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        const img = new Image();
        img.src = e.target.result;
        img.onload = () => {
          const canvas = document.createElement('canvas');
          canvas.width = img.width;
          canvas.height = img.height;
          const ctx = canvas.getContext('2d');
          ctx.drawImage(img, 0, 0, img.width, img.height);
          const imageData = ctx.getImageData(0, 0, img.width, img.height);
          const code = jsQR(imageData.data, img.width, img.height);
          if (code) {
            console.log(code.data);
            document.getElementById("itemCodeBatch").value = code.data;
            setItemCodeBatch(code.data);
            setScanBatch(scan + 1); // trigger scan
          } else {
            console.log('No QR code found in uploaded image.');
            setMessageBatch('No QR code found in uploaded image.');
          }
        };
      };
      reader.readAsDataURL(file);
      setShowCamera(false);
      document.getElementById("uploaderBatch").value = "";
    }
  };

  // Funzione per gestire la scansione dalla fotocamera
  const handleQrScan = (data) => {
    if (data) {
      console.log(data.text);
      document.getElementById("itemCode").value = data.text;
      setItemCode(data.text);
      setScan(scanBatch + 1); // trigger scan
      setShowCamera(false);
    }
  };
  // Funzione per gestire la scansione dalla fotocamera
  const handleQrScanBatch = (data) => {
    if (data) {
      console.log(data.text);
      document.getElementById("itemCodeBatch").value = data.text;
      setItemCodeBatch(data.text);
      setScanBatch(scanBatch + 1); // trigger scan
      setShowCamera(false);
    }
  };

  // Avvia scansione al trigger
  useEffect(() => {
    if (scan > 0) handleScan();
    if (scanBatch > 0) handleScanBatch();
  }, [scan, scanBatch]);

  const handleError = (err) => {
    console.error("QR code scan error:", err);
  };

  // Funzione per aggiungere un prodotto alla cronologia dei prodotti scansionati
  const addToRecentlyScanned = async (productData) => {
    try {
      // Get user ID from localStorage (set during login)
      const userId = localStorage.getItem('email') || 'default';

      // Crea un oggetto con solo le informazioni essenziali
      const scannedProduct = {
        ID: productData.ID,
        Name: productData.Name || "Batch",
        Manufacturer: productData.Manufacturer,
        CreationDate: productData.CreationDate,
        timestamp: new Date().toISOString() // Aggiungi timestamp per ordinare per data di scansione
      };

      // Send to backend
      await axios.post('/api/addRecentlySearched', {
        product: scannedProduct,
        userId: userId
      }, {
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${localStorage.getItem('token')}`
        }
      });

      // Update local state
      // Rimuovi il prodotto se già presente nella lista
      const filteredHistory = recentlyScanned.filter(p => p.ID !== scannedProduct.ID);
      // Aggiungi il prodotto all'inizio della lista
      const updatedHistory = [scannedProduct, ...filteredHistory].slice(0, 5); // Mantieni solo gli ultimi 5 prodotti
      setRecentlyScanned(updatedHistory);
    } catch (error) {
      console.error("Error updating recently searched products:", error);
    }
  };

  // Add useEffect to fetch recently searched products
  useEffect(() => {
    const fetchRecentlySearched = async () => {
      try {
        // Get user ID from localStorage (set during login)
        const userId = localStorage.getItem('email') || 'default';
        const response = await axios.get(`/api/getRecentlySearched?userId=${userId}`, {
          headers: {
            "Authorization": `Bearer ${localStorage.getItem('token')}`
          }
        }
        );
        setRecentlyScanned(response.data);
      } catch (error) {
        console.error("Error fetching recently searched products:", error);
      }
    };

    fetchRecentlySearched();

    // Also fetch liked products in the same useEffect
    const fetchLikedProducts = async () => {
      try {
        // Get user ID from localStorage (set during login)
        const userId = localStorage.getItem('email') || 'default';
        const response = await axios.get(`/api/getLikedProducts?userId=${userId}`, {
          headers: {
            "Authorization": `Bearer ${localStorage.getItem('token')}`
          }
        });
        setLikedProducts(response.data);
      } catch (error) {
        console.error("Error fetching liked products:", error);
      }
    };

    fetchLikedProducts();
  }, []);

  // Update the handleLikeToggle function to include user ID
  const handleLikeToggle = async () => {
    try {
      // Get user ID from localStorage (set during login)
      const userId = localStorage.getItem('email') || 'default';

      // In the handleLikeToggle function, modify the axios.delete call
      if (liked) {
        // If already liked, remove from favorites
        try {
          const response = await axios.delete(`/api/unlikeProduct?productId=${product.ID}&userId=${userId}`, {
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
          });

          console.log(`Product ${product.ID} removed from favorites`, response.data);

          // Update the list of liked products
          const updatedProducts = likedProducts.filter(p => p.ID !== product.ID);
          setLikedProducts(updatedProducts);
          setLiked(false);
        } catch (error) {
          console.error("Error removing product from favorites:", error);
        }
      }
      else {
        // If not liked, add to favorites
        const productToLike = {
          ID: product.ID,
          Name: product.Name,
          Manufacturer: product.Manufacturer,
          CreationDate: product.CreationDate,
          timestamp: new Date().toISOString()
        };

        await axios.post('/api/likeProduct', {
          product: productToLike,
          userId: userId,
        }, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json'
          }
        });

        console.log(`Product ${product.ID} added to favorites`);

        // Update the list of liked products
        setLikedProducts([...likedProducts, productToLike]);
        setLiked(true);
      }
    } catch (error) {
      console.error("Error updating liked products:", error);
      setMessage("Failed to update liked products");
    }
  };

  return (
    <div className="container mt-5">
      {/* Form di inserimento Item Code */}
      {(isProducer || isOperator) && (<form
        id="scanningForm"
        onSubmit={(e) => handleScan(e)}
        className="row justify-content-center"
      >
        <div className="col-md-6">
          <div className="card shadow">
            <div className="card-body">
              <Card.Header>
                <h4>Scan Product 🔎</h4>
                <p style={{ color: "grey" }}>
                  🔗 Insert the item code manually or either scan/upload a QR code
                </p>
              </Card.Header>
              <br />
              <div className="form-group d-flex align-items-center">
                <input
                  type="text"
                  onChange={(e) => setItemCode(e.target.value)}
                  className="form-control me-2"
                  id="itemCode"
                  placeholder="Enter product Item Code"
                />
                <input
                  type="file"
                  id="uploader"
                  onChange={handleImageUpload}
                  onError={handleError}
                  style={{ display: 'none' }}
                />
                <label
                  htmlFor="uploader"
                  className="btn btn-secondary me-1"
                  style={{ backgroundColor: "silver", border: 0 }}
                >
                  <ion-icon name="cloud-upload-outline"></ion-icon><i className="ion-ios-upload" />
                </label>
                <div
                  className="btn btn-secondary"
                  title="Scan QR Code"
                  style={{ backgroundColor: "silver", border: 0 }}
                  onClick={() => setShowCamera(!showCamera)}
                >
                  <ion-icon name="camera-outline"></ion-icon>
                </div>
              </div>
              {showCamera === true ? (
                <QrScanner
                  style={{ width: "100%", paddingTop: "2vw" }}
                  delay={300}
                  onError={handleError}
                  onScan={handleQrScan}
                />
              ) : null}
              <input
                style={{backgroundColor:"#1e90ff", border:"1px solid #1e90ff"}}
                type="submit"
                className="btn btn-primary mt-3 w-100"
                id="scanButton"
                value="Scan Product"
              />
              {message && <p className="mt-3 text-muted">{message}</p>}
            </div>
          </div>
        </div>
      </form>)}
      <br />
      {/* Form di inserimento Item Code */}
      <form
        id="scanningForm"
        onSubmit={(e) => handleScanBatch(e)}
        className="row justify-content-center"
      >
        <div className="col-md-6">
          <div className="card shadow">
            <div className="card-body">
              <Card.Header>
                <h4>Scan Batch 🔎</h4>
                <p style={{ color: "grey" }}>
                  🔗 Insert the item code manually or either scan/upload a QR code
                </p>
              </Card.Header>
              <br />
              <div className="form-group d-flex align-items-center">
                <input
                  type="text"
                  onChange={(e) => setItemCodeBatch(e.target.value)}
                  className="form-control me-2"
                  id="itemCodeBatch"
                  placeholder="Enter batch Item Code"
                />
                <input
                  type="file"
                  id="uploaderBatch"
                  onChange={handleImageUploadBatch}
                  onError={handleError}
                  onClick={() => setShowCamera(false)}
                  style={{ display: 'none' }}
                />
                <label
                  htmlFor="uploaderBatch"
                  className="btn btn-secondary me-1"
                  style={{ backgroundColor: "silver", border: 0 }}
                >
                  <ion-icon name="cloud-upload-outline"></ion-icon><i className="ion-ios-upload" />
                </label>
                <div
                  className="btn btn-secondary"
                  title="Scan QR Code"
                  style={{ backgroundColor: "silver", border: 0 }}
                  onClick={() => setShowCamera(!showCamera)}
                >
                  <ion-icon name="camera-outline"></ion-icon>
                </div>
              </div>
              {showCamera === true ? (
                <QrScanner
                  style={{ width: "100%", paddingTop: "2vw" }}
                  delay={300}
                  onError={handleError}
                  onScan={handleQrScanBatch}
                />
              ) : null}
              <input
                type="submit"
                className="btn btn-primary mt-3 w-100"
                id="scanButton"
                value="Scan Batch"
              />
              {messageBatch && <p className="mt-3 text-muted">{messageBatch}</p>}
            </div>
          </div>
        </div>
      </form>

      {/* Display product details if the product is found */}
      {product && (
        <div className="row justify-content-center mt-5">
          <div className="col-md-8">
            <div className="card shadow">
              <div className="card-body">
                <h4 className="card-title">General Information ℹ️</h4>
                <div className="d-flex justify-content-between align-items-center mb-3">
                  <div></div> {/* Empty div for flex spacing */}
                  <button
                    className={`btn ${liked ? 'btn-danger' : 'btn-outline-danger'}`}
                    onClick={handleLikeToggle}
                    title={liked ? "Unlike this product" : "Like this product"}
                  >
                    <ion-icon name={liked ? "heart" : "heart-outline"}></ion-icon>
                    {liked ? ' Liked' : ' Like'}
                  </button>
                </div>
                {glbFile ? (
                  <div style={{ marginBlock: "2vw" }}>
                    <Viewer3D externalGlbFile={glbFile} />
                  </div>
                ) : (
                  <p style={{ color: "grey" }}>no 3D preview available</p>
                )}
                <Table striped bordered hover>
                  <tbody>
                    {product.Name && (
                      <tr>
                        <th>Name</th>
                        <td>{product.Name}</td>
                      </tr>
                    )}
                    {product.ID && (
                      <tr>
                        <th>ID</th>
                        <td>{product.ID}</td>
                      </tr>
                    )}
                    {product.Manufacturer && (
                      <tr>
                        <th>Manufacturer</th>
                        <td>{product.Manufacturer}</td>
                      </tr>
                    )}
                    {product.SowingDate && (
                      <tr>
                        <th>Sowing Date</th>
                        <td>{product.SowingDate}</td>
                      </tr>
                    )}
                    {product.HarvestDate && (
                      <tr>
                        <th>Harvest Date</th>
                        <td>{product.HarvestDate}</td>
                      </tr>
                    )}
                    {product.Ingredients && (
                      <tr>
                        <th>Ingredients</th>
                        <td>{product.Ingredients}</td>
                      </tr>
                    )}
                    {product.Nutritional_information && (
                      <tr>
                        <th>Nutritional Information</th>
                        <td>{product.Nutritional_information}</td>
                      </tr>
                    )}
                    {product.Allergens && (
                      <tr>
                        <th>Allergens</th>
                        <td>{product.Allergens}</td>
                      </tr>
                    )}

                    {product.PesticideUse && (
                      <tr>
                        <th>Pesticide Use</th>
                        <td>{product.PesticideUse}</td>
                      </tr>
                    )}
                    {product.FertilizerUse && (
                      <tr>
                        <th>Fertilizer Use</th>
                        <td>{product.FertilizerUse}</td>
                      </tr>
                    )}
                    {product.CountryOfOrigin && (
                      <tr>
                        <th>Country Of Origin</th>
                        <td>{product.CountryOfOrigin}</td>
                      </tr>
                    )}
                    {product.CustomObject && product.CustomObject && Object.entries(product.CustomObject).map(([key, value]) => (
                      <tr key={key}>
                        <th>{key}</th>
                        <td>{value}</td>
                      </tr>
                    ))}


                    {/*
                    <tr>
                      <th>Status</th>
                      <td>{status || 'No status available'}</td>
                    </tr>
                    */}
                    <tr>
                      <th>N. Updates *</th>
                      <td>{productHistory.length}</td>
                    </tr>
                    <tr>
                      <th>Last Date *</th>
                      <td>{getLastUpdate() || 'No updates available'}</td>
                    </tr>
                    <tr>
                      <th>First Update *</th>
                      <td>{getFirstUpdate() || 'No updates available'}</td>
                    </tr>
                  </tbody>
                </Table>
                <br/>
                <DataSensors productId={product.ID} />
                <br/>
                <br/>
                <br/>
                <QRCodeCanvas value={product.ID} style={{ marginBottom: "2vw" }} />
                <p>
                  Note: The data marked with <b>(*)</b> is generated automatically by the server through the blockchain,
                  ensuring transparency and reliability.
                  These values are not provided by the manufacturer.
                </p>
                <button
                  className="btn btn-primary mt-3"
                  onClick={handleDownloadHistoryLog}
                >
                  Click here to see all the product updates
                </button>
              </div>
            </div>
          </div>
          {isProducer && product.Manufacturer == localStorage.getItem("manufacturer") &&
            <UpdateProduct
              productId={itemCode}
              productType={{ "Ingredients": product.Ingredients, "HarvestDate": product.HarvestDate }}
              onProductUpdate={handleScan}
            />}
        </div>
      )}

      {/* Display batch details if the batch is found */}
      {batch && (
        <div className="row justify-content-center mt-5">
          <div className="col-md-8">
            <div className="card shadow">
              <div className="card-body">
                <h4 className="card-title">General Information ℹ️</h4>
                <Table striped bordered hover>
                  <tbody>
                    {batch.ID && (
                      <tr>
                        <th>ID</th>
                        <td>{batch.ID}</td>
                      </tr>
                    )}
                    {batch.ProductId && (
                      <tr>
                        <th>Product Id</th>
                        <td>{batch.ProductId}</td>
                      </tr>
                    )}

                    {batch.Operator && (
                      <tr>
                        <th>Operator</th>
                        <td>{batch.Operator}</td>
                      </tr>
                    )}

                    {batch.BatchNumber && (
                      <tr>
                        <th>Batch Number</th>
                        <td>{batch.BatchNumber}</td>
                      </tr>
                    )}
                    {batch.Quantity && (
                      <tr>
                        <th>Quantity</th>
                        <td>{batch.Quantity}</td>
                      </tr>
                    )}
                    {batch.ProductionDate && (
                      <tr>
                        <th>Production Date</th>
                        <td>{batch.ProductionDate}</td>
                      </tr>
                    )}
                    {batch.State && (
                      <tr>
                        <th>Status</th>
                        <td>{batch.State}</td>
                      </tr>
                    )}
                    {batch.CustomObject && Object.entries(batch.CustomObject).map(([key, value]) => (
                      <tr key={key}>
                        <th>{key}</th>
                        <td>{value}</td>
                      </tr>
                    ))}
                    <tr>
                      <th>N. Updates *</th>
                      <td>{batchHistory.length}</td>
                    </tr>
                    <tr>
                      <th>Last Date *</th>
                      <td>{getLastUpdateBatch() || 'No updates available'}</td>
                    </tr>
                    <tr>
                      <th>First Update *</th>
                      <td>{getFirstUpdateBatch() || 'No updates available'}</td>
                    </tr>
                  </tbody>
                </Table>
                <br/>
                <QRCodeCanvas value={batch.ID} style={{ marginBottom: "2vw" }} />
                <p>
                  Note: The data marked with <b>(*)</b> is generated automatically by the server through the blockchain,
                  ensuring transparency and reliability.
                  These values are not provided by the operator.
                </p>
                <button
                  className="btn btn-primary mt-3"
                  onClick={handleDownloadHistoryLogBatch}
                >
                  Click here to see all the batch updates
                </button>
              </div>
            </div>
          </div>
          {batchProduct && (
            <div className="row justify-content-center mt-5">
              <div className="col-md-8">
                <div className="card shadow">
                  <div className="card-body">
                    <h4 className="card-title">Product Information ℹ️</h4>
                    {glbFile ? (
                      <div style={{ marginBlock: "2vw" }}>
                        <Viewer3D externalGlbFile={glbFile} />
                      </div>
                    ) : (
                      <p style={{ color: "grey" }}>no 3D preview available</p>
                    )}
                    <Table striped bordered hover>
                      <tbody>
                        {batchProduct.Name && (
                          <tr>
                            <th>Name</th>
                            <td>{batchProduct.Name}</td>
                          </tr>
                        )}
                        {true && (
                          <tr>
                            <th>ID</th>
                            <td>{batchProduct.ID}</td>
                          </tr>
                        )}
                        {batchProduct.Manufacturer && (
                          <tr>
                            <th>Manufacturer</th>
                            <td>{batchProduct.Manufacturer}</td>
                          </tr>
                        )}
                        {batchProduct.SowingDate && (
                          <tr>
                            <th>Sowing Date</th>
                            <td>{batchProduct.SowingDate}</td>
                          </tr>
                        )}
                        {batchProduct.HarvestDate && (
                          <tr>
                            <th>Harvest Date</th>
                            <td>{batchProduct.HarvestDate}</td>
                          </tr>
                        )}

                        {batchProduct.Ingredients && (
                          <tr>
                            <th>Ingredients</th>
                            <td>{batchProduct.Ingredients}</td>
                          </tr>
                        )}
                        {batchProduct.Nutritional_information && (
                          <tr>
                            <th>Nutritional Information</th>
                            <td>{batchProduct.Nutritional_information}</td>
                          </tr>
                        )}
                        {batchProduct.Allergens && (
                          <tr>
                            <th>Allergens</th>
                            <td>{batchProduct.Allergens}</td>
                          </tr>
                        )}

                        {batchProduct.PesticideUse && (
                          <tr>
                            <th>Pesticide Use</th>
                            <td>{batchProduct.PesticideUse}</td>
                          </tr>
                        )}
                        {batchProduct.FertilizerUse && (
                          <tr>
                            <th>Fertilizer Use</th>
                            <td>{batchProduct.FertilizerUse}</td>
                          </tr>
                        )}
                        {batchProduct.CountryOfOrigin && (
                          <tr>
                            <th>Country Of Origin</th>
                            <td>{batchProduct.CountryOfOrigin}</td>
                          </tr>
                        )}
                        {batchProduct.CustomObject && Object.entries(batchProduct.CustomObject).map(([key, value]) => (
                          <tr key={key}>
                            <th>{key}</th>
                            <td>{value}</td>
                          </tr>
                        ))}
                        {/* <tr>
                      <th>Status</th>
                      <td>{status || 'No status available'}</td>
                    </tr>
                    <tr>
                      <th>N. Updates *</th>
                      <td>{productHistory.length}</td>
                    </tr>
                    <tr>
                      <th>Last Date *</th>
                      <td>{getLastUpdate() || 'No updates available'}</td>
                    </tr>
                    <tr>
                      <th>First Update *</th>
                      <td>{getFirstUpdate() || 'No updates available'}</td>
                    </tr> */}
                      </tbody>
                    </Table>
                    <br/>
                    <DataSensors productId={batchProduct.ID} />
                    <br/>
                    <br/>
                    <br/>
                    <QRCodeCanvas value={batchProduct.ID} style={{ marginBottom: "2vw" }} />
                  </div>
                </div>
              </div>

            </div>
          )}
          {batch.Operator == localStorage.getItem("manufacturer") &&
            <UpdateBatch
              productId={batch.ProductId}
              batchId={batch.ID}
              // batchType={{"Ingredients": product.Ingredients, "HarvestDate": product.HarvestDate}}
              onBatchUpdate={handleScanBatch}
            />}
        </div>
      )}

      <br/>

      {/* Recently Scanned Products Section */}
      {recentlyScanned.length > 0 && (
        <div className="row mt-4 mb-4">
          <div className="col-12">
            <p style={{fontWeight:"bold"}}>Recent uploads/scans 🕒</p>
            <Row xs={1} md={2} lg={3} className="g-4">
              {recentlyScanned.map((scannedProduct) => (
                <Col key={scannedProduct.ID}>
                  <Card className="h-100 shadow-sm">
                    <Card.Body>
                      <Card.Title>{scannedProduct.Name}</Card.Title>
                      <Card.Text>
                        <small className="text-muted">ID: {scannedProduct.ID}</small><br />
                        <small className="text-muted">Manufacturer: {scannedProduct.Manufacturer}</small><br />
                        <small className="text-muted">Created: {scannedProduct.CreationDate}</small>
                      </Card.Text>
                      <div className="d-flex justify-content-between align-items-center">
                        <button
                          className="btn btn-sm btn-outline-primary"
                          onClick={() => {
                            setItemCode(scannedProduct.ID);
                            try{document.getElementById("itemCode").value = scannedProduct.ID;}
                            catch{}
                            window.scrollTo({ top: 0, behavior: 'smooth' })
                          }}
                        >
                          View Details
                        </button>
                        <small className="text-muted">
                          {new Date(scannedProduct.timestamp).toLocaleDateString()}
                        </small>
                      </div>
                    </Card.Body>
                  </Card>
                </Col>
              ))}
            </Row>
          </div>
        </div>
      )}

      {/* Liked Products Section */}
      {likedProducts.length > 0 && (
        <div className="row mt-4 mb-4">
          <div className="col-12">
            <p style={{fontWeight:"bold"}}>Your Liked Products ❤️</p>
            {/* Griglia responsive - 1 column on small screens, 3 on large */}
            <Row xs={1} md={2} lg={3} className="g-4">
              {likedProducts.map((likedProduct) => (
                <Col key={likedProduct.ID}>
                  {/* Card per ogni prodotto preferito */}
                  <Card className="h-100 shadow-sm">
                    <Card.Body>
                      <Card.Title>{likedProduct.Name}</Card.Title>
                      <Card.Text>
                        <small className="text-muted">ID: {likedProduct.ID}</small><br />
                        <small className="text-muted">Manufacturer: {likedProduct.Manufacturer}</small><br />
                        <small className="text-muted">Created: {likedProduct.CreationDate}</small>
                      </Card.Text>
                      <div className="d-flex justify-content-between align-items-center">
                        <button
                          className="btn btn-sm btn-outline-primary"
                          onClick={() => {
                            setItemCode(likedProduct.ID);
                            document.getElementById("itemCode").value = likedProduct.ID;
                            window.scrollTo({ top: 0, behavior: 'smooth' })
                          }}
                        >
                          View Details
                        </button>
                        <button
                          className="btn btn-sm btn-danger"
                          onClick={async () => {
                            // Get user ID from localStorage
                            const userId = localStorage.getItem('email') || 'default';

                            try {
                              // Call the backend to unlike the product
                              const response = await axios.delete(`/api/unlikeProduct?productId=${likedProduct.ID}&userId=${userId}`, {
                                headers: {
                                  'Authorization': `Bearer ${localStorage.getItem('token')}`,
                                  'Content-Type': 'application/json',
                                }
                              });

                              console.log(`Product ${likedProduct.ID} removed from favorites`, response.data);

                              // Update the list of liked products in state
                              const updatedProducts = likedProducts.filter(p => p.ID !== likedProduct.ID);
                              setLikedProducts(updatedProducts);

                              // If this is the currently displayed product, update its liked status
                              if (product && product.ID === likedProduct.ID) setLiked(false);
                            } catch (error) {
                              console.error("Error removing product from favorites:", error);
                            }
                          }}
                        >
                          <ion-icon name="heart-dislike-outline"></ion-icon>
                        </button>
                      </div>
                    </Card.Body>
                  </Card>
                </Col>
              ))}
            </Row>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProductList;