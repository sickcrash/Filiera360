#!/bin/bash
export FABRIC_CFG_PATH=$PWD

cryptogen generate --config=./crypto-config.yaml
configtxgen -profile TwoOrgsOrdererGenesis -outputBlock ./genesis.block -channelID system-channel
configtxgen -profile TwoOrgsChannel -outputCreateChannelTx ./channel.tx -channelID mychannel
