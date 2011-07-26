#ifndef _BLOCKUTILS_H_
#define _BLOCKUTILS_H_

#include <stdio.h>
#include <iostream>
#include <inttypes.h>
#include <fstream>
#include <vector>
#include <queue>
#include <list>
#include <map>

#include "sha2.h"

#define HEADER_SIZE       80
#define HEADERS_PER_CHUNK 10000
#define BHM_CHUNK_SIZE    (HEADER_SIZE*HEADERS_PER_CHUNK)


using namespace std;
typedef vector<uint8_t> BinaryData;


////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
// This class doesn't hold actually block header data, it only holds pointers
// to where the data is in the BlockHeaderManager.  So there is a single place
// where all block headers are stored, and this class tells us where exactly
// is the one we want.
class BlockHeaderPtr
{

public: 

   uint32_t       getVersion(void)    { return *version_;                                }
   BinaryData     getPrevHash(void)   { return  BinaryData(prevHash_, prevHash_+32);     }
   BinaryData     getMerkleRoot(void) { return  BinaryData(merkleRoot_, merkleRoot_+32); }
   uint32_t       getTimestamp(void)  { return *timestamp_;                              }
   BinaryData     getDiffBits(void)   { return  BinaryData(diffBits_, diffBits_+4);      }
   uint32_t       getNonce(void)      { return *nonce_;                                  }
   BinaryData     getThisHash(void)   { return  thisHash_;                               }
   BinaryData     getNextHash(void)   { return  nextHash_;                               }
   uint32_t       getNumTx(void)      { return  numTx_;                                  }
   
   void setVersion(uint32_t i)        { *version_ = i;                           }
   void setPrevHash(BinaryData str)   { memcpy(prevHash_, &str[0], 32);          }
   void setMerkleRoot(BinaryData str) { memcpy(merkleRoot_, &str[0], 32);        }
   void setTimestamp(uint32_t i)      { *timestamp_ = i;                         }
   void setDiffBits(BinaryData str)   { memcpy(diffBits_, &str[0], 4);           }
   void setNonce(uint32_t i)          { *nonce_ = i;                             }
   void setNextHash(BinaryData str)   { memcpy( &(nextHash_[0]), &(str[0]), 32); }

   //BinaryData serialize(void) 
   //{ 
      //BinaryData bdout(HEADER_SIZE);
      //memcpy(&(bdout[0]), blockStart_, HEADER_SIZE);
      //return BinaryData;
   //}

   void  unserialize(BinaryData strIn) 
   { 
      memcpy(blockStart_, &strIn[0], HEADER_SIZE);
   }

   bool isInvalid(void) { return (blockStart_==NULL); }

   BlockHeaderPtr(uint8_t* blkptr=NULL) :
      thisHash_(32),
      nextHash_(32),
      numTx_(-1),
      difficultyFlt_(0.0),
      difficultySum_(0.0),
      isMainBranch_(false),
      isOrphan_(true)
   {
      blockStart_ = blkptr;
      if(blkptr != NULL)
      {
         version_    = (uint32_t*)(blockStart_ +  0);
         prevHash_   =            (blockStart_ +  4);
         merkleRoot_ =            (blockStart_ + 36);
         timestamp_  = (uint32_t*)(blockStart_ + 68);
         diffBits_   =            (blockStart_ + 72);
         nonce_      = (uint32_t*)(blockStart_ + 76);
      }
   }


private:
   uint8_t* blockStart_;

   // All these pointers point to data managed by another class.
   // As such, it is unnecessary to deal with any memory mgmt. 
   uint32_t*  version_;
   uint8_t*   prevHash_;
   uint8_t*   merkleRoot_;
   uint32_t*  timestamp_;
   uint8_t*   diffBits_; 
   uint32_t*  nonce_; 

   // Some more data types to be stored with the header, but not
   // part of the official serialized header data, so these are
   // actual members of the BlockHeaderPtr.
   BinaryData     thisHash_;
   BinaryData     nextHash_;
   uint32_t       numTx_;
   double         difficultyFlt_;
   double         difficultySum_;
   bool           isMainBranch_;
   bool           isOrphan_;
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
// of the BHM class, and then its public members can be used to access the 
// block data that is sitting in memory.
//
class BlockHeadersManager
{
private:
   // We will store headers in chunks of 10,000 (800,000 bytes)
   // We will maintain a std::list of such chunks, so that we can
   // efficiently add more chunks as the number of headers increases
   //
   // Note this is a linked list, but we simulatneously maintain a 
   // list of pointers to these chunks so we can also access by
   // index (copying a vector of pointers to expand it is a lot better
   // than copying a vector of 1MB chunks)
   list<BinaryData>                                   chunks_;
   vector<list<BinaryData>::iterator>                 chunkPtrs_;

   map<BinaryData, BlockHeaderPtr>                    headerMap_;
   vector<map<BinaryData, BlockHeaderPtr>::iterator>  headersByHeight_;
   vector<uint8_t*>                                   rawHeaderPtrs_;
   queue<uint8_t*>                                    deletedPtrs_;
   uint32_t                                           nextHeaderIndex_;  

   static BlockHeadersManager *                       theOnlyBHM_;
   static sha2                                        sha256_;


private:
   // Set the constructor to private so that only one can ever be created
   BlockHeadersManager(void) : 
         chunks_(0), 
         chunkPtrs_(0), 
         nextHeaderIndex_(0) 
   {
      addChunk();
      headerMap_.clear();
   }

public:

