////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2015, Armory Technologies, Inc.                        //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE-ATI or http://www.gnu.org/licenses/agpl.html                  //
//                                                                            //
//                                                                            //
//  Copyright (C) 2016, goatpig                                               //            
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //                                   
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#ifndef _BLOCKCHAIN_H
#define _BLOCKCHAIN_H

#include "BlockObj.h"
#include "lmdb_wrapper.h"

#include <memory>
#include <deque>
#include <map>

////////////////////////////////////////////////////////////////////////////////
struct HeightAndDup
{
   const unsigned height_;
   const uint8_t dup_;

   HeightAndDup(unsigned height, uint8_t dup) :
      height_(height), dup_(dup)
   {}
};

////////////////////////////////////////////////////////////////////////////////
//
// Manages the blockchain, keeping track of all the block headers
// and our longest cord
//
class Blockchain
{
public:
   Blockchain(const HashString &genesisHash);
   void clear();
   
   struct ReorganizationState
   {
      bool prevTopStillValid_ = false;
      bool hasNewTop_ = false;
      shared_ptr<BlockHeader> prevTop_;
      shared_ptr<BlockHeader> newTop_;
      shared_ptr<BlockHeader> reorgBranchPoint_;
   };
   
   /**
    * Adds a block to the chain
    **/
   void addBlock(const HashString &blockhash, 
      shared_ptr<BlockHeader>, bool suppressVerbose);
   void addBlock(const HashString &blockhash, shared_ptr<BlockHeader>,
                         uint32_t height, uint8_t dupId);
   void addNewBlock(const HashString &blockhash,
      shared_ptr<BlockHeader>, bool suppressVerbose);

   set<uint32_t> addBlocksInBulk(const map<HashString, shared_ptr<BlockHeader>>&);
   void forceAddBlocksInBulk(const map<HashString, shared_ptr<BlockHeader>>&);

   ReorganizationState organize(bool verbose);
   ReorganizationState forceOrganize();
   ReorganizationState findReorgPointFromBlock(const BinaryData& blkHash);

   void setDuplicateIDinRAM(LMDBBlockDatabase* iface);

   shared_ptr<BlockHeader> top() const;
   shared_ptr<BlockHeader> getGenesisBlock() const;
   shared_ptr<BlockHeader> getHeaderByHeight(unsigned height);
   const shared_ptr<BlockHeader> getHeaderByHeight(unsigned height) const;
   bool hasHeaderByHeight(unsigned height) const;
   
   const shared_ptr<BlockHeader> getHeaderByHash(HashString const & blkHash) const;
   shared_ptr<BlockHeader> getHeaderByHash(HashString const & blkHash);
   shared_ptr<BlockHeader> getHeaderById(uint32_t id) const;

   bool hasHeaderWithHash(BinaryData const & txHash) const;
   const shared_ptr<BlockHeader> getHeaderPtrForTxRef(const TxRef &txr) const;
   const shared_ptr<BlockHeader> getHeaderPtrForTx(const Tx & txObj) const
   {
      if(txObj.getTxRef().isNull())
      {
         throw runtime_error("TxRef in Tx object is not set, cannot get header ptr");
      }
      
      return getHeaderPtrForTxRef(txObj.getTxRef());
   }
   
   map<HashString, shared_ptr<BlockHeader>>& allHeaders()
   {
      return headerMap_;
   }
   const map<HashString, shared_ptr<BlockHeader>>& allHeaders() const
   {
      return headerMap_;
   }

   void putBareHeaders(LMDBBlockDatabase *db, bool updateDupID=true);
   void putNewBareHeaders(LMDBBlockDatabase *db);
   const set<shared_ptr<BlockHeader>>& getBlockHeightsForFileNum(uint32_t) const;

   unsigned int getNewUniqueID(void) { return topID_.fetch_add(1, memory_order_relaxed); }

   map<unsigned, set<unsigned>> mapIDsPerBlockFile(void) const;
   map<unsigned, HeightAndDup> getHeightAndDupMap(void) const;

private:
   shared_ptr<BlockHeader> organizeChain(bool forceRebuild = false, bool verbose = false);
   /////////////////////////////////////////////////////////////////////////////
   // Update/organize the headers map (figure out longest chain, mark orphans)
   // Start from a node, trace down to the highest solved block, accumulate
   // difficulties and difficultySum values.  Return the difficultySum of 
   // this block.
   double traceChainDown(shared_ptr<BlockHeader> bhpStart);

private:
   //TODO: make this whole class thread safe

   const HashString genesisHash_;
   map<HashString, shared_ptr<BlockHeader>> headerMap_;
   vector<shared_ptr<BlockHeader>> newlyParsedBlocks_;
   deque<shared_ptr<BlockHeader>> headersByHeight_;
   map<uint32_t, shared_ptr<BlockHeader>> headersById_;
   shared_ptr<BlockHeader> topBlockPtr_;
   unsigned topBlockId_ = 0;
   Blockchain(const Blockchain&); // not defined

   atomic<unsigned int> topID_;

   mutable mutex mu_;
};

#endif
