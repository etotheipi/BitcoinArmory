////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2016, goatpig                                               //
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#include "Wallets.h"
#include "BlockDataManagerConfig.h"
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
//// WalletMeta
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
WalletMeta::~WalletMeta()
{}

////////////////////////////////////////////////////////////////////////////////
BinaryData WalletMeta::getDbKey()
{
   if (walletID_.getSize() == 0)
      throw WalletException("empty master ID");

   BinaryWriter bw;
   bw.put_uint8_t(WALLETMETA_PREFIX);
   bw.put_BinaryData(walletID_);

   return bw.getData();
}

////////////////////////////////////////////////////////////////////////////////
BinaryData WalletMeta_Single::serialize() const
{
   BinaryWriter bw;
   bw.put_var_int(4);
   bw.put_uint32_t(type_);

   return bw.getData();
}

////////////////////////////////////////////////////////////////////////////////
bool WalletMeta_Single::shouldLoad() const
{
   return true;
}

////////////////////////////////////////////////////////////////////////////////
BinaryData WalletMeta_Multisig::serialize() const
{
   BinaryWriter bw;
   bw.put_var_int(4);
   bw.put_uint32_t(type_);

   return bw.getData();
}

////////////////////////////////////////////////////////////////////////////////
bool WalletMeta_Multisig::shouldLoad() const
{
   return true;
}

////////////////////////////////////////////////////////////////////////////////
BinaryData WalletMeta_Subwallet::serialize() const
{
   BinaryWriter bw;
   bw.put_var_int(4);
   bw.put_uint32_t(type_);

   return bw.getData();
}

////////////////////////////////////////////////////////////////////////////////
bool WalletMeta_Subwallet::shouldLoad() const
{
   return false;
}

////////////////////////////////////////////////////////////////////////////////
shared_ptr<WalletMeta> WalletMeta::deserialize(
   shared_ptr<LMDBEnv> env, BinaryDataRef key, BinaryDataRef val)
{
   if (key.getSize() < 2)
      throw WalletException("invalid meta key");

   BinaryRefReader brrKey(key);
   auto prefix = brrKey.get_uint8_t();
   if (prefix != WALLETMETA_PREFIX)
      throw WalletException("invalid wallet meta prefix");

   string dbname((char*)brrKey.getCurrPtr(), brrKey.getSizeRemaining());

   BinaryRefReader brrVal(val);
   auto wltType = (WalletMetaType)brrVal.get_uint32_t();

   shared_ptr<WalletMeta> wltMetaPtr;

   switch (wltType)
   {
   case WalletMetaType_Single:
   {
      wltMetaPtr = make_shared<WalletMeta_Single>(env);
      break;
   }

   case WalletMetaType_Subwallet:
   {
      wltMetaPtr = make_shared<WalletMeta_Subwallet>(env);
      break;
   }

   case WalletMetaType_Multisig:
   {
      wltMetaPtr = make_shared<WalletMeta_Multisig>(env);
      break;
   }

   default:
      throw WalletException("invalid wallet type");
   }

   wltMetaPtr->dbName_ = move(dbname);
   wltMetaPtr->walletID_ = brrKey.get_BinaryData(brrKey.getSizeRemaining());
   return wltMetaPtr;
}


////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
//// AssetWallet
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
shared_ptr<AssetWallet_Single> AssetWallet_Single::
createFromPrivateRoot_Armory135(
   const string& folder,
   AddressEntryType defaultAddressType,
   SecureBinaryData&& privateRoot,
   unsigned lookup)
{
   //compute wallet ID
   auto&& pubkey = CryptoECDSA().ComputePublicKey(privateRoot);
   
   //compute master ID as hmac256(root pubkey, "MetaEntry")
   string hmacMasterMsg("MetaEntry");
   auto&& masterID_long = BtcUtils::getHMAC256(
      pubkey, SecureBinaryData(hmacMasterMsg));
   auto&& masterID = BtcUtils::computeID(masterID_long);
   string masterIDStr(masterID.getCharPtr(), masterID.getSize());

   //create wallet file and dbenv
   stringstream pathSS;
   pathSS << folder << "/armory_" << masterIDStr << "_wallet.lmdb";
   auto dbenv = getEnvFromFile(pathSS.str(), 2);

   initWalletMetaDB(dbenv, masterIDStr);

   auto wltMetaPtr = make_shared<WalletMeta_Single>(dbenv);
   wltMetaPtr->parentID_ = masterID;
   
   auto cypher = make_unique<Cypher_AES>();

   auto walletPtr = initWalletDb(
      wltMetaPtr,
      move(cypher),
      defaultAddressType, 
      move(privateRoot), lookup);

   //set as main
   {
      LMDB dbMeta;

      {
         dbMeta.open(dbenv.get(), WALLETMETA_DBNAME);

        LMDBEnv::Transaction metatx(dbenv.get(), LMDB::ReadWrite);
        setMainWallet(&dbMeta, wltMetaPtr);
      }

      dbMeta.close();
   }

   return walletPtr;
}

////////////////////////////////////////////////////////////////////////////////
shared_ptr<AssetWallet_Single> AssetWallet_Single::
createFromPublicRoot_Armory135(
   const string& folder,
   AddressEntryType defaultAddressType,
   SecureBinaryData&& pubRoot,
   SecureBinaryData&& chainCode,
   unsigned lookup)
{
   //compute master ID as hmac256(root pubkey, "MetaEntry")
   string hmacMasterMsg("MetaEntry");
   auto&& masterID_long = BtcUtils::getHMAC256(
      pubRoot, SecureBinaryData(hmacMasterMsg));
   auto&& masterID = BtcUtils::computeID(masterID_long);
   string masterIDStr(masterID.getCharPtr(), masterID.getSize());

   //create wallet file and dbenv
   stringstream pathSS;
   pathSS << folder << "/armory_" << masterIDStr << "_wallet.lmdb";
   auto dbenv = getEnvFromFile(pathSS.str(), 2);

   initWalletMetaDB(dbenv, masterIDStr);

   auto wltMetaPtr = make_shared<WalletMeta_Single>(dbenv);
   wltMetaPtr->parentID_ = masterID;

   auto walletPtr = initWalletDbFromPubRoot(
      wltMetaPtr,
      defaultAddressType,
      move(pubRoot), move(chainCode), 
      lookup);

   //set as main
   {
      LMDB dbMeta;

      {
         dbMeta.open(dbenv.get(), WALLETMETA_DBNAME);

         LMDBEnv::Transaction metatx(dbenv.get(), LMDB::ReadWrite);
         setMainWallet(&dbMeta, wltMetaPtr);
      }

      dbMeta.close();
   }

   return walletPtr;
}

////////////////////////////////////////////////////////////////////////////////
shared_ptr<AssetWallet> AssetWallet::loadMainWalletFromFile(const string& path)
{
   auto dbenv = getEnvFromFile(path.c_str(), 1);

   unsigned count;
   map<BinaryData, shared_ptr<WalletMeta>> metaMap;
   BinaryData masterID;
   BinaryData mainWalletID;

   {
      {
         //db count and names
         count = getDbCountAndNames(
            dbenv, metaMap, masterID, mainWalletID);

         //TODO: global kdf
      }
   }

   //close env, reopen env with proper count
   dbenv.reset();

   auto metaIter = metaMap.find(mainWalletID);
   if (metaIter == metaMap.end())
      throw WalletException("invalid main wallet id");

   auto mainWltMeta = metaIter->second;
   metaMap.clear();

   mainWltMeta->dbEnv_ = getEnvFromFile(path.c_str(), count + 1);
   
   shared_ptr<AssetWallet> wltPtr;

   switch (mainWltMeta->type_)
   {
   case WalletMetaType_Single:
   {
      auto wltSingle = make_shared<AssetWallet_Single>(
         mainWltMeta);
      wltSingle->readFromFile();

      wltPtr = wltSingle;
      break;
   }

   case WalletMetaType_Multisig:
   {
      auto wltMS = make_shared<AssetWallet_Multisig>(
         mainWltMeta);
      wltMS->readFromFile();

      wltPtr = wltMS;
      break;
   }

   default: 
      throw WalletException("unexpected main wallet type");
   }

   return wltPtr;
}

////////////////////////////////////////////////////////////////////////////////
void AssetWallet::putDbName(LMDB* db, shared_ptr<WalletMeta> wltMetaPtr)
{
   auto&& key = wltMetaPtr->getDbKey();
   auto&& val = wltMetaPtr->serialize();

   putData(db, key, val);
}

////////////////////////////////////////////////////////////////////////////////
void AssetWallet::setMainWallet(LMDB* db, shared_ptr<WalletMeta> wltMetaPtr)
{
   BinaryWriter bwKey;
   bwKey.put_uint32_t(MAINWALLET_KEY);

   BinaryWriter bwData;
   bwData.put_var_int(wltMetaPtr->walletID_.getSize());
   bwData.put_BinaryData(wltMetaPtr->walletID_);

   putData(db, bwKey.getData(), bwData.getData());
}

////////////////////////////////////////////////////////////////////////////////
void AssetWallet::initWalletMetaDB(
   shared_ptr<LMDBEnv> dbenv, const string& masterID)
{
   LMDB db;
   {
      db.open(dbenv.get(), WALLETMETA_DBNAME);

      BinaryWriter bwKey;
      bwKey.put_uint32_t(MASTERID_KEY);

      BinaryWriter bwData;
      bwData.put_var_int(masterID.size());

      BinaryDataRef idRef;
      idRef.setRef(masterID);
      bwData.put_BinaryDataRef(idRef);

      LMDBEnv::Transaction tx(dbenv.get(), LMDB::ReadWrite);
      putData(&db, bwKey.getData(), bwData.getData());
   }

   db.close();
}

