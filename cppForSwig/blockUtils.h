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
#define HashString BinaryData

//#define UINT16_SENTINEL numeric_limits<uint16_t>::max()
//#define UINT32_SENTINEL numeric_limits<uint32_t>::max()
//#define UINT64_SENTINEL numeric_limits<uint64_t>::max()

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
   HashString const &  getPrevHash(void) const    { return prevHash_;     }
   HashString const &  getMerkleRoot(void) const  { return merkleRoot_;   }
   uint32_t            getTimestamp(void) const   { return timestamp_;    }
   BinaryData const &  getDiffBits(void) const    { return diffBitsRaw_;  }
   uint32_t            getNonce(void) const       { return nonce_;        }
   HashString const &  getThisHash(void) const    { return thisHash_;     }
   HashString const &  getNextHash(void) const    { return nextHash_;     }
   uint32_t            getNumTx(void) const       { return numTx_;        }
   uint32_t            getBlockHeight(void) const { return blockHeight_;  }
   
   /////////////////////////////////////////////////////////////////////////////
   void setVersion(uint32_t i)        { version_ = i;                    }
   void setPrevHash(HashString str)   { prevHash_.copyFrom(str);         }
   void setMerkleRoot(HashString str) { merkleRoot_.copyFrom(str);       }
   void setTimestamp(uint32_t i)      { timestamp_ = i;                  }
   void setDiffBits(BinaryData str)   { diffBitsRaw_.copyFrom(str);      }
   void setNonce(uint32_t i)          { nonce_ = i;                      }
   void setNextHash(HashString str)   { nextHash_.copyFrom(str);         }

   /////////////////////////////////////////////////////////////////////////////
   void serializeTo(BinaryWriter & bw)
   {
      bw.put_uint32_t  ( version_     );
      bw.put_BinaryData( prevHash_    );
      bw.put_BinaryData( merkleRoot_  );
      bw.put_uint32_t  ( timestamp_   );
      bw.put_BinaryData( diffBitsRaw_ );
      bw.put_uint32_t  ( nonce_       );
   }

   /////////////////////////////////////////////////////////////////////////////
   BinaryData serialize(void)
   {
      BinaryWriter bw(HEADER_SIZE);
      serializeTo(bw);
      return bw.getData();
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

   void unserialize(BinaryReader & br)
   { 
      unserialize(strIn.getPtr());
   }

   BlockHeader( uint8_t const * bhDataPtr,
                HashString* thisHash = NULL) :
      prevHash_(32),
      nextHash_(32),
      numTx_(-1),
      fileByteLoc_(0),  
      difficultyFlt_(-1.0),
      difficultySum_(-1.0),
      blockHeight_(0),
      isMainBranch_(false),
      isOrphan_(false),
      isFinishedCalc_(false)
   {
      unserialize(bhDataPtr);
      if( thisHash != NULL )
         thisHash_.copyFrom(*thisHash);
      else
         getHash(thisHash_.getPtr(), serialize());
   }

   /////////////////////////////////////////////////////////////////////////////
   BlockHeader( BinaryData const * serHeader = NULL,
                HashString const * thisHash  = NULL,
                uint64_t           fileLoc   = UINT64_MAX) :
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
   static void getHash(uint8_t const * blockStart, HashString & hashOut)
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
   HashString     prevHash_;
   HashString     merkleRoot_;
   uint32_t       timestamp_;
   BinaryData     diffBitsRaw_; 
   uint32_t       nonce_; 

   HashString     thisHash_;
   HashString     nextHash_;
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
   static HashString GenesisHash_;
   static HashString EmptyHash_;
   static CryptoPP::SHA256     sha256_;
};


////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
// OutPoint is just a reference to a TxOut
class OutPoint
{
   friend class BlockDataManager;

public:
   OutPoint(void) :
      txHash_(32),
      txOutIndex_(UINT32_MAX)
   {
      // Nothing to put here
   }

   OutPoint(HashString & txHash, uint32_t txOutIndex) :
      txHash_(txHash),
      txOutIndex_(txOutIndex)
   {
      // Nothing to put here
   }

   HashString const & getTxHash(void) { return txHash_; }
   uint32_t getTxOutIndex(void) { return txOutIndex_; }

   void setTxHash(HashString const & hash) { txHash_.copyFrom(hash); }
   void setTxOutIndex(uint32_t idx) { txOutIndex_ = idx; }

