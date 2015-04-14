#ifndef _FILEMAP_H
#define _FILEMAP_H
#include <atomic>
#include <memory>
#include <thread>
#include <condition_variable>
#include "BinaryData.h"
#include <fcntl.h>

enum BFA_PREFETCH
{
   PREFETCH_NONE,
   PREFETCH_FORWARD,
   PREFETCH_BACKWARD
};

enum FILEMAP_FETCH
{
   FETCH_NONE,
   FETCH_FETCHED,
   FETCH_ACCESSED
};

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
   FILEMAP_FETCH fetch_ = FETCH_NONE;

public:
   uint8_t* filemap_ = nullptr;
   uint64_t mapsize_ = 0;
   uint16_t fnum_;

private:
   FileMap(FileMap&& fm);

public:
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
   BFA_PREFETCH prefetch_;

   //prefetch thread members
   std::thread tID_;
   std::mutex prefetchMu_;
   std::condition_variable prefetchCV_;

   bool runThread_ = true;
   uint32_t prefetchFileNum_ = UINT32_MAX;

public:
   ///////
   BlockFileAccessor(shared_ptr<vector<BlkFile>> blkfiles, 
                     BFA_PREFETCH prefetch=PREFETCH_NONE);

   ~BlockFileAccessor(void);

   void getRawBlock(BinaryDataRef& bdr, uint32_t fnum, uint64_t offset,
      uint32_t size, FileMapContainer* fmpPtr = nullptr);

   shared_ptr<FileMap>& getFileMap(uint32_t fnum);
   void dropFileMap(uint32_t fnum);

   static void prefetchThread(BlockFileAccessor* bfaPtr);
};

#endif