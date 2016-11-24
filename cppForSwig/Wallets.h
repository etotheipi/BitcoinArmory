////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2016, goatpig                                               //
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#ifndef _WALLETS_H
#define _WALLETS_H

#include <atomic>
#include <mutex>
#include <memory>
#include <set>
#include <map>
#include <string>

#include "BinaryData.h"
#include "EncryptionUtils.h"
#include "lmdbpp.h"
#include "Script.h"
#include "Signer.h"

using namespace std;

#define PUBKEY_UNCOMPRESSED_BYTE 0x80
#define PUBKEY_COMPRESSED_BYTE 0x81
#define PRIVKEY_BYTE 0x82

#define WALLETTYPE_KEY        0x00000001
#define PARENTID_KEY          0x00000002
#define WALLETID_KEY          0x00000003
#define DERIVATIONSCHEME_KEY  0x00000004
#define ADDRESSENTRYTYPE_KEY  0x00000005
#define TOPUSEDINDEX_KEY      0x00000006
#define ROOTASSET_KEY         0x00000007

#define MASTERID_KEY          0x000000A0
#define MAINWALLET_KEY        0x000000A1

#define WALLETMETA_PREFIX     0xB0
#define ASSETENTRY_PREFIX     0xAA

#define DERIVATIONSCHEME_LEGACY     0xA0
#define DERIVATIONSCHEME_BIP32      0xA1
#define DERIVATIONSCHEME_MULTISIG   0xA2
#define DERIVATION_LOOKUP           100

#define CYPHER_BYTE  0x90

#define WALLETMETA_DBNAME "WalletHeader"
 
class WalletException : public runtime_error
{
public:
   WalletException(const string& msg) : runtime_error(msg)
   {}
};

class NoEntryInWalletException
{};

class AssetUnavailableException
{};

class AssetDeserException : public runtime_error
{
public:
   AssetDeserException(const string& msg) : runtime_error(msg)
   {}
};

class DerivationSchemeDeserException : public runtime_error
{
public:
   DerivationSchemeDeserException(const string& msg) : runtime_error(msg)
   {}
};

class CypherException : public runtime_error
{
public:
   CypherException(const string& msg) : runtime_error(msg)
   {}
};

////////////////////////////////////////////////////////////////////////////////
enum WalletMetaType
{
   WalletMetaType_Single,
   WalletMetaType_Multisig,
   WalletMetaType_Subwallet
};

////
struct WalletMeta
{
   LMDBEnv* dbEnv_;
   WalletMetaType type_;
   BinaryData parentID_;
   BinaryData walletID_;
   string dbName_;

   //tors
   WalletMeta(LMDBEnv* env, WalletMetaType type) :
      dbEnv_(env), type_(type)
   {}

   virtual ~WalletMeta(void) = 0;
   
   //local
   BinaryData getDbKey(void);
   const BinaryData& getWalletID(void) const { return walletID_; }
   string getWalletIDStr(void) const
   {
      if (walletID_.getSize() == 0)
         throw WalletException("empty wallet id");

      string idStr(walletID_.getCharPtr(), walletID_.getSize());
      return idStr;
   }

   //virtual
   virtual BinaryData serialize(void) const = 0;
   virtual bool shouldLoad(void) const = 0;

   //static
   static shared_ptr<WalletMeta> deserialize(LMDBEnv* env,
      BinaryDataRef key, BinaryDataRef val);
};

////
struct WalletMeta_Single : public WalletMeta
{
   //tors
   WalletMeta_Single(LMDBEnv* dbEnv) :
      WalletMeta(dbEnv, WalletMetaType_Single)
   {}

   //virtual
   BinaryData serialize(void) const;
   bool shouldLoad(void) const;
};

////
struct WalletMeta_Multisig : public WalletMeta
{
   //tors
   WalletMeta_Multisig(LMDBEnv* dbEnv) :
      WalletMeta(dbEnv, WalletMetaType_Multisig)
   {}

   //virtual
   BinaryData serialize(void) const;
   bool shouldLoad(void) const;
};

////
struct WalletMeta_Subwallet : public WalletMeta
{
   //tors
   WalletMeta_Subwallet(LMDBEnv* dbEnv) :
      WalletMeta(dbEnv, WalletMetaType_Subwallet)
   {}

   //virtual
   BinaryData serialize(void) const;
   bool shouldLoad(void) const;
};


