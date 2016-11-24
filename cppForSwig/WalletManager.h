////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2016, goatpig                                               //
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#ifndef _WALLET_MANAGER_H
#define _WALLET_MANAGER_H

using namespace std;

#include <mutex>
#include <memory>
#include <string>
#include <map>
#include <iostream>

#include "log.h"
#include "Wallets.h"
#include "SwigClient.h"

////////////////////////////////////////////////////////////////////////////////
class WalletContainer
{
   friend class WalletManager;

private:
   const string id_;
   shared_ptr<AssetWallet> wallet_;
   shared_ptr<SwigClient::BtcWallet> swigWallet_;
   function<SwigClient::BlockDataViewer&(void)> getBDVlambda_;

private:
   WalletContainer(const string& id,
      function<SwigClient::BlockDataViewer&(void)> bdvLbd) :
      id_(id), getBDVlambda_(bdvLbd)
   {}

protected:
   //need this for unit test, but can't have it exposed to SWIG for backwards
   //compatiblity with 2.x (because of the shared_ptr return type)
   virtual shared_ptr<AssetWallet> getWalletPtr(void) const
   {
      return wallet_;
   }

public:
   void registerWithBDV(bool prefix, bool isNew);

   vector<uint64_t> getBalancesAndCount(
      uint32_t topBlockHeight, bool IGNOREZC)
   {
      return swigWallet_->getBalancesAndCount(topBlockHeight, IGNOREZC);
   }

   vector<UTXO> getSpendableTxOutListForValue(
      uint64_t val = UINT64_MAX, bool ignoreZC = true)
   {
      return swigWallet_->getSpendableTxOutListForValue(val, ignoreZC);
   }
   
   map<BinaryData, uint32_t> getAddrTxnCountsFromDB(void)
   {
      return swigWallet_->getAddrTxnCountsFromDB();
   }
   
   map<BinaryData, vector<uint64_t>> getAddrBalancesFromDB(void)
   {
      return swigWallet_->getAddrBalancesFromDB();
   }

   vector<LedgerEntryData> getHistoryPage(uint32_t id)
   {
      return swigWallet_->getHistoryPage(id);
   }

   LedgerEntryData getLedgerEntryForTxHash(
      const BinaryData& txhash)
   {
      return swigWallet_->getLedgerEntryForTxHash(txhash);
   }

   SwigClient::ScrAddrObj getScrAddrObjByKey(const BinaryData& scrAddr,
      uint64_t full, uint64_t spendable, uint64_t unconf, uint32_t count)
   {
      return swigWallet_->getScrAddrObjByKey(
         scrAddr, full, spendable, unconf, count);
   }

   vector<AddressBookEntry> createAddressBook(void) const
   {
      return swigWallet_->createAddressBook();
   }
};

////////////////////////////////////////////////////////////////////////////////
class WalletManager
{
private:
   mutable mutex mu_;

   const string path_;
   map<string, WalletContainer> wallets_;
   SwigClient::BlockDataViewer bdv_;

private:
   void loadWallets();
   SwigClient::BlockDataViewer& getBDVObj(void);

public:
   WalletManager(const string& path) :
      path_(path)
   {
      loadWallets();
   }

   bool hasWallet(const string& id)
   {
      unique_lock<mutex> lock(mu_);
      auto wltIter = wallets_.find(id);
      
      return wltIter != wallets_.end();
   }

   void setBDVObject(const SwigClient::BlockDataViewer& bdv)
   {
      bdv_ = bdv;
   }

   void synchronizeWallet(const string& id, unsigned chainLength);

   void duplicateWOWallet(
      const SecureBinaryData& pubRoot,
      const SecureBinaryData& chainCode,
      unsigned chainLength);

   WalletContainer& getCppWallet(const string& id);
};

#endif