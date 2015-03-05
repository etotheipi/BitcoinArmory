////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2015, Armory Technologies, Inc.                        //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE or http://www.gnu.org/licenses/agpl.html                      //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////
#ifndef _STORED_BLOCK_OBJ_
#define _STORED_BLOCK_OBJ_

#include <vector>
#include <list>
#include <map>
#include "BinaryData.h"
#include "BtcUtils.h"
#include "BlockObj.h"
#include "txio.h"
#include "BlockDataManagerConfig.h"
#include <atomic>

#define ARMORY_DB_VERSION   0x00
#define ARMORY_DB_DEFAULT   ARMORY_DB_FULL
#define UTXO_STORAGE        SCRIPT_UTXO_VECTOR

static const uint64_t UPDATE_BYTES_SSH    = 25;
static const uint64_t UPDATE_BYTES_SUBSSH = 75;
static const uint64_t UPDATE_BYTES_KEY    = 8;

enum BLKDATA_TYPE
{
  NOT_BLKDATA,
  BLKDATA_HEADER,
  BLKDATA_TX,
  BLKDATA_TXOUT
};

enum DB_PREFIX
{
  DB_PREFIX_DBINFO,
  DB_PREFIX_HEADHASH,
  DB_PREFIX_HEADHGT,
  DB_PREFIX_TXDATA,
  DB_PREFIX_TXHINTS,
  DB_PREFIX_SCRIPT,
  DB_PREFIX_UNDODATA,
  DB_PREFIX_TRIENODES,
  DB_PREFIX_COUNT,
  DB_PREFIX_ZCDATA,
  DB_PREFIX_BLKMETA
};

// In ARMORY_DB_PARTIAL and LITE, we may not store full tx, but we will know 
// its block and index, so we can just request the full block from our peer.
enum DB_TX_AVAIL
{
  DB_TX_EXISTS,
  DB_TX_GETBLOCK,
  DB_TX_UNKNOWN
};

enum DB_SELECT
{
   HEADERS,
   BLKDATA,
   HISTORY,
   STXO,
   SPENTNESS,
   TXHINTS,
   ZEROCONF,
   COUNT
};

#define SUBSSHDB_PREFIX_COUNT 16


enum TX_SERIALIZE_TYPE
{
  TX_SER_FULL,
  TX_SER_FRAGGED,
  TX_SER_COUNTOUT
};

enum TXOUT_SPENTNESS
{
  TXOUT_UNSPENT,
  TXOUT_SPENT,
  TXOUT_SPENTUNK,
};

enum MERKLE_SER_TYPE
{
  MERKLE_SER_NONE,
  MERKLE_SER_PARTIAL,
  MERKLE_SER_FULL
};

enum SCRIPT_UTXO_TYPE
{
  SCRIPT_UTXO_VECTOR,
  SCRIPT_UTXO_TREE
};

class BlockHeader;
class Tx;
class TxIn;
class TxOut;
class TxRef;
class TxIOPair;

class DBTx;
class StoredScriptHistory;
class StoredSubHistory;

struct BlkFile
{
   size_t fnum;
   string path;
   uint64_t filesize;
   uint64_t filesizeCumul;
};


template<class T, typename ...Args>
static BinaryData serializeDBValue(const T &o, const Args &...a)
{
   BinaryWriter wr;
   o.serializeDBValue(wr, a...);
   return wr.getData();
}


////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
// Basically making stuff globally accessible through DBUtils singleton
////////////////////////////////////////////////////////////////////////////////
class DBUtils
{
public:

   static uint32_t   hgtxToHeight(const BinaryData& hgtx);
   static uint8_t    hgtxToDupID(const BinaryData& hgtx);
   static BinaryData heightAndDupToHgtx(uint32_t hgt, uint8_t dup);

   /////////////////////////////////////////////////////////////////////////////
   static BinaryData getBlkMetaKey(uint32_t height,
      uint8_t  dup);

   /////////////////////////////////////////////////////////////////////////////
   static BinaryData getBlkDataKey(uint32_t height, 
                            uint8_t  dup);

   /////////////////////////////////////////////////////////////////////////////
   static BinaryData getBlkDataKey(uint32_t height, 
                            uint8_t  dup,
                            uint16_t txIdx);

