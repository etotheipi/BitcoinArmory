#ifndef _BLOCKUTILS_H_
#define _BLOCKUTILS_H_

#include <stdio.h>
#include <iostream>
#ifdef WIN32
   #include <cstdint>
#else
   #include <stdlib.h>
   #include <inttypes.h>
   #include <cstring>
#endif
#include <fstream>
#include <vector>
#include <queue>
#include <deque>
#include <list>
#include <map>
#include <limits>

#include "BinaryData.h"

#include "cryptlib.h"
#include "sha.h"


#define HEADER_SIZE       80

//#ifdef MAIN_NETWORK
   #define MAGICBYTES "f9beb4d9"
   #define GENESIS_HASH_HEX "6fe28c0ab6f1b372c1a6a246ae63f74f931e8365e15a089c68d6190000000000"
//#else
   //#define MAGICBYTES "fabfb5da"
   //#define GENESIS_HASH_HEX "08b067b31dc139ee8e7a76a4f2cfcca477c4c06e1ef89f4ae308951907000000"
//#endif



using namespace std;


////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
// This class doesn't hold actually block header data, it only holds pointers
// to where the data is in the BlockHeaderManager.  So there is a single place
// where all block headers are stored, and this class tells us where exactly
// is the one we want.
class BlockHeader
{

   friend class BlockDataManager;

public: 

   /////////////////////////////////////////////////////////////////////////////
   uint32_t            getVersion(void) const     { return version_;      }
   BinaryData const &  getPrevHash(void) const    { return prevHash_;     }
   BinaryData const &  getMerkleRoot(void) const  { return merkleRoot_;   }
   uint32_t            getTimestamp(void) const   { return timestamp_;    }
   BinaryData const &  getDiffBits(void) const    { return diffBitsRaw_;  }
   uint32_t            getNonce(void) const       { return nonce_;        }
   BinaryData const &  getThisHash(void) const    { return thisHash_;     }
   BinaryData const &  getNextHash(void) const    { return nextHash_;     }
   uint32_t            getNumTx(void) const       { return numTx_;        }
   uint32_t            getBlockHeight(void) const { return blockHeight_;  }
   
   /////////////////////////////////////////////////////////////////////////////
   void setVersion(uint32_t i)        { version_ = i;                    }
   void setPrevHash(BinaryData str)   { prevHash_.copyFrom(str);         }
   void setMerkleRoot(BinaryData str) { merkleRoot_.copyFrom(str);       }
   void setTimestamp(uint32_t i)      { timestamp_ = i;                  }
   void setDiffBits(BinaryData str)   { diffBitsRaw_.copyFrom(str);      }
   void setNonce(uint32_t i)          { nonce_ = i;                      }
   void setNextHash(BinaryData str)   { nextHash_.copyFrom(str);         }

   /////////////////////////////////////////////////////////////////////////////
   BinaryData const & serialize(void)
   {
      if(serialHeader_.getSize() < HEADER_SIZE)
      {
         serialHeader_.resize(HEADER_SIZE);
         uint8_t* start = serialHeader_.getPtr();
         *(uint32_t*)(        start +  0 ) = version_;
         prevHash_.copyTo(    start +  4 );
         merkleRoot_.copyTo(  start + 36 );
         *(uint32_t*)(        start + 68 ) = timestamp_;
         diffBitsRaw_.copyTo( start + 72 );
         *(uint32_t*)(        start + 76 ) = nonce_;
      }
      return serialHeader_;
   }

   /////////////////////////////////////////////////////////////////////////////
   void unserialize(BinaryData const & strIn) 
   { 
      unserialize(strIn.getPtr());
   }

   void unserialize(uint8_t const * start)
   {
      version_ = *(uint32_t*)(   start +  0 );
      prevHash_.copyFrom(        start +  4, 32);
      merkleRoot_.copyFrom(      start + 36, 32 );
      timestamp_ = *(uint32_t*)( start + 68 );
      diffBitsRaw_.copyFrom(     start + 72, 4 );
      nonce_ = *(uint32_t*)(     start + 76 );

   } 


   BlockHeader( uint8_t const * bhDataPtr,
                BinaryData* thisHash = NULL) :
      prevHash_(32),
      nextHash_(32),
      numTx_(-1),
      fileByteLoc_(0),  
      difficultyFlt_(-1.0),
      difficultySum_(-1.0),
      blockHeight_(0),
      isMainBranch_(false),
      isOrphan_(false),
      isFinishedCalc_(false),
      serialHeader_(0)
   {
      unserialize(bhDataPtr);
      serialHeader_.copyFrom(bhDataPtr, HEADER_SIZE);
      if( thisHash != NULL )
         thisHash_.copyFrom(*thisHash);
      else
         getHash(thisHash_.getPtr(), serialHeader_);
   }