////////////////////////////////////////////////////////////////////////////////
enum AssetType
{
   AssetType_PublicKey,
   AssetType_PrivateKey,
   AssetType_MetaData
};

////
enum AssetEntryType
{
   AssetEntryType_Single = 0x01,
   AssetEntryType_Multisig
};

////
enum AddressEntryType
{
   AddressEntryType_P2PKH,
   AddressEntryType_P2SH,
   AddressEntryType_P2WSH,
   AddressEntryType_P2WPKH,
};

enum CypherType
{
   CypherType_AES,
   CypherType_Serpent
};

////////////////////////////////////////////////////////////////////////////////
class Cypher
{
private:
   const CypherType type_;

protected:
   SecureBinaryData iv_;
   //TODO: add kdf

public:

   //tors
   Cypher(CypherType type) :
      type_(type)
   {}

   virtual ~Cypher(void) = 0;

   //locals
   CypherType getType(void) const { return type_; }

   //virtuals
   virtual BinaryData serialize(void) const = 0;
   virtual unique_ptr<Cypher> getCopy(void) const = 0;

   //statics
   static unique_ptr<Cypher> deserialize(BinaryRefReader& brr);
};

////
class Cypher_AES : public Cypher
{
public:
   //tors
   Cypher_AES() :
      Cypher(CypherType_AES)
   {
      //init IV
      iv_ = move(SecureBinaryData().GenerateRandom(BTC_AES::BLOCKSIZE));
   }

   Cypher_AES(SecureBinaryData&& iv) :
      Cypher(CypherType_AES)
   {
      if (iv.getSize() != BTC_AES::BLOCKSIZE)
         throw CypherException("invalid iv length");

      iv_ = move(iv);
   }

   //virtuals
   BinaryData serialize(void) const;
   unique_ptr<Cypher> getCopy(void) const;
};

////////////////////////////////////////////////////////////////////////////////
struct Asset
{
   const AssetType type_;

   Asset(AssetType type) : 
      type_(type)
   {}

   /*TODO: create a mlocked binarywriter class*/

   virtual ~Asset(void) = 0;
   virtual BinaryData serialize(void) const = 0;
};

////////////////////////////////////////////////////////////////////////////////
struct Asset_PublicKey : public Asset
{
public:
   SecureBinaryData uncompressed_;
   SecureBinaryData compressed_;

public:
   Asset_PublicKey(SecureBinaryData&& pubkey) :
      Asset(AssetType_PublicKey)
   {
      switch (pubkey.getSize())
      {
      case 33:
      {
         uncompressed_ = move(CryptoECDSA().UncompressPoint(pubkey));
         compressed_ = move(pubkey);
         break;
      }

      case 65:
      {
         compressed_ = move(CryptoECDSA().CompressPoint(pubkey));
         uncompressed_ = move(pubkey);
         break;
      }

      default:
         throw WalletException("cannot compress/decompress pubkey of that size");
      }
   }

   Asset_PublicKey(SecureBinaryData&& uncompressedKey, 
      SecureBinaryData&& compressedKey) :
      Asset(AssetType_PublicKey), 
      uncompressed_(move(uncompressedKey)),
      compressed_(move(compressedKey))
   {
      if (uncompressed_.getSize() != 65 ||
         compressed_.getSize() != 33)
         throw WalletException("invalid pubkey size");
   }

   const SecureBinaryData& getUncompressedKey(void) const { return uncompressed_; }
   const SecureBinaryData& getCompressedKey(void) const { return compressed_; }

   BinaryData serialize(void) const;
};

////////////////////////////////////////////////////////////////////////////////
struct Asset_PrivateKey : public Asset
{
public:
   SecureBinaryData data_;
   unique_ptr<Cypher> cypher_;

public:
   Asset_PrivateKey(SecureBinaryData&& data, unique_ptr<Cypher> cypher) :
      Asset(AssetType_PrivateKey), data_(move(data))
   {
      if (data_.getSize() == 0)
         return;
      
      if(cypher == nullptr)
         throw WalletException("null cypher for privkey");

      cypher_ = move(cypher);
   }
   
   const SecureBinaryData& getKey(void) const 
   { 
      if (!hasKey())
         throw AssetUnavailableException();

      return data_; 
   }

   BinaryData serialize(void) const;
   bool hasKey(void) const { return (data_.getSize() == 32); }
};

