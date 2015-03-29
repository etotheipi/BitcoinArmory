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

#endif