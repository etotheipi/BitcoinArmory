////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2016, goatpig                                               //
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

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

#define PUBKEY_PLAINTEXT_BYTE 0x80
#define PRIVKEY_PLAINTEXT_BYTE 0x81

#define PARENTID_KEY          0x00000001
#define WALLETID_KEY          0x00000002
#define DERIVATIONSCHEME_KEY  0x00000003
#define ADDRESSTYPEENTRY_KEY  0x00000004
#define TOPUSEDINDEX_KEY      0x00000005
#define ROOTASSET_KEY         0x00000006
#define ASSETENTRY_PREFIX     0xAA

#define DERIVATIONSCHEME_LEGACY  0xA0
#define DERIVATIONSCHEME_BIP32   0xA1

#define DERIVATION_LOOKUP 100
 
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

class AssetEncryptedException
{};

class NeedsDecrypted
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


////////////////////////////////////////////////////////////////////////////////
enum AssetType
{
   Asset_PlainText,
   Asset_Encrypted
};

////
enum AssetEntryType
{
   AssetEntryType_PubPub = 0x01, //plain text pubkey, plain text priv key
   AssetEntryType_PubEnc, //plain text pubkey, encrypted priv key
   AssetEntryType_EncEnc, //both encrypted
   AssetEntryType_PubOff, //plain text pubkey, offline priv key
   AssetEntryType_EncOff  //encrypted pubkey, offline priv key
};

////
enum AddressEntryType
{
   AddressEntryType_P2PKH,
   AddressEntryType_P2SH,
   AddressEntryType_P2WP2SH,
   AddressEntryType_P2WPKH,
};

////////////////////////////////////////////////////////////////////////////////
struct Cypher
{

};

////////////////////////////////////////////////////////////////////////////////
struct Asset
{
   const AssetType type_;

   Asset(AssetType type) : 
      type_(type)
   {}

   virtual ~Asset(void) = 0;
   virtual const SecureBinaryData& getData(void) const = 0;
};

////////////////////////////////////////////////////////////////////////////////
struct PlainTextAsset : public Asset
{
public:
   const SecureBinaryData data_;

public:
   PlainTextAsset(SecureBinaryData&& data) :
     Asset(Asset_PlainText), data_(move(data))
   {}

   const SecureBinaryData& getData(void) const { return data_; }
};

////////////////////////////////////////////////////////////////////////////////
struct EncryptedAsset : public Asset
{
public:
   SecureBinaryData data_;
   SecureBinaryData iv_;
   shared_ptr<Cypher> cypher_;

public:
   EncryptedAsset(SecureBinaryData&& data, SecureBinaryData&& iv, 
      shared_ptr<Cypher> cypher) :
      Asset(Asset_Encrypted), data_(move(data)), iv_(move(iv)), cypher_(cypher)
   {}
   
   const SecureBinaryData& getData(void) const { return data_; }
   void Decrypt(const SecureBinaryData& passphrase);
};

////////////////////////////////////////////////////////////////////////////////
class AssetEntry
{
protected:
   const int index_;
   AssetEntryType type_;

public:
   AssetEntry(AssetEntryType type, int id) :
      type_(type), index_(id)
   {}

   virtual ~AssetEntry(void) = 0;

   int getId(void) const { return index_; }
   const AssetEntryType getType(void) const { return type_; }

   virtual shared_ptr<Asset> getPubKey(void) const = 0;
   virtual shared_ptr<Asset> getPrivKey(void) const = 0;
   virtual const BinaryData& getHash160(void) const = 0;
   virtual shared_ptr<AssetEntry> getNewAsset(
      SecureBinaryData&& pubKey, SecureBinaryData&& privKey) const = 0;

   ////
   virtual BinaryData serialize(void) const = 0;
   BinaryData getDbKey(void) const;

   static shared_ptr<AssetEntry> createFromRawData(AssetEntryType,
      SecureBinaryData&& pub, SecureBinaryData&& priv, int index = -1);
   static shared_ptr<AssetEntry> deserialize(
      BinaryDataRef key, BinaryDataRef value);
   static shared_ptr<AssetEntry> deserDBValue(int index, BinaryDataRef value);
};

////////////////////////////////////////////////////////////////////////////////
class AssetEntry_PubPub : public AssetEntry
{
private:
   shared_ptr<PlainTextAsset> pubkey_;
   shared_ptr<PlainTextAsset> privkey_;

   mutable BinaryData h160_;

public:
   AssetEntry_PubPub(int id,
      SecureBinaryData&& pubkey, SecureBinaryData&& privkey) :
      AssetEntry(AssetEntryType_PubPub, id)
   {
      pubkey_ = make_shared<PlainTextAsset>(move(pubkey));
      privkey_ = make_shared<PlainTextAsset>(move(privkey));
   }

   shared_ptr<Asset> getPubKey(void) const { return pubkey_; }
   shared_ptr<Asset> getPrivKey(void) const { return privkey_; }

   virtual shared_ptr<AssetEntry> getNewAsset(
      SecureBinaryData&& pubKey, SecureBinaryData&& privKey) const
   {
      return make_shared<AssetEntry_PubPub>(
         index_ + 1, move(pubKey), move(privKey));
   }

   const BinaryData& getHash160(void) const;

   ////
   BinaryData serialize(void) const;
};

