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
class TxRef;
class TxIOPair;

class StoredTx;
class StoredTxOut;
class StoredScriptHistory;

////////////////////////////////////////////////////////////////////////////////
class StoredHeader
{
public:
   StoredHeader(void) : 
         isInitialized_(false), dataCopy_(0), thisHash_(0),
         blockHeight_(UINT32_MAX), duplicateID_(UINT8_MAX), 
         merkle_(0), isMainBranch_(false) {}
                           

   bool haveFullBlock(void) const;
   BlockHeader getBlocKHeaderCopy(void) const;
   BinaryData getSerializedBlock(void) const;
   BinaryData getSerializedBlockHeader(void) const;
   void createFromBlockHeader(BlockHeader & bh);

   void addTxToMap(uint16_t txIdx, Tx & tx);
   void addStoredTxToMap(uint16_t txIdx, StoredTx & tx);

   void setParamsTrickle(uint32_t hgt, uint8_t dupID, bool isValid);

   void unserialize(BinaryDataRef header80B);

   
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
   map<uint16_t, StoredTx> txMap_;

   
};


////////////////////////////////////////////////////////////////////////////////
class StoredTx
{
public:
   StoredTx(void) : isInitialized_(false), 
                    thisHash_(0), 
                    dataCopy_(0), 
                    numBytes_(0) {}
   
   bool       haveAllTxOut(void) const;
   void       createFromTx(Tx & tx, bool doFrag=true);
   BinaryData getSerializedTx(void) const;
   Tx         getTxCopy(void) const;

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
   uint32_t             numTxOut_;
   uint32_t             numBytes_;
   map<uint16_t, StoredTxOut> txOutMap_;

};


////////////////////////////////////////////////////////////////////////////////
class StoredTxOut
{
public:
   StoredTxOut(void) : 
      isInitialized_(false), dataCopy_(0), spentByHgtX_(UINT32_MAX) {}

   void unserialize(BinaryData const & data);
   void unserialize(BinaryDataRef data);
   void unserialize(BinaryRefReader & brr);


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
