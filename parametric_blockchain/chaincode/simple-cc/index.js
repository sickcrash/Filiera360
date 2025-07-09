'use strict';

const { Contract } = require('fabric-contract-api');

class SimpleContract extends Contract {

  async InitLedger(ctx) {
    console.log('Ledger initialized');
  }

  async SetValue(ctx, key, value) {
    await ctx.stub.putState(key, Buffer.from(value));
  }

  async GetValue(ctx, key) {
    const value = await ctx.stub.getState(key);
    if (!value || value.length === 0) {
      throw new Error(`Valore per la chiave ${key} non trovato`);
    }
    return value.toString();
  }
}

module.exports = SimpleContract;
