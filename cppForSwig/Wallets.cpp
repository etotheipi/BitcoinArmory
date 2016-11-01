////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2016, goatpig                                               //
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#include "Wallets.h"
#include "BlockDataManagerConfig.h"

const string AssetWallet::walletDbName_ = "assetWallet";

////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
//// AssetWallet
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
shared_ptr<AssetWallet> AssetWallet::openWalletFile(const string& path)
{
   LMDBEnv* env = new LMDBEnv();
   env->open(path);

   auto wltPtr = make_shared<AssetWallet>(env);
   return wltPtr;
}

////////////////////////////////////////////////////////////////////////////////
shared_ptr<AssetWallet> AssetWallet::createWalletFromPrivateRoot(
   shared_ptr<DerivationScheme> derScheme,
   AssetEntryType defaultAssetType,
   AddressEntryType defaultAddressType,
   SecureBinaryData&& privateRoot,
   BinaryData parentID,
   unsigned lookup)
{
   //compute wallet ID
   auto&& pubkey = CryptoECDSA().ComputePublicKey(privateRoot);
   auto&& walletID = BtcUtils::getWalletID(pubkey);
   
   //set parentID to walletID if it's empty
   if (parentID.getSize() == 0)
      parentID = walletID;

   //create wallet file
   stringstream pathSS;
   string walletIDStr(walletID.getCharPtr(), walletID.getSize());
   pathSS << "armory_" << walletIDStr << "_wallet.lmdb";
   auto walletPtr = openWalletFile(pathSS.str());

   //create root AssetEntry
   auto rootAssetEntry = AssetEntry::createFromRawData(defaultAssetType,
      move(pubkey), move(privateRoot));

   //if derScheme is empty, use hardcoded option instead
   if (derScheme == nullptr)
   {
      auto&& chaincode = BtcUtils::computeChainCode_Armory135(privateRoot);
      derScheme = make_shared<DerivationScheme_ArmoryLegacy>(move(chaincode));
   }

   /**insert the original entries**/

   LMDBEnv::Transaction tx(walletPtr->dbEnv_, LMDB::ReadWrite);

   {
      //parent ID
      BinaryWriter bwKey;
      bwKey.put_uint32_t(PARENTID_KEY);

      BinaryWriter bwData;
      bwData.put_var_int(parentID.getSize());
      bwData.put_BinaryData(parentID);

      walletPtr->putData(bwKey, bwData);
   }

   {
      //wallet ID
      BinaryWriter bwKey;
      bwKey.put_uint32_t(WALLETID_KEY);

      BinaryWriter bwData;
      bwData.put_var_int(walletID.getSize());
      bwData.put_BinaryData(walletID);

      walletPtr->putData(bwKey, bwData);
   }

   {
      //derivation scheme
      BinaryWriter bwKey;
      bwKey.put_uint32_t(DERIVATIONSCHEME_KEY);

      auto&& data = derScheme->serialize();
      walletPtr->putData(bwKey.getData(), data);
   }

   {
      //default AddressEntryType
      BinaryWriter bwKey;
      bwKey.put_uint32_t(ADDRESSTYPEENTRY_KEY);

      BinaryWriter bwData;
      bwData.put_var_int(1);
      bwData.put_uint8_t(defaultAddressType);
      
      walletPtr->putData(bwKey, bwData);
   }

   {
      //top used index
      BinaryWriter bwKey;
      bwKey.put_uint32_t(TOPUSEDINDEX_KEY);

      BinaryWriter bwData;
      bwData.put_var_int(4);
      bwData.put_int32_t(0);

      walletPtr->putData(bwKey, bwData);
   }

   {
      //root asset
      BinaryWriter bwKey;
      bwKey.put_uint32_t(ROOTASSET_KEY);

      auto&& data = rootAssetEntry->serialize();

      walletPtr->putData(bwKey.getData(), data);
   }

   {
      auto topEntryPtr = rootAssetEntry;

      if (lookup == UINT32_MAX)
         lookup = DERIVATION_LOOKUP;

      //derivation lookup
      for (unsigned i = 0; i < lookup; i++)
      {
         auto nextEntryPtr = derScheme->getNextAsset(topEntryPtr);
         walletPtr->writeAssetEntry(nextEntryPtr);

         topEntryPtr = nextEntryPtr;
      }
   }

   //init walletptr from file
   walletPtr->readFromFile();

   return walletPtr;
}