   // Define these operators so that we can use OutPoint as a map<> key
   bool operator<(OutPoint const & op2)
   {
      if(txHash_ == op2.txHash_)
         return txOutIndex_ < op2.txOutIndex_;
      else
         return txHash_ < op2.txHash_;
   }
   bool operator==(OutPoint const & op2)
   {
      return (txHash_ == op2.txHash_ && txOutIndex_ == op2.txOutIndex_);
   }

   void serializeTo(BinaryWriter & bw)
   {
      bw.put_BinaryData(txHash_);
      bw.put_uint32_t(txOutIndex_);
   }

   BinaryData serialize(void)
   {
      BinaryWriter bw(36);
      serializeTo(bw);
      return bw.getData();
   }

   void unserialize(BinaryReader & br)
   {
      br.get_BinaryData(txHash_, 32);
      txOutIndex_ = br.get_uint32_t();
   }

   void unserialize(BinaryData const & str)
   {
      unserialize(BinaryReader(str));
   }


private:
   HashString txHash_;
   uint32_t   txOutIndex_;

};


////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
// TxIn 
class TxIn
{
   friend class BlockDataManager;

public:
   TxIn(void) :
      outPoint_(32),
      binScript_(0),
      sequence_(0),
      isCoinbase_(false),
      scriptSize_(0)
   {
      // Nothing to put here
   }

   TxIn(OutPoint const & op,
        BinaryData const & script,
        uint32_t seq,
        bool coinbase) : 
      outPoint_(op),
      binScript_(script),
      sequence_(seq),
      isCoinbase_(coinbase)
   {
      scriptSize_ = (uint32_t)(binScript_.getSize());
   }

   OutPoint const & getOutPoint(void) { return outPoint_; }
   BinaryData const & getBinScript(void) { return binScript_; }
   uint32_t getSequence(void) { return sequence_; }
   void getScriptSize(void) { return scriptSize_; }

   bool getIsCoinbase(void) 
   { 
      // TODO: figure out if this is a coinbase TxIn
      return isCoinbase_;
   }

   void setOutPoint(OutPoint const & op) { outPoint_ = op; }
   void setBinScript(BinaryData const & scr) { binScript_.copyFrom(scr); }
   void setSequence(uint32_t seq) { sequence_ = seq; }
   void setIsCoinbase(bool iscb) { isCoinbase_ = iscb; }


   void serializeTo(BinaryWriter & bw)
   {
      outPoint_.serializeTo(bw);
      bw.put_var_int(scriptSize_);
      bw.put_BinaryData(binScript_);
      bw.put_uint32_t(sequence_);
   }

   BinaryData serialize(void)
   {
      BinaryWriter bw(250);
      serializeTo(bw);
      return bw.getData();
   }

   void unserialize(BinaryReader & br)
   {
      outPoint.unserialize(br);
      scriptSize_ = br.get_var_int();
      br.get_BinaryData(binScript_, scriptSize_);
      sequence_ = br.get_uint32_t();
   }

   void unserialize(BinaryData const & str)
   {
      unserialize(BinaryReader(str));
   }


private:
   OutPoint   outPoint_;
   BinaryData binScript_;
   uint32_t   sequence_;
   bool       isCoinbase_;

   uint32_t   scriptSize_;
};


////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
// TxOut 
class TxOut
{
   friend class BlockDataManager;

public:
   TxOut(void) :
      value_(0),
      pkScript_(0),
      scriptSize_(0)
   {
      // Nothing to put here
   }

   TxOut(uint64_t val, BinaryData const & scr) :
      value_(val),
      pkScript_(scr),
   {
      scriptSize_ = (uint32_t)(pkScript_.getSize());
   }

   uint64_t getValue(void) { return value_; }
   BinaryData const & getPkScript(void) { return pkScript_; }
   void getScriptSize(void) { return scriptSize_; }

   void setValue(uint64_t val) { value_ = val; }
   void setPkScript(BinaryData const & scr) { pkScript_.copyFrom(scr); }


   bool isStandardScript(void) const
   {
      return (pkScript_[0] == 118 &&
              pkScript_[1] == 169 &&
              pkScript_[scriptSize_-2] == 136 &&
              pkScript_[scriptSize_-1] == 172);
   }

