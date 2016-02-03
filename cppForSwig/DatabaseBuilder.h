////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2016, goatpig.                                              //
//  Distributed under the MIT license                                         //
//  See LICENSE                                                               //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#include "BlockDataMap.h"
#include "Blockchain.h"
#include "bdmenums.h"
#include "Progress.h"

typedef function<void(BDMPhase, double, unsigned, unsigned)> ProgressCallback;

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
      return fileID_ >= rhs.fileID_ && offset_ > rhs.offset_;
   }

   bool operator=(const BlockOffset& rhs)
   {
      this->fileID_ = rhs.fileID_;
      this->offset_ = rhs.offset_;
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
};

/////////////////////////////////////////////////////////////////////////////
class DatabaseBuilder
{
private:
   BlockFiles& blockFiles_;
   Blockchain& bc_;
   LMDBBlockDatabase& db_;
   const ProgressCallback progress_;

   const BinaryData magicBytes_;

   BlockOffset topBlockOffset_;

private:
   void findLastKnownBlockPos();
   BlockOffset loadBlockHeadersFromDB(const ProgressCallback &progress);
   
   bool addBlocksToDB(BlockDataLoader& bdl, uint16_t fileID, size_t startOffset);
   void parseBlockFile(const uint8_t* fileMap, size_t fileSize, size_t startOffset,
      function<void(const uint8_t* data, size_t size, size_t offset)>);

public:
   DatabaseBuilder(BlockFiles& blockFiles, LMDBBlockDatabase& db,
      Blockchain& bc, const ProgressCallback &progress)
      : blockFiles_(blockFiles), db_(db), bc_(bc), progress_(progress),
      magicBytes_(db_.getMagicBytes()), topBlockOffset_(0, 0)
   {}

   void init(void);
   void updateDB(const ProgressCallback &progress);
};