////////////////////////////////////////////////////////////////////////////////
BinaryDataRef AssetWallet::getDataRefForKey(const BinaryData& key) const
{
   /** The reference lifetime is tied to the db tx lifetime. The caller has to
   maintain the tx for as long as the data ref needs to be valid **/

   CharacterArrayRef keyRef(key.getSize(), key.getPtr());
   auto ref = db_->get_NoCopy(keyRef);

   if (ref.data == nullptr)
      throw NoEntryInWalletException();

   BinaryRefReader brr((const uint8_t*)ref.data, ref.len);
   auto len = brr.get_var_int();
   if (len != brr.getSizeRemaining())
      throw WalletException("on disk data length mismatch");

   return brr.get_BinaryDataRef(brr.getSizeRemaining());
}

////////////////////////////////////////////////////////////////////////////////
void AssetWallet::readFromFile()
{
   //sanity check
   if (dbEnv_ == nullptr || db_ == nullptr)
      throw WalletException("uninitialized wallet object");

   LMDBEnv::Transaction tx(dbEnv_, LMDB::ReadOnly);

   {
      //parentId
      BinaryWriter bwKey;
      bwKey.put_uint32_t(PARENTID_KEY);

      try
      {
         auto parentIdRef = getDataRefForKey(bwKey.getData());
         parentID_ = parentIdRef;
      }
      catch (NoEntryInWalletException&)
      {
         //empty wallet, return
         return;
      }
   }

   {
      //walletId
      BinaryWriter bwKey;
      bwKey.put_uint32_t(WALLETID_KEY);
      auto walletIdRef = getDataRefForKey(bwKey.getData());

      walletID_ = walletIdRef;
   }

   {
      //derivation scheme
      BinaryWriter bwKey;
      bwKey.put_uint32_t(DERIVATIONSCHEME_KEY);
      auto derSchemeRef = getDataRefForKey(bwKey.getData());

      auto derScheme_ = DerivationScheme::deserialize(derSchemeRef);
   }

   {
      //default AddressEntryType
      BinaryWriter bwKey;
      bwKey.put_uint32_t(ADDRESSTYPEENTRY_KEY);
      auto defaultAetRef = getDataRefForKey(bwKey.getData());

      if (defaultAetRef.getSize() != 1)
         throw WalletException("invalid aet length");

      default_aet_ = (AddressEntryType)*defaultAetRef.getPtr();
   }

   {
      //top used index
      BinaryWriter bwKey;
      bwKey.put_uint32_t(TOPUSEDINDEX_KEY);
      auto topIndexRef = getDataRefForKey(bwKey.getData());

      if (topIndexRef.getSize() != 4)
         throw WalletException("invalid topindex length");

      BinaryRefReader brr(topIndexRef);
      highestUsedAddressIndex_.store(brr.get_int32_t(), memory_order_relaxed);
   }

   {
      //root asset
      BinaryWriter bwKey;
      bwKey.put_uint32_t(ROOTASSET_KEY);
      auto rootAssetRef = getDataRefForKey(bwKey.getData());

      root_ = AssetEntry::deserDBValue(-1, rootAssetRef);
   }

   {
      //asset entries
      auto dbIter = db_->begin();

      BinaryWriter bwKey;
      bwKey.put_uint8_t(ASSETENTRY_PREFIX);
      CharacterArrayRef keyRef(bwKey.getSize(), bwKey.getData().getPtr());

      dbIter.seek(keyRef, LMDB::Iterator::Seek_GE);

      while (dbIter.isValid())
      {
         auto iterkey = dbIter.key();
         auto itervalue = dbIter.value();

         BinaryDataRef keyBDR((uint8_t*)iterkey.mv_data, iterkey.mv_size);
         BinaryDataRef valueBDR((uint8_t*)itervalue.mv_data, itervalue.mv_size);

         //check value's advertized size is packet size and strip it
         BinaryRefReader brrVal(valueBDR);
         auto valsize = brrVal.get_var_int();
         if (valsize != brrVal.getSizeRemaining())
            throw WalletException("entry val size mismatch");
         
         try
         {
            auto entryPtr = AssetEntry::deserialize(keyBDR, 
               brrVal.get_BinaryDataRef(brrVal.getSizeRemaining()));
            entries_.insert(make_pair(entryPtr->getId(), entryPtr));
         }
         catch (AssetDeserException& e)
         {
            LOGERR << e.what();
            break;
         }

         dbIter.advance();
      }
   }
}


