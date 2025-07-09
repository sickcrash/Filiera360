#!/bin/bash

# Imposta il nome del channel qui
CHANNEL_NAME="mychannel"
DELAY="3"
MAX_RETRY="5"
ORDERER_CA=./crypto-config/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem
ORDERER_ADDRESS=orderer.example.com:7050
CHANNEL_TX_FILE=./channel-artifacts/${CHANNEL_NAME}.tx
CHANNEL_BLOCK=./channel-artifacts/${CHANNEL_NAME}.block

CORE_PEER_LOCALMSPID="Org1MSP"
CORE_PEER_MSPCONFIGPATH=./crypto-config/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp
CORE_PEER_ADDRESS=localhost:7051
CORE_PEER_TLS_ENABLED=false

echo "Creazione canale: '$CHANNEL_NAME'..."

peer channel create \
  -o ${ORDERER_ADDRESS} \
  -c ${CHANNEL_NAME} \
  -f ${CHANNEL_TX_FILE} \
  --outputBlock ${CHANNEL_BLOCK} \
  --tls ${CORE_PEER_TLS_ENABLED} \
  --cafile ${ORDERER_CA}


echo "Join del peer nel canale..."
peer channel join -b ${CHANNEL_BLOCK}

peer channel list

echo "Canale '${CHANNEL_NAME}' creato e join completato con successo!"

