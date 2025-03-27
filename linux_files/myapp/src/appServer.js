/*
 * Copyright IBM Corp. All Rights Reserved.
 *
 * SPDX-License-Identifier: Apache-2.0
 */
const express = require('express');
const bodyParser = require('body-parser');

const grpc = require('@grpc/grpc-js');
const { connect, signers } = require('@hyperledger/fabric-gateway');
const crypto = require('node:crypto');
const fs = require('node:fs/promises');
const path = require('node:path');
const { TextDecoder } = require('node:util');


const app = express();
app.use(bodyParser.json());

const channelName = envOrDefault('CHANNEL_NAME', 'mychannel');
const chaincodeName = envOrDefault('CHAINCODE_NAME', 'basic');
const mspId = envOrDefault('MSP_ID', 'Org1MSP');

// Path to crypto materials.
const cryptoPath = envOrDefault(
    'CRYPTO_PATH',
    path.resolve(
        __dirname,
        '..',
        '..',
        'test-network',
        'organizations',
        'peerOrganizations',
        'org1.example.com'
    )
);

// Path to user private key directory.
const keyDirectoryPath = envOrDefault(
    'KEY_DIRECTORY_PATH',
    path.resolve(
        cryptoPath,
        'users',
        'User1@org1.example.com',
        'msp',
        'keystore'
    )
);

// Path to user certificate directory.
const certDirectoryPath = envOrDefault(
    'CERT_DIRECTORY_PATH',
    path.resolve(
        cryptoPath,
        'users',
        'User1@org1.example.com',
        'msp',
        'signcerts'
    )
);

// Path to peer tls certificate.
const tlsCertPath = envOrDefault(
    'TLS_CERT_PATH',
    path.resolve(cryptoPath, 'peers', 'peer0.org1.example.com', 'tls', 'ca.crt')
);

// Gateway peer endpoint.
const peerEndpoint = envOrDefault('PEER_ENDPOINT', 'localhost:7051');

// Gateway peer SSL host name override.
const peerHostAlias = envOrDefault('PEER_HOST_ALIAS', 'peer0.org1.example.com');

const utf8Decoder = new TextDecoder();
//const productId = `product0123456789`;

async function main() {
    displayInputParameters();

    // The gRPC client connection should be shared by all Gateway connections to this endpoint.
    const client = await newGrpcConnection();

    const gateway = connect({
        client,
        identity: await newIdentity(),
        signer: await newSigner(),
        // Default timeouts for different gRPC calls
        evaluateOptions: () => {
            return { deadline: Date.now() + 5000 }; // 5 seconds
        },
        endorseOptions: () => {
            return { deadline: Date.now() + 15000 }; // 15 seconds
        },
        submitOptions: () => {
            return { deadline: Date.now() + 5000 }; // 5 seconds
        },
        commitStatusOptions: () => {
            return { deadline: Date.now() + 60000 }; // 1 minute
        },
    });

    try {
        // Get a network instance representing the channel where the smart contract is deployed.
        const network = gateway.getNetwork(channelName);

        // Get the smart contract from the network.
        const contract = network.getContract(chaincodeName);

        // Initialize a set of product data on the ledger using the chaincode 'InitLedger' function.
        await initLedger(contract);

        // Return all the current Products on the ledger.
        //await getAllProducts(contract);

        // Create a new product on the ledger.
        // await createProductDefault(contract);

        // Update an existing product asynchronously.
        //await transferProductAsync(contract);

        // Get the procut details by productID.
        //await readProductByID(contract);

        // Update a product which does not exist.
        //await updateNonExistentProduct(contract);
    } finally {
        gateway.close();
        client.close();
    }
}

async function initGateway() {
    const client = await newGrpcConnection();
    gateway = connect({
        client,
        identity: await newIdentity(),
        signer: await newSigner(),
        evaluateOptions: () => ({ deadline: Date.now() + 5000 }),
        endorseOptions: () => ({ deadline: Date.now() + 15000 }),
        submitOptions: () => ({ deadline: Date.now() + 5000 }),
        commitStatusOptions: () => ({ deadline: Date.now() + 60000 })
    });
}