   /////////////////////////////////////////////////////////////////////////////
   BlockHeader( BinaryData const * serHeader = NULL,
                BinaryData const * thisHash = NULL,
                uint64_t    fileLoc = numeric_limits<uint64_t>::max()) :
      prevHash_(32),
      thisHash_(32),
      nextHash_(32),
      numTx_(-1),
      fileByteLoc_(fileLoc),  
      difficultyFlt_(-1.0),
      difficultySum_(-1.0),
      blockHeight_(0),
      isMainBranch_(false),
      isOrphan_(false),
      isFinishedCalc_(false),
      serialHeader_(0)
   {
      if(serHeader != NULL)
      {
         unserialize(*serHeader);
         serialHeader_.copyFrom(*serHeader);
         if( thisHash != NULL )
            thisHash_.copyFrom(*thisHash);
         else
            getHash(thisHash_.getPtr(), serialHeader_);

      }
   }

   /////////////////////////////////////////////////////////////////////////////
   static void getHash(uint8_t const * blockStart, BinaryData & hashOut)
   {
      if(hashOut.getSize() != 32)
         hashOut.resize(32);
      sha256_.CalculateDigest(hashOut.getPtr(), blockStart, HEADER_SIZE);
      sha256_.CalculateDigest(hashOut.getPtr(), hashOut.getPtr(), 32);
   }

   /////////////////////////////////////////////////////////////////////////////
   static double convertDiffBitsToDouble(uint32_t diffBits)
   {
       int nShift = (diffBits >> 24) & 0xff;
       double dDiff = (double)0x0000ffff / (double)(diffBits & 0x00ffffff);
   
       while (nShift < 29)
       {
           dDiff *= 256.0;
           nShift++;
       }
       while (nShift > 29)
       {
           dDiff /= 256.0;
           nShift--;
       }
       return dDiff;
   }

   /////////////////////////////////////////////////////////////////////////////
   void printBlockHeader(ostream & os=cout)
   {
      os << "Block Information: " << blockHeight_ << endl;
      os << " Hash:       " << thisHash_.toHex().c_str() << endl;
      os << " Timestamp:  " << getTimestamp() << endl;
      os << " Prev Hash:  " << prevHash_.toHex().c_str() << endl;
      os << " MerkleRoot: " << getMerkleRoot().toHex().c_str() << endl;
      os << " Difficulty: " << (uint64_t)(difficultyFlt_)
                             << "    (" << getDiffBits().toHex().c_str() << ")" << endl;
      os << " CumulDiff:  " << (uint64_t)(difficultySum_) << endl;
      os << " Nonce:      " << getNonce() << endl;
      os << " FileOffset: " << fileByteLoc_ << endl;
   }


private:

   // All these pointers point to data managed by another class.
   // As such, it is unnecessary to deal with any memory mgmt. 

   // Some more data types to be stored with the header, but not
   // part of the official serialized header data, so these are
   // actual members of the BlockHeader.
   uint32_t       version_;
   BinaryData     prevHash_;
   BinaryData     merkleRoot_;
   uint32_t       timestamp_;
   BinaryData     diffBitsRaw_; 
   uint32_t       nonce_; 

   BinaryData     thisHash_;
   BinaryData     nextHash_;
   uint32_t       numTx_;
   uint32_t       blockHeight_;
   uint64_t       fileByteLoc_;
   double         difficultyFlt_;
   double         difficultySum_;
   bool           isMainBranch_;
   bool           isOrphan_;
   bool           isFinishedCalc_;

   BinaryData     serialHeader_;

   // We should keep the genesis hash handy 
   static BinaryData GenesisHash_;
   static BinaryData EmptyHash_;
   static CryptoPP::SHA256     sha256_;
};



////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
//
// The goal of this class is to create a memory pool in RAM that looks exactly
// the same as the block-headers storage on disk.  There is no serialization
// or unserialization, we just copy back and forth between disk and RAM, and 
// we're done.  So it should be about as fast as theoretically possible, you 
// are limited only by your disk I/O speed.
//
// This is more of a simple test, which will later be applied to the entire
// blockchain.  If it works as expected, then this will potentially be useful
// for the official BTC client which seems to have some speed problems at 
// startup and shutdown.
//
// This class is a singleton -- there can only ever be one, accessed through
// the static method GetInstance().  This method gets the single instantiation
// of the BDM class, and then its public members can be used to access the 
// block data that is sitting in memory.
//
class BlockDataManager
{
private:

