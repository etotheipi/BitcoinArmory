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

#include <deque>
#include <map>

////////////////////////////////////////////////////////////////////////////////
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
      bool prevTopStillValid=false;
      bool hasNewTop=false;
      BlockHeader *prevTop=nullptr;
      BlockHeader *newTop = nullptr;
      BlockHeader *reorgBranchPoint=nullptr;
   };
   
   /**
    * Adds a block to the chain
    **/
   BlockHeader& addBlock(const HashString &blockhash, 
      const BlockHeader &block, bool suppressVerbose);
   BlockHeader& addBlock(const HashString &blockhash, const BlockHeader &block,
                         uint32_t height, uint8_t dupId);
   BlockHeader& addNewBlock(const HashString &blockhash, 
      const BlockHeader &block, bool suppressVerbose);

   set<uint32_t> addBlocksInBulk(const map<HashString, BlockHeader>&);
   void forceAddBlocksInBulk(const map<HashString, BlockHeader>&);

   ReorganizationState organize(bool verbose);
   ReorganizationState forceOrganize();
   ReorganizationState findReorgPointFromBlock(const BinaryData& blkHash);

   void setDuplicateIDinRAM(LMDBBlockDatabase* iface);

   BlockHeader& top() const;
   BlockHeader& getGenesisBlock() const;
   BlockHeader& getHeaderByHeight(unsigned height) const;
   bool hasHeaderByHeight(unsigned height) const;
   
   const BlockHeader& getHeaderByHash(HashString const & blkHash) const;
   BlockHeader& getHeaderByHash(HashString const & blkHash);
   BlockHeader& getHeaderById(uint32_t id) const;

   bool hasHeaderWithHash(BinaryData const & txHash) const;
   const BlockHeader& getHeaderPtrForTxRef(const TxRef &txr) const;
   const BlockHeader& getHeaderPtrForTx(const Tx & txObj) const
   {
      if(txObj.getTxRef().isNull())
      {
         throw runtime_error("TxRef in Tx object is not set, cannot get header ptr");
      }
      
      return getHeaderPtrForTxRef(txObj.getTxRef());
   }
   
   map<HashString, BlockHeader>& allHeaders()
   {
      return headerMap_;
   }
   const map<HashString, BlockHeader>& allHeaders() const
   {
      return headerMap_;
   }

   void putBareHeaders(LMDBBlockDatabase *db, bool updateDupID=true);
   void putNewBareHeaders(LMDBBlockDatabase *db);
   const set<BlockHeader*>& getBlockHeightsForFileNum(uint32_t) const;

   unsigned int getNewUniqueID(void) { return topID_.fetch_add(1, memory_order_relaxed); }

private:
   BlockHeader* organizeChain(bool forceRebuild=false, bool verbose=false);
   /////////////////////////////////////////////////////////////////////////////
   // Update/organize the headers map (figure out longest chain, mark orphans)
   // Start from a node, trace down to the highest solved block, accumulate
   // difficulties and difficultySum values.  Return the difficultySum of 
   // this block.
   double traceChainDown(BlockHeader & bhpStart);

private:
   //TODO: make this whole class thread safe

   const HashString genesisHash_;
   map<HashString, BlockHeader> headerMap_;
   vector<BlockHeader*> newlyParsedBlocks_;
   deque<BlockHeader*> headersByHeight_;
   map<uint32_t, BlockHeader*> headersById_;
   BlockHeader *topBlockPtr_;
   BlockHeader *genesisBlockBlockPtr_;
   map<uint32_t, uint32_t> fileNumToKey_;
   Blockchain(const Blockchain&); // not defined

   atomic<unsigned int> topID_;

   mutex mu_;
};

#endif