main().catch((error) => {
    console.error('******** FAILED to run the application:', error);
    process.exitCode = 1;
});

async function newGrpcConnection() {
    const tlsRootCert = await fs.readFile(tlsCertPath);
    const tlsCredentials = grpc.credentials.createSsl(tlsRootCert);
    return new grpc.Client(peerEndpoint, tlsCredentials, {
        'grpc.ssl_target_name_override': peerHostAlias,
    });
}

async function newIdentity() {
    const certPath = await getFirstDirFileName(certDirectoryPath);
    const credentials = await fs.readFile(certPath);
    return { mspId, credentials };
}

async function getFirstDirFileName(dirPath) {
    const files = await fs.readdir(dirPath);
    const file = files[0];
    if (!file) {
        throw new Error(`No files in directory: ${dirPath}`);
    }
    return path.join(dirPath, file);
}

async function newSigner() {
    const keyPath = await getFirstDirFileName(keyDirectoryPath);
    const privateKeyPem = await fs.readFile(keyPath);
    const privateKey = crypto.createPrivateKey(privateKeyPem);
    return signers.newPrivateKeySigner(privateKey);
}

/**
 * This type of transaction would typically only be run once by an application the first time it was started after its
 * initial deployment. A new version of the chaincode deployed later would likely not need to run an "init" function.
 */
async function initLedger(contract) {
    console.log(
        '\n--> Submit Transaction: initLedger, function creates the initial set of products on the ledger'
    );

    await contract.submitTransaction('initLedger');

    console.log('*** Transaction committed successfully');
}