   map<BinaryData, BlockHeader>      headerMap_;
   deque<BlockHeader*>               headersByHeight_;
   BlockHeader*                      topBlockPtr_;
   BlockHeader*                      genBlockPtr_;

   static BlockDataManager *      theOnlyBDM_;



private:
   // Set the constructor to private so that only one can ever be created
   BlockDataManager(void) : 
         topBlockPtr_(NULL),
         genBlockPtr_(NULL)
   {
      headerMap_.clear();
      headersByHeight_.clear();
   }

public:

   /////////////////////////////////////////////////////////////////////////////
   // The only way to "create" a BDM is with this method, which creates it
   // if one doesn't exist yet, or returns a reference to the only one
   // that will ever exist
   static BlockDataManager & GetInstance(void) 
   {
      static bool bdmCreatedYet_ = false;
      if( !bdmCreatedYet_ )
      {
         theOnlyBDM_ = new BlockDataManager;
         bdmCreatedYet_ = true;
      }
      return (*theOnlyBDM_);
   }

   /////////////////////////////////////////////////////////////////////////////
   BlockHeader getTopBlock(void)
   {
      return *topBlockPtr_;
   }

   /////////////////////////////////////////////////////////////////////////////
   BlockHeader & getGenesisBlock(void)
   {
      if(genBlockPtr_ == NULL)
         genBlockPtr_ = &(headerMap_[BlockHeader::GenesisHash_]);
      return *genBlockPtr_;
   }

   /////////////////////////////////////////////////////////////////////////////
   // Get a blockheader based on its height on the main chain
   BlockHeader & getHeaderByHeight(int index)
   {
      if( index>=0 && index<(int)headersByHeight_.size())
         return *headersByHeight_[index];
   }

   /////////////////////////////////////////////////////////////////////////////
   // The most common access method is to get a block by its hash
   BlockHeader * getHeaderByHash(BinaryData const & blkHash)
   {
      map<BinaryData, BlockHeader>::iterator it = headerMap_.find(blkHash);
      if(it==headerMap_.end())
         return NULL;
      else
         return &(it->second);
   }


   /////////////////////////////////////////////////////////////////////////////
   // Add headers from a file that is serialized identically to the way
   // we have laid it out in memory.  Return the number of bytes read
   uint64_t importHeadersFromHeaderFile(std::string filename)
   {
      cout << "Reading block headers from file: " << filename.c_str() << endl;
      ifstream is(filename.c_str(), ios::in | ios::binary);
      is.seekg(0, ios::end);
      size_t filesize = (size_t)is.tellg();
      is.seekg(0, ios::beg);
      cout << filename.c_str() << " is " << filesize << " bytes" << endl;
      if((unsigned int)filesize % HEADER_SIZE != 0)
      {
         cout << "filesize=" << filesize << " is not a multiple of header size!" << endl;
         return -1;
      }
      BinaryData allHeaders(filesize);
      uint8_t* front = allHeaders.getPtr();
      is.read((char*)front, filesize);
      BinaryData thisHash(32);
      for(int offset=0; offset<(int)filesize; offset+=HEADER_SIZE)
      {
         //static void getHash(uint8_t* blockStart, BinaryData & hashOut)
         uint8_t* thisPtr = front + offset;
         BlockHeader::getHash(thisPtr, thisHash);
         headerMap_[thisHash] = BlockHeader(thisPtr, &thisHash);
      }
      cout << "Done with everything!  " << filesize << " bytes read!" << endl;
      return filesize;      
   }


