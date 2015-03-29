#ifndef _FILEMAP_H
#define _FILEMAP_H
#include <atomic>
#include <memory>
#include "BinaryData.h"
#include <fcntl.h>

struct BlkFile
{
   size_t fnum;
   string path;
   uint64_t filesize;
   uint64_t filesizeCumul;
};

class FileMap
{
   friend class BlockFileAccessor;

private:
   std::atomic<uint64_t> lastSeenCumulated_;

private:
   FileMap(FileMap&& fm);

public:
   uint8_t* filemap_ = nullptr;
   uint64_t mapsize_ = 0;
   uint16_t fnum_;

   FileMap(BlkFile& blk);

   ~FileMap(void);


   void getRawBlock(BinaryDataRef& bdr, uint64_t offset, uint32_t size,
      std::atomic<uint64_t>& lastSeenCumulative);
};

struct FileMapContainer
{
   std::shared_ptr<FileMap> current_;
   std::shared_ptr<FileMap>* prev_ = nullptr;
};

class BlockFileAccessor
{
private:
   shared_ptr<vector<BlkFile>> blkFiles_;
   map<uint16_t, shared_ptr<FileMap> > blkMaps_;
   atomic<uint64_t> lastSeenCumulative_;

   static const uint64_t threshold_ = 50 * 1024 * 1024LL;
   uint64_t nextThreshold_ = threshold_;

   mutex mu_;

public:
   ///////
   BlockFileAccessor(shared_ptr<vector<BlkFile>> blkfiles);

   void getRawBlock(BinaryDataRef& bdr, uint32_t fnum, uint64_t offset,
      uint32_t size, FileMapContainer* fmpPtr = nullptr);

   shared_ptr<FileMap>& getFileMap(uint32_t fnum);
   void dropFileMap(uint32_t fnum);
};

#endif