/* crea prodotto default 'product0123456789'
async function createProductDefault(contract) {
    console.log(
        '\n--> Submit Transaction: CreateProduct, creates new product with ID, Name, Manufacturer, CreationDate, ExpiryDate, Ingredients, Nutritional_information and Allergens arguments'
    );

    await contract.submitTransaction(
        'createProduct',
        productId,
        'NewProduct',
        'Manifacturer server',
        '01/11/2011',
        '02/02/2022',
        'Water, Flowr',
        '100% carbs',
        'Yeast',
        ''
    );

    console.log('*** Transaction committed successfully');
} */

    async function createProduct(contract, productData) {
        console.log('\n--> Submit Transaction: CreateProduct, creates new product with provided arguments');
        if (!productData) {
            console.error("❌ ERRORE: productData è undefined o nullo!");
            return;
        }
        console.log('productData non è undefined');
        console.log("📌 Dati ricevuti:", productData);
        
        const { 
            ID = "",
            Name = "",
            Manufacturer = "",
            ExpiryDate = "",
            Ingredients = "",
            Allergens = "",
            Nutritional_information = "",
            HarvestDate = "",
            PesticideUse = "",
            FertilizerUse = "",
            CountryOfOrigin = "",
            CustomObject = {}  // Corretta destrutturazione
        } = productData;
    
        console.log("📌 CustomObject ricevuto:", CustomObject);
    
        // Verifica la struttura di CustomObject
        if (typeof CustomObject !== 'object') {
            console.error("❌ ERRORE: CustomObject non è un oggetto valido!", CustomObject);
            return;
        }
    
        // Assicurati che CustomObject venga serializzato correttamente
        try {
            const customObjectJson = JSON.stringify(CustomObject);
            console.log("📌 CustomObject dopo JSON.stringify:", customObjectJson);
        } catch (error) {
            console.error("❌ ERRORE nella serializzazione di CustomObject:", error);
            return;
        }
    
        console.log('\n--> Sto facendo partire la funzione per il submit');
    
        try {
            // Aggiungi logging per verificare i parametri
            console.log("📌 Parametri passati alla transazione:", {
                ID, Name, Manufacturer, ExpiryDate, Ingredients, Allergens, Nutritional_information,
                HarvestDate, PesticideUse, FertilizerUse, CountryOfOrigin, CustomObject
            });
    
            // Submit della transazione
            await contract.submitTransaction(
                'createProduct',
                ID,
                Name,
                Manufacturer,
                ExpiryDate,
                Ingredients,
                Allergens,
                Nutritional_information,
                HarvestDate,
                PesticideUse,
                FertilizerUse,
                CountryOfOrigin,
                JSON.stringify(CustomObject)  // Corretta conversione JSON
            );
    
            console.log('✅ *** Transaction committed successfully ***');
        } catch (error) {
            console.error('❌ Errore nella submitTransaction:', error);
        }
    }
    
    async function createBatch(contract, batchData) {
        console.log('\n--> Submit Transaction: CreateBatch, creates new batch with provided arguments');
        if (!batchData) {
            console.error("❌ ERRORE: batchData è undefined o nullo!");
            return;
        }
        console.log('batchData non è undefined');
        console.log("📌 Dati ricevuti:", batchData);
        
        const { 
            ID = "",
            ProductId = "",
            Operator = "",
            BatchNumber = "",
            Quantity = "",
            ProductionDate = "",
            CustomObject = {}  // Corretta destrutturazione
        } = batchData;
    
        console.log("📌 CustomObject ricevuto:", CustomObject);
    
        // Verifica la struttura di CustomObject
        if (typeof CustomObject !== 'object') {
            console.error("❌ ERRORE: CustomObject non è un oggetto valido!", CustomObject);
            return;
        }
    
        // Assicurati che CustomObject venga serializzato correttamente
        try {
            const customObjectJson = JSON.stringify(CustomObject);
            console.log("📌 CustomObject dopo JSON.stringify:", customObjectJson);
        } catch (error) {
            console.error("❌ ERRORE nella serializzazione di CustomObject:", error);
            return;
        }
    
        console.log('\n--> Sto facendo partire la funzione per il submit');
    
        try {
            // Aggiungi logging per verificare i parametri
            console.log("📌 Parametri passati alla transazione:", {
                ID, ProductId, Operator, BatchNumber, Quantity, ProductionDate, CustomObject
            });
    
            // Submit della transazione
            await contract.submitTransaction(
                'createBatch',
                ID,
                ProductId,
                Operator,
                BatchNumber,
                Quantity,
                ProductionDate,
                JSON.stringify(CustomObject)  // Corretta conversione JSON
            );
    
            console.log('✅ *** Transaction committed successfully ***');
        } catch (error) {
            console.error('❌ Errore nella submitTransaction:', error);
        }
    }   
    
async function readProductByIDdefault(contract) {
    console.log(
        '\n--> Evaluate Transaction: ReadProduct, function returns product attributes'
    );

    const resultBytes = await contract.evaluateTransaction(
        'ReadProduct',
        productId
    );

    const resultJson = utf8Decoder.decode(resultBytes);
    const result = JSON.parse(resultJson);
    console.log('*** Result:', result);
}

function envOrDefault(key, defaultValue) {
    return process.env[key] || defaultValue;
}

/**
 * displayInputParameters() will print the global scope parameters used by the main driver routine.
 */
function displayInputParameters() {
    console.log(`channelName:       ${channelName}`);
    console.log(`chaincodeName:     ${chaincodeName}`);
    console.log(`mspId:             ${mspId}`);
    console.log(`cryptoPath:        ${cryptoPath}`);
    console.log(`keyDirectoryPath:  ${keyDirectoryPath}`);
    console.log(`certDirectoryPath: ${certDirectoryPath}`);
    console.log(`tlsCertPath:       ${tlsCertPath}`);
    console.log(`peerEndpoint:      ${peerEndpoint}`);
    console.log(`peerHostAlias:     ${peerHostAlias}`);
}