////////////////////////////////////////////////////////////////////////////////
struct DerivationScheme
{
public:
   virtual ~DerivationScheme(void) = 0;
   virtual shared_ptr<AssetEntry> getNextAsset(shared_ptr<AssetEntry>) = 0;

   virtual BinaryData serialize(void) const = 0;
   static shared_ptr<DerivationScheme> deserialize(BinaryDataRef);
};

////
struct DerivationScheme_ArmoryLegacy : public DerivationScheme
{
private:
   SecureBinaryData chainCode_;

public:
   DerivationScheme_ArmoryLegacy(SecureBinaryData&& chainCode) :
      chainCode_(move(chainCode))
   {}

   shared_ptr<AssetEntry> getNextAsset(shared_ptr<AssetEntry>);
   BinaryData serialize(void) const;
};

////////////////////////////////////////////////////////////////////////////////
class AddressEntry
{
private:
   const AddressEntryType type_;

public:
   AddressEntry(AddressEntryType aetype) :
      type_(aetype)
   {}

   AddressEntryType getType(void) const { return type_; }

   //
   virtual ~AddressEntry(void) = 0;
   virtual const BinaryData& getAddress(void) const = 0;
   virtual int getIndex(void) const = 0;

   //
   virtual shared_ptr<ScriptRecipient> getRecipient(uint64_t) const = 0;
};

////////////////////////////////////////////////////////////////////////////////
class AddressEntryP2PKH : public AddressEntry
{
private:
   const shared_ptr<AssetEntry> asset_;
   mutable BinaryData address_;

public:
   AddressEntryP2PKH(shared_ptr<AssetEntry> asset) :
      AddressEntry(AddressEntryType_P2PKH), asset_(asset)
   {}

   int getIndex(void) const { return asset_->getId(); }
   const BinaryData& getAddress(void) const;
   shared_ptr<ScriptRecipient> getRecipient(uint64_t) const;
};

////////////////////////////////////////////////////////////////////////////////
class AssetWallet
{
   friend class AssetWalletSigner;

private:
   static const string walletDbName_;

   LMDBEnv* dbEnv_ = nullptr;
   LMDB* db_ = nullptr;

   ////
   mutex walletMutex_;
   atomic<int> highestUsedAddressIndex_;

   shared_ptr<AssetEntry> root_;
   map<int, shared_ptr<AssetEntry>> entries_;
   map<int, shared_ptr<AddressEntry>> addresses_;

   shared_ptr<DerivationScheme> derScheme_;
   AddressEntryType default_aet_ = AddressEntryType_P2PKH;

   ////
   BinaryData parentID_;
   BinaryData walletID_;
   
private:
   shared_ptr<AddressEntry> getAddressEntryForAsset(shared_ptr<AssetEntry>,
      AddressEntryType);
   shared_ptr<AssetEntry> getNextAsset(shared_ptr<AssetEntry>);

   void writeAssetEntry(shared_ptr<AssetEntry>);
   void readFromFile(void);
   BinaryDataRef getDataRefForKey(const BinaryData& key) const;

   void putData(const BinaryData& key, const BinaryData& data);
   void putData(BinaryWriter& key, BinaryWriter& data);

public:
   AssetWallet(LMDBEnv* env) :
      dbEnv_(env)
   {
      {
         LMDBEnv::Transaction tx(env, LMDB::ReadWrite);
         db_ = new LMDB(env, walletDbName_);
      }

      readFromFile();
   }

   ~AssetWallet()
   {
      if (db_ != nullptr)
      {
         db_->close();
         delete db_;
         db_ = nullptr;
      }

      if (dbEnv_ != nullptr)
      {
         dbEnv_->close();
         delete dbEnv_;
         dbEnv_ = nullptr;
      }

      addresses_.clear();
      entries_.clear();
   }

   shared_ptr<AddressEntry> getNewAddress(AddressEntryType aet);
   static shared_ptr<AssetWallet> openWalletFile(const string& path);
   static shared_ptr<AssetWallet> createWalletFromPrivateRoot(
      shared_ptr<DerivationScheme>,
      AssetEntryType,
      AddressEntryType,
      SecureBinaryData&& privateRoot,
      BinaryData parentID = BinaryData(),
      unsigned lookup = UINT32_MAX);

   vector<BinaryData> getHash160Vec(void) const;
   string getID(void) const;
};

////////////////////////////////////////////////////////////////////////////////
class AssetWalletSigner : public ResolverFeed
{
private:
   shared_ptr<AssetWallet> wltPtr_;

   map<BinaryDataRef, BinaryDataRef> h160_to_pubkey_;
   map<BinaryDataRef, shared_ptr<AssetEntry>> pubkey_to_privkeyAsset_;

public:
   AssetWalletSigner(shared_ptr<AssetWallet> wltPtr) :
      wltPtr_(wltPtr)
   {
      for (auto& entry : wltPtr->entries_)
      {
         auto h160Ref = BinaryDataRef(entry.second->getHash160());
         auto pubkeyRef = BinaryDataRef(entry.second->getPubKey()->getData());

         h160_to_pubkey_.insert(make_pair(h160Ref, pubkeyRef));
         pubkey_to_privkeyAsset_.insert(make_pair(pubkeyRef, entry.second));
      }
   }

   BinaryData getByVal(const BinaryData& key)
   {
      auto keyRef = BinaryDataRef(key);
      auto iter = h160_to_pubkey_.find(keyRef);
      if (iter == h160_to_pubkey_.end())
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
      return privkeyAsset->getData();
   }
};