////////////////////////////////////////////////////////////////////////////////
class AssetEntry
{
protected:
   const int index_;
   AssetEntryType type_;

public:
   //tors
   AssetEntry(AssetEntryType type, int id) :
      type_(type), index_(id)
   {}

   virtual ~AssetEntry(void) = 0;

   //local
   int getId(void) const { return index_; }
   const AssetEntryType getType(void) const { return type_; }
   BinaryData getDbKey(void) const;

   //virtual
   virtual BinaryData serialize(void) const = 0;

   //static
   static shared_ptr<AssetEntry> deserialize(
      BinaryDataRef key, BinaryDataRef value);
   static shared_ptr<AssetEntry> deserDBValue(
      int index, BinaryDataRef value);
};

////
class AssetEntry_Single : public AssetEntry
{
private:
   shared_ptr<Asset_PublicKey> pubkey_;
   shared_ptr<Asset_PrivateKey> privkey_;

   mutable BinaryData h160Uncompressed_;
   mutable BinaryData h160Compressed_;
   mutable BinaryData h256Compressed_;

public:
   //tors
   AssetEntry_Single(int id,
      SecureBinaryData&& pubkey, SecureBinaryData&& privkey,
      unique_ptr<Cypher> cypher) :
      AssetEntry(AssetEntryType_Single, id)
   {
      pubkey_ = make_shared<Asset_PublicKey>(move(pubkey));
      privkey_ = make_shared<Asset_PrivateKey>(move(privkey), move(cypher));
   }

   AssetEntry_Single(int id,
      SecureBinaryData&& pubkeyUncompressed,
      SecureBinaryData&& pubkeyCompressed, 
      SecureBinaryData&& privkey,
      unique_ptr<Cypher> cypher) :
      AssetEntry(AssetEntryType_Single, id)
   {
      pubkey_ = make_shared<Asset_PublicKey>(
         move(pubkeyUncompressed), move(pubkeyCompressed));
      privkey_ = make_shared<Asset_PrivateKey>(move(privkey), move(cypher));
   }

   AssetEntry_Single(int id,
      shared_ptr<Asset_PublicKey> pubkey,
      shared_ptr<Asset_PrivateKey> privkey) :
      AssetEntry(AssetEntryType_Single, id),
      pubkey_(pubkey), privkey_(privkey)
   {}

   //local
   shared_ptr<Asset_PublicKey> getPubKey(void) const { return pubkey_; }
   shared_ptr<Asset_PrivateKey> getPrivKey(void) const { return privkey_; }

   const BinaryData& getHash160Uncompressed(void) const;
   const BinaryData& getHash160Compressed(void) const;
   const BinaryData& getHash256Compressed(void) const;

   //virtual
   BinaryData serialize(void) const;
};

////
class AssetEntry_Multisig : public AssetEntry
{
   friend class ResolvedFeed_AssetWalletMS;

private:
   const map<BinaryData, shared_ptr<AssetEntry>> assetMap_;
   const unsigned m_;
   const unsigned n_;

   mutable BinaryData multisigScript_;
   mutable BinaryData h160_;
   mutable BinaryData h256_;

public:
   //tors
   AssetEntry_Multisig(int id,
      const map<BinaryData, shared_ptr<AssetEntry>>& assetMap,
      unsigned m, unsigned n) :
      AssetEntry(AssetEntryType_Multisig, id), 
      assetMap_(assetMap), m_(m), n_(n)
   {
      if (assetMap.size() != n)
         throw WalletException("asset count mismatch in multisig entry");
   }
   
   //local
   const BinaryData& getScript(void) const;
   const BinaryData& getHash160(void) const;
   const BinaryData& getHash256(void) const;

   //virtual
   BinaryData serialize(void) const 
   { 
      throw AssetDeserException("no serialization for MS assets"); 
   }

};

////////////////////////////////////////////////////////////////////////////////
struct DerivationScheme
{
public:
   //tors
   virtual ~DerivationScheme(void) = 0;

   //virtual
   virtual vector<shared_ptr<AssetEntry>> extendChain(
      shared_ptr<AssetEntry>, unsigned) = 0;
   virtual BinaryData serialize(void) const = 0;

   //static
   static shared_ptr<DerivationScheme> deserialize(BinaryDataRef);
};