////////////////////////////////////////////////////////////////////////////////
unsigned AssetWallet::getDbCountAndNames(shared_ptr<LMDBEnv> dbEnv,
   map<BinaryData, shared_ptr<WalletMeta>>& metaMap,
   BinaryData& masterID, BinaryData& mainWalletID)
{
   if (dbEnv == nullptr)
      throw WalletException("invalid dbenv");

   unsigned dbcount = 0;

   LMDB db;
   db.open(dbEnv.get(), WALLETMETA_DBNAME);

   {
      LMDBEnv::Transaction tx(dbEnv.get(), LMDB::ReadOnly);

      {
         //masterID
         BinaryWriter bwKey;
         bwKey.put_uint32_t(MASTERID_KEY);

         try
         {
            masterID = getDataRefForKey(bwKey.getData(), &db);
         }
         catch (NoEntryInWalletException&)
         {
            throw runtime_error("missing masterID entry");
         }
      }

      {
         //mainWalletID
         BinaryWriter bwKey;
         bwKey.put_uint32_t(MAINWALLET_KEY);

         try
         {
            mainWalletID = getDataRefForKey(bwKey.getData(), &db);
         }
         catch (NoEntryInWalletException&)
         {
            throw runtime_error("missing main wallet entry");
         }
      }

      //meta map
      auto dbIter = db.begin();

      BinaryWriter bwKey;
      bwKey.put_uint8_t(WALLETMETA_PREFIX);
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
            auto metaPtr = WalletMeta::deserialize(
               dbEnv,
               keyBDR,
               brrVal.get_BinaryDataRef(brrVal.getSizeRemaining()));

            dbcount++;
            if (metaPtr->shouldLoad())
               metaMap.insert(make_pair(
               metaPtr->getWalletID(), metaPtr));
         }
         catch (exception& e)
         {
            LOGERR << e.what();
            break;
         }

         dbIter.advance();
      }
   }

   db.close();
   return dbcount + 1;
}

////////////////////////////////////////////////////////////////////////////////
BinaryData AssetWallet_Single::computeWalletID(
   shared_ptr<DerivationScheme> derScheme,
   shared_ptr<AssetEntry> rootEntry)
{
   auto&& addrVec = derScheme->extendChain(rootEntry, 1);
   if (addrVec.size() != 1)
      throw WalletException("unexpected chain derivation output");

   auto firstEntry = dynamic_pointer_cast<AssetEntry_Single>(addrVec[0]);
   if (firstEntry == nullptr)
      throw WalletException("unexpected asset entry type");

   return BtcUtils::computeID(firstEntry->getPubKey()->getUncompressedKey());
}

////////////////////////////////////////////////////////////////////////////////
shared_ptr<AssetWallet_Single> AssetWallet_Single::initWalletDb(
   shared_ptr<WalletMeta> metaPtr,
   unique_ptr<Cypher> cypher,
   AddressEntryType addressType,
   SecureBinaryData&& privateRoot,
   unsigned lookup)
{
   //chaincode
   auto&& chaincode = BtcUtils::computeChainCode_Armory135(privateRoot);
   auto derScheme = make_shared<DerivationScheme_ArmoryLegacy>(move(chaincode));

   //create root AssetEntry
   auto&& pubkey = CryptoECDSA().ComputePublicKey(privateRoot);
   auto rootAssetEntry = make_shared<AssetEntry_Single>(-1,
      move(pubkey), move(privateRoot), move(cypher));

   //compute wallet ID if it is missing
   if (metaPtr->walletID_.getSize() == 0)
      metaPtr->walletID_ = move(computeWalletID(derScheme, rootAssetEntry));
   
   if (metaPtr->dbName_.size() == 0)
   {
      string walletIDStr(metaPtr->getWalletIDStr());
      metaPtr->dbName_ = walletIDStr;
   }

   auto walletPtr = make_shared<AssetWallet_Single>(metaPtr);

   {
      LMDB metadb;

      {
         metadb.open(walletPtr->dbEnv_.get(), WALLETMETA_DBNAME);

         LMDBEnv::Transaction tx(walletPtr->dbEnv_.get(), LMDB::ReadWrite);
         putDbName(&metadb, metaPtr);
      }

      metadb.close();
   }


   /**insert the original entries**/
   LMDBEnv::Transaction tx(walletPtr->dbEnv_.get(), LMDB::ReadWrite);
   walletPtr->putHeaderData(
      metaPtr->parentID_, metaPtr->walletID_, derScheme, addressType, 0);

   {
      //root asset
      BinaryWriter bwKey;
      bwKey.put_uint32_t(ROOTASSET_KEY);

      auto&& data = rootAssetEntry->serialize();

      walletPtr->putData(bwKey.getData(), data);
   }
   
   //init walletptr from file
   walletPtr->readFromFile();

   {
      //asset lookup
      auto topEntryPtr = rootAssetEntry;

      if (lookup == UINT32_MAX)
         lookup = DERIVATION_LOOKUP;

      walletPtr->extendChain(rootAssetEntry, lookup);
   }

   return walletPtr;
}

////////////////////////////////////////////////////////////////////////////////
shared_ptr<AssetWallet_Single> AssetWallet_Single::initWalletDbFromPubRoot(
   shared_ptr<WalletMeta> metaPtr,
   AddressEntryType addressType,
   SecureBinaryData&& pubRoot,
   SecureBinaryData&& chainCode,
   unsigned lookup)
{
   //derScheme
   auto derScheme = make_shared<DerivationScheme_ArmoryLegacy>(move(chainCode));

   //create root AssetEntry
   auto rootAssetEntry = make_shared<AssetEntry_Single>(-1,
      move(pubRoot), move(SecureBinaryData()), nullptr);

   //compute wallet ID
   if (metaPtr->walletID_.getSize() == 0)
      metaPtr->walletID_ = move(computeWalletID(derScheme, rootAssetEntry));

   if (metaPtr->dbName_.size() == 0)
   {
      string walletIDStr(metaPtr->getWalletIDStr());
      metaPtr->dbName_ = walletIDStr;
   }

   auto walletPtr = make_shared<AssetWallet_Single>(metaPtr);

   {
      LMDB metadb;

      {
         metadb.open(walletPtr->dbEnv_.get(), WALLETMETA_DBNAME);

         LMDBEnv::Transaction tx(walletPtr->dbEnv_.get(), LMDB::ReadWrite);
         putDbName(&metadb, metaPtr);
      }

      metadb.close();
   }

   /**insert the original entries**/
   LMDBEnv::Transaction tx(walletPtr->dbEnv_.get(), LMDB::ReadWrite);
   walletPtr->putHeaderData(
      metaPtr->parentID_, metaPtr->walletID_, derScheme, addressType, 0);

   {
      //root asset
      BinaryWriter bwKey;
      bwKey.put_uint32_t(ROOTASSET_KEY);

      auto&& data = rootAssetEntry->serialize();

      walletPtr->putData(bwKey.getData(), data);
   }

   //init walletptr from file
   walletPtr->readFromFile();

   {
      //asset lookup
      auto topEntryPtr = rootAssetEntry;

      if (lookup == UINT32_MAX)
         lookup = DERIVATION_LOOKUP;

      walletPtr->extendChain(rootAssetEntry, lookup);
   }

   return walletPtr;
}

////////////////////////////////////////////////////////////////////////////////
void AssetWallet_Single::putHeaderData(const BinaryData& parentID,
   const BinaryData& walletID,
   shared_ptr<DerivationScheme> derScheme,
   AddressEntryType aet, int topUsedIndex)
{
   LMDBEnv::Transaction tx(dbEnv_.get(), LMDB::ReadWrite);

   {
      //wallet type
      BinaryWriter bwKey;
      bwKey.put_uint32_t(WALLETTYPE_KEY);

      BinaryWriter bwData;
      bwData.put_var_int(4);
      bwData.put_uint32_t(WalletMetaType_Single);

      putData(bwKey, bwData);
   }

   AssetWallet::putHeaderData(parentID, walletID, derScheme, aet, topUsedIndex);
}

////////////////////////////////////////////////////////////////////////////////
shared_ptr<AssetWallet_Multisig> AssetWallet_Multisig::createFromPrivateRoot(
   const string& folder,
   AddressEntryType aet,
   unsigned M, unsigned N,
   SecureBinaryData&& privateRoot,
   unsigned lookup)
{
   if (aet != AddressEntryType_Nested_Multisig && 
       aet != AddressEntryType_P2WSH &&
       aet != AddressEntryType_Nested_P2WSH)
      throw WalletException("invalid AddressEntryType for MS wallet");

   //pub root
   auto&& pubkey = CryptoECDSA().ComputePublicKey(privateRoot);
   
   //compute master ID as hmac256(root pubkey, "MetaEntry")
   string hmacMasterMsg("MetaEntry");
   auto&& masterID_long = BtcUtils::getHMAC256(
      pubkey, SecureBinaryData(hmacMasterMsg));
   auto&& masterID = BtcUtils::computeID(masterID_long);
   string masterIDStr(masterID.getCharPtr(), masterID.getSize());

   //create wallet file
   stringstream pathSS;
   pathSS << folder << "/armory_" << masterIDStr << "_wallet.lmdb";
   
   //create dbenv: N subwallets, 1 top db, 1 meta db
   auto dbenv = getEnvFromFile(pathSS.str(), N + 2); 
   
   //create meta entry
   initWalletMetaDB(dbenv, masterIDStr);
   auto mainWltMetaPtr = make_shared<WalletMeta_Multisig>(dbenv);

   //compute wallet ID as hmac256(root pubkey, "M_of_N")
   stringstream mofn;
   mofn << M << "_of_" << N;
   auto&& longID = BtcUtils::getHMAC256(pubkey, SecureBinaryData(mofn.str()));
   auto&& walletID = BtcUtils::computeID(longID);
   
   mainWltMetaPtr->walletID_ = walletID;
   string walletIDStr(walletID.getCharPtr(), walletID.getSize());
   mainWltMetaPtr->dbName_ = walletIDStr;

   auto walletPtr = make_shared<AssetWallet_Multisig>(mainWltMetaPtr);

   LMDB dbMeta;
   {
      //put main name in meta db
      dbMeta.open(dbenv.get(), WALLETMETA_DBNAME);
   
      LMDBEnv::Transaction metatx(dbenv.get(), LMDB::ReadWrite);
      putDbName(&dbMeta, mainWltMetaPtr);
      setMainWallet(&dbMeta, mainWltMetaPtr);
   }

   //create N sub wallets
   map<BinaryData, shared_ptr<AssetWallet_Single>> subWallets;

   for (unsigned i = 0; i < N; i++)
   {
      //get sub wallet root
      stringstream hmacMsg;
      hmacMsg << "Subwallet-" << i;

      SecureBinaryData subRoot(32);
      BtcUtils::getHMAC256(privateRoot.getPtr(), privateRoot.getSize(),
         hmacMsg.str().c_str(), hmacMsg.str().size(), subRoot.getPtr());

      auto subWalletMeta = make_shared<WalletMeta_Single>(dbenv);
      subWalletMeta->parentID_ = walletID;
      subWalletMeta->dbName_ = hmacMsg.str();

      auto cypher = make_unique<Cypher_AES>();
      auto subWalletPtr = AssetWallet_Single::initWalletDb(
         subWalletMeta, move(cypher),
         AddressEntryType_P2PKH, move(subRoot), lookup);

      subWallets[subWalletPtr->getID()] = subWalletPtr;
   }

   //create derScheme
   auto derScheme = make_shared<DerivationScheme_Multisig>(
      subWallets, N, M);

   {
      LMDBEnv::Transaction tx(walletPtr->dbEnv_.get(), LMDB::ReadWrite);

      {
         //wallet type
         BinaryWriter bwKey;
         bwKey.put_uint32_t(WALLETTYPE_KEY);

         BinaryWriter bwData;
         bwData.put_var_int(4);
         bwData.put_uint32_t(WalletMetaType_Multisig);

         walletPtr->putData(bwKey, bwData);
      }

      //header
      walletPtr->putHeaderData(
         masterID, walletID, derScheme, aet, 0);

      {
         //chainlength
         BinaryWriter bwKey;
         bwKey.put_uint8_t(ASSETENTRY_PREFIX);

         BinaryWriter bwData;
         bwData.put_var_int(4);
         bwData.put_uint32_t(lookup);

         walletPtr->putData(bwKey, bwData);
      }
   }

   //clean subwallets ptr and derScheme
   derScheme.reset();
   subWallets.clear();

   //load from db
   walletPtr->readFromFile();

   return walletPtr;
}