   BinaryData const & getRecipientAddr(void)
   {
      if( !isStandardScript() )
         return BinaryData();

      if(recipientAddr_.getSize() < 1)
      {
         BinaryReader binReader(pkScript_);
         binReader.advance(2);
         uint64_t addrLength = binReader.get_var_int();
         recipientAddr_.resize(addrLength);
         binReader.get_BinaryData(recipientAddr_, addrLength);
      }

      return recipientAddr_;
   }


   void serializeTo(BinaryWriter & bw)
   {
      bw.put_uint64_t(value_);
      bw.put_var_int(scriptSize_);
      bw.put_BinaryData(pkScript_);
   }

   BinaryData serialize(void)
   {
      BinaryWriter bw(45);
      serializeTo(bw);
      return bw.getData();
   }

   void unserialize(BinaryReader & br)
   {
      value_ = br.get_uint64_t();
      scriptSize_ = br.get_var_int();
      br.get_BinaryData(pkScript_, scriptSize_);
   }

   void unserialize(BinaryData const & str)
   {
      unserialize(BinaryReader(str));
   }

private:
   uint64_t   value_;
   BinaryData pkScript_;
   uint32_t   scriptSize_;
   BinaryData recipientAddr_;

   bool       isMine_;

};



////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
class Tx
{
   friend class BlockDataManager;

public:
   Tx(void) :
      version_(0),
      numTxIn_(0),
      numTxOut_(0),
      txInList_(0),
      txOutList_(0),
      lockTime_(UINT32_MAX),
      isMine_(false),
      thisHash_(32)
   {
      // Nothing to put here
   }

     
   OutPoint getOutPoint(int index)
   {
      if(thisHash_.getSize() < 1)
         getHash(void);
      return OutPoint(thisHash_, index);
   }


   void serializeTo(BinaryWriter & bw)
   {
      bw.put_uint32_t(version_);
      bw.put_var_int(numTxIn_);
      for(int i=0; i<numTxIn_; i++)
      {
         txInList_[i].serializeTo(bw);
      }
      bw.put_var_int(numTxOut_);
      for(int i=0; i<numTxOut_; i++)
      {
         txOutList_[i].serializeTo(bw);
      }
      bw.put_uint32_t(lockTime_);
   }

   BinaryData serialize(void)
   {
      BinaryWriter bw(300);
      serializeTo(bw);
      return bw.getData();
   }

   void unserialize(BinaryReader & br)
   {
      value_ = br.get_uint64_t();
      scriptSize_ = br.get_var_int();
      br.get_BinaryData(pkScript_, scriptSize_);
   }

   void unserialize(BinaryData const & str)
   {
      unserialize(BinaryReader(str));
   }

private:
   uint32_t      version_;
   uint32_t      numTxIn_;
   uint32_t      numTxOut_;
   vector<TxIn>  txInList_;
   vector<TxOut> txOutList_;
   uint32_t      lockTime_;
   
   bool          isMine_;
   HashString    thisHash_;

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

   static BlockDataManager *         theOnlyBDM_;

   map<HashString, BlockHeader>      headerMap_;
   deque<BlockHeader*>               headersByHeight_;
   BlockHeader*                      topBlockPtr_;
   BlockHeader*                      genBlockPtr_;


   map<HashString, Tx>               txMap_;
   map<OutPoint, TxOut*>             relevantOuts_;



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
   BlockHeader * getHeaderByHash(HashString const & blkHash)
   {
      map<HashString, BlockHeader>::iterator it = headerMap_.find(blkHash);
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
      HashString thisHash(32);
      for(int offset=0; offset<(int)filesize; offset+=HEADER_SIZE)
      {
         //static void getHash(uint8_t* blockStart, HashString & hashOut)
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
      HashString thisHash(32);
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
      HashString theHash(32); 
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
         map<HashString, BlockHeader>::iterator iter;
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

      HashString const & GenesisHash_ = BlockHeader::GenesisHash_;
      HashString const & EmptyHash_   = BlockHeader::EmptyHash_;
      if(topBlockPtr_ == NULL)
         topBlockPtr_ = &genBlock;

      // Store the old top block so we can later check whether it is included 
      // in the new chain organization
      BlockHeader* prevTopBlockPtr = topBlockPtr_;

      // Iterate over all blocks, track the maximum difficulty-sum block
      map<HashString, BlockHeader>::iterator iter;
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

         HashString & childHash        = thisBlockPtr->thisHash_;
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
      map<HashString, BlockHeader>::iterator iter;
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
      map<HashString, BlockHeader>::iterator iter;
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