////
struct DerivationScheme_ArmoryLegacy : public DerivationScheme
{
private:
   SecureBinaryData chainCode_;

public:
   //tors
   DerivationScheme_ArmoryLegacy(SecureBinaryData&& chainCode) :
      chainCode_(move(chainCode))
   {}

   //virtuals
   vector<shared_ptr<AssetEntry>> extendChain(
      shared_ptr<AssetEntry>, unsigned);
   BinaryData serialize(void) const;

   const SecureBinaryData& getChainCode(void) const { return chainCode_; }
};

class AssetWallet;
class AssetWallet_Single;

////
struct DerivationScheme_Multisig : public DerivationScheme
{
private:
   const unsigned n_;
   const unsigned m_;

   set<BinaryData> walletIDs_;
   map<BinaryData, shared_ptr<AssetWallet_Single>> wallets_;


public:
   //tors
   DerivationScheme_Multisig(
      const map<BinaryData, shared_ptr<AssetWallet_Single>>& wallets,
      unsigned n, unsigned m) :
      n_(n), m_(m), wallets_(wallets)
   {
      for (auto& wallet : wallets)
         walletIDs_.insert(wallet.first);
   }

   DerivationScheme_Multisig(const set<BinaryData>& walletIDs,
      unsigned n, unsigned m) :
      n_(n), m_(m), walletIDs_(walletIDs)
   {}

   //local
   shared_ptr<AssetEntry_Multisig> getAssetForIndex(unsigned) const;
   unsigned getN(void) const { return n_; }
   const set<BinaryData>& getWalletIDs(void) const { return walletIDs_; }
   void setSubwalletPointers(
      map<BinaryData, shared_ptr<AssetWallet_Single>> ptrMap);

   //virtual
   BinaryData serialize(void) const;
   vector<shared_ptr<AssetEntry>> extendChain(
      shared_ptr<AssetEntry>, unsigned);
};

////////////////////////////////////////////////////////////////////////////////
class AddressEntry
{
protected:
   const AddressEntryType type_;
   const shared_ptr<AssetEntry> asset_;

public:
   //tors
   AddressEntry(AddressEntryType aetype, shared_ptr<AssetEntry> asset) :
      asset_(asset), type_(aetype)
   {}

   virtual ~AddressEntry(void) = 0;

   //local
   AddressEntryType getType(void) const { return type_; }
   int getIndex(void) const { return asset_->getId(); }

   //virtual
   virtual const BinaryData& getAddress(void) const = 0;
   virtual shared_ptr<ScriptRecipient> getRecipient(uint64_t) const = 0;
};

////////////////////////////////////////////////////////////////////////////////
class AddressEntry_P2PKH : public AddressEntry
{
private:
   mutable BinaryData address_;

public:
   //tors
   AddressEntry_P2PKH(shared_ptr<AssetEntry> asset) :
      AddressEntry(AddressEntryType_P2PKH, asset)
   {}

   //virtual
   const BinaryData& getAddress(void) const;
   shared_ptr<ScriptRecipient> getRecipient(uint64_t) const;
};

////////////////////////////////////////////////////////////////////////////////
class AddressEntry_P2WPKH : public AddressEntry
{
private:
   mutable BinaryData address_;

public:
   //tors
   AddressEntry_P2WPKH(shared_ptr<AssetEntry> asset) :
      AddressEntry(AddressEntryType_P2WPKH, asset)
   {}

   //virtual
   const BinaryData& getAddress(void) const;
   shared_ptr<ScriptRecipient> getRecipient(uint64_t) const;
};

////////////////////////////////////////////////////////////////////////////////
class AddressEntry_P2SH : public AddressEntry
{
private:
   mutable BinaryData address_;

public:
   //tors
   AddressEntry_P2SH(shared_ptr<AssetEntry> asset) :
      AddressEntry(AddressEntryType_P2SH, asset)
   {}

   //virtual
   const BinaryData& getAddress(void) const;
   shared_ptr<ScriptRecipient> getRecipient(uint64_t) const;
};

////////////////////////////////////////////////////////////////////////////////
class AddressEntry_P2WSH : public AddressEntry
{
private:
   mutable BinaryData address_;

public:
   //tors
   AddressEntry_P2WSH(shared_ptr<AssetEntry> asset) :
      AddressEntry(AddressEntryType_P2WSH, asset)
   {}

   //virtual
   const BinaryData& getAddress(void) const;
   shared_ptr<ScriptRecipient> getRecipient(uint64_t) const;
};

