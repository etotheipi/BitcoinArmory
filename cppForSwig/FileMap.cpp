#include "FileMap.h"

FileMap::FileMap(BlkFile& blk)
{
   lastSeenCumulated_.store(0, std::memory_order_relaxed);
   fnum_ = blk.fnum;
#ifdef WIN32
   int fd = _open(blk.path.c_str(), _O_RDONLY | _O_BINARY);
   if (fd == -1)
      throw std::runtime_error("failed to open file");

   mapsize_ = blk.filesize;
   filemap_ = (uint8_t*)malloc(mapsize_);
   _read(fd, filemap_, mapsize_);
   _close(fd);
#else
   int fd = open(blk.path.c_str(), O_RDONLY);
   if (fd == -1)
      throw std::runtime_error("failed to open file");

   mapsize_ = blk.filesize;
   filemap_ = (uint8_t*)malloc(mapsize_);
   read(fd, filemap_, mapsize_);

   close(fd);
#endif

   fetch_.store(FETCH_FETCHED, memory_order_release);
}

////////////////////////////////////////////////////////////////////////////////
FileMap::FileMap(FileMap&& fm)
{
   this->filemap_ = fm.filemap_;
   this->mapsize_ = fm.mapsize_;
   lastSeenCumulated_.store(0, std::memory_order_relaxed);

   fnum_ = fm.fnum_;
   fm.filemap_ = nullptr;
   
   fetch_.store(fm.fetch_.load(memory_order_relaxed), 
      memory_order_relaxed);
}


////////////////////////////////////////////////////////////////////////////////
FileMap::~FileMap()
{
   if (filemap_ != nullptr)
      free(filemap_);

   filemap_ = nullptr;
}

////////////////////////////////////////////////////////////////////////////////
void FileMap::getRawBlock(BinaryDataRef& bdr, uint64_t offset, uint32_t size,
   std::atomic<uint64_t>& lastSeenCumulative)
{
   bdr.setRef(filemap_ + offset, size);

   lastSeenCumulated_.store(
      lastSeenCumulative.fetch_add(size, std::memory_order_relaxed) + size,
      std::memory_order_relaxed);
}

////////////////////////////////////////////////////////////////////////////////
///
/// BlockFileAccessor
///
////////////////////////////////////////////////////////////////////////////////
BlockFileAccessor::BlockFileAccessor(shared_ptr<vector<BlkFile>> blkfiles,
   BFA_PREFETCH prefetch)
   : blkFiles_(blkfiles), prefetch_(prefetch)
{
   lastSeenCumulative_.store(0, memory_order_relaxed);

   cleanupTID_ = thread(cleanupThread, this);

   if (prefetch == PREFETCH_NONE)
      return;

   prefetchTID_ = thread(prefetchThread, this);
}

////////////////////////////////////////////////////////////////////////////////
BlockFileAccessor::~BlockFileAccessor()
{
   //make sure to shutdown the prefetch thread before returning from the dtor
   {
      unique_lock<mutex> lock(globalMutex_);
      runThread_ = false;
      cv_.notify_all();
   }

   if (cleanupTID_.joinable())
      cleanupTID_.join();
   
   if (!prefetchTID_.joinable())
      return;

   prefetchTID_.join();
}

////////////////////////////////////////////////////////////////////////////////
void BlockFileAccessor::getRawBlock(BinaryDataRef& bdr, uint32_t fnum,
   uint64_t offset, uint32_t size, FileMapContainer* fmpPtr)
{
   shared_ptr<FileMap> fmptr;
   if (fmpPtr != nullptr &&
      fmpPtr->prev_ != nullptr)
   {
      if (fmpPtr->prev_->fnum_ == fnum)
         fmptr = fmpPtr->prev_;
   }

   if (fmptr == nullptr)
      fmptr = getFileMap(fnum);

   fmptr->getRawBlock(bdr, offset, size, lastSeenCumulative_);

   if (fmpPtr != nullptr)
      fmpPtr->current_ = fmptr;
}