   /////////////////////////////////////////////////////////////////////////////
   static BinaryData getBlkDataKey(uint32_t height, 
                            uint8_t  dup,
                            uint16_t txIdx,
                            uint16_t txOutIdx);

   /////////////////////////////////////////////////////////////////////////////
   static BinaryData getBlkDataKeyNoPrefix(uint32_t height, 
                                           uint8_t  dup);

   /////////////////////////////////////////////////////////////////////////////
   static BinaryData getBlkDataKeyNoPrefix(uint32_t height, 
                                           uint8_t  dup,
                                           uint16_t txIdx);

   /////////////////////////////////////////////////////////////////////////////
   static BinaryData getBlkDataKeyNoPrefix(uint32_t height, 
                                           uint8_t  dup,
                                           uint16_t txIdx,
                                           uint16_t txOutIdx);



   /////////////////////////////////////////////////////////////////////////////
   static BLKDATA_TYPE readBlkDataKey( BinaryRefReader & brr,
                                       uint32_t & height,
                                       uint8_t  & dupID);

   /////////////////////////////////////////////////////////////////////////////
   static BLKDATA_TYPE readBlkDataKey( BinaryRefReader & brr,
                                       uint32_t & height,
                                       uint8_t  & dupID,
                                       uint16_t & txIdx);

   /////////////////////////////////////////////////////////////////////////////
   static BLKDATA_TYPE readBlkDataKey( BinaryRefReader & brr,
                                       uint32_t & height,
                                       uint8_t  & dupID,
                                       uint16_t & txIdx,
                                       uint16_t & txOutIdx);
   /////////////////////////////////////////////////////////////////////////////
   static BLKDATA_TYPE readBlkDataKeyNoPrefix( 
                                       BinaryRefReader & brr,
                                       uint32_t & height,
                                       uint8_t  & dupID);

   /////////////////////////////////////////////////////////////////////////////
   static BLKDATA_TYPE readBlkDataKeyNoPrefix( 
                                       BinaryRefReader & brr,
                                       uint32_t & height,
                                       uint8_t  & dupID,
                                       uint16_t & txIdx);

   /////////////////////////////////////////////////////////////////////////////
   static BLKDATA_TYPE readBlkDataKeyNoPrefix( 
                                       BinaryRefReader & brr,
                                       uint32_t & height,
                                       uint8_t  & dupID,
                                       uint16_t & txIdx,
                                       uint16_t & txOutIdx);
   


   static string getPrefixName(uint8_t prefixInt);
   static string getPrefixName(DB_PREFIX pref);

   static bool checkPrefixByte(       BinaryRefReader & brr, 
                                      DB_PREFIX prefix,
                                      bool rewindWhenDone=false);
   static bool checkPrefixByteWError( BinaryRefReader & brr, 
                                      DB_PREFIX prefix,
                                      bool rewindWhenDone=false);
};

////////////////////////////////////////////////////////////////////////////////
class StoredDBInfo
{
public:
   StoredDBInfo(void)
   {}

   bool isInitialized(void) const { return magic_.getSize() > 0; }
   bool isNull(void) { return !isInitialized(); }

   static BinaryData getDBKey(void);
   
   void       unserializeDBValue(BinaryRefReader & brr);
   void         serializeDBValue(BinaryWriter &    bw ) const;
   void       unserializeDBValue(BinaryData const & bd);
   void       unserializeDBValue(BinaryDataRef      bd);
   void       unserializeDBKey(BinaryDataRef key) {}

   void pprintOneLine(uint32_t indent=3);

   BinaryData      magic_;
   uint32_t        topBlkHgt_=0;
   BinaryData      topBlkHash_; //hash of last block commited
   BinaryData      topScannedBlkHash_; //commited to SSH
   uint32_t        appliedToHgt_=0; // only used in BLKDATA DB
   uint32_t        armoryVer_=ARMORY_DB_VERSION;
   ARMORY_DB_TYPE  armoryType_=ARMORY_DB_WHATEVER;
   DB_PRUNE_TYPE   pruneType_=DB_PRUNE_WHATEVER;
};

