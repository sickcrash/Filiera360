import React, { useEffect, useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import { Card, Form, Button } from "react-bootstrap";
import { QRCodeCanvas } from "qrcode.react";
import Viewer3D from "./components/Viewer3D";
import Papa from "papaparse"; // Assicurati che sia installato
// Estraggo fuori costanti comuni
const inputWidth = "30%";
const placeholderText = "+ add new";
const AddProduct = () => {
  let navigate = useNavigate();

  const [manufacturer, setManufacturer] = useState("");

  const [id, setId] = useState("");
  const [name, setName] = useState("");
  const [expiryDate, setExpiryDate] = useState("");
  const [ingredients, setIngredients] = useState("");
  const [allergens, setAllergens] = useState("");
  const [nutritionalInformation, setNutritionalInformation] = useState("");
  const [harvestDate, setHarvestDate] = useState("");
  const [pesticideUse, setPesticideUse] = useState("");
  const [fertilizerUse, setFertilizerUse] = useState("");
  const [countryOfOrigin, setCountryOfOrigin] = useState("");
  const [message, setMessage] = useState("");
  const [view, setView] = useState("");
  const [lastAdded, setLastAdded] = useState("");
  const [glbFile, setGlbFile] = useState("");
  const [productType, setProductType] = useState("");
  const [csvFile, setCsvFile] = useState(null);
  const [viewProduct, setViewProduct] = useState(false);
  // Batch fields
  const [operator, setOperator] = useState("");
  const [idBatch, setIdBatch] = useState("");
  const [productId, setProductId] = useState("");
  const [batchNumber, setBatchNumber] = useState("");
  const [quantity, setQuantity] = useState("");
  const [productionDate, setProductionDate] = useState("");
  const [customBatchFields, setCustomBatchFields] = useState([]);
  const [csvBatchFile, setCsvBatchFile] = useState(null);
  const [viewBatch, setViewBatch] = useState(false);

  // UI states
  const [messageProduct, setMessageProduct] = useState("");
  const [messageBatch, setMessageBatch] = useState("");
  const [lastAddedProduct, setLastAddedProduct] = useState("");
  const [lastAddedBatch, setLastAddedBatch] = useState("");
  // ----------------- LOAD LOCALSTORAGE -----------------
  useEffect(() => {
    setManufacturer(localStorage.getItem("manufacturer") || "");
    const role = localStorage.getItem("role");
    if (role !== "producer") {
      navigate("/account");
    }
    setOperator(localStorage.getItem("manufacturer") || ""); // Da sostituire con altro gruppo in futuro
  }, []);

  const resetForm = () => {
    setId("");
    setName("");
    setExpiryDate("");
    setIngredients("");
    setAllergens("");
    setNutritionalInformation("");
    setHarvestDate("");
    setPesticideUse("");
    setFertilizerUse("");
    setCountryOfOrigin("");
    setView("");
    setProductType("");
    setGlbFile("");
    setCustomFields([]); // Ensure it's an array
  };
  const resetBatchForm = () => {
    setIdBatch("");
    setProductId("");
    setBatchNumber("");
    setQuantity("");
    setProductionDate("");
    setCustomBatchFields([]);
  };
  // ----------------- CUSTOM FIELDS FUNCTIONS -----------------
  // Product

  // Metodo per aggiungere un nuovo campo personalizzato con chiave-valore
  const addCustomField = () => {
    setCustomFields([...customFields, { key: "", value: "" }]);
  };
  // Metodo per aggiornare il nuovo campo personalizzato
  const updateCustomField = (index, key, value) => {
    const newFields = [...customFields];
    newFields[index] = { key, value };
    setCustomFields(newFields);
  };
  const removeCustomField = (index) => {
    setCustomFields(customFields.filter((_, i) => i !== index));
  };
  // Batch
  const addCustomBatchField = () =>
    setCustomBatchFields([...customBatchFields, { key: "", value: "" }]);
  const updateCustomBatchField = (index, key, value) => {
    const newBatchFields = [...customBatchFields];
    newBatchFields[index] = { key, value };
    setCustomBatchFields(newBatchFields);
  };
  const removeCustomBatchField = (index) => {
    setCustomBatchFields(customBatchFields.filter((_, i) => i !== index));
  };
  // ----------------- FILE CONVERSION FOR 3D MODEL -----------------

  const convertFileToBase64 = async (glbFile) => {
    try {
      const response = await fetch(glbFile);
      const blob = await response.blob();
      return await new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onloadend = () => resolve(reader.result);
        reader.onerror = reject;
        reader.readAsDataURL(blob);
      });
    } catch (error) {
      console.error("Error converting 3D model:", error);
      throw new Error("Failed to convert 3D model.");
    }
  };
  // ----------------- UPLOAD PRODUCT -----------------

  const handleUploadProduct = async (e) => {
    e.preventDefault();

    // Verifica se la data di scadenza è maggiore della data di raccolta
    if (new Date(expiryDate) <= new Date(harvestDate)) {
      alert("Expiry Date must be after Harvest Date");
      return;
    }
    // Crea un oggetto con tutti i dati del prodotto
    const productData = {
      ID: id,
      Name: name,
      Manufacturer: manufacturer,
      HarvestDate: harvestDate,
      ExpiryDate: expiryDate,
      Nutritional_information: nutritionalInformation,
      CountryOfOrigin: countryOfOrigin,
      Ingredients: ingredients,
      Allergens: allergens,
      PesticideUse: pesticideUse,
      FertilizerUse: fertilizerUse,
      CustomObject: customFields.reduce((obj, field) => {
        if (field.key.trim()) obj[field.key] = field.value;
        return obj;
      }, {}),
      // Movements: [],
      // SensorData: [],
      // Certifications: []
    };
    // Funzione per recuperare il Blob da un URL e convertirlo in base64
    const convertFileToBase64 = async (glbFile) => {
      return fetch(glbFile)
        .then((response) => response.blob()) // Recupera il Blob dall'URL
        .then((blob) => {
          return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onloadend = () => {
              resolve(reader.result);
            };
            reader.onerror = reject;
            reader.readAsDataURL(blob);
          });
        })
        .catch((error) => {
          console.error("Error fetching blob:", error);
          throw new Error("Failed to convert blob URL to base64.");
        });
    };
    // Funzione per fare POST del modello 3D
    const uploadModel = async () => {
      try {
        const base64File = await convertFileToBase64(glbFile);
        const postData = {
          ID: id,
          ModelBase64: base64File,
        };
        const token = localStorage.getItem("token");
        const response = await axios.post(
          "http://127.0.0.1:5000/uploadModel",
          postData,
          {
            headers: { Authorization: `Bearer ${token}` },
          }
        );
        console.log("Model uploaded successfully!");
        resetForm();
      } catch (error) {
        console.log("Failed to upload model.");
      }
    };
    // POST del nuovo prodotto + POST modello 3D
    try {
      const token = localStorage.getItem("token");
      console.log("invio dati al backend", productData);
      await axios.post(
        "http://127.0.0.1:5000/uploadProduct",
        JSON.stringify(productData),
        {
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        }
      );
      setMessageProduct("Product uploaded successfully!");
      setLastAddedProduct(productData.ID);
    } catch (error) {
      setMessageProduct(
        error.response?.data?.message || "Failed to upload product."
      );
    }
    if (glbFile) {
      try {
        const base64File = await convertFileToBase64(glbFile);
        await axios.post(
          "http://127.0.0.1:5000/uploadModel",
          {
            ID: id,
            ModelBase64: base64File,
          },
          {
            headers: {
              Authorization: `Bearer ${localStorage.getItem("token")}`,
            },
          }
        );
      } catch (error) {
        console.error("Failed to upload 3D model.");
      }
    }
    //Fai il resei dei dati del Form Product
    resetProductForm();

    //Nascondere i form di inserimento manuale che mostri solo quando l'utente clicca su "+ New Product" o "+ New Batch".
    setViewProduct(false);

    // nasconde il form Batch
    setViewBatch(false);

    //Resetta lo stato del file CSV caricato per i Product, svuotando il campo file.
    setCsvFile(null);
  };
  // ----------------- UPLOAD BATCH -----------------

  const handleUploadBatch = async (e) => {
    e.preventDefault();

    if (!idBatch.startsWith("L")) {
      alert('L\'ID del Batch deve iniziare con la lettera "L".');
      return; // blocca l'upload
    }
    //Controllo che la quantità non sia nulla o inferiore a zero

    if (isNaN(quantity) || Number(quantity) <= 0) {
      alert("Quantity must be a positive number.");
      return;
    }
    //L'id del batch deve iniziare con la lettera L per legge
    let batchIdFormatted = idBatch.startsWith("L") ? idBatch : "L" + idBatch;
    const batchData = {
      ID: batchIdFormatted,
      ProductId: productId,
      Operator: operator,
      BatchNumber: batchNumber,
      Quantity: quantity,
      ProductionDate: productionDate,
      CustomObject: customBatchFields.reduce((obj, field) => {
        if (field.key.trim()) obj[field.key] = field.value;
        return obj;
      }, {}),
    };
    try {
      const token = localStorage.getItem("token");
      console.log(batchData);
      await axios.post("http://127.0.0.1:5000/uploadBatch", batchData, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setMessageBatch("Batch uploaded successfully!");
      console.log(batchData.ID);
      setLastAddedBatch(batchData.ID);

      //Fai il resei dei dati del Form Batch
      resetBatchForm();

      //Resetta lo stato del file CSV caricato per i Batch, svuotando il campo file.
      setCsvBatchFile(null);

      //Nasconde i form di inserimento manuale che mostri solo quando l'utente clicca su "+ New Product".
      setViewBatch(false);

      //Nasconde i form di inserimento manuale che mostri solo quando l'utente clicca su "+ New Batch".
      setViewProduct(false);
    } catch (error) {
      setMessageBatch(
        error.response?.data?.message || "Failed to upload batch."
      );
    }
  };
  // ----------------- CSV Product -----------------

  const handleCsvChange = (e) => {
    setCsvFile(e.target.files[0]);
  };

  const handleCsvUpload = async () => {
    if (!csvFile) {
      setMessageProduct("Please upload a CSV file first.");
      return;
    }

    Papa.parse(csvFile, {
      complete: async (result) => {
        for (let row of result.data) {
          // Costruisci l'oggetto Product per ogni riga
          const postData = {
            ID: row[0],
            Name: row[1],
            Manufacturer: manufacturer,
            HarvestDate: row[2],
            ExpiryDate: row[3],
            Nutritional_information: row[4],
            CountryOfOrigin: row[5],
            Ingredients: row[6],
            Allergens: row[7],
            PesticideUse: row[8],
            FertilizerUse: row[9],
            CustomObject: JSON.parse(row[10] || "{}"), // Assicurati che sia JSON valido
          };

          try {
            const token = localStorage.getItem("token");
            await axios.post("http://127.0.0.1:5000/uploadProduct", postData, {
              headers: {
                Authorization: `Bearer ${token}`,
              },
            });
            console.log(`Product ${postData.ID} uploaded successfully!`);
          } catch (error) {
            console.error(`Error uploading product ${postData.ID}`, error);
            setMessageProduct(`Error uploading product ${postData.ID}`);
          }
        }
        setMessageProduct("CSV Product upload completed successfully!");
        setCsvFile(null);
        setViewProduct(false);
      },
      header: false, // Il CSV non contiene intestazioni
    });
  };

  // ----------------- CSV Batch -----------------
  const handleCsvBatchChange = (e) => {
    setCsvBatchFile(e.target.files[0]);
  };
  const handleCsvUploadBatch = async () => {
    if (!csvBatchFile) {
      setMessageBatch("Please upload a CSV file first.");
      return;
    }

    Papa.parse(csvBatchFile, {
      complete: async (result) => {
        for (let row of result.data) {
          // Formatta ID batch con la lettera L
          let batchIdFormatted = row[0].startsWith("L") ? row[0] : "L" + row[0];

          // Costruisci l'oggetto Batch per ogni riga
          const postBatchData = {
            ID: batchIdFormatted,
            ProductId: row[1],
            Operator: operator,
            BatchNumber: row[2],
            Quantity: row[3],
            ProductionDate: row[4],
            CustomObject: JSON.parse(row[5] || "{}"), // Assicurati che sia JSON valido
          };

          try {
            const token = localStorage.getItem("token");
            await axios.post(
              "http://127.0.0.1:5000/uploadBatch",
              postBatchData,
              {
                headers: {
                  Authorization: `Bearer ${token}`,
                },
              }
            );
            console.log(`Batch ${postBatchData.ID} uploaded successfully!`);
          } catch (error) {
            console.error(`Error uploading batch ${postBatchData.ID}`, error);
            setMessageBatch(`Error uploading batch ${postBatchData.ID}`);
          }
        }
        setMessageBatch("CSV Batch upload completed successfully!");
        setCsvBatchFile(null);
        setViewBatch(false);
      },
      header: false, // Il CSV non contiene intestazioni
    });
  };
  return (
    <div className="container mt-5">
      <div className="row justify-content-center">
        <div className="col-md-6">
          <div className="card shadow">
            <div className="card-body">
              <Card.Header>
                <h4>Upload Product 🌱</h4>
                <p style={{ color: "grey" }}>
                  ℹ️ Add your product and complete its details to enhance
                  traceability and transparency
                  <br />
                  🖼️ Insert and visualize your product with a 3D model
                </p>
              </Card.Header>
              <br />
              {messageProduct && !viewProduct && (
                <div>
                  {lastAddedProduct && (
                    <div>
                      <QRCodeCanvas
                        value={lastAddedProduct}
                        style={{ marginBottom: "2vw" }}
                      />
                      <p>
                        Product ID: <b>{lastAddedProduct}</b>
                      </p>
                    </div>
                  )}
                </div>
              )}
              {!viewProduct && (
                <button
                  className="btn btn-primary mt-3 w-100"
                  onClick={() => {
                    setViewProduct(true);
                    setViewBatch(false);
                    setMessageProduct("");
                  }}
                >
                  + New Product
                </button>
              )}
              {viewProduct && (
                <Card.Body>
                  {/* CSV File Upload */}
                  <Form.Group
                    className="d-flex align-items-center mb-3"
                    style={{ marginTop: "1vw" }}
                  >
                    <Form.Label style={{ width: inputWidth }} className="me-3">
                      Upload CSV
                    </Form.Label>
                    <Form
                      style={{
                        display: "flex",
                        width: "100%",
                        alignItems: "center",
                        justifyContent: "center",
                        gap: "2vw",
                        border: "1px dashed silver",
                        borderRadius: "1vw",
                        padding: "1vw",
                      }}
                    >
                      {csvFile ? (
                        <ion-icon
                          name="trash-outline"
                          style={{ cursor: "pointer", color: "grey" }}
                          onClick={() => {
                            document.getElementById("csvFile").value = "";
                            setCsvFile("");
                          }}
                        />
                      ) : (
                        <ion-icon
                          name="folder-outline"
                          style={{ color: "grey" }}
                        ></ion-icon>
                      )}
                      <label
                        htmlFor="csvFile"
                        style={{
                          color: "grey",
                          textDecoration: "underline",
                          cursor: "pointer",
                        }}
                      >
                        {csvFile
                          ? JSON.stringify(csvFile.name)
                          : "upload data Batch from CSV file"}
                      </label>
                      <input
                        style={{ display: "none" }}
                        id="csvFile"
                        type="file"
                        accept=".csv"
                        onChange={handleCsvChange}
                      />
                      {csvFile && (
                        <Button
                          variant="primary"
                          style={{ borderRadius: "2vw", paddingBlock: "0" }}
                          onClick={handleCsvUpload}
                          disabled={!csvFile}
                        >
                          Submit
                        </Button>
                      )}
                    </Form>
                  </Form.Group>
                  {csvFile && <p>{messageProduct}</p>}
                  {/* Separator */}
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      margin: "20px 0",
                    }}
                  >
                    <hr
                      style={{
                        flex: 1,
                        border: "none",
                        borderTop: "1px solid #666",
                      }}
                    />
                    <span
                      style={{
                        margin: "0 10px",
                        color: "#666",
                        fontWeight: "bold",
                      }}
                    >
                      or
                    </span>
                    <hr
                      style={{
                        flex: 1,
                        border: "none",
                        borderTop: "1px solid #666",
                      }}
                    />
                  </div>

                  <Form onSubmit={handleUploadProduct}>
                    {/* Display basic fields */}
                    <Form.Group
                      controlId="id"
                      className="d-flex align-items-center mb-3"
                    >
                      <Form.Label
                        style={{ width: inputWidth }}
                        className="me-3"
                      >
                        ID
                      </Form.Label>
                      <Form.Control
                        type="text"
                        value={id}
                        onChange={(e) => setId(e.target.value)}
                        placeholder={placeholderText}
                        required
                      />
                    </Form.Group>
                    {/* Name Field */}
                    <Form.Group
                      controlId="name"
                      className="d-flex align-items-center mb-3"
                    >
                      <Form.Label
                        style={{ width: inputWidth }}
                        className="me-3"
                      >
                        Name
                      </Form.Label>
                      <Form.Control
                        type="text"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        placeholder={placeholderText}
                        required
                      />
                    </Form.Group>
                    {/*Harvest Date Field*/}
                    <Form.Group
                      controlId="harvestDate"
                      className="d-flex align-items-center mb-3"
                    >
                      <Form.Label
                        style={{ width: inputWidth }}
                        className="me-3"
                      >
                        Harvest Date
                      </Form.Label>
                      <Form.Control
                        type="date"
                        value={harvestDate}
                        onChange={(e) => setHarvestDate(e.target.value)}
                      />
                    </Form.Group>
                    {/* Expire Date Field*/}
                    <Form.Group
                      controlId="expiryDate"
                      className="d-flex align-items-center mb-3"
                    >
                      <Form.Label
                        style={{ width: inputWidth }}
                        className="me-3"
                      >
                        Expiry Date
                      </Form.Label>
                      <Form.Control
                        type="date"
                        value={expiryDate}
                        onChange={(e) => setExpiryDate(e.target.value)}
                        required
                      />
                    </Form.Group>

                    <Form.Group
                      controlId="nutritionalInformation"
                      className="d-flex align-items-center mb-3"
                    >
                      <Form.Label
                        style={{ width: inputWidth }}
                        className="me-3"
                      >
                        Nutritional Information
                      </Form.Label>
                      <Form.Control
                        type="text"
                        value={nutritionalInformation}
                        onChange={(e) =>
                          setNutritionalInformation(e.target.value)
                        }
                        placeholder={placeholderText}
                      />
                    </Form.Group>

                    <Form.Group
                      controlId="countryOfOrigin"
                      className="d-flex align-items-center mb-3"
                    >
                      <Form.Label
                        style={{ width: inputWidth }}
                        className="me-3"
                      >
                        Country of Origin
                      </Form.Label>
                      <Form.Control
                        type="text"
                        value={countryOfOrigin}
                        onChange={(e) => setCountryOfOrigin(e.target.value)}
                        placeholder={placeholderText}
                      />
                    </Form.Group>
                    <Form.Group
                      controlId="pesticideUse"
                      className="d-flex align-items-center mb-3"
                    >
                      <Form.Label
                        style={{ width: inputWidth }}
                        className="me-3"
                      >
                        Pesticide Use
                      </Form.Label>
                      <Form.Control
                        type="text"
                        value={pesticideUse}
                        onChange={(e) => setPesticideUse(e.target.value)}
                        placeholder={placeholderText}
                      />
                    </Form.Group>
                    <Form.Group
                      controlId="fertilizerUse"
                      className="d-flex align-items-center mb-3"
                    >
                      <Form.Label
                        style={{ width: inputWidth }}
                        className="me-3"
                      >
                        Fertilizer Use
                      </Form.Label>
                      <Form.Control
                        type="text"
                        value={fertilizerUse}
                        onChange={(e) => setFertilizerUse(e.target.value)}
                        placeholder={placeholderText}
                      />
                    </Form.Group>
                    <Form.Group
                      controlId="ingredients"
                      className="d-flex align-items-center mb-3"
                    >
                      <Form.Label
                        style={{ width: inputWidth }}
                        className="me-3"
                      >
                        Ingredients
                      </Form.Label>
                      <Form.Control
                        type="text"
                        value={ingredients}
                        onChange={(e) => setIngredients(e.target.value)}
                        placeholder={placeholderText}
                      />
                    </Form.Group>
                    <Form.Group
                      controlId="allergens"
                      className="d-flex align-items-center mb-3"
                    >
                      <Form.Label
                        style={{ width: inputWidth }}
                        className="me-3"
                      >
                        Allergens
                      </Form.Label>
                      <Form.Control
                        type="text"
                        value={allergens}
                        onChange={(e) => setAllergens(e.target.value)}
                        placeholder={placeholderText}
                      />
                    </Form.Group>
                    {/* Upload 3D Model */}
                    <div className="mb-3">
                      <Viewer3D onGlbUpload={setGlbFile} />
                    </div>
                    {/* Separator */}
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        margin: "20px 0",
                      }}
                    >
                      <hr
                        style={{
                          flex: 1,
                          border: "none",
                          borderTop: "1px solid #666",
                        }}
                      />
                      <span
                        style={{
                          margin: "0 10px",
                          color: "#666",
                          fontWeight: "bold",
                        }}
                      ></span>
                      <hr
                        style={{
                          flex: 1,
                          border: "none",
                          borderTop: "1px solid #666",
                        }}
                      />
                    </div>
                    <h5>Custom Fields</h5>
                    {customFields.map((field, index) => (
                      <div
                        key={index}
                        className="d-flex mb-2 align-items-center"
                      >
                        <Form.Control
                          type="text"
                          placeholder="Field Name"
                          value={field.key}
                          onChange={(e) =>
                            updateCustomField(
                              index,
                              e.target.value,
                              field.value
                            )
                          }
                          className="me-2"
                        />
                        <Form.Control
                          type="text"
                          placeholder="Value"
                          value={field.value}
                          onChange={(e) =>
                            updateCustomField(index, field.key, e.target.value)
                          }
                        />
                        {/* Pulsante di rimozione con icona*/}
                        <button
                          type="button"
                          className="btn btn-light btn-sm ms-2 p-1"
                          onClick={() => removeCustomField(index)}
                          style={{
                            border: "none",
                            background: "transparent",
                            fontSize: "18px",
                            cursor: "pointer",
                            color: "#ff4d4d",
                          }}
                        >
                          ✖️
                        </button>
                      </div>
                    ))}

                    <Button
                      variant="primary"
                      onClick={addCustomField}
                      className="my-3 d-block mx-auto"
                    >
                      + Add Field
                    </Button>
                    {/* Separator */}
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        margin: "20px 0",
                      }}
                    >
                      <hr
                        style={{
                          flex: 1,
                          border: "none",
                          borderTop: "1px solid #666",
                        }}
                      />
                      <span
                        style={{
                          margin: "0 10px",
                          color: "#666",
                          fontWeight: "bold",
                        }}
                      ></span>
                      <hr
                        style={{
                          flex: 1,
                          border: "none",
                          borderTop: "1px solid #666",
                        }}
                      />
                    </div>
                    <Button
                      variant="primary"
                      type="submit"
                      disabled={
                        !id ||
                        !name ||
                        !expiryDate ||
                        !harvestDate ||
                        !ingredients ||
                        !nutritionalInformation ||
                        !allergens ||
                        !pesticideUse ||
                        !countryOfOrigin ||
                        !fertilizerUse
                      }
                    >
                      Upload Product
                    </Button>
                  </Form>
                </Card.Body>
              )}
            </div>
          </div>
          <div className="card shadow">
            <div className="card-body">
              <Card.Header>
                <h4>Upload Batch 📦</h4>
                <p style={{ color: "grey" }}>
                  ℹ️ Add your batch and complete its details to enhance
                  traceability and transparency
                  <br />
                </p>
              </Card.Header>
              <br />
              {messageBatch && !viewBatch && (
                <div>
                  {lastAddedBatch && (
                    <div>
                      <QRCodeCanvas
                        value={lastAddedBatch}
                        style={{ marginBottom: "2vw" }}
                      />
                      <p>
                        Batch ID: <b>{lastAddedBatch}</b>
                      </p>
                    </div>
                  )}
                </div>
              )}
              {!viewBatch && (
                <button
                  className="btn btn-primary mt-3 w-100"
                  onClick={() => {
                    setViewBatch(true);
                    setViewProduct(false);
                    setMessageBatch("");
                  }}
                >
                  + New Batch
                </button>
              )}
              {viewBatch && (
                <Card.Body>
                  {/* CSV File Upload */}
                  <Form.Group
                    className="d-flex align-items-center mb-3"
                    style={{ marginTop: "1vw" }}
                  >
                    <Form.Label style={{ width: inputWidth }} className="me-3">
                      Upload CSV Batch
                    </Form.Label>
                    <Form
                      style={{
                        display: "flex",
                        width: "100%",
                        alignItems: "center",
                        justifyContent: "center",
                        gap: "2vw",
                        border: "1px dashed silver",
                        borderRadius: "1vw",
                        padding: "1vw",
                      }}
                    >
                      {csvBatchFile ? (
                        <ion-icon
                          name="trash-outline"
                          style={{ cursor: "pointer", color: "grey" }}
                          onClick={() => {
                            document.getElementById("csvBatchFile").value = "";
                            setCsvBatchFile("");
                          }}
                        />
                      ) : (
                        <ion-icon
                          name="folder-outline"
                          style={{ color: "grey" }}
                        ></ion-icon>
                      )}
                      <label
                        htmlFor="csvBatchFile"
                        style={{
                          color: "grey",
                          textDecoration: "underline",
                          cursor: "pointer",
                        }}
                      >
                        {csvBatchFile
                          ? JSON.stringify(csvBatchFile.name)
                          : "upload data Batch from CSV file"}
                      </label>
                      <input
                        style={{ display: "none" }}
                        id="csvBatchFile"
                        type="file"
                        accept=".csv"
                        onChange={handleCsvBatchChange}
                      />
                      {csvBatchFile && (
                        <Button
                          variant="primary"
                          style={{ borderRadius: "2vw", paddingBlock: "0" }}
                          onClick={handleCsvUploadBatch}
                          disabled={!csvBatchFile}
                        >
                          Submit
                        </Button>
                      )}
                    </Form>
                  </Form.Group>
                  {csvBatchFile && <p>{messageBatch}</p>}
                  {/* Separator */}
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      margin: "20px 0",
                    }}
                  >
                    <hr
                      style={{
                        flex: 1,
                        border: "none",
                        borderTop: "1px solid #666",
                      }}
                    />
                    <span
                      style={{
                        margin: "0 10px",
                        color: "#666",
                        fontWeight: "bold",
                      }}
                    >
                      or
                    </span>
                    <hr
                      style={{
                        flex: 1,
                        border: "none",
                        borderTop: "1px solid #666",
                      }}
                    />
                  </div>

                  <Form onSubmit={handleUploadBatch}>
                    {/* Display basic fields */}
                    <Form.Group
                      controlId="id"
                      className="d-flex align-items-center mb-3"
                    >
                      <Form.Label
                        style={{ width: inputWidth }}
                        className="me-3"
                      >
                        ID
                      </Form.Label>
                      <Form.Control
                        type="text"
                        value={idBatch}
                        onChange={(e) => setIdBatch(e.target.value)}
                        placeholder={"LXXX"}
                        required
                      />
                    </Form.Group>
                    {/* Product Id */}
                    <Form.Group
                      controlId="productId"
                      className="d-flex align-items-center mb-3"
                    >
                      <Form.Label
                        style={{ width: inputWidth }}
                        className="me-3"
                      >
                        Product Id
                      </Form.Label>
                      <Form.Control
                        type="text"
                        value={productId}
                        onChange={(e) => setProductId(e.target.value)}
                        placeholder={placeholderText}
                        required
                      />
                    </Form.Group>
                    {/*Batch Number*/}
                    <Form.Group
                      controlId="batchNumber"
                      className="d-flex align-items-center mb-3"
                    >
                      <Form.Label
                        style={{ width: inputWidth }}
                        className="me-3"
                      >
                        Batch Number
                      </Form.Label>
                      <Form.Control
                        type="text"
                        value={batchNumber}
                        onChange={(e) => setBatchNumber(e.target.value)}
                      />
                    </Form.Group>
                    {/* Quantity*/}
                    <Form.Group
                      controlId="quantity"
                      className="d-flex align-items-center mb-3"
                    >
                      <Form.Label
                        style={{ width: inputWidth }}
                        className="me-3"
                      >
                        Quantity
                      </Form.Label>
                      <Form.Control
                        type="text"
                        value={quantity}
                        onChange={(e) => setQuantity(e.target.value)}
                        required
                      />
                    </Form.Group>

                    <Form.Group
                      controlId="productionDate"
                      className="d-flex align-items-center mb-3"
                    >
                      <Form.Label
                        style={{ width: inputWidth }}
                        className="me-3"
                      >
                        Production Date
                      </Form.Label>
                      <Form.Control
                        type="date"
                        value={productionDate}
                        onChange={(e) => setProductionDate(e.target.value)}
                        placeholder={placeholderText}
                      />
                    </Form.Group>
                    {/* Separator */}
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        margin: "20px 0",
                      }}
                    >
                      <hr
                        style={{
                          flex: 1,
                          border: "none",
                          borderTop: "1px solid #666",
                        }}
                      />
                      <span
                        style={{
                          margin: "0 10px",
                          color: "#666",
                          fontWeight: "bold",
                        }}
                      ></span>
                      <hr
                        style={{
                          flex: 1,
                          border: "none",
                          borderTop: "1px solid #666",
                        }}
                      />
                    </div>
                    <h5>Custom Batch Fields</h5>
                    <p style={{ color: "gray" }}>
                      edit existing custom fields or add new ones
                    </p>
                    {customBatchFields.map((field, index) => (
                      <div
                        key={index}
                        className="d-flex mb-2 align-items-center"
                      >
                        <Form.Control
                          type="text"
                          placeholder="Batch Field Name"
                          value={field.key}
                          onChange={(e) =>
                            updateCustomBatchField(
                              index,
                              e.target.value,
                              field.value
                            )
                          }
                          className="me-2"
                        />
                        <Form.Control
                          type="text"
                          placeholder="Value"
                          value={field.value}
                          onChange={(e) =>
                            updateCustomBatchField(
                              index,
                              field.key,
                              e.target.value
                            )
                          }
                        />
                        {/* Pulsante di rimozione con icona*/}
                        <button
                          type="button"
                          className="btn btn-light btn-sm ms-2 p-1"
                          onClick={() => removeCustomBatchField(index)}
                          style={{
                            border: "none",
                            background: "transparent",
                            fontSize: "18px",
                            cursor: "pointer",
                            color: "#ff4d4d",
                          }}
                        >
                          ✖️
                        </button>
                      </div>
                    ))}

                    <Button
                      variant="primary"
                      onClick={addCustomBatchField}
                      className="my-3 d-block mx-auto"
                    >
                      + Add Batch Field
                    </Button>

                    {/* Separator */}
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        margin: "20px 0",
                      }}
                    >
                      <hr
                        style={{
                          flex: 1,
                          border: "none",
                          borderTop: "1px solid #666",
                        }}
                      />
                      <span
                        style={{
                          margin: "0 10px",
                          color: "#666",
                          fontWeight: "bold",
                        }}
                      ></span>
                      <hr
                        style={{
                          flex: 1,
                          border: "none",
                          borderTop: "1px solid #666",
                        }}
                      />
                    </div>
                    <Button
                      variant="primary"
                      type="submit"
                      disabled={
                        !idBatch ||
                        !productId ||
                        !batchNumber ||
                        !quantity ||
                        !productionDate
                      }
                    >
                      Upload Batch
                    </Button>
                  </Form>
                </Card.Body>
              )}
            </div>
          </div>
        </div>
      </div>

      <br />
      <br />
    </div>
  );
};

export default AddProduct;