async function readProductByID(contract, productId) {
    console.log('\n--> Evaluate Transaction: ReadProduct, function returns product attributes');
    const resultBytes = await contract.evaluateTransaction('ReadProduct', productId);
    const resultJson = utf8Decoder.decode(resultBytes);
    const result = JSON.parse(resultJson);
    console.log('*** Result:', result);
    return result;
}
async function readBatchByID(contract, idBatch) {
    console.log('\n--> Evaluate Transaction: ReadBatch, function returns product attributes!');
    const resultBytes = await contract.evaluateTransaction('ReadBatch', idBatch);
    const resultJson = utf8Decoder.decode(resultBytes);
    const result = JSON.parse(resultJson);
    console.log('*** Result:', result);
    return result;
}
// nuova aggiunta
async function getProductHistoryByID(contract, productId) {
    console.log('\n--> Evaluate Transaction: GetProductHistory, function returns product history');
    const resultBytes = await contract.evaluateTransaction('GetProductHistory', productId);
    const resultJson = utf8Decoder.decode(resultBytes);
    const result = JSON.parse(resultJson);
    console.log('*** Result:', result);
    return result;
}
async function getBatchHistoryByID(contract, batchId) {
    console.log('\n--> Evaluate Transaction: GetBatchHistory, function returns batch history');
    const resultBytes = await contract.evaluateTransaction('GetBatchHistory', batchId);
    const resultJson = utf8Decoder.decode(resultBytes);
    const result = JSON.parse(resultJson);
    console.log('*** Result:', result);
    return result;
}

app.get('/readProduct', async (req, res) => {
    const { productId } = req.query;
    try {
        const network = gateway.getNetwork(channelName);
        const contract = network.getContract(chaincodeName);
        const result = await readProductByID(contract, productId);
        res.json(result);
    } catch (error) {
        console.error('Error reading product by ID:', error);
        res.status(500).json({ error: error.message });
    }
});

app.get('/readBatch', async (req, res) => {
    console.log('sono in readBatch');
    const { idBatch } = req.query;
    try {
        const network = gateway.getNetwork(channelName);
        const contract = network.getContract(chaincodeName);
        const result = await readBatchByID(contract, idBatch);
        res.json(result);
        console.log('Batch read successfully');
    } catch (error) {
        console.error('Error reading product by ID:', error);
        res.status(500).json({ error: error.message });
    }
});

// nuova aggiunta
app.get('/productHistory', async (req, res) => {
    const { productId } = req.query;
    try {
        const network = gateway.getNetwork(channelName);
        const contract = network.getContract(chaincodeName);
        const result = await getProductHistoryByID(contract, productId);
        res.json(result);
    } catch (error) {
        console.error('Error reading product history by ID:', error);
        res.status(500).json({ error: error.message });
    }
});
// nuova aggiunta
app.get('/batchHistory', async (req, res) => {
    const { batchId } = req.query;
    try {
        const network = gateway.getNetwork(channelName);
        const contract = network.getContract(chaincodeName);
        const result = await getBatchHistoryByID(contract, batchId);
        res.json(result);
    } catch (error) {
        console.error('Error reading batchId history by ID:', error);
        res.status(500).json({ error: error.message });
    }
});
app.post('/uploadProduct', async (req, res) => {
    const productData = req.body;
    console.log('Received product data:', productData);

    const { ID } = productData;

    try {
        const network = gateway.getNetwork(channelName);
        const contract = network.getContract(chaincodeName);

        // Check if product already exists
        try {
            const existingProduct = await readProductByID(contract, ID);
            if (existingProduct) {
                res.status(400).json({ message: `Product with ID ${ID} already exists.` });
                return;
            }
        } catch (error) {
            if (error.message.includes(`The product ${ID} does not exist`)) {
                // This is expected if the product doesn't exist, so we can continue
                console.log('Product not found, proceeding to create it.');
            } else {
                // Unexpected error
                console.error('Error checking for existing product:', error);
                res.status(500).json({ message: 'Failed to check for existing product.' });
                return;
            }
        }

        await createProduct(contract, productData);
        res.json({ message: 'Product created successfully' });
        console.log('Product created successfully');
    } catch (error) {
        console.error('Error creating product:', error);
        res.status(500).json({ error: error.message });
    }
});
//NUOVA FUNZIONE UPLOAD BATCH
app.post('/uploadBatch', async (req, res) => {
    const batchData = req.body;
    console.log('Received batch data:', batchData);

    const { ID } = batchData;

    try {
        const network = gateway.getNetwork(channelName);
        const contract = network.getContract(chaincodeName);

        // Check if batch already exists
        try {
            const existingBatch = await readBatchByID(contract, ID);
            if (existingBatch) {
                res.status(400).json({ message: `Batch with ID ${ID} already exists.` });
                return;
            }
        } catch (error) {
            if (error.message.includes(`The batch ${ID} does not exist`)) {
                // This is expected if the batch doesn't exist, so we can continue
                console.log('Batch not found, proceeding to create it.');
            } else {
                // Unexpected error
                console.error('Error checking for existing batch:', error);
                res.status(500).json({ message: 'Failed to check for existing batch.' });
                return;
            }
        }

        await createBatch(contract, batchData);
        res.json({ message: 'Batch created successfully' });
        console.log('Batch created successfully');
    } catch (error) {
        console.error('Error creating batch:', error);
        res.status(500).json({ error: error.message });
    }
});