////////////////////////////////////////////////////////////////////////////////
class StoredTxOut
{
public:
   StoredTxOut(void)
      : txVersion_(UINT32_MAX),
      dataCopy_(0),
      blockHeight_(UINT32_MAX),
      duplicateID_(UINT8_MAX),
      txIndex_(UINT16_MAX),
      txOutIndex_(UINT16_MAX),
      parentHash_(0),
      spentness_(TXOUT_UNSPENT),
      isCoinbase_(false),
      spentByTxInKey_(0)
   {}

   bool isInitialized(void) const { return getSize() > 0; }
   bool isNull(void) { return !isInitialized(); }
   void unserialize(BinaryData const & data);
   void unserialize(BinaryDataRef data);
   void unserialize(BinaryRefReader & brr);

   void unserializeDBValue(BinaryRefReader &  brr);
   void serializeDBValue(BinaryWriter & bw, ARMORY_DB_TYPE dbType,
      DB_PRUNE_TYPE pruneType,
      bool forceSaveSpent = false) const;
   void       unserializeDBValue(BinaryData const & bd);
   void       unserializeDBValue(BinaryDataRef      bd);
   void       unserializeDBKey(BinaryDataRef key);

   BinaryData getDBKey(bool withPrefix = true) const;
   BinaryData getDBKeyOfParentTx(bool withPrefix = true) const;
   BinaryData& getHgtX(void);

   StoredTxOut & createFromTxOut(TxOut & txout);
   BinaryData    getSerializedTxOut(void) const;
   TxOut         getTxOutCopy(void) const;

   const BinaryData& getScrAddress(void) const;
   BinaryDataRef     getScriptRef(void) const;
   uint64_t          getValue(void) const;

   bool matchesDBKey(BinaryDataRef dbkey) const;

   bool isSpent(void) { return spentness_ == TXOUT_SPENT; }
   void pprintOneLine(uint32_t indent = 3);

   size_t getSize(void) const
   { return dataCopy_.getSize(); }

   uint32_t          txVersion_;
   BinaryData        dataCopy_;
   uint32_t          blockHeight_;
   uint8_t           duplicateID_;
   uint16_t          txIndex_;
   uint16_t          txOutIndex_;
   BinaryData        parentHash_;
   BinaryData        hashAndId_;
   TXOUT_SPENTNESS   spentness_;
   bool              isCoinbase_;
   BinaryData        spentByTxInKey_;
   BinaryData        hgtX_;

   mutable BinaryData scrAddr_;

   // We don't actually enforce these members.  They're solely for recording
   // the values that were unserialized with everything else, so that we can
   // leter check that it
   uint32_t          unserArmVer_;
   uint32_t          unserDbType_;
};

////////////////////////////////////////////////////////////////////////////////
class DBTx
{
public:
   bool       isInitialized(void) const { return getDataCopyRef().getSize() > 0; }
   bool       isNull(void) { return !isInitialized(); }

   BinaryData getSerializedTxFragged(void) const;
   Tx         getTxCopy(void) const;
   void       setKeyData(uint32_t height, uint8_t dup, uint16_t txIdx);

   void unserialize(BinaryData const & data, bool isFragged = false);
   void unserialize(BinaryDataRef data, bool isFragged = false);
   virtual void unserialize(BinaryRefReader & brr, bool isFragged = false);

   void       unserializeDBValue(BinaryRefReader & brr);
   void       unserializeDBValue(BinaryData const & bd);
   void       unserializeDBValue(BinaryDataRef      bd);
   BinaryData   serializeDBValue(ARMORY_DB_TYPE dbType,
      DB_PRUNE_TYPE pruneType) const;
   void       unserializeDBKey(BinaryDataRef key);

   BinaryData getDBKey(bool withPrefix = true) const;
   BinaryData getDBKeyOfChild(uint16_t i, bool withPrefix = true) const;
   BinaryData getHgtX(void) const { return getDBKey(false).getSliceCopy(0, 4); }

   void pprintOneLine(uint32_t indent = 3);

   virtual StoredTxOut& initAndGetStxoByIndex(uint16_t index) = 0;
   virtual bool haveAllTxOut(void) const = 0;
   
   virtual const BinaryDataRef getDataCopyRef(void) const = 0;
   virtual BinaryData& getDataCopy(void) = 0;
   /////