////////////////////////////////////////////////////////////////////////////////
void AssetWallet::putHeaderData(const BinaryData& parentID,
   const BinaryData& walletID, 
   shared_ptr<DerivationScheme> derScheme,
   AddressEntryType aet, int topUsedIndex)
{
   LMDBEnv::Transaction tx(dbEnv_.get(), LMDB::ReadWrite);

   {
      //parent ID
      BinaryWriter bwKey;
      bwKey.put_uint32_t(PARENTID_KEY);

      BinaryWriter bwData;
      bwData.put_var_int(parentID.getSize());
      bwData.put_BinaryData(parentID);

      putData(bwKey, bwData);
   }

   {
      //wallet ID
      BinaryWriter bwKey;
      bwKey.put_uint32_t(WALLETID_KEY);

      BinaryWriter bwData;
      bwData.put_var_int(walletID.getSize());
      bwData.put_BinaryData(walletID);

      putData(bwKey, bwData);
   }

   {
      //derivation scheme
      BinaryWriter bwKey;
      bwKey.put_uint32_t(DERIVATIONSCHEME_KEY);

      auto&& data = derScheme->serialize();
      putData(bwKey.getData(), data);
   }

   {
      //default AddressEntryType
      BinaryWriter bwKey;
      bwKey.put_uint32_t(ADDRESSENTRYTYPE_KEY);

      BinaryWriter bwData;
      bwData.put_var_int(1);
      bwData.put_uint8_t(aet);

      putData(bwKey, bwData);
   }

   {
      //top used index
      BinaryWriter bwKey;
      bwKey.put_uint32_t(TOPUSEDINDEX_KEY);

      BinaryWriter bwData;
      bwData.put_var_int(4);
      bwData.put_int32_t(topUsedIndex);

      putData(bwKey, bwData);
   }
}

////////////////////////////////////////////////////////////////////////////////
BinaryDataRef AssetWallet::getDataRefForKey(const BinaryData& key) const
{
   /** The reference lifetime is tied to the db tx lifetime. The caller has to
   maintain the tx for as long as the data ref needs to be valid **/

   return getDataRefForKey(key, db_);
}

////////////////////////////////////////////////////////////////////////////////
BinaryDataRef AssetWallet::getDataRefForKey(const BinaryData& key, LMDB* db)
{
   CharacterArrayRef keyRef(key.getSize(), key.getPtr());
   auto ref = db->get_NoCopy(keyRef);

   if (ref.data == nullptr)
      throw NoEntryInWalletException();

   BinaryRefReader brr((const uint8_t*)ref.data, ref.len);
   auto len = brr.get_var_int();
   if (len != brr.getSizeRemaining())
      throw WalletException("on disk data length mismatch");

   return brr.get_BinaryDataRef(brr.getSizeRemaining());
}