app.post('/api/product/updateProduct', async (req, res) => {
    console.log('questa è la request', req.body);
    const productData = req.body;
    console.log('Received product data:', productData);

    try {
        console.log('test 1');

        const network = gateway.getNetwork(channelName);
        const contract = network.getContract(chaincodeName);
        console.log("Dati inviati al chaincode:", productData);

        await contract.submitTransaction('UpdateProduct',
            productData.ID, 
            productData.Name, 
            productData.Manufacturer,  
            productData.ExpiryDate, 
            productData.Ingredients, 
            productData.Allergens, 
            productData.Nutritional_information, 
            productData.HarvestDate, 
            productData.PesticideUse, 
            productData.FertilizerUse, 
            productData.CountryOfOrigin, 
            JSON.stringify(productData.CustomObject));
        res.status(200).json({ message: `product updated` });
    }

    catch (error) {
        console.error(`Failed to update product: ${error}`);
        res.status(500).json({ error: `Failed to update product: ${error.message}` });
    }
});

app.post('/api/batch/updateBatch', async (req, res) => {
    console.log('Sono su Appserver e questa è la request', req.body);
    const batchData = req.body;
    console.log('Received batch data:', batchData);

    try {
        console.log('test 1');

        const network = gateway.getNetwork(channelName);
        const contract = network.getContract(chaincodeName);
        console.log("Dati inviati al chaincode:", batchData);

        await contract.submitTransaction('UpdateBatch',
            batchtData.ID, 
            batchData.ProductId, 
            batchData.Operator,  
            batchData.BatchNumber, 
            batchData.Quantity, 
            batchData.ProductionDate, 
            JSON.stringify(batchData.CustomObject));
        res.status(200).json({ message: `batch updated` });
    }

    catch (error) {
        console.error(`Failed to update batch: ${error}`);
        res.status(500).json({ error: `Failed to update batch: ${error.message}` });
    }
});

// app.post('/api/product/sensor', async (req, res) => {
//     try {
//         const { id, SensorId, Temperature, Humidity, Timestamp } = req.body;
//         console.log("Recerived data sensor: " + id + ", " + SensorId + ", " + Temperature + ", " + Humidity + ", " + Timestamp)
//         const network = gateway.getNetwork(channelName);
//         const contract = network.getContract(chaincodeName);
//         await contract.submitTransaction('AddSensorData', id, SensorId, Temperature, Humidity, Timestamp);

//         res.status(200).json({ message: `Dati del sensore aggiunti per il prodotto ${id}` });
//     } catch (error) {
//         console.error(`Failed to add sensor data: ${error}`);
//         res.status(500).json({ error: `Errore durante l'aggiunta dei dati del sensore: ${error.message}` });
//     }
// });

// app.post('/api/product/movement', async (req, res) => {
//     try {
//         const { id, location, status, date } = req.body;
//         const network = gateway.getNetwork(channelName);
//         const contract = network.getContract(chaincodeName);
//         await contract.submitTransaction('UpdateProductLocation', id, location, status, date);