   BinaryData           thisHash_;
   uint32_t             lockTime_ = 0;
   uint32_t             unixTime_ = 0;

   bool                 isFragged_ = false;
   uint32_t             version_ = 0;
   uint32_t             blockHeight_ = UINT32_MAX;
   uint8_t              duplicateID_ = UINT8_MAX;
   uint16_t             txIndex_ = UINT16_MAX;
   uint16_t             numTxOut_ = UINT16_MAX;
   uint32_t             numBytes_ = UINT32_MAX;
   uint32_t             fragBytes_ = UINT32_MAX;

   // We don't actually enforce these members.  They're solely for recording
   // the values that were unserialized with everything else, so that we can
   // leter check that it
   uint32_t          unserArmVer_;
   uint32_t          unserTxVer_;
   TX_SERIALIZE_TYPE unserTxType_;
};

////////////////////////////////////////////////////////////////////////////////
class StoredTx : public DBTx
{
public:
   StoredTx&  createFromTx(Tx & tx,
      bool doFrag = true,
      bool withTxOuts = true);
   StoredTx& createFromTx(BinaryDataRef rawTx,
      bool doFrag = true,
      bool withTxOuts = true);


   void         serializeDBValue(
      BinaryWriter &    bw,
      ARMORY_DB_TYPE dbType, DB_PRUNE_TYPE pruneType
      ) const;

   BinaryData getSerializedTx(void) const;
   Tx         getTxCopy(void) const;
   void       setKeyData(uint32_t height, uint8_t dup, uint16_t txIdx);

   void addTxOutToMap(uint16_t idx, TxOut & txout);
   void addStoredTxOutToMap(uint16_t idx, StoredTxOut & txout);

   void pprintFullTx(uint32_t indent = 3);

   /////
   virtual StoredTxOut& initAndGetStxoByIndex(uint16_t index)
   {
      auto& stxo = stxoMap_[index];
      stxo.parentHash_ = thisHash_;
      stxo.txVersion_ = version_;
      return stxo;
   }

   virtual bool haveAllTxOut(void) const;

   virtual const BinaryDataRef getDataCopyRef(void) const
   { return dataCopy_.getRef(); }

   virtual BinaryData& getDataCopy(void)
   { return dataCopy_; }


   ////
   BinaryData           dataCopy_;
   map<uint16_t, StoredTxOut> stxoMap_;
};

////////////////////////////////////////////////////////////////////////////////
class DBBlock
{
public:

   virtual ~DBBlock() {}

   bool isInitialized(void) const {return dataCopy_.getSize() > 0;}
   bool isNull(void) const {return !isInitialized(); }
   BlockHeader getBlockHeaderCopy(void) const;
   BinaryData getSerializedBlock(void) const;
   BinaryData getSerializedBlockHeader(void) const;
   void createFromBlockHeader(const BlockHeader & bh);

   uint32_t getNumTx() { return (isNull() ? 0 : numTx_); } 

   void setHeightAndDup(uint32_t hgt, uint8_t dupID);
   void setHeightAndDup(BinaryData hgtx);

   void setHeaderData(BinaryData const & header80B);

   void unserializeDBValue( DB_SELECT         db,
                            BinaryRefReader & brr,
                            bool              ignoreMerkle = false);
   void serializeDBValue( 
      BinaryWriter &    bw,
      DB_SELECT         db,
      ARMORY_DB_TYPE dbType,
      DB_PRUNE_TYPE pruneType
   ) const;

   void unserializeDBValue(DB_SELECT db, BinaryData const & bd, bool ignMrkl=false);
   void unserializeDBValue(DB_SELECT db, BinaryDataRef bdr,     bool ignMrkl=false);
   void unserializeDBKey  (DB_SELECT db, BinaryDataRef key);

   BinaryData getDBKey(bool withPrefix=true) const;

   bool isMerkleCreated(void) { return (merkle_.getSize() != 0);}

   void pprintOneLine(uint32_t indent=3);

   virtual DBTx& getTxByIndex(uint16_t index) = 0;
   virtual void unserializeFullBlock(BinaryRefReader brr,
      bool doFrag = true,
      bool withPrefix8 = false) = 0;
   ////
   
