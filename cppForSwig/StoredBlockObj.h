#ifndef _STORED_BLOCK_OBJ_
#define _STORED_BLOCK_OBJ_

#include <vector>
#include <list>
#include <map>
#include "BinaryData.h"
#include "BtcUtils.h"
#include "BlockObj.h"

#define ARMORY_DB_VERSION   0x00
#define ARMORY_DB_DEFAULT   ARMORY_DB_FULL
#define UTXO_STORAGE        SCRIPT_UTXO_VECTOR

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
  DB_PREFIX_MULTISIG,
  DB_PREFIX_UNDODATA,
  DB_PREFIX_TRIENODES,
  DB_PREFIX_COUNT
};


enum ARMORY_DB_TYPE
{
  ARMORY_DB_LITE,
  ARMORY_DB_PARTIAL,
  ARMORY_DB_FULL,
  ARMORY_DB_SUPER,
  ARMORY_DB_WHATEVER
};

enum DB_PRUNE_TYPE
{
  DB_PRUNE_ALL,
  DB_PRUNE_NONE,
  DB_PRUNE_WHATEVER
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
  DB_COUNT
};


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

class StoredTx;
class StoredTxOut;
class StoredScriptHistory;


#define ARMDB DBUtils::GetInstance()


////////////////////////////////////////////////////////////////////////////////
class StoredHeader
{
public:
   StoredHeader(void) : isInitialized_(false), 
                        dataCopy_(0), 
                        thisHash_(0), 
                        numTx_(UINT32_MAX), 
                        numBytes_(UINT32_MAX), 
                        blockHeight_(UINT32_MAX), 
                        duplicateID_(UINT8_MAX), 
                        merkle_(0), 
                        isMainBranch_(false) {}
                           

   bool isInitialized(void) const {return isInitialized_;}
   bool haveFullBlock(void) const;
   BlockHeader getBlockHeaderCopy(void) const;
   BinaryData getSerializedBlock(void) const;
   BinaryData getSerializedBlockHeader(void) const;
   void createFromBlockHeader(BlockHeader & bh);

   void addTxToMap(uint16_t txIdx, Tx & tx);
   void addStoredTxToMap(uint16_t txIdx, StoredTx & tx);

   void setParamsTrickle(uint32_t hgt, uint8_t dupID, bool isValid);
   void setHeightAndDup(uint32_t hgt, uint8_t dupID);
   void setHeightAndDup(BinaryData hgtx);

   void unserialize(BinaryData const & header80B);
   void unserialize(BinaryDataRef header80B);
   void unserialize(BinaryRefReader brr);

   void unserializeFullBlock(BinaryDataRef block, 
                             bool doFrag=true,
                             bool withPrefix8=false);

   void unserializeFullBlock(BinaryRefReader brr, 
                             bool doFrag=true,
                             bool withPrefix8=false);

   bool serializeFullBlock( BinaryWriter & bw) const;

   void unserializeDBValue( DB_SELECT         db,
                            BinaryRefReader & brr,
                            bool              ignoreMerkle = false);
   void   serializeDBValue( DB_SELECT         db,
                            BinaryWriter &    bw) const;



   bool isMerkleCreated(void) { return (merkle_.getSize() != 0);}

   
   bool           isInitialized_;
   BinaryData     dataCopy_;
   BinaryData     thisHash_;
   uint32_t       numTx_;
   uint32_t       numBytes_;
   uint32_t       blockHeight_;
   uint8_t        duplicateID_;
   BinaryData     merkle_;
   bool           merkleIsPartial_;
   uint8_t        isMainBranch_;

   bool           isPartial_;
   map<uint16_t, StoredTx> stxMap_;

   // We don't actually enforce these members.  They're solely for recording
   // the values that were unserialized with everything else, so that we can
   // leter check that DB data matches what we were expecting
   uint32_t        unserArmVer_;
   uint32_t        unserBlkVer_;
   ARMORY_DB_TYPE  unserDbType_;
   DB_PRUNE_TYPE   unserPrType_;
   MERKLE_SER_TYPE unserMkType_;
   
};


////////////////////////////////////////////////////////////////////////////////
class StoredTx
{
public:
   StoredTx(void) : isInitialized_(false), 
                    thisHash_(0), 
                    dataCopy_(0), 
                    blockHeight_(UINT32_MAX),
                    blockDupID_(UINT8_MAX),
                    txIndex_(UINT16_MAX),
                    numTxOut_(UINT16_MAX),
                    numBytes_(UINT32_MAX),
                    fragBytes_(UINT32_MAX) {}
   
   bool       isInitialized(void) const {return isInitialized_;}
   bool       haveAllTxOut(void) const;
   StoredTx&  createFromTx(Tx & tx, bool doFrag=true, bool withTxOuts=true);
   BinaryData getSerializedTx(void) const;
   BinaryData getSerializedTxFragged(void) const;
   Tx         getTxCopy(void) const;

   void addTxOutToMap(uint16_t idx, TxOut & txout);
   void addStoredTxOutToMap(uint16_t idx, StoredTxOut & txout);

   void unserialize(BinaryData const & data, bool isFragged=false);
   void unserialize(BinaryDataRef data,      bool isFragged=false);
   void unserialize(BinaryRefReader & brr,   bool isFragged=false);

   void unserializeDBValue(BinaryRefReader & brr);
   void   serializeDBValue(BinaryWriter &    bw ) const;



   BinaryData           thisHash_;
   BinaryData           lockTime_;
   bool                 isInitialized_;

