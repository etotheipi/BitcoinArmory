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
#include "Signer.h"
#include "BlockDataManagerConfig.h"

enum AddressType
{
   AddressType_P2PKH,
   AddressType_P2SH
};

////////////////////////////////////////////////////////////////////////////////
class WalletContainer
{
   friend class WalletManager;
   friend class PythonSigner;

private:
   const string id_;
   shared_ptr<AssetWallet> wallet_;
   shared_ptr<SwigClient::BtcWallet> swigWallet_;
   function<SwigClient::BlockDataViewer&(void)> getBDVlambda_;

   map<BinaryData, vector<uint64_t>> balanceMap_;
   map<BinaryData, uint32_t> countMap_;

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
   void registerWithBDV(bool isNew);

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
      auto wallet_aet = wallet_->getDefaultAddressType();
      uint8_t wltAddrPrefix;
      
      switch (wallet_aet)
      {
      case AddressEntryType_P2PKH:
         wltAddrPrefix = BlockDataManagerConfig::getPubkeyHashPrefix();
         break;

      case AddressEntryType_P2SH:
      case AddressEntryType_Nested_P2SH:
         wltAddrPrefix = BlockDataManagerConfig::getScriptHashPrefix();
         break;

      default:
         throw WalletException("unsupported address entry type");
      }

      bool updateWallet = false;

      auto&& countmap = swigWallet_->getAddrTxnCountsFromDB();

      for (auto count : countmap)
      {
         if (count.first.getSize() == 0)
            continue;

         //save count
         countMap_[count.first] = count.second;

         //figure out address type
         auto prefix = count.first.getPtr();

         if (*prefix == wltAddrPrefix)
            continue;

         //not the default prefix, let's fetch the asset
         auto assetIndex = wallet_->getAssetIndexForAddr(count.first);
         auto asset = wallet_->getAssetForIndex(assetIndex);
         /*if (asset->getAddrType() != AddressEntryType_Default)
            continue;*/

         auto hashType = asset->getAddressTypeForHash(
            count.first.getSliceRef(1, count.first.getSize() - 1));
         updateWallet = asset->setAddressEntryType(hashType);
      }

      if (updateWallet)
         wallet_->update();

      return countMap_;
   }
   
   map<BinaryData, vector<uint64_t>> getAddrBalancesFromDB(void)
   {

      auto&& balancemap = swigWallet_->getAddrBalancesFromDB();

      for (auto& balVec : balancemap)
      {
         if (balVec.first.getSize() == 0)
            continue;

         //save balance
         balanceMap_[balVec.first] = balVec.second;
      }

      return balanceMap_;
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

   BinaryData getNestedAddressForIndex(unsigned chainIndex)
   {
      return wallet_->getNestedAddressForIndex(chainIndex);
   }

   void extendAddressChain(unsigned count)
   {
      wallet_->extendChain(count);
   }

   bool extendAddressChainTo(unsigned count)
   {
      return wallet_->extendChainTo(count);
   }

   bool hasScrAddr(const BinaryData& scrAddr)
   {
      return wallet_->hasScrAddr(scrAddr);
   }

   unsigned getAssetIndexForAddr(const BinaryData& scrAddr)
   {
      return wallet_->getAssetIndexForAddr(scrAddr);
   }

   const BinaryData& getP2SHScriptForHash(const BinaryData& script)
   {
      return wallet_->getP2SHScriptForHash(script);
   }

   AddressType getAddrTypeForIndex(int index)
   {
      auto addrType = wallet_->getAddrTypeForIndex(index);

      AddressType type;
      switch (addrType)
      {
      case AddressEntryType_P2PKH:
         type = AddressType_P2PKH;
         break;

      case AddressEntryType_P2SH:
      case AddressEntryType_Nested_P2SH:
         type = AddressType_P2SH;
         break;

      default:
         throw WalletException("invalid address type");
      }

      return type;
   }

   SwigClient::ScrAddrObj getAddrObjByIndex(int index)
   {
      auto addrPtr = wallet_->getAddressEntryForIndex(index);

      uint64_t full = 0, spend = 0, unconf = 0;
      auto balanceIter = balanceMap_.find(addrPtr->getPrefixedHash());
      if (balanceIter != balanceMap_.end())
      {
         full = balanceIter->second[0];
         spend = balanceIter->second[1];
         unconf = balanceIter->second[2];
      }

      uint32_t count = 0;
      auto countIter = countMap_.find(addrPtr->getPrefixedHash());
      if (countIter != countMap_.end())
         count = countIter->second;


      if (swigWallet_ != nullptr)
      {
         SwigClient::ScrAddrObj saObj(
            swigWallet_.get(), addrPtr->getAddress(), index,
            full, spend, unconf, count);
         saObj.addrHash_ = addrPtr->getPrefixedHash();

         return saObj;
      }
      else
      {
         SwigClient::ScrAddrObj saObj(
            addrPtr->getAddress(), addrPtr->getPrefixedHash(), index);

         return saObj;
      }
   }
};