   BinaryData     dataCopy_;
   BinaryData     thisHash_;
   uint32_t       numTx_=UINT32_MAX;
   size_t         numBytes_=UINT32_MAX;
   uint32_t       blockHeight_=UINT32_MAX;
   uint8_t        duplicateID_=UINT8_MAX;
   BinaryData     merkle_;
   bool           merkleIsPartial_=false;
   bool           isMainBranch_=false;
   bool           blockAppliedToDB_=false;

   bool           isPartial_=false;

   // We don't actually enforce these members.  They're solely for recording
   // the values that were unserialized with everything else, so that we can
   // leter check that DB data matches what we were expecting
   uint32_t        unserArmVer_;
   uint32_t        unserBlkVer_;
   ARMORY_DB_TYPE  unserDbType_;
   DB_PRUNE_TYPE   unserPrType_;
   MERKLE_SER_TYPE unserMkType_;
   
   bool hasBlockHeader_=false;
};

////////////////////////////////////////////////////////////////////////////////
class StoredHeader : public DBBlock
{
public:
   BinaryData getSerializedBlock(void) const;

   Tx getTxCopy(uint16_t i);
   BinaryData getSerializedTx(uint16_t i);
   bool haveFullBlock(void) const;

   void addTxToMap(uint16_t txIdx, Tx & tx);
   void addStoredTxToMap(uint16_t txIdx, StoredTx & tx);

   void unserializeFullBlock(BinaryDataRef block,
      bool doFrag = true,
      bool withPrefix8 = false);

   virtual void unserializeFullBlock(BinaryRefReader brr,
      bool doFrag = true,
      bool withPrefix8 = false);

   bool serializeFullBlock(BinaryWriter & bw) const;
   void setKeyData(uint32_t hgt, uint8_t dupID = UINT8_MAX);
   
   void pprintFullBlock(uint32_t indent = 3);

   virtual DBTx& getTxByIndex(uint16_t index)
   { return static_cast<DBTx&>(stxMap_[index]); }

   ///
   map<uint16_t, StoredTx> stxMap_;
};

////////////////////////////////////////////////////////////////////////////////
// We must break out script histories into isolated sub-histories, to
// accommodate thoroughly re-used addresses like 1VayNert* and 1dice*.  If 
// we didn't do it, those DB entries would be many megabytes, and those many
// MB would be updated multiple times per block.   So we break them into
// subhistories by block.  This is exceptionally well-suited for SatoshiDice
// addresses since transactions in one block tend to be related to 
// transactions in the previous few blocks before it.  
class StoredSubHistory
{
   friend class BlockWriteBatcher;
   friend class DataToCommit;
public:

   StoredSubHistory(void) : uniqueKey_(0), hgtX_(0), height_(0), dupID_(0),
                            txioCount_(0) 
   {
   }
                               

   bool isInitialized(void) { return uniqueKey_.getSize() > 0; }
   bool isNull(void) { return !isInitialized(); }

   void       unserializeDBValue(BinaryRefReader & brr);
   void         serializeDBValue(BinaryWriter    & bw, LMDBBlockDatabase *db, ARMORY_DB_TYPE dbType, DB_PRUNE_TYPE pruneType ) const;
   void       unserializeDBValue(BinaryData const & bd);
   void       unserializeDBValue(BinaryDataRef      bd);
   void       unserializeDBKey(BinaryDataRef key, bool withPrefix=true);
   void       getSummary(BinaryRefReader & brr);

   BinaryData    getDBKey(bool withPrefix=true) const;
   SCRIPT_PREFIX getScriptType(void) const;

   TxIOPair*   findTxio(BinaryData const & dbKey8B, bool includeMultisig=false);
   TxIOPair& insertTxio(TxIOPair const & txio, 
                        uint64_t* additionalSize = nullptr);
   bool      eraseTxio(BinaryData const & dbKey8B);

   
   // This adds the TxOut if it doesn't exist yet
   void markTxOutSpent(const BinaryData& txOutKey8B);

   void markTxOutUnspent(const BinaryData& txOutKey8B,
                             uint64_t&  additionalSize,
                             const uint64_t&  value,
                             bool       isCoinbase,
                             bool       isMultisigRef,
                             bool       increment);

