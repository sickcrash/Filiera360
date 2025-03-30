import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Card, Table, Row, Col } from 'react-bootstrap';
import UpdateProduct from './update_prod/UpdateProduct';
import { QRCodeCanvas } from 'qrcode.react';
import QrScanner from 'react-qr-scanner';
import jsQR from 'jsqr';
import Viewer3D from './Viewer3D';

const ProductList = ({ onProductSelect }) => {
  const [itemCode, setItemCode] = useState('');
  const [message, setMessage] = useState('');
  const [product, setProduct] = useState(null);
  const [productHistory, setProductHistory] = useState([]);
  const [status, setStatus] = useState('');
  const [showCamera, setShowCamera] = useState('false');
  const [scan, setScan] = useState(0);
  const [glbFile, setGlbFile] = useState(null);
  
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
    
    // controllo il prodotto scannerizzato è gia stato preferito
    setLiked(likedProducts.some(p => p.ID === itemCode)); // Check if product is already liked
    
    try {
      console.log("Scanning for Item Code: " + itemCode);

      // Fetch product details from the server
      const response = await axios.get(`http://127.0.0.1:5000/getProduct?productId=${itemCode}`);
      const historyResponse = await axios.get(`http://127.0.0.1:5000/getProductHistory?productId=${itemCode}`);

      if (response.status === 200) {
        const productData = response.data;
        setProduct(productData); // Set product details in state
        setMessage(`Product ${itemCode} found!`);
        console.log(`Product ${itemCode} found!`);
        onProductSelect(itemCode);
        setProductHistory(historyResponse.data || "");
        
        // Aggiungi il prodotto alla cronologia dei prodotti scansionati
        addToRecentlyScanned(productData);
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
      const modelResponse = await axios.get(`http://127.0.0.1:5000/getModel?productId=${itemCode}`);

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
    try {
      const movementsResponse = await axios.get(`http://127.0.0.1:5000/getAllMovements?productId=${itemCode}`);
      if (movementsResponse.status === 200) {
        const movementsFound = movementsResponse.data;
        setStatus(movementsFound[movementsFound.length - 1]?.Status || "");
      } else {
        setStatus("");
      }
    } catch (error) {
      setStatus("");
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

  const getFirstUpdate = () => {
    if (productHistory.length > 0) {
      const firstUpdate = productHistory[0].Timestamp;
      const date = new Date(firstUpdate.seconds * 1000 + firstUpdate.nanos / 1000000);
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
      logContent += `Creation Date: ${valueData.CreationDate}\n`;
      logContent += `Expiry Date: ${valueData.ExpiryDate}\n`;
      logContent += `More Information: ${valueData.Moreinfo || 'No additional information'}\n\n`;
      logContent += `Ingredients: ${valueData.Ingredients}\n`;
      logContent += `Nutritional Information: ${valueData.Nutritional_information || 'N/A'}\n`;
      logContent += `Allergens: ${valueData.Allergens || 'N/A'}\n`;
      logContent += `Harvest Date: ${valueData.HarvestDate}\n`;
      logContent += `Pesticide Use: ${valueData.PesticideUse || 'N/A'}\n`;
      logContent += `Fertilizer Use: ${valueData.FertilizerUse || 'N/A'}\n`;
      logContent += `Country Of Origin: ${valueData.CountryOfOrigin || 'N/A'}\n`;
    });

    const blob = new Blob([logContent], { type: 'text/plain' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `${itemCode}_product_history.txt`;

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
            setMessage('No QR code found in uploaded image.');
          }
        };
      };
      reader.readAsDataURL(file);
      setShowCamera(false);
      document.getElementById("uploader").value = "";
    }
  };

  // Funzione per gestire la scansione dalla fotocamera
  const handleQrScan = (data) => {
    if (data) {
      console.log(data.text);
      document.getElementById("itemCode").value = data.text;
      setItemCode(data.text);
      setScan(scan + 1); // trigger scan
      setShowCamera(false);
    }
  };

  // Avvia scansione al trigger
  useEffect(() => {
    if (scan > 0) handleScan();
  }, [scan]);

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
        Name: productData.Name,
        Manufacturer: productData.Manufacturer,
        CreationDate: productData.CreationDate,
        timestamp: new Date().toISOString() // Aggiungi timestamp per ordinare per data di scansione
      };
      
      // Send to backend
      await axios.post('http://127.0.0.1:5000/addRecentlySearched', {
        product: scannedProduct,
        userId: userId
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
        const response = await axios.get(`http://127.0.0.1:5000/getRecentlySearched?userId=${userId}`);
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
        const response = await axios.get(`http://127.0.0.1:5000/getLikedProducts?userId=${userId}`);
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
          const response = await axios.delete(`http://127.0.0.1:5000/unlikeProduct?productId=${product.ID}&userId=${userId}`, {
            headers: {
              'Content-Type': 'application/json',
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
        
        await axios.post('http://127.0.0.1:5000/likeProduct', {
          product: productToLike,
          userId: userId
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
      <form
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
                  onClick={(e) => {
                    const userRole = localStorage.getItem("role"); 

                    if (userRole !== "producer") {
                      e.preventDefault();
                      window.location.href = "/access-denied"; 
                    }
                  }}
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
                type="submit"
                className="btn btn-primary mt-3 w-100"
                id="scanButton"
                value="Scan Product"
              />
              {message && <p className="mt-3 text-muted">{message}</p>}
            </div>
          </div>
        </div>
      </form>

      {/* Recently Scanned Products Section */}
      {recentlyScanned.length > 0 && (
        <div className="row mt-4 mb-4">
          <div className="col-12">
            <h4>Recently Scanned Products 🕒</h4>
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
                            document.getElementById("itemCode").value = scannedProduct.ID;
                            const syntheticEvent = { preventDefault: () => {} };
                            handleScan(syntheticEvent);
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
            <h4>Your Liked Products ❤️</h4>
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
                            handleScan();
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
                              const response = await axios.delete(`http://127.0.0.1:5000/unlikeProduct?productId=${likedProduct.ID}&userId=${userId}`, {
                                headers: {
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
                    {product.CreationDate && (
                      <tr>
                        <th>Creation Date</th>
                        <td>{product.CreationDate}</td>
                      </tr>
                    )}
                    {product.ExpiryDate && (
                      <tr>
                        <th>Expiry Date</th>
                        <td>{product.ExpiryDate}</td>
                      </tr>
                    )}
                    {product.Moreinfo && (
                      <tr>
                        <th>More Information</th>
                        <td>{product.Moreinfo}</td>
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
                    {product.HarvestDate && (
                      <tr>
                        <th>Harvest Date</th>
                        <td>{product.HarvestDate}</td>
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
                    <tr>
                      <th>Status</th>
                      <td>{status || 'No status available'}</td>
                    </tr>
                    <tr>
                      <th>N. Updates *</th>
                      <td>{productHistory.length}</td>
                    </tr>
                    <tr>
                      <th>Creation Date *</th>
                      <td>{getLastUpdate() || 'No updates available'}</td>
                    </tr>
                    <tr>
                      <th>Last Update *</th>
                      <td>{getFirstUpdate() || 'No updates available'}</td>
                    </tr>
                  </tbody>
                </Table>
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
          {/* Rest of your component */}
        </div>
      )}
    </div>
  );
};

export default ProductList;