   BinaryData           dataCopy_;
   bool                 isFragged_;
   uint32_t             version_;
   uint32_t             blockHeight_;
   uint8_t              blockDupID_;
   uint16_t             txIndex_;
   uint16_t             numTxOut_;
   uint32_t             numBytes_;
   uint32_t             fragBytes_;
   map<uint16_t, StoredTxOut> stxoMap_;

   // We don't actually enforce these members.  They're solely for recording
   // the values that were unserialized with everything else, so that we can
   // leter check that it
   uint32_t          unserArmVer_;
   uint32_t          unserTxVer_; 
   TX_SERIALIZE_TYPE unserTxType_;
};


////////////////////////////////////////////////////////////////////////////////
class StoredTxOut
{
public:
   StoredTxOut(void) : isInitialized_(false),   
                       txVersion_(UINT32_MAX), 
                       dataCopy_(0), 
                       blockHeight_(UINT32_MAX), 
                       blockDupID_(UINT8_MAX), 
                       txIndex_(UINT16_MAX), 
                       txOutIndex_(UINT16_MAX), 
                       spentness_(TXOUT_SPENTUNK), 
                       isCoinbase_(false), 
                       spentByTxInKey_(0) {}

   bool isInitialized(void) const {return isInitialized_;}
   void unserialize(BinaryData const & data);
   void unserialize(BinaryDataRef data);
   void unserialize(BinaryRefReader & brr);

   void unserializeDBValue(BinaryRefReader & brr);
   void   serializeDBValue(BinaryWriter &    bw,
                           bool              forceSaveSpentness=false) const;

   StoredTxOut & createFromTxOut(TxOut & txout); 
   BinaryData    getSerializedTxOut(void) const;
   TxOut         getTxOutCopy(void) const;

   uint64_t getValue(void) 
   { 
      return dataCopy_.getSize()>=8 ? READ_UINT64_LE(dataCopy_.getPtr()) : UINT64_MAX;
   }
         

   bool              isInitialized_;
   uint32_t          txVersion_;
   BinaryData        dataCopy_;
   uint32_t          blockHeight_;
   uint8_t           blockDupID_;
   uint16_t          txIndex_;
   uint16_t          txOutIndex_;
   TXOUT_SPENTNESS   spentness_;
   bool              isCoinbase_;
   BinaryData        spentByTxInKey_;

   // We don't actually enforce these members.  They're solely for recording
   // the values that were unserialized with everything else, so that we can
   // leter check that it
   uint32_t          unserArmVer_;
};


////////////////////////////////////////////////////////////////////////////////
class StoredScriptHistory
{
public:

   StoredScriptHistory(void) : uniqueKey_(0), 
                               version_(UINT32_MAX),
                               scriptType_(SCRIPT_PREFIX_NONSTD),
                               alreadyScannedUpToBlk_(0),
                               hasMultisigEntries_(false) {}

   bool isInitialized(void) { return uniqueKey_.getSize() > 0; }

   void unserializeDBValue(BinaryRefReader & brr);
   void   serializeDBValue(BinaryWriter    & bw ) const;


   BinaryData     uniqueKey_;  // includes the prefix byte!
   uint32_t       version_;
   SCRIPT_PREFIX  scriptType_;
   uint32_t       alreadyScannedUpToBlk_;
   bool           hasMultisigEntries_;

   vector<TxIOPair> txioVect_;
};




////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
// Basically making stuff globally accessible through DBUtils singleton
////////////////////////////////////////////////////////////////////////////////
class DBUtils
{
public:

   uint32_t   hgtxToHeight(BinaryData hgtx);
   uint8_t    hgtxToDupID(BinaryData hgtx);
   BinaryData heightAndDupToHgtx(uint32_t hgt, uint8_t dup);

   BinaryData getBlkDataKey(uint32_t height, 
                            uint8_t  dup);

   BinaryData getBlkDataKey(uint32_t height, 
                            uint8_t  dup,
                            uint16_t txIdx);

   BinaryData getBlkDataKey(uint32_t height, 
                            uint8_t  dup,
                            uint16_t txIdx,
                            uint16_t txOutIdx);

   BinaryData getBlkDataKeyNoPrefix(uint32_t height, 
                                    uint8_t  dup);

   BinaryData getBlkDataKeyNoPrefix(uint32_t height, 
                                    uint8_t  dup,
                                    uint16_t txIdx);

   BinaryData getBlkDataKeyNoPrefix(uint32_t height, 
                                    uint8_t  dup,
                                    uint16_t txIdx,
                                    uint16_t txOutIdx);

   string getPrefixName(uint8_t prefixInt);
   string getPrefixName(DB_PREFIX pref);

   bool checkPrefixByte(BinaryRefReader brr, 
                        DB_PREFIX prefix,
                        bool rewindWhenDone=false);

   void setArmoryDbType(ARMORY_DB_TYPE adt) { armoryDbType_ = adt; }
   void setDbPruneType( DB_PRUNE_TYPE dpt)  { dbPruneType_  = dpt; }

   ARMORY_DB_TYPE getArmoryDbType(void) { return armoryDbType_; }
   DB_PRUNE_TYPE  getDbPruneType(void)  { return dbPruneType_;  }

   static DBUtils& GetInstance(void)
   {
      static DBUtils* theOneUtilsObj = NULL;
      if(theOneUtilsObj==NULL)
      {
         theOneUtilsObj = new DBUtils;
      
         // Default database structure
         theOneUtilsObj->setArmoryDbType(ARMORY_DB_FULL);
         theOneUtilsObj->setDbPruneType(DB_PRUNE_NONE);
      }

      return (*theOneUtilsObj);
   }


   
private:
   DBUtils(void) {}
   
   DB_PRUNE_TYPE  dbPruneType_;
   ARMORY_DB_TYPE armoryDbType_;
};


#endif