   uint64_t getSubHistoryBalance(bool withMultisig=false);
   uint64_t getSubHistoryReceived(bool withMultisig=false);

   void pprintFullSubSSH(uint32_t indent=3);
   
   StoredSubHistory(const StoredSubHistory& copy)
   {
      *this = copy;
   }

   StoredSubHistory& operator=(const StoredSubHistory& copy)
   {
      if (&copy == this)
         return *this;

      uniqueKey_ = copy.uniqueKey_;
      hgtX_ = copy.hgtX_;
      txioMap_ = copy.txioMap_;
      height_ = copy.height_;
      dupID_ = copy.dupID_;
      txioCount_ = copy.txioCount_;

      //std::atomic types are copyable, and we do not copy
      //accessing_, as this flag is meant to signify 
      //access to the particular object, not that data per say

      return *this;
   }

   // Store all TxIOs for this ScrAddr and block
   BinaryData     uniqueKey_;  // includes the prefix byte!
   BinaryData     hgtX_;
   map<BinaryData, TxIOPair> txioMap_;
   uint32_t height_;
   uint8_t  dupID_;
   uint32_t txioCount_;

private:
   //BWB members, ignore outside of scans
   vector<BinaryData> keysToDelete_;
};


////////////////////////////////////////////////////////////////////////////////
// TODO:  I just realized that this should probably hold a "first-born-block"
//        field for each address in the summary entry.  Though, maybe it's 
//        sufficient to just look at the first subSSH entry to get that info...
class StoredScriptHistory
{
public:

   StoredScriptHistory(void) : uniqueKey_(0), 
                               version_(UINT32_MAX),
                               alreadyScannedUpToBlk_(0),
                               totalTxioCount_(0),
                               totalUnspent_(0) {}
                               

   bool isInitialized(void) const { return uniqueKey_.getSize() > 0; }
   bool isNull(void) { return !isInitialized(); }

   void       unserializeDBValue(BinaryRefReader & brr);
   void         serializeDBValue(BinaryWriter    & bw, ARMORY_DB_TYPE dbType, DB_PRUNE_TYPE pruneType ) const;
   void       unserializeDBValue(BinaryData const & bd);
   void       unserializeDBValue(BinaryDataRef      bd);
   void       unserializeDBKey(BinaryDataRef key, bool withPrefix=true);

   BinaryData    getDBKey(bool withPrefix=true) const;
   BinaryData    getSubKey() const;
   SCRIPT_PREFIX getScriptType(void) const;

   void pprintOneLine(uint32_t indent=3);
   void pprintFullSSH(uint32_t indent=3);

   uint64_t getScriptReceived(bool withMultisig=false);
   uint64_t getScriptBalance(bool withMultisig=false);

   bool     haveFullHistoryLoaded(void) const;

   TxIOPair*   findTxio(BinaryData const & dbKey8B, bool inclMultisig=false);

   bool getFullTxioMap(map<BinaryData, TxIOPair> & mapToFill,
                       bool withMultisig=false);

   void mergeSubHistory(const StoredSubHistory& subssh);
   void insertTxio(const TxIOPair& txio);
   void eraseTxio(const TxIOPair& txio);


   /////
   BinaryData     uniqueKey_;  // includes the prefix byte!
   uint32_t       version_;
   uint32_t       alreadyScannedUpToBlk_;
   uint64_t       totalTxioCount_;
   uint64_t       totalUnspent_;
   
   uint8_t        dbPrefix_ = 0;
   uint8_t        keyLength_ = 0;

   // If this SSH has only one TxIO (most of them), then we don't bother
   // with supplemental entries just to hold that one TxIO in the DB.
   // We always stored them in RAM using the StoredSubHistory 
   // objects which will have the per-block lists of TxIOs.  But when 
   // it gets serialized to disk, we will store single-Txio SSHs in
   // the base entry and forego extra DB entries.
   map<BinaryData, StoredSubHistory> subHistMap_;
};


////////////////////////////////////////////////////////////////////////////////
// TODO:  it turns out that outPointsAddedByBlock_ is not "right."  If a Tx has
//        20 txOuts, there's no reason to write 36 * 20 = 720 bytes when you 
//        can just as easily write the header once, and the numTxOut and create
//        the OutPoints yourself.  Will fix this later.
class StoredUndoData
{
public:
   StoredUndoData(void) {}