//         res.status(200).json({ message: `Posizione del prodotto ${id} aggiornata con successo` });
//     } catch (error) {
//         console.error(`Failed to update product location: ${error}`);
//         res.status(500).json({ error: `Errore durante l'aggiornamento della posizione: ${error.message}` });
//     }
// });

// app.post('/api/product/certification', async (req, res) => {
//     try {
//         const { id, certificationType, certifyingBody, issueDate } = req.body;
//         console.log(req.body)
//         const network = gateway.getNetwork(channelName);
//         const contract = network.getContract(chaincodeName);
//         await contract.submitTransaction('AddCertification', id, certificationType, certifyingBody, issueDate);

//         res.status(200).json({ message: `Certification added to product ${id}` });
//     } catch (error) {
//         console.error(`Failed to update certification: ${error}`);
//         res.status(500).json({ error: `Error while adding certification: ${error.message}` });
//     }
// });

app.post('/api/product/verifyProductCompliance', async (req, res) => {
    try {
        const { id, maxTemperature, minHumidity } = req.body;

        const network = gateway.getNetwork(channelName);
        const contract = network.getContract(chaincodeName);
        const response = await contract.evaluateTransaction('VerifyProductCompliance', id, maxTemperature, minHumidity);
        const result = utf8Decoder.decode(response);
        // Log the decoded response for debugging
        console.log('Decoded response from smart contract:', result);

        // Parse the response as JSON
        let parsedResponse;
        try {
            parsedResponse = JSON.parse(result);
        } catch (err) {
            console.error('Failed to parse JSON:', err.message);
            return res.status(500).json({ error: `Invalid JSON format: ${decodedResponse}` });
        }

        // Check if the product is compliant
        if (parsedResponse.compliant) {
            res.status(200).json({ message: parsedResponse.message });
        } else {
            res.status(400).json({ error: parsedResponse.message });
        }

    } catch (error) {
        console.error(`Failed to check product compliance: ${error}`);
        res.status(500).json({ error: `Failed to check product compliance: ${error.message}` });
    }
});

// app.get('/api/product/getMovements', async (req, res) => {
//     try {
//         const id = req.query.productId
//         const network = gateway.getNetwork(channelName);
//         const contract = network.getContract(chaincodeName)
//         const response = await contract.evaluateTransaction('GetAllMovements', id);
//         const result = utf8Decoder.decode(response);
//         console.log(result)
//         const resultJson = JSON.parse(result);
//         res.json(resultJson)
//     }
//     catch (error) {
//         console.error(`Failed to retrieve all movements: ${error}`);
//         res.status(500).json({ error: `Failed to retrieve all movements: ${error.message}` });
//     }
// })

// app.get('/api/product/getSensorData', async (req, res) => {
//     try {
//         const id = req.query.productId
//         const network = gateway.getNetwork(channelName);
//         const contract = network.getContract(chaincodeName)
//         const response = await contract.evaluateTransaction('GetAllSensorData', id);
//         const result = utf8Decoder.decode(response);
//         console.log(result)
//         const resultJson = JSON.parse(result);
//         res.json(resultJson)
//     }
//     catch (error) {
//         console.error(`Failed to retrieve all sensor data: ${error}`);
//         res.status(500).json({ error: `Failed to retrieve all sensor data: ${error.message}` });
//     }
// })

// app.get('/api/product/getCertifications', async (req, res) => {
//     try {
//         const id = req.query.productId
//         const network = gateway.getNetwork(channelName);
//         const contract = network.getContract(chaincodeName)
//         const response = await contract.evaluateTransaction('GetAllCertifications', id);
//         const result = utf8Decoder.decode(response);
//         console.log(result)
//         const resultJson = JSON.parse(result);
//         res.json(resultJson)
//     }
//     catch (error) {
//         console.error(`Failed to retrieve all certification data: ${error}`);
//         res.status(500).json({ error: `Failed to retrieve all certification data: ${error.message}` });
//     }
// })

app.listen(3000, async () => {
    await initGateway();
    console.log('JavaScript server running on port 3000');
});


