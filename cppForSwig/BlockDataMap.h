////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2016, goatpig.                                              //
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //                                      
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#ifndef _BLOCKDATAMAP_H
#define _BLOCKDATAMAP_H

#include <stdint.h>

#include <mutex>
#include <condition_variable>
#include <thread>
#include <memory>
#include <future>
#include <atomic>

#include <iostream>
#include <string>
#include <sstream>
#include <iomanip>

#include <map>

using namespace std;

#ifdef _WIN32
#include <Windows.h>
#include <io.h>
#include <fcntl.h>
#else
#include <errno.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <fcntl.h>
#endif

#include "BlockObj.h"
#include "BinaryData.h"

#define OffsetAndSize pair<size_t, size_t>

////////////////////////////////////////////////////////////////////////////////
struct BCTX
{
   const uint8_t* data_;
   const size_t size_;

   uint32_t version_;
   uint32_t lockTime_;

   bool usesWitness_ = false;

   vector<OffsetAndSize> txins_;
   vector<OffsetAndSize> txouts_;
   vector<OffsetAndSize> witnesses_;

   mutable BinaryData txHash_;

   bool isCoinbase_ = false;

   BCTX(const uint8_t* data, size_t size) :
      data_(data), size_(size)
   {}

   BCTX(const BinaryDataRef& bdr) :
      data_(bdr.getPtr()), size_(bdr.getSize())
   {}

   const BinaryData& getHash(void) const
   {
      if(txHash_.getSize() == 0)
      {
         if (usesWitness_)
         {
            BinaryData noWitData;
            BinaryDataRef version(data_, 4);
           
            auto& lastTxOut = txouts_.back();
            auto witnessOffset = lastTxOut.first + lastTxOut.second;
            BinaryDataRef txinout(data_ + 6, witnessOffset - 6);
            BinaryDataRef locktime(data_ + size_ - 4, 4);
           
            noWitData.append(version);
            noWitData.append(txinout);
            noWitData.append(locktime);
            
            BtcUtils::getHash256(noWitData, txHash_);
         }
         else
         {
            BinaryDataRef hashdata(data_, size_);
            BtcUtils::getHash256(hashdata, txHash_);
         }
      }

      return txHash_;
   }

   BinaryData&& moveHash(void)
   {
      getHash();

      return move(txHash_);
   }

   BinaryDataRef getTxInRef(unsigned inputId) const
   {
      if (inputId >= txins_.size())
         throw range_error("txin index overflow");

      auto txinIter = txins_.cbegin() + inputId;

      return BinaryDataRef(data_ + (*txinIter).first,
         (*txinIter).second);
   }

   BinaryDataRef getTxOutRef(unsigned outputId) const
   {
      if (outputId >= txouts_.size())
         throw range_error("txout index overflow");

      auto txoutIter = txouts_.cbegin() + outputId;

      return BinaryDataRef(data_ + (*txoutIter).first,
         (*txoutIter).second);
   }

   static shared_ptr<BCTX> parse(
      BinaryRefReader brr, unsigned id = UINT32_MAX)
   {
      return parse(brr.getCurrPtr(), brr.getSizeRemaining(), id);
   }

   static shared_ptr<BCTX> parse(
      const uint8_t* data, size_t len, unsigned id=UINT32_MAX)
   {
      vector<size_t> offsetIns, offsetOuts, offsetsWitness;
      auto txlen = BtcUtils::TxCalcLength(
         data, len,
         &offsetIns, &offsetOuts, &offsetsWitness);

      auto txPtr = make_shared<BCTX>(data, txlen);

      //create BCTX object and fill it up
      txPtr->version_ = READ_UINT32_LE(data);

      // Check the marker and flag for witness transaction
      auto brrPtr = data + 4;
      auto marker = (const uint16_t*)brrPtr;
      if (*marker == 0x0100)
         txPtr->usesWitness_ = true;

      //convert offsets to offset + size pairs
      for (int y = 0; y < offsetIns.size() - 1; y++)
         txPtr->txins_.push_back(
         make_pair(
         offsetIns[y],
         offsetIns[y + 1] - offsetIns[y]));

      for (int y = 0; y < offsetOuts.size() - 1; y++)
         txPtr->txouts_.push_back(
         make_pair(
         offsetOuts[y],
         offsetOuts[y + 1] - offsetOuts[y]));

      if (txPtr->usesWitness_)
      {
         for (int y = 0; y < offsetsWitness.size() - 1; y++)
            txPtr->witnesses_.push_back(
            make_pair(
            offsetsWitness[y],
            offsetsWitness[y + 1] - offsetsWitness[y]));
      }

      txPtr->lockTime_ = READ_UINT32_LE(data + offsetsWitness.back());

      if (id != UINT32_MAX)
      {
         txPtr->isCoinbase_ = (id == 0);
      }
      else if (txPtr->txins_.size() == 1)
      {
         auto txinref = txPtr->getTxInRef(0);
         auto bdr = txinref.getSliceRef(0, 32);
         if (bdr == BtcUtils::EmptyHash_)
            txPtr->isCoinbase_ = true;
      }

      return txPtr;
   }
};