   bool isInitialized(void) { return (outPointsAddedByBlock_.size() > 0);}
   bool isNull(void) { return !isInitialized(); }

   void       unserializeDBValue(BinaryRefReader & brr, ARMORY_DB_TYPE dbType, DB_PRUNE_TYPE pruneType);
   void         serializeDBValue(BinaryWriter    & bw, ARMORY_DB_TYPE dbType, DB_PRUNE_TYPE pruneType ) const;
   void       unserializeDBValue(BinaryData const & bd, ARMORY_DB_TYPE dbType, DB_PRUNE_TYPE pruneType);
   void       unserializeDBValue(BinaryDataRef      bd, ARMORY_DB_TYPE dbType, DB_PRUNE_TYPE pruneType);

   BinaryData getDBKey(bool withPrefix=true) const;

   BinaryData  blockHash_;
   uint32_t    blockHeight_;
   uint8_t     duplicateID_;

   vector<StoredTxOut>  stxOutsRemovedByBlock_;
   vector<OutPoint>     outPointsAddedByBlock_;
};


////////////////////////////////////////////////////////////////////////////////
class StoredTxHints
{
public:
   StoredTxHints(void) : txHashPrefix_(0), dbKeyList_(0), preferredDBKey_(0) {}

   bool isInitialized(void) { return txHashPrefix_.getSize() > 0; }
   bool isNull(void) { return !isInitialized(); }

   size_t        getNumHints(void) const   { return dbKeyList_.size();      }
   BinaryDataRef getHint(uint32_t i) const { return dbKeyList_[i].getRef(); }

   void setPreferredTx(uint32_t height, uint8_t dupID, uint16_t txIndex) 
      { preferredDBKey_ = DBUtils::getBlkDataKeyNoPrefix(height,dupID,txIndex); }
   void setPreferredTx(BinaryData dbKey6B_) { preferredDBKey_ = dbKey6B_; }

   void       unserializeDBValue(BinaryRefReader & brr);
   void         serializeDBValue(BinaryWriter    & bw ) const;
   void       unserializeDBValue(BinaryData const & bd);
   void       unserializeDBValue(BinaryDataRef      bd);
   BinaryData   serializeDBValue(void) const;
   void       unserializeDBKey(BinaryDataRef key, bool withPrefix=true);

   BinaryData getDBKey(bool withPrefix=true) const;

   BinaryData         txHashPrefix_; 
   vector<BinaryData> dbKeyList_;
   BinaryData         preferredDBKey_;
};

////////////////////////////////////////////////////////////////////////////////
class StoredHeadHgtList
{
public:
   StoredHeadHgtList(void) : height_(UINT32_MAX), preferredDup_(UINT8_MAX) {}

   void       unserializeDBValue(BinaryRefReader & brr);
   void         serializeDBValue(BinaryWriter    & bw ) const;
   void       unserializeDBValue(BinaryData const & bd);
   void       unserializeDBValue(BinaryDataRef      bd);
   BinaryData   serializeDBValue(void) const;
   void       unserializeDBKey(BinaryDataRef key);

   void addDupAndHash(uint8_t dup, BinaryDataRef hash)
   {
      for(uint32_t i=0; i<dupAndHashList_.size(); i++)
      {
         if(dupAndHashList_[i].first == dup)
         {
            if(dupAndHashList_[i].second != hash)
               LOGERR << "Pushing different hash into existing HHL dupID"; 
            dupAndHashList_[i] = make_pair(dup,hash);
            return;
         }
      }
      dupAndHashList_.push_back(make_pair(dup,hash));
   }

   BinaryData getDBKey(bool withPrefix=true) const;

   bool isInitialized(void) { return (height_ != UINT32_MAX);}
   bool isNull(void) { return !isInitialized(); }

   void setPreferredDupID(uint8_t newDup) {preferredDup_ = newDup;}

   uint32_t           height_;
   vector<pair<uint8_t, BinaryData> > dupAndHashList_;
   uint8_t            preferredDup_;
};


#endif

// kate: indent-width 3; replace-tabs on;