   /////////////////////////////////////////////////////////////////////////////
   uint32_t importHeadersFromBlockFile(std::string filename)
   {
      BinaryStreamBuffer bsb(filename, 25*1024*1024);  // use 25 MB buffer
      
      bool readMagic  = false;
      bool readVarInt = false;
      bool readBlock  = false;
      uint32_t numBlockBytes;

      BinaryData magicBucket(4);
      BinaryData magicStr(4);
      magicStr.createFromHex(MAGICBYTES);
      BinaryData thisHash(32);
      BinaryData thisHeaderBD(HEADER_SIZE);
      BlockHeader thisHeaderBH;


      // While there is still data left in the stream (file), pull it
      while(bsb.streamPull())
      {
         // Data has been pulled into the buffer, process all of it
         while(bsb.getBufferSizeRemaining() > 1)
         {
            static int i = 0;
            if( !readMagic )
            {
               if(bsb.getBufferSizeRemaining() < 4)
                  break;
               bsb.reader().get_BinaryData(magicBucket, 4);
               if( !(magicBucket == magicStr) )
               {
                  //cerr << "Magic string does not match network!" << endl;
                  //cerr << "\tExpected: " << MAGICBYTES << endl;
                  //cerr << "\tReceived: " << magicBucket.toHex() << endl;
                  break;
               }
               readMagic = true;
            }

            // If we haven't read the blockdata-size yet, do it
            if( !readVarInt )
            {
               // TODO:  Whoops, this isn't a VAR_INT, just a 4-byte num
               if(bsb.getBufferSizeRemaining() < 4)
                  break;
               numBlockBytes = bsb.reader().get_uint32_t();
               readVarInt = true;
            }


            // If we haven't read the header yet, do it
            uint64_t blkByteOffset = bsb.getFileByteLocation();
            if( !readBlock )
            {
               if(bsb.getBufferSizeRemaining() < numBlockBytes)
                  break;


               bsb.reader().get_BinaryData(thisHeaderBD, HEADER_SIZE);
               thisHeaderBH.unserialize(thisHeaderBD);

               // Here we are only reading headers, so we advance past txData
               bsb.reader().advance((uint32_t)(numBlockBytes-HEADER_SIZE));
               readBlock = true;
            }

            
            readMagic  = false;
            readVarInt = false;
            readBlock  = false;

            // The header has been added to the memory pool, but not indexed
            // in a way that we can locate it efficiently.
            BlockHeader::getHash(thisHeaderBD.getPtr(), thisHash);
            //cout << thisHash.toHex().c_str() << endl;
            headerMap_[thisHash] = BlockHeader(&thisHeaderBD, 
                                               &thisHash,
                                               blkByteOffset+HEADER_SIZE);
         }
      }

      return (uint32_t)headerMap_.size();
   }


   /////////////////////////////////////////////////////////////////////////////
   // Not sure exactly when this would get used...
   void addHeader(BinaryData const & binHeader)
   {
      BinaryData theHash(32); 
      BlockHeader::getHash(binHeader.getPtr(), theHash);
      headerMap_[theHash] = BlockHeader( &binHeader, &theHash);
   }



   // This returns false if our new main branch does not include the previous
   // topBlock.  If this returns false, that probably means that we have
   // previously considered some blocks to be valid that no longer are valid.
   bool organizeChain(bool forceRebuild=false)
   {
      // If rebuild, we zero out any original organization data and do a 
      // rebuild of the chain from scratch.  This will need to be done in
      // the event that our first call to organizeChain returns false, which
      // means part of blockchain that was previously valid, has become
      // invalid.  Rather than get fancy, just rebuild all which takes less
      // than a second, anyway.
      if(forceRebuild)
      {
         map<BinaryData, BlockHeader>::iterator iter;
         for( iter  = headerMap_.begin(); 
              iter != headerMap_.end(); 
              iter++)
         {
            iter->second.difficultySum_ = -1;
            iter->second.difficultyFlt_ = -1;
            iter->second.blockHeight_   =  0;
            iter->second.isFinishedCalc_ = false;
         }
      }

      // Set genesis block
      BlockHeader & genBlock = getGenesisBlock();
      genBlock.blockHeight_    = 0;
      genBlock.difficultyFlt_  = 1.0;
      genBlock.difficultySum_  = 1.0;
      genBlock.isMainBranch_   = true;
      genBlock.isOrphan_       = false;
      genBlock.isFinishedCalc_ = true;

      BinaryData const & GenesisHash_ = BlockHeader::GenesisHash_;
      BinaryData const & EmptyHash_   = BlockHeader::EmptyHash_;
      if(topBlockPtr_ == NULL)
         topBlockPtr_ = &genBlock;

      // Store the old top block so we can later check whether it is included 
      // in the new chain organization
      BlockHeader* prevTopBlockPtr = topBlockPtr_;

      // Iterate over all blocks, track the maximum difficulty-sum block
      map<BinaryData, BlockHeader>::iterator iter;
      uint32_t maxBlockHeight = 0;
      double   maxDiffSum = 0;
      for( iter = headerMap_.begin(); iter != headerMap_.end(); iter ++)
      {
         // *** The magic happens here
         double thisDiffSum = traceChainDown(iter->second);
         // ***
         
         if(thisDiffSum > maxDiffSum)
         {
            maxDiffSum     = thisDiffSum;
            topBlockPtr_   = &(iter->second);
         }
      }

      // Walk down the list one more time, set nextHash fields
      // Also set headersByHeight_;
      topBlockPtr_->nextHash_ = EmptyHash_;
      BlockHeader* thisBlockPtr = topBlockPtr_;
      bool prevChainStillValid = (thisBlockPtr == prevTopBlockPtr);
      headersByHeight_.resize(topBlockPtr_->getBlockHeight()+1);
      while( !thisBlockPtr->isFinishedCalc_ )
      {
         thisBlockPtr->isFinishedCalc_ = true;
         thisBlockPtr->isMainBranch_   = true;
         headersByHeight_[thisBlockPtr->getBlockHeight()] = thisBlockPtr;

         BinaryData & childHash        = thisBlockPtr->thisHash_;
         thisBlockPtr                  = &(headerMap_[thisBlockPtr->prevHash_]);
         thisBlockPtr->nextHash_       = childHash;

         if(thisBlockPtr == prevTopBlockPtr)
            prevChainStillValid = true;
      }

      // Not sure if this should be automatic... for now I don't think it hurts
      if( !prevChainStillValid )
         organizeChain(true); // force-rebuild the blockchain

      return prevChainStillValid;
   }

private:

   /////////////////////////////////////////////////////////////////////////////
   // Start from a node, trace down to the highest solved block, accumulate
   // difficulties and difficultySum values.  Return the difficultySum of 
   // this block.
   double traceChainDown(BlockHeader & bhpStart)
   {
      if(bhpStart.difficultySum_ > 0)
         return bhpStart.difficultySum_;

      // Prepare some data structures for walking down the chain
      vector<double>          difficultyStack(headerMap_.size());
      vector<BlockHeader*>     bhpPtrStack(headerMap_.size());
      uint32_t blkIdx = 0;
      double thisDiff;

      // Walk down the chain of prevHash_ values, until we find a block
      // that has a definitive difficultySum value (i.e. >0). 
      BlockHeader* thisPtr = &bhpStart;
      map<BinaryData, BlockHeader>::iterator iter;
      while( thisPtr->difficultySum_ < 0)
      {
         thisDiff = BlockHeader::convertDiffBitsToDouble(
                              *(uint32_t*)(thisPtr->diffBitsRaw_.getPtr()));
         difficultyStack[blkIdx] = thisDiff;
         bhpPtrStack[blkIdx]     = thisPtr;
         blkIdx++;


         iter = headerMap_.find(thisPtr->prevHash_);
         if( iter != headerMap_.end() )
            thisPtr = &(iter->second);
         else
         {
            // We didn't hit a known block, but we don't have this block's
            // ancestor in the memory pool, so this is an orphan chain...
            // at least temporarily
            markOrphanChain(bhpStart);
            return 0.0;
         }
      }


      // Now we have a stack of difficulties and pointers.  Walk back up
      // (by pointer) and accumulate the difficulty values 
      double   seedDiffSum = thisPtr->difficultySum_;
      uint32_t blkHeight   = thisPtr->blockHeight_;
      for(int32_t i=blkIdx-1; i>=0; i--)
      {
         seedDiffSum += difficultyStack[i];
         blkHeight++;
         thisPtr                 = bhpPtrStack[i];
         thisPtr->difficultyFlt_ = difficultyStack[i];
         thisPtr->difficultySum_ = seedDiffSum;
         thisPtr->blockHeight_   = blkHeight;
      }
      
      // Finally, we have all the difficulty sums calculated, return this one
      return bhpStart.difficultySum_;
     
   }


   /////////////////////////////////////////////////////////////////////////////
   void markOrphanChain(BlockHeader & bhpStart)
   {
      bhpStart.isOrphan_ = true;
      bhpStart.isMainBranch_ = false;
      map<BinaryData, BlockHeader>::iterator iter;
      iter = headerMap_.find(bhpStart.getPrevHash());
      while( iter != headerMap_.end() )
      {
         iter->second.isOrphan_ = true;
         iter->second.isMainBranch_ = false;
         iter = headerMap_.find(iter->second.prevHash_);
      }
   }


   
};



#endif