////////////////////////////////////////////////////////////////////////////////
void AssetWallet::putData(const BinaryData& key, const BinaryData& data)
{
   /** the caller is responsible for the db transaction **/

   CharacterArrayRef keyRef(key.getSize(), key.getPtr());
   CharacterArrayRef dataRef(data.getSize(), data.getPtr());

   db_->insert(keyRef, dataRef);
}

////////////////////////////////////////////////////////////////////////////////
void AssetWallet::putData(BinaryWriter& key, BinaryWriter& data)
{
   putData(key.getData(), data.getData());
}

////////////////////////////////////////////////////////////////////////////////
unsigned AssetWallet::getAndBumpHighestUsedIndex()
{
   LMDBEnv::Transaction tx(dbEnv_, LMDB::ReadWrite);

   auto index = highestUsedAddressIndex_.fetch_add(1, memory_order_relaxed);

   BinaryWriter bwKey;
   bwKey.put_uint32_t(TOPUSEDINDEX_KEY);

   BinaryWriter bwData;
   bwData.put_var_int(4);
   bwData.put_int32_t(highestUsedAddressIndex_.load(memory_order_relaxed));

   putData(bwKey, bwData);

   return index;
}

////////////////////////////////////////////////////////////////////////////////
shared_ptr<AddressEntry> AssetWallet::getNewAddress()
{
   shared_ptr<AddressEntry> aePtr = nullptr;

   //increment top used address counter & update
   auto index = getAndBumpHighestUsedIndex();

   //lock
   unique_lock<mutex> walletLock(walletMutex_);

   //check look up
   auto entryIter = entries_.find(index);
   if (entryIter != entries_.end())
   {
      auto addrIter = addresses_.find(index);
      if (addrIter != addresses_.end())
         return addrIter->second;

      aePtr = getAddressEntryForAsset(entryIter->second, default_aet_);
   }
   else
   {
      //not in look up, compute it
      auto topIter = entries_.rbegin();
      auto topIndex = topIter->first;
      auto topEntry = topIter->second;

      while (topIndex < index)
      {
         auto newEntry = getNextAsset(topEntry);

         writeAssetEntry(newEntry);

         entries_.insert(make_pair(++topIndex, newEntry));
         topEntry = newEntry;
      }

      aePtr = getAddressEntryForAsset(topEntry, default_aet_);
   }

   //insert new entry
   addresses_[aePtr->getIndex()] = aePtr;

   return aePtr;
}

////////////////////////////////////////////////////////////////////////////////
shared_ptr<AddressEntry> AssetWallet::getAddressEntryForAsset(
   shared_ptr<AssetEntry> assetPtr, AddressEntryType ae_type)
{
   shared_ptr<AddressEntry> aePtr = nullptr;

   switch (ae_type)
   {
   case AddressEntryType_P2PKH:
      aePtr = make_shared<AddressEntryP2PKH>(assetPtr);
      break;

   case AddressEntryType_P2WPKH:
      aePtr = make_shared<AddressEntryP2WPKH>(assetPtr);
      break;

   default:
      throw WalletException("unsupported address entry type");
   }

   return aePtr;
}

////////////////////////////////////////////////////////////////////////////////
shared_ptr<AssetEntry> AssetWallet::getNextAsset(
   shared_ptr<AssetEntry> assetPtr)
{
   return derScheme_->getNextAsset(assetPtr);
}

////////////////////////////////////////////////////////////////////////////////
void AssetWallet::writeAssetEntry(shared_ptr<AssetEntry> entryPtr)
{
   auto&& serializedEntry = entryPtr->serialize();
   auto&& dbKey = entryPtr->getDbKey();

   CharacterArrayRef keyRef(dbKey.getSize(), dbKey.getPtr());
   CharacterArrayRef dataRef(serializedEntry.getSize(), serializedEntry.getPtr());

   LMDBEnv::Transaction(dbEnv_, LMDB::ReadWrite);
   db_->insert(keyRef, dataRef);
}

////////////////////////////////////////////////////////////////////////////////
vector<BinaryData> AssetWallet::getHash160Vec(void) const
{
   vector<BinaryData> h160Vec;

   for (auto& entry : entries_)
   {
      BinaryWriter bw;
      bw.put_uint8_t(SCRIPT_PREFIX_HASH160);
      bw.put_BinaryData(entry.second->getHash160());

      h160Vec.push_back(move(bw.getData()));
   }

   return h160Vec;
}

