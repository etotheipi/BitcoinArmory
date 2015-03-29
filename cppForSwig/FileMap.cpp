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
}

////////////////////////////////////////////////////////////////////////////////
FileMap::FileMap(FileMap&& fm)
{
   this->filemap_ = fm.filemap_;
   this->mapsize_ = fm.mapsize_;
   lastSeenCumulated_.store(0, std::memory_order_relaxed);

   fnum_ = fm.fnum_;
   fm.filemap_ = nullptr;
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

