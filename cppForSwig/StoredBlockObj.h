#ifndef _STORED_BLOCK_OBJ_
#define _STORED_BLOCK_OBJ_

#include <vector>
#include <list>
#include <map>
#include "BinaryData.h"
#include "BtcUtils.h"
#include "BlockObj.h"


class BlockHeader;
class Tx;
class TxIn;
class TxOut;
class TxRef;
class TxIOPair;

class StoredTx;
class StoredTxOut;
class StoredScriptHistory;

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

   void unserialize(BinaryData const & header80B);
   void unserialize(BinaryDataRef header80B);
   void unserialize(BinaryRefReader brr);

   void unserializeFullBlock(BinaryDataRef block, 
                             bool doFrag=true,
                             bool withPrefix8=false);

   void unserializeFullBlock(BinaryRefReader brr, 
                             bool doFrag=true,
                             bool withPrefix8=false);

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
                    numBytes_(UINT32_MAX) {}
   
   bool       isInitialized(void) const {return isInitialized_;}
   bool       haveAllTxOut(void) const;
   StoredTx&  createFromTx(Tx & tx, bool doFrag=true, bool withTxOuts=true);
   BinaryData getSerializedTx(void) const;
   Tx         getTxCopy(void) const;

   void addTxOutToMap(uint16_t idx, TxOut & txout);
   void addStoredTxOutToMap(uint16_t idx, StoredTxOut & txout);

   void unserialize(BinaryData const & data, bool isFragged=false);
   void unserialize(BinaryDataRef data,      bool isFragged=false);
   void unserialize(BinaryRefReader & brr,   bool isFragged=false);


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
   map<uint16_t, StoredTxOut> stxoMap_;

};


////////////////////////////////////////////////////////////////////////////////
class StoredTxOut
{
public:
   StoredTxOut(void) : 
      isInitialized_(false), dataCopy_(0), spentByHgtX_(UINT32_MAX) {}

   bool isInitialized(void) const {return isInitialized_;}
   void unserialize(BinaryData const & data);
   void unserialize(BinaryDataRef data);
   void unserialize(BinaryRefReader & brr);


   StoredTxOut & createFromTxOut(TxOut & txout); 
   BinaryData getSerializedTxOut(void) const;

   bool writeToDB(bool skipIfExists=false);

   uint32_t          txVersion_;
   BinaryData        dataCopy_;
   bool              isInitialized_;
   uint32_t          version_;
   uint32_t          blockHeight_;
   uint8_t           blockDupID_;
   uint16_t          txIndex_;
   uint16_t          txOutIndex_;
   bool              isSpent_;
   bool              isFromCoinbase_;
   uint32_t          spentByHgtX_;
   uint16_t          spentByTxIndex_;
   uint16_t          spentByTxInIndex_;
};


////////////////////////////////////////////////////////////////////////////////
class StoredScriptHistory
{
public:

   StoredScriptHistory(void) : uniqueKey_(0), version_(UINT32_MAX) {}

   bool isInitialized(void) { return uniqueKey_.getSize() > 0; }

   uint32_t       version_;
   BinaryData     uniqueKey_;  // includes the prefix byte!
   SCRIPT_PREFIX  scriptType_;
   uint32_t       alreadyScannedUpToBlk_;
   bool           hasMultisigEntries_;

   vector<TxIOPair> txioVect_;
};



#endif