////////////////////////////////////////////////////////////////////////////////
string AssetWallet::getID(void) const
{
   return string(walletID_.getCharPtr(), walletID_.getSize());
}


////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
//// DerivationScheme
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
DerivationScheme::~DerivationScheme() 
{}

////////////////////////////////////////////////////////////////////////////////
shared_ptr<DerivationScheme> DerivationScheme::deserialize(BinaryDataRef data)
{
   BinaryRefReader brr(data);

   //get derivation scheme type
   auto schemeType = brr.get_uint8_t();

   shared_ptr<DerivationScheme> derScheme;

   switch (schemeType)
   {
   case DERIVATIONSCHEME_LEGACY:
   {
      //get chaincode;
      auto len = brr.get_var_int();
      auto&& chainCode = SecureBinaryData(brr.get_BinaryDataRef(len));
      derScheme = make_shared<DerivationScheme_ArmoryLegacy>(move(chainCode));

      break;
   }

   default:
      throw DerivationSchemeDeserException("unsupported derscheme type");
   }

   return derScheme;
}

////////////////////////////////////////////////////////////////////////////////
shared_ptr<AssetEntry> DerivationScheme_ArmoryLegacy::getNextAsset(
   shared_ptr<AssetEntry> assetPtr)
{
   auto getRawData = [](shared_ptr<Asset> asset)->SecureBinaryData
   {
      try
      {
         auto keyData = asset->getData();
         return keyData;
      }
      catch (AssetEncryptedException&)
      {
         //TODO: implement decryption process
         throw NeedsDecrypted();
      }
   };

   //get pubkey
   auto pubkey = assetPtr->getPubKey();
   auto&& pubkeyData = getRawData(pubkey);

   auto&& nextPubkey = CryptoECDSA().ComputeChainedPublicKey(
      pubkeyData, chainCode_, nullptr);

   //try to get priv key
   SecureBinaryData nextPrivkey;
   try
   {
      auto privkey = assetPtr->getPrivKey();
      auto&& privkeyData = getRawData(privkey);

      nextPrivkey = move(CryptoECDSA().ComputeChainedPrivateKey(
         privkeyData, chainCode_, pubkeyData, nullptr));
   }
   catch (AssetUnavailableException&)
   {
      //no priv key, ignore
   }
   catch (NeedsDecrypted&)
   {
      //ignore, not going to prompt user for password with priv key derivation
   }

   //no need to encrypt the new data, asset ctor will deal with it
   return assetPtr->getNewAsset(move(nextPubkey), move(nextPrivkey));
}

////////////////////////////////////////////////////////////////////////////////
BinaryData DerivationScheme_ArmoryLegacy::serialize() const
{
   BinaryWriter bw;
   bw.put_uint8_t(DERIVATIONSCHEME_LEGACY);
   bw.put_var_int(chainCode_.getSize());
   bw.put_BinaryData(chainCode_);

   BinaryWriter final;
   final.put_var_int(bw.getSize());
   final.put_BinaryData(bw.getData());

   return final.getData();
}

////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
//// AddressEntry
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
AddressEntry::~AddressEntry()
{}

////////////////////////////////////////////////////////////////////////////////
const BinaryData& AddressEntryP2PKH::getAddress() const
{
   if (address_.getSize() == 0)
   {
      auto& h160 = asset_->getHash160();

      //get and prepend network byte
      auto networkByte = BlockDataManagerConfig::getPubkeyHashPrefix();

      BinaryData addr160;
      addr160.append(networkByte);

      //b58 encode
      address_ = move(BtcUtils::scrAddrToBase58(addr160));
   }

   return address_;
}

////////////////////////////////////////////////////////////////////////////////
shared_ptr<ScriptRecipient> AddressEntryP2PKH::getRecipient(
   uint64_t value) const
{
   auto& h160 = asset_->getHash160();
   return make_shared<Recipient_P2PKH>(h160, value);
}

////////////////////////////////////////////////////////////////////////////////
const BinaryData& AddressEntryP2WPKH::getAddress() const
{
   if (address_.getSize() == 0)
   {
      //no address standard for SW yet, consider BIP142
      address_ = asset_->getHash160();
   }

   return address_;
}