////////////////////////////////////////////////////////////////////////////////
shared_ptr<FileMap> BlockFileAccessor::getFileMap(uint32_t fnum)
{
   unique_lock<mutex> lock(globalMutex_);

   auto mapIter = blkMaps_.find(fnum);
   if (mapIter == blkMaps_.end())
   {
      shared_ptr<FileMap> fm(new FileMap((*blkFiles_)[fnum]));
      fm->lastSeenCumulated_.store(
         lastSeenCumulative_.load(memory_order_relaxed),
         memory_order_release);
      auto result = blkMaps_.insert(make_pair(fnum, fm));
      mapIter = result.first;
   }

   if (mapIter->second->fetch_.load(memory_order_relaxed) != FETCH_ACCESSED && 
       prefetch_ != PREFETCH_NONE)
   {
      //signal the prefetch thread to grab the next file
      uint32_t nextFnum = fnum + 1;
      if (prefetch_ == PREFETCH_FORWARD)
      {
         if (nextFnum > blkFiles_->size() - 1)
            nextFnum = UINT32_MAX;
      }
      else
      {
         nextFnum = fnum - 1;
      }

      //We only try to lock the prefetch thread mutex. If it fails, it means
      //another thread is already filling the prefetch queue, or the thread is
      //busy.
      unique_lock<mutex> lock(prefetchMutex_, defer_lock);
      if (lock.try_lock())
      {
         prefetchFileNum_ = nextFnum;
      }
   }

   cv_.notify_all();
   mapIter->second->fetch_.store(FETCH_ACCESSED, memory_order_release);
   return mapIter->second;
}

////////////////////////////////////////////////////////////////////////////////
void BlockFileAccessor::dropFileMap(uint32_t fnum)
{
   unique_lock<mutex> lock(globalMutex_);
   blkMaps_.erase(fnum);
}

////////////////////////////////////////////////////////////////////////////////
void BlockFileAccessor::prefetchThread(BlockFileAccessor* bfaPtr)
{
   try
   {
      if (bfaPtr == nullptr)
         return;

      unique_lock<mutex> prefetchLock(bfaPtr->prefetchMutex_);

      while (bfaPtr->runThread_)
      {
         {
            unique_lock<mutex> bfaLock(bfaPtr->globalMutex_);

            if (bfaPtr->prefetchFileNum_ != UINT32_MAX)
            {
               auto mapIter = bfaPtr->blkMaps_.find(bfaPtr->prefetchFileNum_);
               if (mapIter == bfaPtr->blkMaps_.end())
               {
                  shared_ptr<FileMap> fm(
                     new FileMap((*bfaPtr->blkFiles_)[bfaPtr->prefetchFileNum_]));

                  bfaPtr->blkMaps_[bfaPtr->prefetchFileNum_] = fm;
               }
            }
         }

         bfaPtr->cv_.wait(prefetchLock);
      }
   }
   catch (exception &e)
   {
      LOGERR << e.what();
   }
   catch (...)
   {
      LOGERR << "error in prefetchThread()";
   }
}

////////////////////////////////////////////////////////////////////////////////
void BlockFileAccessor::cleanupThread(BlockFileAccessor* bfaPtr)
{
   //clean up maps that haven't been used for a while

   while (bfaPtr->runThread_)
   {
      unique_lock<mutex> lock(bfaPtr->globalMutex_);
      uint64_t lastSeen = bfaPtr->lastSeenCumulative_.load(memory_order_relaxed);

      if (lastSeen >= bfaPtr->nextThreshold_)
      {
         auto mapIter = bfaPtr->blkMaps_.begin();

         while (mapIter != bfaPtr->blkMaps_.end())
         {
            if (mapIter->second->fetch_.load(memory_order_relaxed) == 
                FETCH_ACCESSED 
                &&
                mapIter->second->lastSeenCumulated_ + threshold_ <
                lastSeen)
            {
               if (mapIter->second.use_count() == 1)
               {
                  bfaPtr->blkMaps_.erase(mapIter++);
                  continue;
               }
            }

            ++mapIter;
         }

         bfaPtr->nextThreshold_ =
            lastSeen + threshold_;
      }

      bfaPtr->cv_.wait(lock);
   }
}
