#ifndef _BLOCKWRITEBATCHER_H
#define _BLOCKWRITEBATCHER_H

#include "BinaryData.h"
#include "BlockObj.h"

class StoredHeader;
class StoredUndoData;
class StoredTx;
class StoredScriptHistory;
struct BlockDataManagerConfig;

/*
 This class accumulates changes to write to the database,
 and will do so when it gets to a certain threshold
*/
class BlockWriteBatcher
{
public:
   static const uint64_t UPDATE_BYTES_THRESH = 96*1024*1024;
   
   BlockWriteBatcher(const BlockDataManagerConfig &config, LMDBBlockDatabase* iface);
   ~BlockWriteBatcher();
   
   void applyBlockToDB(StoredHeader &sbh);
   void applyBlockToDB(uint32_t hgt, uint8_t dup);
   void undoBlockFromDB(StoredUndoData &sud);

private:
   // We have accumulated enough data, actually write it to the db
   void commit();
   
   // search for entries in sshToModify_ that are empty and should
   // be deleted, removing those empty ones from sshToModify
   set<BinaryData> searchForSSHKeysToDelete();
   
   bool applyTxToBatchWriteData(
                           StoredTx &       thisSTX,
                           StoredUndoData * sud);
private:
   const BlockDataManagerConfig &config_;
   LMDBBlockDatabase* const iface_;

   // turn off batches by setting this to 0
   uint64_t dbUpdateSize_;
   map<BinaryData, StoredTx>              stxToModify_;
   map<BinaryData, StoredScriptHistory>   sshToModify_;
   
   // (theoretically) incremented for each
   // applyBlockToDB and decremented for each
   // undoBlockFromDB
   uint32_t mostRecentBlockApplied_;
};


#endif