////////////////////////////////////////////////////////////////////////////////
shared_ptr<ScriptRecipient> AddressEntryP2WPKH::getRecipient(
   uint64_t value) const
{
   auto& h160 = asset_->getHash160();
   return make_shared<Recipient_P2WPKH>(h160, value);
}


////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
//// Asset
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
Asset::~Asset()
{}

////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
//// AssetEntry
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
AssetEntry::~AssetEntry(void)
{}

////////////////////////////////////////////////////////////////////////////////
const BinaryData& AssetEntry_PubPub::getHash160() const
{
   if (h160_.getSize() == 0)
      h160_ = move(BtcUtils::getHash160(pubkey_->getData()));

   return h160_;
}

////////////////////////////////////////////////////////////////////////////////
shared_ptr<AssetEntry> AssetEntry::createFromRawData(
   AssetEntryType type, SecureBinaryData&& pub, SecureBinaryData&& priv,
   int index)
{
   shared_ptr<AssetEntry> aePtr;

   switch (type)
   {
   case AssetEntryType_PubPub:
   {
      aePtr = make_shared<AssetEntry_PubPub>(index, move(pub), move(priv));
      break;
   }

   default:
      throw WalletException("unsupported AssetEntry type");
   }

   return aePtr;
}

////////////////////////////////////////////////////////////////////////////////
BinaryData AssetEntry::getDbKey() const
{
   BinaryWriter bw;
   bw.put_uint8_t(ASSETENTRY_PREFIX);
   bw.put_int32_t(index_);

   return bw.getData();
}

////////////////////////////////////////////////////////////////////////////////
shared_ptr<AssetEntry> AssetEntry::deserialize(
   BinaryDataRef key, BinaryDataRef value)
{
   BinaryRefReader brrKey(key);

   auto prefix = brrKey.get_uint8_t();
   if (prefix != ASSETENTRY_PREFIX)
      throw AssetDeserException("invalid prefix");

   auto index = brrKey.get_int32_t();

   return deserDBValue(index, value);
}

////////////////////////////////////////////////////////////////////////////////
shared_ptr<AssetEntry> AssetEntry::deserDBValue(int index, BinaryDataRef value)
{
   SecureBinaryData privKey;
   SecureBinaryData pubKey;

   vector<BinaryDataRef> dataVec;
   BinaryRefReader brrVal(value);

   auto entryType = (AssetEntryType)brrVal.get_uint8_t();

   while (brrVal.getSizeRemaining() > 0)
   {
      auto len = brrVal.get_var_int();
      auto valref = brrVal.get_BinaryDataRef(len);

      dataVec.push_back(valref);
   }

   for (auto& dataRef : dataVec)
   {
      BinaryRefReader brrData(dataRef);
      auto keybyte = brrData.get_uint8_t();

      switch (keybyte)
      {
      case PUBKEY_PLAINTEXT_BYTE:
      {
         if (pubKey.getSize() != 0)
            throw AssetDeserException("multiple pub keys for entry");

         pubKey = move(SecureBinaryData(
            brrData.get_BinaryDataRef(
            brrData.getSizeRemaining())));
         
         break;
      }

      case PRIVKEY_PLAINTEXT_BYTE:
      {
         if (privKey.getSize() != 0)
            throw AssetDeserException("multiple pub keys for entry");

         privKey = move(SecureBinaryData(
            brrData.get_BinaryDataRef(
            brrData.getSizeRemaining())));
         
         break;
      }

      default:
         throw AssetDeserException("unknown key type byte");
      }
   }

   //TODO: add IVs as args for encrypted entries
   return createFromRawData(entryType, move(pubKey), move(privKey), index);
}

////////////////////////////////////////////////////////////////////////////////
BinaryData AssetEntry_PubPub::serialize() const
{
   BinaryWriter bw;
   bw.put_uint8_t(getType());

   auto& pubkeyData = pubkey_->getData();
   bw.put_var_int(pubkeyData.getSize() + 1);
   bw.put_uint8_t(PUBKEY_PLAINTEXT_BYTE);
   bw.put_BinaryData(pubkeyData);
   
   auto& privkeyData = privkey_->getData();
   bw.put_var_int(privkeyData.getSize() + 1);
   bw.put_uint8_t(PRIVKEY_PLAINTEXT_BYTE);
   bw.put_BinaryData(privkeyData);

   BinaryWriter finalBw;

   finalBw.put_var_int(bw.getSize());
   finalBw.put_BinaryData(bw.getData());

   return finalBw.getData();
}