////////////////////////////////////////////////////////////////////////////////
class BlockData
{
private:
   shared_ptr<BlockHeader> headerPtr_;
   const uint8_t* data_ = nullptr;
   size_t size_ = SIZE_MAX;

   vector<shared_ptr<BCTX>> txns_;

   unsigned fileID_ = UINT32_MAX;
   size_t offset_ = SIZE_MAX;

   BinaryData blockHash_;
   TxFilter<TxFilterType> txFilter_;

   uint32_t uniqueID_ = UINT32_MAX;

public:
   BlockData(void) {}

   BlockData(uint32_t blockid) 
      : uniqueID_(blockid)
   {}

   void deserialize(const uint8_t* data, size_t size,
      const shared_ptr<BlockHeader>, 
      function<unsigned int(const BinaryData&)> getID, bool checkMerkle,
      bool keepHashes);

   bool isInitialized(void) const
   {
      return (data_ != nullptr);
   }

   const vector<shared_ptr<BCTX>>& getTxns(void) const
   {
      return txns_;
   }

   const shared_ptr<BlockHeader> header(void) const
   {
      return headerPtr_;
   }

   const size_t size(void) const
   {
      return size_;
   }

   void setFileID(unsigned fileid) { fileID_ = fileid; }
   void setOffset(size_t offset) { offset_ = offset; }

   shared_ptr<BlockHeader> createBlockHeader(void) const;
   const BinaryData& getHash(void) const { return blockHash_; }
   
   TxFilter<TxFilterType> computeTxFilter(const vector<BinaryData>&) const;
   const TxFilter<TxFilterType>& getTxFilter(void) const { return txFilter_; }
   uint32_t uniqueID(void) const { return uniqueID_; }
   shared_ptr<BlockHeader> getHeaderPtr(void) const { return headerPtr_; }
};

/////////////////////////////////////////////////////////////////////////////
struct BlockOffset
{
   uint16_t fileID_;
   size_t offset_;

   BlockOffset(uint16_t fileID, size_t offset)
      : fileID_(fileID), offset_(offset)
   {}

   bool operator>(const BlockOffset& rhs)
   {
      if (fileID_ == rhs.fileID_)
         return offset_ > rhs.offset_;

      return fileID_ > rhs.fileID_;
   }

   BlockOffset& operator=(const BlockOffset& rhs)
   {
      if (this != &rhs)
      {
         this->fileID_ = rhs.fileID_;
         this->offset_ = rhs.offset_;
      }

      return *this;
   }
};

/////////////////////////////////////////////////////////////////////////////
class BlockFiles
{
private:
   map<uint32_t, string> filePaths_;
   const string folderPath_;
   size_t totalBlockchainBytes_ = 0;

public:
   BlockFiles(const string& folderPath) :
      folderPath_(folderPath)
   {}

   void detectAllBlockFiles(void);
   const string& folderPath(void) const { return folderPath_; }
   const unsigned fileCount(void) const { return filePaths_.size(); }
};

/////////////////////////////////////////////////////////////////////////////
class BlockDataFileMap
{
   friend class BlockFileMapPointer;
   friend class BlockDataLoader;

private:
   uint8_t* fileMap_ = nullptr;
   size_t size_ = 0;

   atomic<int> useCounter_;

public:
   BlockDataFileMap(const string& filename);

   ~BlockDataFileMap(void)
   {
      //close file mmap
      if (fileMap_ != nullptr)
      {
#ifdef _WIN32
         UnmapViewOfFile(fileMap_);
#else
         munmap(fileMap_, size_);
#endif
         fileMap_ = nullptr;
      }
   }

   const uint8_t* getPtr() const
   {
      return fileMap_;
   }

   size_t size(void) const { return size_; }
};

/////////////////////////////////////////////////////////////////////////////
class BlockDataLoader
{
private:     
   const string path_;
   const string prefix_;

private:   

   BlockDataLoader(const BlockDataLoader&) = delete; //no copies

   uint32_t nameToIntID(const string& filename);
   string intIDToName(uint32_t fileid);

   shared_ptr<BlockDataFileMap>
      getNewBlockDataMap(uint32_t fileid);

public:
   BlockDataLoader(const string& path);

   ~BlockDataLoader(void)
   {}

   shared_ptr<BlockDataFileMap> get(const string& filename);
   shared_ptr<BlockDataFileMap> get(uint32_t fileid);
};

#endif
