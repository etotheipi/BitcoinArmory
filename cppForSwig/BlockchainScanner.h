////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2016, goatpig.                                              //
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //                                      
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#include "Blockchain.h"
#include "lmdb_wrapper.h"
#include "BDM_supportClasses.h"
#include "BlockDataMap.h"

#include <future>

#ifndef _BLOCKCHAINSCANNER_H
#define _BLOCKCHAINSCANNER_H

struct BlockData
{
   uint8_t* data_;
   size_t length_;

   shared_ptr<shared_future<BlockData>> next_;
};

struct BlockDataBatch
{
   shared_ptr<shared_future<BlockData>> top_;
   
   //keep a reference to the file mmaps used by this object since we don't copy 
   //the data, just point at it.
   vector<shared_ptr<BlockDataFileMap>> fileMaps_;

   //only for addresses and utxos we track
   map<BinaryData, StoredTxOut> utxos_;
   map<BinaryData, StoredScriptHistory> ssh_;
};

class BlockchainScanner
{
private:
   Blockchain* blockchain_;
   LMDBBlockDatabase* db_;
   shared_ptr<ScrAddrFilter> scrAddrFilter_;

   const unsigned nBlockFilesPerBatch_ = 4;
   const unsigned totalThreadCount_;

   void readBlockData(unsigned startBlock, unsigned endBlock);


public:
   BlockchainScanner(Blockchain* bc, LMDBBlockDatabase* db,
      shared_ptr<ScrAddrFilter> saf) :
      blockchain_(bc), db_(db), scrAddrFilter_(saf),
      totalThreadCount_(thread::hardware_concurrency())
   {}

   void scan(uint32_t startHeight);
};

#endif