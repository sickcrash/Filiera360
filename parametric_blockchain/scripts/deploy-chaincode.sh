#!/bin/bash

export CORE_PEER_LOCALMSPID="Org1MSP"
export CORE_PEER_ADDRESS="peer0.org1.example.com:7051"
export CORE_PEER_MSPCONFIGPATH=/etc/hyperledger/fabric/msp

CC_NAME="simplecc"
CC_VERSION="1.0"
CC_SEQUENCE="1"
CC_SRC_PATH="./chaincode/simple-cc"
CC_RUNTIME_LANGUAGE="node"

docker exec peer0.org1.example.com bash -c "
  cd /opt/gopath/src/github.com/chaincode &&
  mkdir -p ${CC_NAME} &&
  cp -r ${CC_SRC_PATH}/* ${CC_NAME}/ &&
  npm install --prefix ${CC_NAME}
"

peer lifecycle chaincode package ${CC_NAME}.tar.gz --path ${CC_SRC_PATH} --lang ${CC_RUNTIME_LANGUAGE} --label ${CC_NAME}_${CC_VERSION}

docker cp ${CC_NAME}.tar.gz peer0.org1.example.com:/opt/gopath/src/github.com/
docker exec peer0.org1.example.com peer lifecycle chaincode install /opt/gopath/src/github.com/${CC_NAME}.tar.gz
docker exec peer0.org1.example.com peer lifecycle chaincode queryinstalled
# Sostituire il package ID nel comando seguente con quello stampato sopra
# docker exec peer0.org1.example.com peer lifecycle chaincode approveformyorg ...