   // The only way to "create" a BHM is with this method, which creates it
   // if one doesn't exist yet, or returns a reference to the only one
   // that will ever exist
   static BlockHeadersManager & GetInstance(void) 
   {
      static bool bhmCreatedYet_ = false;
      if( !bhmCreatedYet_ )
      {
         theOnlyBHM_ = new BlockHeadersManager;
         bhmCreatedYet_ = false;
      }
      return (*theOnlyBHM_);
   }

   // Get a blockheader based on its height on the main chain
   BlockHeaderPtr getHeaderByHeight(int index)
   {
      if( index>=0 && index<(int)headersByHeight_.size())
         return headersByHeight_[index]->second;
   }

   // The most common access method is to get a block by its hash
   BlockHeaderPtr getHeaderByHash(BinaryData blkHash)
   {
      map<BinaryData, BlockHeaderPtr>::iterator it = headerMap_.find(blkHash);
      if(it==headerMap_.end())
         return BlockHeaderPtr(NULL);
      else
         return headerMap_[blkHash];
   }


   // Add headers from a file that is serialized identically to the way
   // we have laid it out in memory.  Return the number of bytes read
   long importDataFromFile(std::string filename)
   {
      cout << "Reading block headers from file: " << filename.c_str() << endl;
      ifstream is(filename.c_str(), ios::in | ios::binary);
      is.seekg(0, ios::end);
      long filesize = is.tellg();
      is.seekg(0, ios::beg);
      if(filesize % HEADER_SIZE != 0)
         return - 1;
      
      // We'll need this information to do the indexing, later
      int numHeadersToAdd = filesize / HEADER_SIZE;

      int numHeadersLeft = numHeadersToAdd;
      int numToCopy = nHeadersLeftInChunk();  // the first copy
      while(numToCopy>0) 
      {
         cout << "\tCopying " << numHeadersLeft << " headers" << endl;
         int nBytes = numToCopy * HEADER_SIZE;
         is.read( (char *)getNextEmptyPtr(), nBytes);
         incrementHeaderIndex(numToCopy);
         
         numHeadersLeft -= numToCopy;
         numToCopy = min(numHeadersLeft, HEADERS_PER_CHUNK);
      }

      cout << "Done reading headers, now indexing the new data." << endl;
      // Now with all the data in memory, create BlockHeaderPtr objects
      for( int i=0; i<numHeadersToAdd; i++)
      {
         // we'll come back to this
      }

      cout << "Done with everything!  " << filesize << " bytes read!" << endl;
      return filesize;      
   }

   /////////////////////////////////////////////////////////////////////////////
   // We accommodate two different kinds of accesses:  
   //    (1) Someone supplies a chunk of header data, and we intelligently
   //        copy it into the memory pool
   //    (2) We provide a pointer to the next empty location, and let the
   //        requestor copy data in, probably directly from a ifstream.read()
   //        call. 
   //
   // Method (2) is UNSAFE, but may not actually be necessary, except for
   // within this class for reading in files.  
   //        
   /////////////////////////////////////////////////////////////////////////////


   int nHeadersLeftInChunk(void)
   {
      return (HEADERS_PER_CHUNK - (nextHeaderIndex_ % HEADERS_PER_CHUNK));
   }


   void defrag(void)
   {
      // TODO:  Still need to write this.  Will move the headers at the
      //        back of the list into spots previously occupied by other
      //        block that were deleted.
      //          
   }
   

private:
   // Add another chunk of 10,000 block headers to the global memory pool
   void addChunk(void)
   {
      chunks_.push_back(BinaryData(BHM_CHUNK_SIZE));
      list<BinaryData>::iterator iter = chunks_.end();
      iter--;
      chunkPtrs_.push_back(iter);
   }

   // Bulk-allocate some space for a certain number of headers
   //void allocate(int nHeaders)
   //{
      //int prevNChunk = (int)chunks_.size();
      //int needNChunk = (nHeaders / HEADERS_PER_CHUNK) + 1;
      //for(int i=prevNChunk+1; i<=needNChunk; i++)
         //addChunk();
   //}

   static void getHash(BinaryData blkHeaderIn, BinaryData & hashOut)
   {
      hashOut.resize(32);
      string const & theHash = sha256_.GetHash(sha2::enuSHA256, &(blkHeaderIn[0]), HEADER_SIZE);
      memcpy(&(hashOut[0]), theHash.c_str(), 32);
   }

   uint8_t* getNextEmptyPtr(void) const
   { 
      int chunkIndex  = nextHeaderIndex_ / HEADERS_PER_CHUNK;
      int headerIndex = nextHeaderIndex_ % HEADERS_PER_CHUNK;
      BinaryData & chnkptr = *(chunkPtrs_[chunkIndex]);
      return &(chnkptr[0]) + HEADER_SIZE * headerIndex;
   }

   bool incrementHeaderIndex(int nIncr=1)
   {
      int oldChunkIndex = nextHeaderIndex_ / HEADERS_PER_CHUNK;
      nextHeaderIndex_ += nIncr;
      int newChunkIndex = nextHeaderIndex_ / HEADERS_PER_CHUNK;
      // We return a indicator that we are in a different chunk than
      // we started.  This may 
      if(oldChunkIndex != newChunkIndex)
         return false;
   }
   
};



#endif