////////////////////////////////////////////////////////////////////////////////
class AssetWallet
{
   friend class ResolvedFeed_AssetWalletSingle;
   friend class ResolvedFeed_AssetWalletMS;

protected:
   LMDBEnv* dbEnv_ = nullptr;
   LMDB* db_ = nullptr;
   const string dbName_;
   bool ownsEnv_ = false;

   mutex walletMutex_;
   size_t mutexTID_ = SIZE_MAX;

   ////
   struct LockStruct
   {
      AssetWallet* wltPtr_;
      unique_ptr<unique_lock<mutex>> lock_;

      LockStruct(AssetWallet* wltPtr) :
         wltPtr_(wltPtr)
      {
         if (wltPtr == nullptr)
            throw WalletException("empty wlt ptr");

         lock_ = 
            make_unique<unique_lock<mutex>>(wltPtr->walletMutex_, defer_lock);
         if (wltPtr->mutexTID_ != this_thread::get_id().hash())
         { 
            lock_->lock();
            wltPtr->mutexTID_ = this_thread::get_id().hash();
         }
      }

      ~LockStruct(void)
      {
         if (lock_ == nullptr)
            return;

         if (lock_->owns_lock())
         {
            if (wltPtr_ != nullptr)
               wltPtr_->mutexTID_ = SIZE_MAX;
         }
      }
   };

   atomic<int> highestUsedAddressIndex_;

   shared_ptr<AssetEntry> root_;
   map<int, shared_ptr<AssetEntry>> assets_;
   map<int, shared_ptr<AddressEntry>> addresses_;

   shared_ptr<DerivationScheme> derScheme_;
   AddressEntryType default_aet_;

   ////
   BinaryData parentID_;
   BinaryData walletID_;
   
protected:
   //tors
   AssetWallet(shared_ptr<WalletMeta> metaPtr) :
      dbEnv_(metaPtr->dbEnv_), dbName_(metaPtr->dbName_)
   {
      db_ = new LMDB(dbEnv_, dbName_);
   }

   static LMDBEnv* getEnvFromFile(const string& path, unsigned dbCount = 3)
   {
      LMDBEnv* env = new LMDBEnv(dbCount);
      env->open(path);

      return env;
   }

   //local
   void writeAssetEntry(shared_ptr<AssetEntry>);
   BinaryDataRef getDataRefForKey(const BinaryData& key) const;

   void putData(const BinaryData& key, const BinaryData& data);
   void putData(BinaryWriter& key, BinaryWriter& data);

   unsigned getAndBumpHighestUsedIndex(void);

   //virtual
   virtual void putHeaderData(const BinaryData& parentID,
      const BinaryData& walletID,
      shared_ptr<DerivationScheme>,
      AddressEntryType,
      int topUsedIndex);

   virtual shared_ptr<AddressEntry> getAddressEntryForAsset(
      shared_ptr<AssetEntry>, 
      AddressEntryType) = 0;

   //static
   static BinaryDataRef getDataRefForKey(const BinaryData& key, LMDB* db);
   static unsigned getDbCountAndNames(
      LMDBEnv* dbEnv, 
      map<BinaryData, shared_ptr<WalletMeta>>&, 
      BinaryData& masterID, 
      BinaryData& mainWalletID);
   static void putDbName(LMDB* db, shared_ptr<WalletMeta>);
   static void setMainWallet(LMDB* db, shared_ptr<WalletMeta>);
   static void putData(LMDB* db, const BinaryData& key, const BinaryData& data);
   static void initWalletMetaDB(LMDBEnv*, const string&);

   //locking local

public:
   //tors
   ~AssetWallet()
   {
      derScheme_.reset();

      if (db_ != nullptr)
      {
         db_->close();
         delete db_;
         db_ = nullptr;
      }

      if (dbEnv_ != nullptr && 
          ownsEnv_)
      {
         dbEnv_->close();
         delete dbEnv_;
         dbEnv_ = nullptr;
      }

      addresses_.clear();
      assets_.clear();
   }

   //local
   shared_ptr<AddressEntry> getNewAddress();
   string getID(void) const;   
   
   shared_ptr<AssetEntry> getAssetForIndex(unsigned) const;
   unsigned getAssetCount(void) const { return assets_.size(); }
   void extendChain(unsigned);
   void extendChainTo(unsigned);
   void extendChain(shared_ptr<AssetEntry>, unsigned);