////////////////////////////////////////////////////////////////////////////////
class PythonSigner
{
   friend class ResolvedFeed_PythonWalletSingle;

private:
   unique_ptr<Signer> signer_;
   shared_ptr<AssetWallet> walletPtr_;
   shared_ptr<ResolvedFeed_PythonWalletSingle> feedPtr_;

public:
   PythonSigner(WalletContainer& wltContainer)
   {
      walletPtr_ = wltContainer.wallet_;
      signer_ = make_unique<Signer>();
      signer_->setFlags(SCRIPT_VERIFY_SEGWIT);

      //create feed
      auto walletSingle = dynamic_pointer_cast<AssetWallet_Single>(walletPtr_);
      if (walletSingle == nullptr)
         throw WalletException("unexpected wallet type");

      feedPtr_ = make_shared<ResolvedFeed_PythonWalletSingle>(
         walletSingle, this);

   }

   void addSpender(
      uint64_t value, 
      uint32_t height, uint16_t txindex, uint16_t outputIndex, 
      const BinaryData& txHash, const BinaryData& script)
   {
      UTXO utxo(value, height, txindex, outputIndex, txHash, script);

      //set spenders
      signer_->addSpender(make_shared<ScriptSpender>(utxo, feedPtr_));
   }

   void addRecipient(const BinaryData& script, uint64_t value)
   {
      auto txOutRef = BtcUtils::getTxOutScrAddrNoCopy(script);

      auto p2pkh_prefix =
        SCRIPT_PREFIX(BlockDataManagerConfig::getPubkeyHashPrefix());
      auto p2sh_prefix =
         SCRIPT_PREFIX(BlockDataManagerConfig::getScriptHashPrefix());

      shared_ptr<ScriptRecipient> recipient;
      if (txOutRef.type_ == p2pkh_prefix)
         recipient = make_shared<Recipient_P2PKH>(txOutRef.scriptRef_, value);
      else if (txOutRef.type_ == p2sh_prefix)
         recipient = make_shared<Recipient_P2SH>(txOutRef.scriptRef_, value);
      else
         throw WalletException("unexpected output type");

      signer_->addRecipient(recipient);
   }

   void signTx(void)
   {
      signer_->sign();
      if (!signer_->verify())
         throw runtime_error("failed signature");
   }

   BinaryData getSignedTx(void)
   {
      BinaryData finalTx(signer_->serialize());
      return finalTx;
   }

   virtual ~PythonSigner(void) = 0;
   virtual const SecureBinaryData& getPrivateKeyForIndex(unsigned) = 0;
};

////////////////////////////////////////////////////////////////////////////////
class ResolvedFeed_PythonWalletSingle : public ResolvedFeed_AssetWalletSingle
{
private:
   PythonSigner* signerPtr_ = nullptr;

public:
   ResolvedFeed_PythonWalletSingle(
      shared_ptr<AssetWallet_Single> walletPtr,
      PythonSigner* signerptr) :
      ResolvedFeed_AssetWalletSingle(walletPtr),
      signerPtr_(signerptr)
   {
      if (signerPtr_ == nullptr)
         throw WalletException("null signer ptr");
   }

   const SecureBinaryData& getPrivKeyForPubkey(const BinaryData& pubkey)
   {
      auto pubkeyref = BinaryDataRef(pubkey);
      auto iter = pubkey_to_privkeyAsset_.find(pubkeyref);
      if (iter == pubkey_to_privkeyAsset_.end())
         throw runtime_error("invalid value");


      return signerPtr_->getPrivateKeyForIndex(iter->second->getId());
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