////////////////////////////////////////////////////////////////////////////////
void AssetWallet_Single::readFromFile()
{
   //sanity check
   if (dbEnv_ == nullptr || db_ == nullptr)
      throw WalletException("uninitialized wallet object");

   LMDBEnv::Transaction tx(dbEnv_.get(), LMDB::ReadOnly);

   {
      //parentId
      BinaryWriter bwKey;
      bwKey.put_uint32_t(PARENTID_KEY);

      auto parentIdRef = getDataRefForKey(bwKey.getData());
      parentID_ = parentIdRef;
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

      derScheme_ = DerivationScheme::deserialize(derSchemeRef);
   }

   {
      //default AddressEntryType
      BinaryWriter bwKey;
      bwKey.put_uint32_t(ADDRESSENTRYTYPE_KEY);
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
            assets_.insert(make_pair(entryPtr->getId(), entryPtr));
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
void AssetWallet_Multisig::readFromFile()
{
   //sanity check
   if (dbEnv_ == nullptr || db_ == nullptr)
      throw WalletException("uninitialized wallet object");

   {
      LMDBEnv::Transaction tx(dbEnv_.get(), LMDB::ReadOnly);

      {
         //parentId
         BinaryWriter bwKey;
         bwKey.put_uint32_t(PARENTID_KEY);

         auto parentIdRef = getDataRefForKey(bwKey.getData());
         parentID_ = parentIdRef;
      }

      {
         //walletId
         BinaryWriter bwKey;
         bwKey.put_uint32_t(WALLETID_KEY);
         auto walletIdRef = getDataRefForKey(bwKey.getData());

         walletID_ = walletIdRef;
      }

      {
         //default AddressEntryType
         BinaryWriter bwKey;
         bwKey.put_uint32_t(ADDRESSENTRYTYPE_KEY);
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
         //derivation scheme
         BinaryWriter bwKey;
         bwKey.put_uint32_t(DERIVATIONSCHEME_KEY);
         auto derSchemeRef = getDataRefForKey(bwKey.getData());

         derScheme_ = DerivationScheme::deserialize(derSchemeRef);
      }

      {
         //lookup
         {
            BinaryWriter bwKey;
            bwKey.put_uint8_t(ASSETENTRY_PREFIX);
            auto lookupRef = getDataRefForKey(bwKey.getData());

            BinaryRefReader brr(lookupRef);
            chainLength_ = brr.get_uint32_t();
         }
      }
   }

   {
      //sub wallets
      auto derSchemeMS =
         dynamic_pointer_cast<DerivationScheme_Multisig>(derScheme_);

      if (derSchemeMS == nullptr)
         throw WalletException("unexpected derScheme ptr type");

      auto n = derSchemeMS->getN();

      map<BinaryData, shared_ptr<AssetWallet_Single>> walletPtrs;
      for (unsigned i = 0; i < n; i++)
      {
         stringstream ss;
         ss << "Subwallet-" << i;

         auto subWltMeta = make_shared<WalletMeta_Subwallet>(dbEnv_);
         subWltMeta->dbName_ = ss.str();

         auto subwalletPtr = make_shared<AssetWallet_Single>(subWltMeta);
         subwalletPtr->readFromFile();
         walletPtrs[subwalletPtr->getID()] = subwalletPtr;

      }

      derSchemeMS->setSubwalletPointers(walletPtrs);
   }

   {
      auto derSchemeMS = dynamic_pointer_cast<DerivationScheme_Multisig>(derScheme_);
      if (derSchemeMS == nullptr)
         throw WalletException("unexpected derScheme type");

      //build AssetEntry map
      for (unsigned i = 0; i < chainLength_; i++)
         assets_[i] = derSchemeMS->getAssetForIndex(i);
   }
}

////////////////////////////////////////////////////////////////////////////////
void AssetWallet::putData(const BinaryData& key, const BinaryData& data)
{
   /** the caller is responsible for the db transaction **/
   putData(db_, key, data);
}

////////////////////////////////////////////////////////////////////////////////
void AssetWallet::putData(
   LMDB* db, const BinaryData& key, const BinaryData& data)
{
   CharacterArrayRef keyRef(key.getSize(), key.getPtr());
   CharacterArrayRef dataRef(data.getSize(), data.getPtr());

   db->insert(keyRef, dataRef);
}

////////////////////////////////////////////////////////////////////////////////
void AssetWallet::putData(BinaryWriter& key, BinaryWriter& data)
{
   putData(key.getData(), data.getData());
}

////////////////////////////////////////////////////////////////////////////////
unsigned AssetWallet::getAndBumpHighestUsedIndex()
{
   LMDBEnv::Transaction tx(dbEnv_.get(), LMDB::ReadWrite);

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
   //increment top used address counter & update
   auto index = getAndBumpHighestUsedIndex();

   //lock
   ReentrantLock lock(this);

   auto addrIter = addresses_.find(index);
   if (addrIter != addresses_.end())
      return addrIter->second;

   //check look up
   auto entryIter = assets_.find(index);
   if (entryIter == assets_.end())
   {
      if (assets_.size() == 0)
         throw WalletException("uninitialized wallet");
      extendChain(DERIVATION_LOOKUP);

      entryIter = assets_.find(index);
      if (entryIter == assets_.end())
         throw WalletException("requested index overflows max lookup");
   }
   
   auto aePtr = getAddressEntryForAsset(entryIter->second, default_aet_);

   //insert new entry
   addresses_[aePtr->getIndex()] = aePtr;

   return aePtr;
}

////////////////////////////////////////////////////////////////////////////////
bool AssetWallet::hasScrAddr(const BinaryData& scrAddr)
{
   return getAssetIndexForAddr(scrAddr) != INT32_MAX;
}

////////////////////////////////////////////////////////////////////////////////
int AssetWallet::getAssetIndexForAddr(const BinaryData& scrAddr)
{
   auto getIndexForAddr = [&](BinaryDataRef scriptHash)->int
   {
      auto prefix = scriptHash.getPtr();
      auto hashRef = scriptHash.getSliceRef(1, scriptHash.getSize() - 1);

      switch (*prefix)
      {
      case SCRIPT_PREFIX_HASH160:
      case SCRIPT_PREFIX_HASH160_TESTNET:
      {
         auto iter = hashMaps_.hashCompressed_.find(hashRef);
         if (iter != hashMaps_.hashCompressed_.end())
            return iter->second;

         auto iter2 = hashMaps_.hashUncompressed_.find(hashRef);
         if (iter2 != hashMaps_.hashUncompressed_.end())
            return iter2->second;

         break;
      }

        
      case SCRIPT_PREFIX_P2SH:
      case SCRIPT_PREFIX_P2SH_TESTNET:
      {
         auto iter1 = hashMaps_.hashNestedP2PK_.find(hashRef);
         if (iter1 != hashMaps_.hashNestedP2PK_.end())
            return iter1->second;
         
         auto iter2 = hashMaps_.hashNestedP2WPKH_.find(hashRef);
         if (iter2 != hashMaps_.hashNestedP2WPKH_.end())
            return iter2->second;

         auto iter3 = hashMaps_.hashNestedMultisig_.find(hashRef);
         if (iter3 != hashMaps_.hashNestedMultisig_.end())
            return iter3->second;

         auto iter4 = hashMaps_.hashNestedP2WSH_.find(hashRef);
         if (iter4 != hashMaps_.hashNestedP2WSH_.end())
            return iter4->second;

         break;
      }

      default:
         throw runtime_error("invalid script hash prefix");
      }

      return INT32_MAX;
   };

   auto getIndexForAddrNoPrefix = [&](BinaryDataRef scriptHash)->int
   {
      auto iter = hashMaps_.hashCompressed_.find(scriptHash);
      if (iter != hashMaps_.hashCompressed_.end())
         return iter->second;

      auto iter2 = hashMaps_.hashUncompressed_.find(scriptHash);
      if (iter2 != hashMaps_.hashUncompressed_.end())
         return iter2->second;

      auto iter3 = hashMaps_.hashNestedP2PK_.find(scriptHash);
      if (iter3 != hashMaps_.hashNestedP2PK_.end())
         return iter3->second;

      auto iter4 = hashMaps_.hashNestedP2WPKH_.find(scriptHash);
      if (iter4 != hashMaps_.hashNestedP2WPKH_.end())
         return iter4->second;

      auto iter5 = hashMaps_.hashNestedMultisig_.find(scriptHash);
      if (iter5 != hashMaps_.hashNestedMultisig_.end())
         return iter5->second;

      auto iter6 = hashMaps_.hashNestedP2WSH_.find(scriptHash);
      if (iter6 != hashMaps_.hashNestedP2WSH_.end())
         return iter6->second;

      return INT32_MAX;
   };

   ReentrantLock lock(this);

   fillHashIndexMap();

   if (scrAddr.getSize() == 21)
   {
      try
      {
         return getIndexForAddr(scrAddr.getRef());
      }
      catch (...)
      {
      }
   }
   else if (scrAddr.getSize() == 20)
   {
      return getIndexForAddrNoPrefix(scrAddr.getRef());
   }

   auto&& scriptHash = BtcUtils::base58toScriptAddr(scrAddr);
   return getIndexForAddr(scriptHash);
}

////////////////////////////////////////////////////////////////////////////////
AddressEntryType AssetWallet::getAddrTypeForIndex(int index)
{
   ReentrantLock lock(this);
   AddressEntryType addrType;
   
   auto addrIter = addresses_.find(index);
   if (addrIter != addresses_.end())
      addrType = addrIter->second->getType();

   auto assetIter = assets_.find(index);
   if (assetIter == assets_.end())
      throw WalletException("invalid index");

   addrType = assetIter->second->getAddrType();

   if (addrType == AddressEntryType_Default)
      addrType = default_aet_;
   return addrType;
}

////////////////////////////////////////////////////////////////////////////////
shared_ptr<AddressEntry> AssetWallet_Single::getAddressEntryForAsset(
   shared_ptr<AssetEntry> assetPtr, AddressEntryType ae_type)
{
   ReentrantLock lock(this);
   
   if (ae_type == AddressEntryType_Default)
      ae_type = default_aet_;

   auto prev_aet = assetPtr->getAddrType();

   auto addrIter = addresses_.find(assetPtr->getId());
   if (addrIter != addresses_.end())
   {
      if(addrIter->second->getType() == ae_type)
         return addrIter->second;
   }

   shared_ptr<AddressEntry> aePtr = nullptr;
   switch (ae_type)
   {
   case AddressEntryType_P2PKH:
      aePtr = make_shared<AddressEntry_P2PKH>(assetPtr);
      break;

   case AddressEntryType_P2WPKH:
      aePtr = make_shared<AddressEntry_P2WPKH>(assetPtr);
      break;

   case AddressEntryType_Nested_P2WPKH:
      aePtr = make_shared<AddressEntry_Nested_P2WPKH>(assetPtr);
      break;

   case AddressEntryType_Nested_P2PK:
      aePtr = make_shared<AddressEntry_Nested_P2PK>(assetPtr);
      break;

   default:
      throw WalletException("unsupported address entry type");
   }

   if (ae_type == prev_aet)
      assetPtr->doNotCommit();
   else
      writeAssetEntry(assetPtr);

   addresses_[assetPtr->getId()] = aePtr;
   return aePtr;
}

////////////////////////////////////////////////////////////////////////////////
shared_ptr<AddressEntry> AssetWallet_Multisig::getAddressEntryForAsset(
   shared_ptr<AssetEntry> assetPtr, AddressEntryType ae_type)
{
   ReentrantLock lock(this);

   auto addrIter = addresses_.find(assetPtr->getId());
   if (addrIter != addresses_.end())
      return addrIter->second;

   shared_ptr<AddressEntry> aePtr = nullptr;
   switch (ae_type)
   {
   case AddressEntryType_Nested_Multisig:
      aePtr = make_shared<AddressEntry_Nested_Multisig>(assetPtr);
      break;

   case AddressEntryType_P2WSH:
      aePtr = make_shared<AddressEntry_P2WSH>(assetPtr);
      break;

   case AddressEntryType_Nested_P2WSH:
      aePtr = make_shared<AddressEntry_Nested_P2WSH>(assetPtr);
      break;

   default:
      throw WalletException("unsupported address entry type");
   }

   addresses_.insert(make_pair(assetPtr->getId(), aePtr));
   return aePtr;
}

////////////////////////////////////////////////////////////////////////////////
shared_ptr<AddressEntry> AssetWallet::getAddressEntryForIndex(int index)
{
   ReentrantLock lock(this);

   auto addrIter = addresses_.find(index);
   if (addrIter != addresses_.end())
      return addrIter->second;

   auto asset = getAssetForIndex(index);
   return getAddressEntryForAsset(asset, asset->getAddrType());
}

////////////////////////////////////////////////////////////////////////////////
void AssetWallet::writeAssetEntry(shared_ptr<AssetEntry> entryPtr)
{
   if (!entryPtr->needsCommit())
      return;

   auto&& serializedEntry = entryPtr->serialize();
   auto&& dbKey = entryPtr->getDbKey();

   CharacterArrayRef keyRef(dbKey.getSize(), dbKey.getPtr());
   CharacterArrayRef dataRef(serializedEntry.getSize(), serializedEntry.getPtr());

   LMDBEnv::Transaction tx(dbEnv_.get(), LMDB::ReadWrite);
   db_->insert(keyRef, dataRef);

   entryPtr->doNotCommit();
}

////////////////////////////////////////////////////////////////////////////////
void AssetWallet::deleteAssetEntry(shared_ptr<AssetEntry> entryPtr)
{
   auto&& dbKey = entryPtr->getDbKey();
   CharacterArrayRef keyRef(dbKey.getSize(), dbKey.getPtr());

   LMDBEnv::Transaction tx(dbEnv_.get(), LMDB::ReadWrite);
   db_->erase(keyRef);
}


////////////////////////////////////////////////////////////////////////////////
void AssetWallet::update()
{
   LMDBEnv::Transaction tx(dbEnv_.get(), LMDB::ReadWrite);

   for (auto& entryPtr : assets_)
      writeAssetEntry(entryPtr.second);
}

////////////////////////////////////////////////////////////////////////////////
void AssetWallet::deleteImports(const vector<BinaryData>& addrVec)
{
   ReentrantLock lock(this);

   for (auto& scrAddr : addrVec)
   {
      int importIndex = INT32_MAX;
      try
      {
         //if import index does not exist or isnt negative, continue
         //only imports use a negative derivation index
         importIndex = getAssetIndexForAddr(scrAddr);
         if (importIndex > 0 || importIndex == INT32_MAX)
            continue;
      }
      catch (...)
      {
         continue;
      }

      auto assetIter = assets_.find(importIndex);
      if (assetIter == assets_.end())
         continue;

      auto assetPtr = assetIter->second;

      //remove from wallet's maps
      assets_.erase(importIndex);
      addresses_.erase(importIndex);

      //erase from file
      deleteAssetEntry(assetPtr);
   }
}

////////////////////////////////////////////////////////////////////////////////
void AssetWallet_Single::fillHashIndexMap()
{
   ReentrantLock lock(this);

   if ((assets_.size() > 0 && lastKnownIndex_ != assets_.rbegin()->first) ||
      lastAssetMapSize_ != assets_.size())
   {
      hashMaps_.clear();

      for (auto& entry : assets_)
      {
         auto assetSingle = dynamic_pointer_cast<AssetEntry_Single>(entry.second);
         auto&& hashMap = assetSingle->getScriptHashMap();
         
         hashMaps_.hashUncompressed_.insert(make_pair(
            hashMap[ScriptHash_P2PKH_Uncompressed], assetSingle->getId()));
         
         hashMaps_.hashCompressed_.insert(make_pair(
            hashMap[ScriptHash_P2PKH_Compressed], assetSingle->getId()));
         
         hashMaps_.hashNestedP2WPKH_.insert(make_pair(
            hashMap[ScriptHash_P2WPKH], assetSingle->getId()));

         hashMaps_.hashNestedP2PK_.insert(make_pair(
            hashMap[ScriptHash_Nested_P2PK], assetSingle->getId()));
      }

      lastKnownIndex_ = assets_.rbegin()->first;
      lastAssetMapSize_ = assets_.size();
   }
}

////////////////////////////////////////////////////////////////////////////////
set<BinaryData> AssetWallet_Single::getAddrHashSet()
{
   ReentrantLock lock(this);

   fillHashIndexMap();

   set<BinaryData> addrHashSet;
   uint8_t prefix = BlockDataManagerConfig::getPubkeyHashPrefix();

   for (auto& hashIndexPair : hashMaps_.hashUncompressed_)
   {
      BinaryWriter bw;
      bw.put_uint8_t(prefix);
      bw.put_BinaryDataRef(hashIndexPair.first);
      addrHashSet.insert(bw.getData());
   }

   prefix = BlockDataManagerConfig::getScriptHashPrefix();

   for (auto& hashIndexPair : hashMaps_.hashNestedP2WPKH_)
   {
      BinaryWriter bw;
      bw.put_uint8_t(prefix);
      bw.put_BinaryDataRef(hashIndexPair.first);
      addrHashSet.insert(bw.getData());
   }

   for (auto& hashIndexPair : hashMaps_.hashNestedP2PK_)
   {
      BinaryWriter bw;
      bw.put_uint8_t(prefix);
      bw.put_BinaryDataRef(hashIndexPair.first);
      addrHashSet.insert(bw.getData());
   }

   return addrHashSet;
}

////////////////////////////////////////////////////////////////////////////////
const SecureBinaryData& AssetWallet_Single::getPublicRoot() const
{
   auto rootEntry = dynamic_pointer_cast<AssetEntry_Single>(root_);
   auto pubEntry = rootEntry->getPubKey();

   return pubEntry->getUncompressedKey();
}

////////////////////////////////////////////////////////////////////////////////
const SecureBinaryData& AssetWallet_Single::getChainCode() const
{
   auto derSchemeA135 =
      dynamic_pointer_cast<DerivationScheme_ArmoryLegacy>(derScheme_);

   return derSchemeA135->getChainCode();
}

////////////////////////////////////////////////////////////////////////////////
void AssetWallet_Multisig::fillHashIndexMap()
{
   ReentrantLock lock(this);

   if ((assets_.size() > 0 && lastKnownIndex_ != assets_.rbegin()->first) ||
      lastAssetMapSize_ != assets_.size())
   {
      hashMaps_.clear();

      switch (default_aet_)
      {
      case AddressEntryType_Nested_P2WSH:
      {
         for (auto& entry : assets_)
         {
            auto assetMS = dynamic_pointer_cast<AssetEntry_Multisig>(entry.second);
            hashMaps_.hashNestedP2WSH_.insert(
               make_pair(assetMS->getP2WSHScriptH160().getRef(), assetMS->getId()));
         }

         break;
      }

      case AddressEntryType_P2WSH:
      {
         for (auto& entry : assets_)
         {
            auto assetMS = dynamic_pointer_cast<AssetEntry_Multisig>(entry.second);
            hashMaps_.hashP2WSH_.insert(
               make_pair(assetMS->getHash256().getRef(), assetMS->getId()));
         }

         break;
      }

      case AddressEntryType_Nested_Multisig:
      {
         for (auto& entry : assets_)
         {
            auto assetMS = dynamic_pointer_cast<AssetEntry_Multisig>(entry.second);
            hashMaps_.hashNestedMultisig_.insert(
               make_pair(assetMS->getHash160().getRef(), assetMS->getId()));
         }

         break;
      }

      default:
         throw WalletException("unexpected AddressEntryType for MS wallet");
      }

      lastKnownIndex_ = assets_.rbegin()->first;
      lastAssetMapSize_ = assets_.size();
   }
}

////////////////////////////////////////////////////////////////////////////////
set<BinaryData> AssetWallet_Multisig::getAddrHashSet()
{
   ReentrantLock lock(this);

   fillHashIndexMap();

   set<BinaryData> addrHashSet;
   uint8_t prefix = BlockDataManagerConfig::getScriptHashPrefix();
   
   for (auto& hashIndexPair : hashMaps_.hashNestedMultisig_)
   {
      BinaryWriter bw;
      bw.put_uint8_t(prefix);
      bw.put_BinaryDataRef(hashIndexPair.first);
      addrHashSet.insert(bw.getData());
   }

   for (auto& hashIndexPair : hashMaps_.hashNestedP2WSH_)
   {
      BinaryWriter bw;
      bw.put_uint8_t(prefix);
      bw.put_BinaryDataRef(hashIndexPair.first);
      addrHashSet.insert(bw.getData());
   }

   for (auto& hashIndexPair : hashMaps_.hashP2WSH_)
   {
      addrHashSet.insert(hashIndexPair.first);
   }

   return addrHashSet;
}

////////////////////////////////////////////////////////////////////////////////
BinaryData AssetWallet_Multisig::getPrefixedHashForIndex(
   unsigned index) const
{
   auto assetPtr = getAssetForIndex(index);
   auto assetMS = dynamic_pointer_cast<AssetEntry_Multisig>(assetPtr);
   if (assetMS == nullptr)
      throw WalletException("unexpected asset type");

   BinaryWriter bw;
   bw.put_uint8_t(BlockDataManagerConfig::getScriptHashPrefix());

   switch (default_aet_)
   {
   case AddressEntryType_Nested_Multisig:
      bw.put_BinaryData(assetMS->getHash160());
      break;

   case AddressEntryType_P2WSH:
     return assetMS->getHash256();

   case AddressEntryType_Nested_P2WSH:
      bw.put_BinaryData(assetMS->getP2WSHScriptH160());
      break;

   default:
      throw WalletException("invalid aet");
   }

   return bw.getData();
}

////////////////////////////////////////////////////////////////////////////////
shared_ptr<AssetEntry> AssetWallet::getAssetForIndex(unsigned index) const
{
   ReentrantLock lock(this);

   auto iter = assets_.find(index);
   if (iter == assets_.end())
      throw WalletException("invalid asset index");

   return iter->second;
}

////////////////////////////////////////////////////////////////////////////////
const BinaryData& AssetWallet::getP2SHScriptForHash(const BinaryData& script)
{
   fillHashIndexMap();

   auto getEntryPtr = [this](const BinaryData& hash)->shared_ptr<AssetEntry>
   {
      auto iter1 = hashMaps_.hashNestedP2PK_.find(hash);
      if (iter1 != hashMaps_.hashNestedP2PK_.end())
         return getAssetForIndex(iter1->second);

      auto iter2 = hashMaps_.hashNestedP2WPKH_.find(hash);
      if (iter2 != hashMaps_.hashNestedP2WPKH_.end())
         return getAssetForIndex(iter2->second);

      auto iter3 = hashMaps_.hashNestedMultisig_.find(hash);
      if (iter3 != hashMaps_.hashNestedMultisig_.end())
         return getAssetForIndex(iter3->second);

      auto iter4 = hashMaps_.hashNestedP2WSH_.find(hash);
      if (iter4 != hashMaps_.hashNestedP2WSH_.end())
         return getAssetForIndex(iter4->second);

      return nullptr;
   };

   auto&& hash = BtcUtils::getTxOutRecipientAddr(script);
   auto entryPtr = getEntryPtr(hash);

   if (entryPtr == nullptr)
      throw WalletException("unkonwn hash");

   auto assetSingle = dynamic_pointer_cast<AssetEntry_Single>(entryPtr);
   if (assetSingle != nullptr)
   {
      auto& p2pkHash = assetSingle->getP2PKScriptH160();
      if (p2pkHash == hash)
         return assetSingle->getP2PKScript();
      else
         return assetSingle->getWitnessScript();
   }

   auto assetMS = dynamic_pointer_cast<AssetEntry_Multisig>(entryPtr);
   if (assetMS == nullptr)
      throw WalletException("unexpected entry type");

   auto& nestedP2WSHhash = assetMS->getP2WSHScriptH160();
   if (nestedP2WSHhash == hash)
      return assetMS->getP2WSHScript();
   else
      return assetMS->getScript();
}

////////////////////////////////////////////////////////////////////////////////
const BinaryData& AssetWallet::getNestedSWAddrForIndex(
   unsigned chainIndex)
{
   ReentrantLock lock(this);

   auto assetPtr = getAssetForIndex(chainIndex);
   auto addrEntry = getAddressEntryForAsset(
      assetPtr, AddressEntryType_Nested_P2WPKH);

   return addrEntry->getAddress();
}

////////////////////////////////////////////////////////////////////////////////
const BinaryData& AssetWallet::getNestedP2PKAddrForIndex(
   unsigned chainIndex)
{
   ReentrantLock lock(this);

   auto assetPtr = getAssetForIndex(chainIndex);
   auto addrEntry = getAddressEntryForAsset(
      assetPtr, AddressEntryType_Nested_P2PK);

   return addrEntry->getAddress();
}

////////////////////////////////////////////////////////////////////////////////
const BinaryData& AssetWallet::getP2PKHAddrForIndex(unsigned chainIndex)
{
   ReentrantLock lock(this);

   auto assetPtr = getAssetForIndex(chainIndex);
   auto addrEntry = getAddressEntryForAsset(
      assetPtr, AddressEntryType_P2PKH);

   return addrEntry->getAddress();
}

////////////////////////////////////////////////////////////////////////////////
int AssetWallet::getLastComputedIndex(void) const
{
   if (getAssetCount() == 0)
      return -1;

   auto iter = assets_.rbegin();
   return iter->first;
}

////////////////////////////////////////////////////////////////////////////////
string AssetWallet::getID(void) const
{
   return string(walletID_.getCharPtr(), walletID_.getSize());
}

////////////////////////////////////////////////////////////////////////////////
void AssetWallet::extendChain(unsigned count)
{
   ReentrantLock lock(this);

   //add *count* entries to address chain
   if (assets_.size() == 0)
      throw WalletException("empty asset map");
   
   if (count == 0)
      return;

   extendChain(assets_.rbegin()->second, count);
}

////////////////////////////////////////////////////////////////////////////////
bool AssetWallet::extendChainTo(unsigned count)
{
   ReentrantLock lock(this);

   //make address chain at least *count* long
   auto lastComputedIndex = max(getLastComputedIndex(), 0);
   if (lastComputedIndex > count)
      return false;

   auto toCompute = count - lastComputedIndex;

   extendChain(toCompute);
   return true;
}

////////////////////////////////////////////////////////////////////////////////
void AssetWallet::extendChain(shared_ptr<AssetEntry> assetPtr, unsigned count)
{
   if (count == 0)
      return;

   ReentrantLock lock(this);

   auto&& assetVec = derScheme_->extendChain(assetPtr, count);

   LMDBEnv::Transaction tx(dbEnv_.get(), LMDB::ReadWrite);

   {
      for (auto& asset : assetVec)
      {
         auto id = asset->getId();
         auto iter = assets_.find(id);
         if (iter != assets_.end())
            continue;

         writeAssetEntry(asset);
         assets_.insert(make_pair(
            id, asset));
      }
   }
}

////////////////////////////////////////////////////////////////////////////////
bool AssetWallet_Single::setImport(
   int importID, const SecureBinaryData& pubkey)
{
   auto importIndex = convertToImportIndex(importID);
   
   ReentrantLock lock(this);

   auto assetIter = assets_.find(importIndex);
   if (assetIter != assets_.end())
      return false;

   auto pubkey_copy = pubkey;
   auto empty_privkey = SecureBinaryData();
   auto newAsset = make_shared<AssetEntry_Single>(
      importIndex, move(pubkey_copy), move(empty_privkey), nullptr);

   assets_.insert(make_pair(importIndex, newAsset));
   writeAssetEntry(newAsset);

   return true;
}

////////////////////////////////////////////////////////////////////////////////
bool AssetWallet_Multisig::setImport(
   int importID, const SecureBinaryData& pubkey)
{
   throw WalletException("setImport not implemented for multisig wallets");
   return false;
}

////////////////////////////////////////////////////////////////////////////////
int AssetWallet::convertToImportIndex(int importID)
{
   return INT32_MIN + importID;
}

////////////////////////////////////////////////////////////////////////////////
int AssetWallet::convertFromImportIndex(int importID)
{
   return INT32_MAX + 1 + importID;
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

   case DERIVATIONSCHEME_MULTISIG:
   {
      //grab n, m
      auto m = brr.get_uint32_t();
      auto n = brr.get_uint32_t();

      set<BinaryData> ids;
      while (brr.getSizeRemaining() > 0)
      {
         auto len = brr.get_var_int();
         auto&& id = brr.get_BinaryData(len);
         ids.insert(move(id));
      }

      if (ids.size() != n)
         throw DerivationSchemeDeserException("id count mismatch");

      derScheme = make_shared<DerivationScheme_Multisig>(ids, n, m);

      break;
   }

   default:
      throw DerivationSchemeDeserException("unsupported derivation scheme");
   }

   return derScheme;
}

////////////////////////////////////////////////////////////////////////////////
vector<shared_ptr<AssetEntry>> DerivationScheme_ArmoryLegacy::extendChain(
   shared_ptr<AssetEntry> firstAsset, unsigned count)
{
   auto nextAsset = [this](
      shared_ptr<AssetEntry> assetPtr)->shared_ptr<AssetEntry>
   {
      auto assetSingle =
         dynamic_pointer_cast<AssetEntry_Single>(assetPtr);

      //get pubkey
      auto pubkey = assetSingle->getPubKey();
      auto& pubkeyData = pubkey->getUncompressedKey();

      auto&& nextPubkey = CryptoECDSA().ComputeChainedPublicKey(
         pubkeyData, chainCode_, nullptr);

      auto&& nextPubKey_2 = CryptoECDSA().ComputeChainedPublicKey(
         pubkeyData, chainCode_, nullptr);

      if (nextPubkey != nextPubKey_2)
         throw runtime_error("failed pubkey derivation");

      //try to get priv key
      auto privkey = assetSingle->getPrivKey();
      SecureBinaryData nextPrivkey;
      try
      {
         auto& privkeyData = privkey->getKey();

         nextPrivkey = move(CryptoECDSA().ComputeChainedPrivateKey(
            privkeyData, chainCode_, pubkeyData, nullptr));

         if (!CryptoECDSA().CheckPubPrivKeyMatch(nextPrivkey, nextPubkey))
            throw runtime_error("failed privkey derivation");
      }
      catch (AssetUnavailableException&)
      {
         //no priv key, ignore
      }
      catch (CypherException&)
      {
         //ignore, not going to prompt user for password with priv key derivation
      }

      //no need to encrypt the new data, asset ctor will deal with it
      unique_ptr<Cypher> cypher;
      if (privkey->cypher_ != nullptr)
         cypher = move(privkey->cypher_->getCopy());

      return make_shared<AssetEntry_Single>(
         assetSingle->getId() + 1,
         move(nextPubkey), move(nextPrivkey), move(cypher));
   };
   
   vector<shared_ptr<AssetEntry>> assetVec;
   auto currentAsset = firstAsset;

   for (unsigned i = 0; i < count; i++)
   { 
      currentAsset = nextAsset(currentAsset);
      assetVec.push_back(currentAsset);
   }

   return assetVec;
}

////////////////////////////////////////////////////////////////////////////////
vector<shared_ptr<AssetEntry>> DerivationScheme_Multisig::extendChain(
   shared_ptr<AssetEntry> firstAsset, unsigned count)
{
   //synchronize wallet chains length
   unsigned bottom = UINT32_MAX;
   auto total = firstAsset->getId() + 1 + count; 
 
   for (auto& wltPtr : wallets_)
   {
      wltPtr.second->extendChain(
         total - wltPtr.second->getAssetCount());
   }

   vector<shared_ptr<AssetEntry>> assetVec;
   for (unsigned i = firstAsset->getId() + 1; i < total; i++)
      assetVec.push_back(getAssetForIndex(i));

   return assetVec;
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
BinaryData DerivationScheme_Multisig::serialize() const
{
   if (walletIDs_.size() != n_)
      throw WalletException("multisig wallet is missing subwallets");

   BinaryWriter bw;
   bw.put_uint8_t(DERIVATIONSCHEME_MULTISIG);
   bw.put_uint32_t(m_);
   bw.put_uint32_t(n_);
   
   for (auto& id : walletIDs_)
   {
      bw.put_var_int(id.getSize());
      bw.put_BinaryData(id);
   }

   BinaryWriter bwFinal;
   bwFinal.put_var_int(bw.getSize());
   bwFinal.put_BinaryData(bw.getData());

   return bwFinal.getData();
}

////////////////////////////////////////////////////////////////////////////////
void DerivationScheme_Multisig::setSubwalletPointers(
   map<BinaryData, shared_ptr<AssetWallet_Single>> ptrMap)
{
   set<BinaryData> ids;
   for (auto& wltPtr : ptrMap)
      ids.insert(wltPtr.first);

   if (ids != walletIDs_)
      throw DerivationSchemeDeserException("ids set mismatch");

   wallets_ = ptrMap;
}

////////////////////////////////////////////////////////////////////////////////
shared_ptr<AssetEntry_Multisig> DerivationScheme_Multisig::getAssetForIndex(
   unsigned index) const
{
   //gather assets
   map<BinaryData, shared_ptr<AssetEntry>> assetMap;

   for (auto wltPtr : wallets_)
   {
      auto asset = wltPtr.second->getAssetForIndex(index);
      assetMap.insert(make_pair(wltPtr.first, asset));
   }

   //create asset
   return make_shared<AssetEntry_Multisig>(index, assetMap, m_, n_);
}

////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
//// AddressEntry
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
AddressEntry::~AddressEntry()
{}

////////////////////////////////////////////////////////////////////////////////
const BinaryData& AddressEntry_P2PKH::getPrefixedHash() const
{
   if (hash_.getSize() == 0)
   {
      auto assetSingle = dynamic_pointer_cast<AssetEntry_Single>(asset_);
      if (assetSingle == nullptr)
         throw WalletException("unexpected asset entry type");

      auto& h160 = assetSingle->getHash160Uncompressed();

      //get and prepend network byte
      auto networkByte = BlockDataManagerConfig::getPubkeyHashPrefix();

      hash_.append(networkByte);
      hash_.append(h160);
   }

   return hash_;
}

////////////////////////////////////////////////////////////////////////////////
const BinaryData& AddressEntry_P2PKH::getAddress() const
{
   if (address_.getSize() == 0)
      address_ = move(BtcUtils::scrAddrToBase58(getPrefixedHash()));

   return address_;
}

////////////////////////////////////////////////////////////////////////////////
shared_ptr<ScriptRecipient> AddressEntry_P2PKH::getRecipient(
   uint64_t value) const
{
   auto assetSingle = dynamic_pointer_cast<AssetEntry_Single>(asset_);
   if (assetSingle == nullptr)
      throw WalletException("unexpected asset entry type");

   auto& h160 = assetSingle->getHash160Uncompressed();
   return make_shared<Recipient_P2PKH>(h160, value);
}

////////////////////////////////////////////////////////////////////////////////
const BinaryData& AddressEntry_P2WPKH::getPrefixedHash() const
{
   if (hash_.getSize() == 0)
   {
      auto assetSingle = dynamic_pointer_cast<AssetEntry_Single>(asset_);
      if (assetSingle == nullptr)
         throw WalletException("unexpected asset entry type");

      //no address standard for SW yet, consider BIP142
      hash_ = assetSingle->getHash160Compressed();
   }

   return hash_;
}

////////////////////////////////////////////////////////////////////////////////
const BinaryData& AddressEntry_P2WPKH::getAddress() const
{
   if (address_.getSize() == 0)
      address_ = getPrefixedHash();

   return address_;
}

////////////////////////////////////////////////////////////////////////////////
shared_ptr<ScriptRecipient> AddressEntry_P2WPKH::getRecipient(
   uint64_t value) const
{
   auto assetSingle = dynamic_pointer_cast<AssetEntry_Single>(asset_);
   if (assetSingle == nullptr)
      throw WalletException("unexpected asset entry type");

   auto& h160 = assetSingle->getHash160Compressed();
   return make_shared<Recipient_P2WPKH>(h160, value);
}

////////////////////////////////////////////////////////////////////////////////
const BinaryData& AddressEntry_Nested_Multisig::getPrefixedHash() const
{
   auto prefix = BlockDataManagerConfig::getScriptHashPrefix();

   if (hash_.getSize() == 0)
   {
      switch (asset_->getType())
      {
      case AssetEntryType_Single:
      {
         auto assetSingle = dynamic_pointer_cast<AssetEntry_Single>(asset_);
         if (assetSingle == nullptr)
            throw WalletException("unexpected asset entry type");

         hash_.append(prefix);
         hash_.append(assetSingle->getHash160Compressed());
         break;
      }

      case AssetEntryType_Multisig:
      {
         auto assetMS = dynamic_pointer_cast<AssetEntry_Multisig>(asset_);
         if (assetMS == nullptr)
            throw WalletException("unexpected asset entry type");

         hash_.append(prefix);
         hash_.append(assetMS->getHash160());
         break;
      }

      default:
         throw WalletException("unexpected asset type");
      }
   }

   return hash_;
}

////////////////////////////////////////////////////////////////////////////////
const BinaryData& AddressEntry_Nested_Multisig::getAddress() const
{
   auto prefix = BlockDataManagerConfig::getScriptHashPrefix();

   if (address_.getSize() == 0)
      address_ = move(BtcUtils::scrAddrToBase58(getPrefixedHash()));

   return address_;
}

////////////////////////////////////////////////////////////////////////////////
shared_ptr<ScriptRecipient> AddressEntry_Nested_Multisig::getRecipient(
   uint64_t value) const
{
   BinaryDataRef h160;
   switch (asset_->getType())
   {
   case AssetEntryType_Multisig:
   {
      auto assetMS = dynamic_pointer_cast<AssetEntry_Multisig>(asset_);
      if (assetMS == nullptr)
         throw WalletException("unexpected asset entry type");

      h160 = assetMS->getHash160();
      break;
   }

   default:
      throw WalletException("unexpected asset type");
   }

   return make_shared<Recipient_P2SH>(h160, value);
}

////////////////////////////////////////////////////////////////////////////////
size_t AddressEntry_Nested_Multisig::getInputSize() const
{
   switch (asset_->getType())
   {
   case AssetEntryType_Multisig:
   {
      auto assetMS = dynamic_pointer_cast<AssetEntry_Multisig>(asset_);
      if (assetMS == nullptr)
         throw WalletException("unexpected asset entry type");

      auto m = assetMS->getM();

      size_t size = assetMS->getScript().getSize() + 2;
      size += 73 * m + 40; //m sigs + outpoint

      return size;
   }

   default:
      throw WalletException("unexpected asset type");
   }

   return SIZE_MAX;
}

////////////////////////////////////////////////////////////////////////////////
const BinaryData& AddressEntry_P2WSH::getPrefixedHash() const
{
   if (hash_.getSize() == 0)
   {
      switch (asset_->getType())
      {
      case AssetEntryType_Multisig:
      {
         auto assetMS = dynamic_pointer_cast<AssetEntry_Multisig>(asset_);
         if (assetMS == nullptr)
            throw WalletException("unexpected asset entry type");

         hash_ = move(assetMS->getHash256());
         break;
      }

      default:
         throw WalletException("unexpected asset type");
      }
   }

   return hash_;
}

////////////////////////////////////////////////////////////////////////////////
const BinaryData& AddressEntry_P2WSH::getAddress() const
{
   if (address_.getSize() == 0)
      address_ = getPrefixedHash();

   return address_;
}

////////////////////////////////////////////////////////////////////////////////
shared_ptr<ScriptRecipient> AddressEntry_P2WSH::getRecipient(
   uint64_t value) const
{
   BinaryDataRef scriptHash;
   switch (asset_->getType())
   {
   case AssetEntryType_Multisig:
   {
      auto assetMS = dynamic_pointer_cast<AssetEntry_Multisig>(asset_);
      if (assetMS == nullptr)
         throw WalletException("unexpected asset entry type");

      scriptHash = assetMS->getHash256();
      break;
   }

   default:
      throw WalletException("unexpected asset type");
   }

   return make_shared<Recipient_PW2SH>(scriptHash, value);
}

////////////////////////////////////////////////////////////////////////////////
size_t AddressEntry_P2WSH::getWitnessDataSize() const
{
   switch (asset_->getType())
   {
   case AssetEntryType_Multisig:
   {
      auto assetMS = dynamic_pointer_cast<AssetEntry_Multisig>(asset_);
      if (assetMS == nullptr)
         throw WalletException("unexpected asset entry type");

      auto m = assetMS->getM();

      size_t size = assetMS->getScript().getSize() + 2;
      size += 73 * m + 2;
      
      return size;
   }

   default:
      throw WalletException("unexpected asset type");
   }

   return SIZE_MAX;
}

////////////////////////////////////////////////////////////////////////////////
const BinaryData& AddressEntry_Nested_P2WPKH::getPrefixedHash() const
{
   uint8_t prefix = BlockDataManagerConfig::getScriptHashPrefix();

   if (hash_.getSize() == 0)
   {
      switch (asset_->getType())
      {
      case AssetEntryType_Single:
      {
         auto assetSingle = dynamic_pointer_cast<AssetEntry_Single>(asset_);
         if (assetSingle == nullptr)
            throw WalletException("unexpected asset entry type");

         hash_.append(prefix);
         hash_.append(assetSingle->getWitnessScriptH160());

         break;
      }

      default:
         throw WalletException("unexpected asset type");
      }
   }

   return hash_;
}

////////////////////////////////////////////////////////////////////////////////
const BinaryData& AddressEntry_Nested_P2WPKH::getAddress() const
{
   if (address_.getSize() == 0)
      address_ = move(BtcUtils::scrAddrToBase58(getPrefixedHash()));

   return address_;
}

////////////////////////////////////////////////////////////////////////////////
shared_ptr<ScriptRecipient> AddressEntry_Nested_P2WPKH::getRecipient(
   uint64_t value) const
{
   BinaryDataRef scriptHash;

   switch (asset_->getType())
   {
   case AssetEntryType_Single:
   {
      auto assetSingle = dynamic_pointer_cast<AssetEntry_Single>(asset_);
      if (assetSingle == nullptr)
         throw WalletException("unexpected asset entry type");

      scriptHash = assetSingle->getWitnessScriptH160();
      
      break;
   }

   default:
      throw WalletException("unexpected asset type");
   }

   return make_shared<Recipient_P2SH>(scriptHash, value);
}

////////////////////////////////////////////////////////////////////////////////
const BinaryData& AddressEntry_Nested_P2WSH::getPrefixedHash() const
{
   uint8_t prefix = BlockDataManagerConfig::getScriptHashPrefix();

   if (hash_.getSize() == 0)
   {
      switch (asset_->getType())
      {
      case AssetEntryType_Multisig:
      {
         auto assetMS = dynamic_pointer_cast<AssetEntry_Multisig>(asset_);
         if (assetMS == nullptr)
            throw WalletException("unexpected asset entry type");

         hash_.append(prefix);
         hash_.append(assetMS->getP2WSHScriptH160());

         break;
      }

      default:
         throw WalletException("unexpected asset type");
      }
   }

   return hash_;
}

////////////////////////////////////////////////////////////////////////////////
const BinaryData& AddressEntry_Nested_P2WSH::getAddress() const
{
   if (address_.getSize() == 0)
      address_ = move(BtcUtils::scrAddrToBase58(getPrefixedHash()));

   return address_;
}

////////////////////////////////////////////////////////////////////////////////
shared_ptr<ScriptRecipient> AddressEntry_Nested_P2WSH::getRecipient(
   uint64_t value) const
{
   BinaryDataRef scriptHash;

   switch (asset_->getType())
   {
   case AssetEntryType_Multisig:
   {
      auto assetMS = dynamic_pointer_cast<AssetEntry_Multisig>(asset_);
      if (assetMS == nullptr)
         throw WalletException("unexpected asset entry type");

      scriptHash = assetMS->getP2WSHScriptH160();

      break;
   }

   default:
      throw WalletException("unexpected asset type");
   }

   return make_shared<Recipient_P2SH>(scriptHash, value);
}

////////////////////////////////////////////////////////////////////////////////
size_t AddressEntry_Nested_P2WSH::getWitnessDataSize() const
{
   switch (asset_->getType())
   {
   case AssetEntryType_Multisig:
   {
      auto assetMS = dynamic_pointer_cast<AssetEntry_Multisig>(asset_);
      if (assetMS == nullptr)
         throw WalletException("unexpected asset entry type");

      auto m = assetMS->getM();

      size_t size = assetMS->getScript().getSize() + 2;
      size += 73 * m + 2;

      return size;
   }

   default:
      throw WalletException("unexpected asset type");
   }

   return SIZE_MAX;
}

////////////////////////////////////////////////////////////////////////////////
const BinaryData& AddressEntry_Nested_P2PK::getPrefixedHash() const
{
   uint8_t prefix = BlockDataManagerConfig::getScriptHashPrefix();

   if (hash_.getSize() == 0)
   {
      switch (asset_->getType())
      {
      case AssetEntryType_Single:
      {
         auto assetSingle = dynamic_pointer_cast<AssetEntry_Single>(asset_);
         if (assetSingle == nullptr)
            throw WalletException("unexpected asset entry type");

         hash_.append(prefix);
         hash_.append(assetSingle->getP2PKScriptH160());

         break;
      }

      default:
         throw WalletException("unexpected asset type");
      }
   }

   return hash_;
}

////////////////////////////////////////////////////////////////////////////////
const BinaryData& AddressEntry_Nested_P2PK::getAddress() const
{
   if (address_.getSize() == 0)
      address_ = move(BtcUtils::scrAddrToBase58(getPrefixedHash()));

   return address_;
}

////////////////////////////////////////////////////////////////////////////////
shared_ptr<ScriptRecipient> AddressEntry_Nested_P2PK::getRecipient(
   uint64_t value) const
{
   BinaryDataRef scriptHash;

   switch (asset_->getType())
   {
   case AssetEntryType_Single:
   {
      auto assetSingle = dynamic_pointer_cast<AssetEntry_Single>(asset_);
      if (assetSingle == nullptr)
         throw WalletException("unexpected asset entry type");

      scriptHash = assetSingle->getP2PKScriptH160();

      break;
   }

   default:
      throw WalletException("unexpected asset type");
   }

   return make_shared<Recipient_P2SH>(scriptHash, value);
}

////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
//// Asset
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
Asset::~Asset()
{}

////////////////////////////////////////////////////////////////////////////////
BinaryData Asset_PublicKey::serialize() const
{
   BinaryWriter bw;
  
   bw.put_var_int(uncompressed_.getSize() + 1);
   bw.put_uint8_t(PUBKEY_UNCOMPRESSED_BYTE);
   bw.put_BinaryData(uncompressed_);

   bw.put_var_int(compressed_.getSize() + 1);
   bw.put_uint8_t(PUBKEY_COMPRESSED_BYTE);
   bw.put_BinaryData(compressed_);

   return bw.getData();
}

////////////////////////////////////////////////////////////////////////////////
BinaryData Asset_PrivateKey::serialize() const
{
   BinaryWriter bw;

   bw.put_var_int(data_.getSize() + 1);
   bw.put_uint8_t(PRIVKEY_BYTE);
   bw.put_BinaryData(data_);

   auto&& cypherData = cypher_->serialize();
   bw.put_var_int(cypherData.getSize());
   bw.put_BinaryData(cypherData);

   return bw.getData();
}

////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
//// AssetEntry
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
AssetEntry::~AssetEntry(void)
{}

////////////////////////////////////////////////////////////////////////////////
const BinaryData& AssetEntry_Single::getHash160Uncompressed() const
{
   if (h160Uncompressed_.getSize() == 0)
      h160Uncompressed_ = 
         move(BtcUtils::getHash160_RunTwice(pubkey_->getUncompressedKey()));

   return h160Uncompressed_;
}

////////////////////////////////////////////////////////////////////////////////
const BinaryData& AssetEntry_Single::getHash160Compressed() const
{
   if (h160Compressed_.getSize() == 0)
      h160Compressed_ =
         move(BtcUtils::getHash160_RunTwice(pubkey_->getCompressedKey()));

   return h160Compressed_;
}

////////////////////////////////////////////////////////////////////////////////
const BinaryData& AssetEntry_Single::getWitnessScript() const
{
   if (witnessScript_.getSize() == 0)
   {
      auto& hash = getHash160Compressed();
      Recipient_P2WPKH recipient(hash, 0);

      auto& script = recipient.getSerializedScript();

      witnessScript_ = move(script.getSliceCopy(9, script.getSize() - 9));
   }

   return witnessScript_;
}

////////////////////////////////////////////////////////////////////////////////
const BinaryData& AssetEntry_Single::getWitnessScriptH160() const
{
   if (witnessScriptH160_.getSize() == 0)
      witnessScriptH160_ =
         move(BtcUtils::getHash160_RunTwice(getWitnessScript()));

   return witnessScriptH160_;
}

////////////////////////////////////////////////////////////////////////////////
const BinaryData& AssetEntry_Single::getP2PKScript() const
{
   if (p2pkScript_.getSize() == 0)
   {
      p2pkScript_.append(33); //push data opcode for pubkey len
      p2pkScript_.append(pubkey_->getCompressedKey()); //compressed pubkey
      p2pkScript_.append(OP_CHECKSIG); 
   }

   return p2pkScript_;
}

////////////////////////////////////////////////////////////////////////////////
const BinaryData& AssetEntry_Single::getP2PKScriptH160() const
{
   if (p2pkScriptH160_.getSize() == 0)
      p2pkScriptH160_ =
         move(BtcUtils::getHash160_RunTwice(getP2PKScript()));

   return p2pkScriptH160_;
}

////////////////////////////////////////////////////////////////////////////////
AddressEntryType AssetEntry_Single::getAddressTypeForHash(
   BinaryDataRef hashRef) const
{
   auto& h160Unc = getHash160Uncompressed();
   if (hashRef == h160Unc)
      return AddressEntryType_P2PKH;
   
   auto& nestedP2PKScriptHash = getP2PKScriptH160();
   if (hashRef == nestedP2PKScriptHash)
      return AddressEntryType_Nested_P2PK;

   auto& nestedScriptHash = getWitnessScriptH160();
   if (hashRef == nestedScriptHash)
      return AddressEntryType_Nested_P2WPKH;


   return AddressEntryType_Default;
}

////////////////////////////////////////////////////////////////////////////////
map<ScriptHashType, BinaryDataRef> AssetEntry_Single::getScriptHashMap() const
{
   map<ScriptHashType, BinaryDataRef> result;

   result.insert(make_pair(
      ScriptHash_P2PKH_Uncompressed, getHash160Uncompressed().getRef()));

   result.insert(make_pair(
      ScriptHash_P2PKH_Compressed, getHash160Compressed().getRef()));

   result.insert(make_pair(
      ScriptHash_P2WPKH, getWitnessScriptH160().getRef()));

   result.insert(make_pair(
      ScriptHash_Nested_P2PK, getP2PKScriptH160().getRef()));

   return result;
}

////////////////////////////////////////////////////////////////////////////////
const BinaryData& AssetEntry_Multisig::getScript() const
{
   if (multisigScript_.getSize() == 0)
   {
      BinaryWriter bw;

      //convert m to opcode and push
      auto m = m_ + OP_1 - 1;
      if (m > OP_16)
         throw WalletException("m exceeds OP_16");
      bw.put_uint8_t(m);

      //put pub keys
      for (auto& asset : assetMap_)
      {
         auto assetSingle =
            dynamic_pointer_cast<AssetEntry_Single>(asset.second);

         if (assetSingle == nullptr)
            WalletException("unexpected asset entry type");

         //using compressed keys
         auto& pubkeyCpr = assetSingle->getPubKey()->getCompressedKey();
         if (pubkeyCpr.getSize() != 33)
            throw WalletException("unexpected compress pub key len");

         bw.put_uint8_t(33);
         bw.put_BinaryData(pubkeyCpr);
      }

      //convert n to opcode and push
      auto n = n_ + OP_1 - 1;
      if (n > OP_16 || n < m)
         throw WalletException("invalid n");
      bw.put_uint8_t(n);

      bw.put_uint8_t(OP_CHECKMULTISIG);
      multisigScript_ = bw.getData();
   }

   return multisigScript_;
}

////////////////////////////////////////////////////////////////////////////////
const BinaryData& AssetEntry_Multisig::getHash160() const
{
   if (assetMap_.size() != n_)
      throw WalletException("asset count mismatch in multisig entry");

   if (h160_.getSize() == 0)
   {
      auto& msScript = getScript();
      h160_ = move(BtcUtils::getHash160_RunTwice(msScript));
   }

   return h160_;
}

////////////////////////////////////////////////////////////////////////////////
const BinaryData& AssetEntry_Multisig::getHash256() const
{
   if (assetMap_.size() != n_)
      throw WalletException("asset count mismatch in multisig entry");

   if (h256_.getSize() == 0)
   {
      auto& msScript = getScript();
      h256_ = move(BtcUtils::getSha256_RunTwice(msScript));
   }

   return h256_;
}

////////////////////////////////////////////////////////////////////////////////
const BinaryData& AssetEntry_Multisig::getP2WSHScript() const
{
   if (p2wshScript_.getSize() == 0)
   {
      auto& hash256 = getHash256();

      Recipient_PW2SH recipient(hash256, 0);
      auto& script = recipient.getSerializedScript();

      p2wshScript_ = move(script.getSliceCopy(9, script.getSize() - 9));
   }

   return p2wshScript_;
}

////////////////////////////////////////////////////////////////////////////////
const BinaryData& AssetEntry_Multisig::getP2WSHScriptH160() const
{
   if (p2wshScriptH160_.getSize() == 0)
   {
      auto& script = getP2WSHScript();

      p2wshScriptH160_ = move(BtcUtils::getHash160_RunTwice(script));
   }

   return p2wshScriptH160_;
}

////////////////////////////////////////////////////////////////////////////////
AddressEntryType AssetEntry_Multisig::getAddressTypeForHash(
   BinaryDataRef hashRef) const
{
   auto& nested = getP2WSHScriptH160();
   if (nested == hashRef)
      return AddressEntryType_Nested_P2WSH;

   auto& p2sh = getHash160();
   if (p2sh == hashRef)
      return AddressEntryType_Nested_Multisig;

   return AddressEntryType_Default;
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
bool AssetEntry::setAddressEntryType(AddressEntryType type)
{
   if (type == addressType_)
      return false;

   addressType_ = type;
   needsCommit_ = true;

   return true;
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
   BinaryRefReader brrVal(value);
   auto val = brrVal.get_uint8_t();

   auto entryType = AssetEntryType(val & 0x0F);
   auto addressType = AddressEntryType((val & 0xF0) >> 4);

   switch (entryType)
   {
   case AssetEntryType_Single:
   {
      SecureBinaryData privKey;
      SecureBinaryData pubKeyCompressed;
      SecureBinaryData pubKeyUncompressed;
      unique_ptr<Cypher> cypher;

      vector<BinaryDataRef> dataVec;

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
         case PUBKEY_UNCOMPRESSED_BYTE:
         {
            if (pubKeyUncompressed.getSize() != 0)
               throw AssetDeserException("multiple pub keys for entry");

            pubKeyUncompressed = move(SecureBinaryData(
               brrData.get_BinaryDataRef(
               brrData.getSizeRemaining())));

            break;
         }

         case PUBKEY_COMPRESSED_BYTE:
         {
            if (pubKeyCompressed.getSize() != 0)
               throw AssetDeserException("multiple pub keys for entry");

            pubKeyCompressed = move(SecureBinaryData(
               brrData.get_BinaryDataRef(
               brrData.getSizeRemaining())));

            break;
         }

         case PRIVKEY_BYTE:
         {
            if (privKey.getSize() != 0)
               throw AssetDeserException("multiple pub keys for entry");

            privKey = move(SecureBinaryData(
               brrData.get_BinaryDataRef(
               brrData.getSizeRemaining())));

            break;
         }

         case CYPHER_BYTE:
         {
            if (cypher != nullptr)
               throw AssetDeserException("multiple cyphers for entry");

            cypher = move(Cypher::deserialize(brrData));

            break;
         }

         default:
            throw AssetDeserException("unknown key type byte");
         }
      }

      //TODO: add IVs as args for encrypted entries
      auto addrEntry = make_shared<AssetEntry_Single>(index, 
         move(pubKeyUncompressed), move(pubKeyCompressed), move(privKey), move(cypher));
      
      addrEntry->setAddressEntryType(addressType);
      addrEntry->doNotCommit();

      return addrEntry;
   }

   default:
      throw AssetDeserException("invalid asset entry type");
   }
}

////////////////////////////////////////////////////////////////////////////////
BinaryData AssetEntry_Single::serialize() const
{
   BinaryWriter bw;
   auto entryType = getType();
   auto addressType = getAddrType() << 4;
   bw.put_uint8_t(addressType | entryType);

   bw.put_BinaryData(pubkey_->serialize());
   if (privkey_->hasKey())
      bw.put_BinaryData(privkey_->serialize());
   
   BinaryWriter finalBw;

   finalBw.put_var_int(bw.getSize());
   finalBw.put_BinaryData(bw.getData());

   return finalBw.getData();
}

////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
//// Cypher
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
Cypher::~Cypher()
{}

////////////////////////////////////////////////////////////////////////////////
unique_ptr<Cypher> Cypher::deserialize(BinaryRefReader& brr)
{
   unique_ptr<Cypher> cypher;
   auto type = brr.get_uint8_t();

   switch (type)
   {
   case CypherType_AES:
   {
      auto len = brr.get_var_int();
      auto&& iv = SecureBinaryData(brr.get_BinaryDataRef(len));

      cypher = move(make_unique<Cypher_AES>(move(iv)));

      break;
   }

   default:
      throw CypherException("unexpected cypher type");
   }

   return move(cypher);
}

////////////////////////////////////////////////////////////////////////////////
BinaryData Cypher_AES::serialize() const
{
   BinaryWriter bw;
   bw.put_uint8_t(CYPHER_BYTE);
   bw.put_uint8_t(getType());
   bw.put_var_int(iv_.getSize());
   bw.put_BinaryData(iv_);

   return bw.getData();
}

////////////////////////////////////////////////////////////////////////////////
unique_ptr<Cypher> Cypher_AES::getCopy() const
{
   return make_unique<Cypher_AES>();
}