   //virtual
   virtual vector<BinaryData> getAddrHashVec(bool forceMainnetPrefix) const = 0;

   //static
   static shared_ptr<AssetWallet> loadMainWalletFromFile(const string& path);
};

////
class AssetWallet_Single : public AssetWallet
{
   friend class AssetWallet;
   friend class AssetWallet_Multisig;

protected:
   //locals
   void readFromFile(void);

   //virtual
   void putHeaderData(const BinaryData& parentID,
      const BinaryData& walletID,
      shared_ptr<DerivationScheme>,
      AddressEntryType,
      int topUsedIndex);

   shared_ptr<AddressEntry> getAddressEntryForAsset(
      shared_ptr<AssetEntry>,
      AddressEntryType);

   //static
   static shared_ptr<AssetWallet_Single> initWalletDb(
      shared_ptr<WalletMeta>,
      unique_ptr<Cypher>,
      AddressEntryType, 
      SecureBinaryData&& privateRoot,
      unsigned lookup);

   static shared_ptr<AssetWallet_Single> initWalletDbFromPubRoot(
      shared_ptr<WalletMeta>,
      AddressEntryType,
      SecureBinaryData&& pubRoot,
      SecureBinaryData&& chainCode,
      unsigned lookup);

   static BinaryData computeWalletID(
      shared_ptr<DerivationScheme>,
      shared_ptr<AssetEntry>);

public:
   //tors
   AssetWallet_Single(shared_ptr<WalletMeta> metaPtr) :
      AssetWallet(metaPtr)
   {}

   //virtual
   vector<BinaryData> getAddrHashVec(bool forceMainnetPrefix) const;

   //static
   static shared_ptr<AssetWallet_Single> createFromPrivateRoot_Armory135(
      const string& folder,
      AddressEntryType,
      SecureBinaryData&& privateRoot,
      unsigned lookup = UINT32_MAX);

   static shared_ptr<AssetWallet_Single> createFromPublicRoot_Armory135(
      const string& folder,
      AddressEntryType,
      SecureBinaryData&& privateRoot,
      SecureBinaryData&& chainCode,
      unsigned lookup = UINT32_MAX);

   //local

   /*These methods for getting hash vectors do not allow for prefix
   forcing as they are mostly there for unit tests*/
   vector<BinaryData> getHash160VecUncompressed(void) const;
   vector<BinaryData> getHash160VecCompressed(void) const;

   const SecureBinaryData& getPublicRoot(void) const;
   const SecureBinaryData& getChainCode(void) const;
};

////
class AssetWallet_Multisig : public AssetWallet
{
   friend class AssetWallet;

private:
   atomic<unsigned> chainLength_;

protected:
   //local
   void readFromFile(void);

public:
   //tors
   AssetWallet_Multisig(shared_ptr<WalletMeta> metaPtr) :
      AssetWallet(metaPtr)
   {}

   //virtual
   vector<BinaryData> getAddrHashVec(bool forceMainnetPrefix) const;

   shared_ptr<AddressEntry> getAddressEntryForAsset(
      shared_ptr<AssetEntry>,
      AddressEntryType);

   //static
   static shared_ptr<AssetWallet_Multisig> createFromPrivateRoot(
      const string& folder,
      AddressEntryType aet,
      unsigned M, unsigned N,
      SecureBinaryData&& privateRoot,
      unsigned lookup = UINT32_MAX
      );

   static shared_ptr<AssetWallet> createFromWallets(
      vector<shared_ptr<AssetWallet>> wallets,
      unsigned M,
      unsigned loopup = UINT32_MAX);
};

////////////////////////////////////////////////////////////////////////////////
class ResolvedFeed_AssetWalletSingle : public ResolverFeed
{
private:
   shared_ptr<AssetWallet> wltPtr_;

