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
   // implemented but not used:
   //vector<BlockHeader*> getHeadersNotOnMainChain(void);

   void clear();
   
   struct ReorganizationState
   {
      bool prevTopBlockStillValid=false;
      bool hasNewTop=false;
      BlockHeader *prevTopBlock=nullptr;
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

   void addBlocksInBulk(const map<HashString, BlockHeader>&);

   ReorganizationState organize();
   ReorganizationState forceOrganize();
   ReorganizationState findReorgPointFromBlock(const BinaryData& blkHash);

   void setDuplicateIDinRAM(LMDBBlockDatabase* iface);

   BlockHeader& top() const;
   BlockHeader& getGenesisBlock() const;
   BlockHeader& getHeaderByHeight(unsigned height) const;
   bool hasHeaderByHeight(unsigned height) const;
   
   const BlockHeader& getHeaderByHash(HashString const & blkHash) const;
   BlockHeader& getHeaderByHash(HashString const & blkHash);
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
   
   /**
    * @return a map of all headers, even with duplicates
    **/
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

private:
   BlockHeader* organizeChain(bool forceRebuild=false);
   /////////////////////////////////////////////////////////////////////////////
   // Update/organize the headers map (figure out longest chain, mark orphans)
   // Start from a node, trace down to the highest solved block, accumulate
   // difficulties and difficultySum values.  Return the difficultySum of 
   // this block.
   double traceChainDown(BlockHeader & bhpStart);

private:
   const HashString genesisHash_;
   map<HashString, BlockHeader> headerMap_;
   vector<BlockHeader*> newlyParsedBlocks_;
   deque<BlockHeader*> headersByHeight_;
   BlockHeader *topBlockPtr_;
   BlockHeader *genesisBlockBlockPtr_;
   Blockchain(const Blockchain&); // not defined

   mutex mu_;
};

#endif