   map<BinaryDataRef, BinaryDataRef> hash_to_pubkey_;
   map<BinaryDataRef, shared_ptr<AssetEntry_Single>> pubkey_to_privkeyAsset_;

public:
   //tors
   ResolvedFeed_AssetWalletSingle(shared_ptr<AssetWallet_Single> wltPtr) :
      wltPtr_(wltPtr)
   {
      for (auto& entry : wltPtr->assets_)
      {
         auto assetSingle = 
            dynamic_pointer_cast<AssetEntry_Single>(entry.second);
         if (assetSingle == nullptr)
            throw WalletException("unexpected asset entry type in single wallet");

         auto h160UncompressedRef = BinaryDataRef(assetSingle->getHash160Uncompressed());
         auto h160CompressedRef = BinaryDataRef(assetSingle->getHash160Compressed());
         auto pubkeyUncompressedRef = 
            BinaryDataRef(assetSingle->getPubKey()->getUncompressedKey());
         auto pubkeyCompressedRef =
            BinaryDataRef(assetSingle->getPubKey()->getCompressedKey());

         hash_to_pubkey_.insert(make_pair(h160UncompressedRef, pubkeyUncompressedRef));
         hash_to_pubkey_.insert(make_pair(h160CompressedRef, pubkeyCompressedRef));
         
         pubkey_to_privkeyAsset_.insert(make_pair(pubkeyUncompressedRef, assetSingle));
         pubkey_to_privkeyAsset_.insert(make_pair(pubkeyCompressedRef, assetSingle));
      }
   }

   //virtual
   BinaryData getByVal(const BinaryData& key)
   {
      auto keyRef = BinaryDataRef(key);
      auto iter = hash_to_pubkey_.find(keyRef);
      if (iter == hash_to_pubkey_.end())
         throw runtime_error("invalid value");

      return iter->second;
   }

   SecureBinaryData getPrivKeyForPubkey(const BinaryData& pubkey)
   {
      auto pubkeyref = BinaryDataRef(pubkey);
      auto iter = pubkey_to_privkeyAsset_.find(pubkeyref);
      if (iter == pubkey_to_privkeyAsset_.end())
         throw runtime_error("invalid value");

      const auto& privkeyAsset = iter->second->getPrivKey();
      return privkeyAsset->getKey();
   }
};

////////////////////////////////////////////////////////////////////////////////
class ResolvedFeed_AssetWalletMS : public ResolverFeed
{
private:
   shared_ptr<AssetWallet> wltPtr_;

   map<BinaryDataRef, BinaryDataRef> hash_to_script_;
   map<BinaryDataRef, shared_ptr<AssetEntry_Single>> pubkey_to_privKeyasset_;

public:
   //tors
   ResolvedFeed_AssetWalletMS(shared_ptr<AssetWallet_Multisig> wltPtr) :
      wltPtr_(wltPtr)
   {
      for (auto& entry : wltPtr->assets_)
      {
         auto assetMS =
            dynamic_pointer_cast<AssetEntry_Multisig>(entry.second);
         if (assetMS == nullptr)
            throw WalletException("unexpected asset entry type in ms wallet");

         BinaryDataRef hash;
         switch (wltPtr->default_aet_)
         {
         case AddressEntryType_P2SH:
            hash = assetMS->getHash160().getRef();
            break;

         case AddressEntryType_P2WSH:
            hash = assetMS->getHash256().getRef();
            break;

         default:
            throw WalletException("unexpected AddressEntryType for MS wallet");
         }

         auto script = assetMS->getScript().getRef();
         hash_to_script_.insert(make_pair(hash, script));

         for (auto assetptr : assetMS->assetMap_)
         {
            auto assetSingle = 
               dynamic_pointer_cast<AssetEntry_Single>(assetptr.second);
            if (assetSingle == nullptr)
               throw WalletException("unexpected asset entry type in ms wallet");

            auto pubkeyCpr = 
               assetSingle->getPubKey()->getCompressedKey().getRef();

            pubkey_to_privKeyasset_.insert(make_pair(pubkeyCpr, assetSingle));
         }
      }
   }

   //virtual
   BinaryData getByVal(const BinaryData& key)
   {
      auto keyRef = BinaryDataRef(key);
      auto iter = hash_to_script_.find(keyRef);
      if (iter == hash_to_script_.end())
         throw runtime_error("invalid value");

      return iter->second;
   }

   SecureBinaryData getPrivKeyForPubkey(const BinaryData& pubkey)
   {
      auto pubkeyref = BinaryDataRef(pubkey);
      auto iter = pubkey_to_privKeyasset_.find(pubkeyref);
      if (iter == pubkey_to_privKeyasset_.end())
         throw runtime_error("invalid value");

      const auto& privkeyAsset = iter->second->getPrivKey();
      return privkeyAsset->getKey();
   }
};

#endif