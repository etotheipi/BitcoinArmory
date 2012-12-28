////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2013, Alan C. Reiner    <alan.reiner@gmail.com>        //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE or http://www.gnu.org/licenses/agpl.html                      //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#ifndef _FILEDATAPTR_H_
#define _FILEDATAPTR_H_


#include <fstream>
#include <vector>
#include <string>
#include "BinaryData.h"
#include "BtcUtils.h"


#define DEFAULT_CACHE_SIZE (1*1024*1024)

////////////////////////////////////////////////////////////////////////////////
//
// The goal of this class is to replace mmap on OSes/architectures where it 
// doesn't perform well.  Specifically: Windows.  But probably also 32-bit
// Linux when blockchain size exceeds 4 GB -- I believe that is when the 
// per-process virtual memory limit is exceeded and even 32-bit linux will
// stop working.
//
// Don't need the crazy optimizations and smart-caching.  Just need to to 
// remember the last X MB of requests in case something is accessed lots of 
// times all at once (like iterating through TxIns and TxOuts in a Tx, so
// the Tx gets loaded once into RAM for multiple accesses).  Blockchain 
// scanning will actually be implemented completely separately from this, 
// so this solution doesn't need to accommodate high-volume accesses.
//
//
// NOTE: I made start-byte a uint32_t because one of the reasons for
//       designing this class the way I did was that the blockchain 
//       files never exceed 2 GB.  Therefore, the file offset will never
//       overflow this variable.  For other applications, this may 
//       necessitate a change.  But for now, this reduces the size of
//       the individual FileDataPtr objects, which is actually quite useful.
//
//
////////////////////////////////////////////////////////////////////////////////

class FileDataCache;

// All data will be stored as one of these sortable file references
class FileDataPtr
{
public:
   FileDataPtr(void) :
      fileIndex_(UINT16_MAX), 
      startByte_(UINT32_MAX),
      numBytes_(0) {}

   FileDataPtr(uint16_t fidx, uint32_t start, uint32_t nbytes) : 
      fileIndex_(fidx), 
      startByte_(start),
      numBytes_(nbytes) {}


   uint16_t getFileIndex(void) const {return fileIndex_;}
   uint32_t getStartByte(void) const {return startByte_;}
   uint32_t getNumBytes(void) const  {return numBytes_;}

   void     setFileIndex(uint16_t i) {fileIndex_ = i;}
   void     setStartByte(uint32_t b) {startByte_ = b;}
   void     setNumBytes(uint32_t n)  {numBytes_  = n;}

   // We need to be able to sort these things...
   bool operator<(FileDataPtr const & loc2) const
   {
      if(fileIndex_ == loc2.fileIndex_)
      {
         if(startByte_ == loc2.startByte_)
            return (numBytes_<loc2.numBytes_);
         else
            return (startByte_<loc2.startByte_);
      }
      else
         return (fileIndex_<loc2.fileIndex_);
   }

   // An equality operator helps
   bool operator==(FileDataPtr const & loc2) const
   {
      if(startByte_ == loc2.startByte_ && 
         fileIndex_ == loc2.fileIndex_ && 
         numBytes_  == loc2.numBytes_)
         return true;
      return false;
   }


   // This returns a pointer to the data in cache -- it's pulled into the
   // cache if it wasn't there already.  It's unsafe because the pointer
   // could become invalid if new data is pulled into cache and this data
   // is removed from the cache... 
   // It can be used safely only if you guarantee that no other cache ops
   // will be executed between calling this method and using the pointer.
   uint8_t* getUnsafeDataPtr(void) const;

   // This is always safe.  If the data is cached, it is copied to the 
   // return value.  If not, it's retrieved from disk and then copied.
   BinaryData getDataCopy(void) const;  

   // All this does is retrieve the data as if it was requested, but
   // doesn't actually return it.  Therefore it will pull it into the 
   // cache, so that calls requesting relevant data will be pre-cached.
   // For instance, you may use this for a full 2MB chunk of data, which
   // you know contains a dozens of data requests you're about to make.
   void preCacheThisChunk(void) const; 

   // Use this to set the size of the cache, if you don't want the default
   static void SetupFileCaching(uint64_t maxCacheSize_=DEFAULT_CACHE_SIZE);

   // Sometimes we need to do a sequence of operations on the FileDataCache
   // itself, so you might as well just get a reference to it and use that.
   // Under most conditions, though, you won't need this...
   // (usually only when specifying what files to track)
   static FileDataCache & getGlobalCacheRef(void) { return globalCache_; }

private:
   uint16_t fileIndex_;
   uint32_t startByte_;
   uint32_t numBytes_;

   static FileDataCache globalCache_;
};





class FileDataCache
{
public:

   /////////////////////////////////////////////////////////////////////////////
   FileDataCache(uint64_t maxSize=DEFAULT_CACHE_SIZE)
   { 
      clear(); 
      setCacheSize(maxSize); 
   }

   /////////////////////////////////////////////////////////////////////////////
   ~FileDataCache(void)
   { 
      clear(); 
   }

   /////////////////////////////////////////////////////////////////////////////
   void clear(void)
   {
      for(uint8_t i=0; i<openFiles_.size(); i++)
         if(openFiles_[i] != NULL)
            delete openFiles_[i];

      openFiles_.clear();
      cachedData_.clear();
      cacheMap_.clear();
      cacheUsed_ = 0;
      cacheSize_ = 0;
   }

   /////////////////////////////////////////////////////////////////////////////
   void setCacheSize(uint64_t newSize)
   {
      cacheSize_ = newSize;
      clearExcessCacheData();
   }

   /////////////////////////////////////////////////////////////////////////////
   uint32_t refreshLastFile(void)
   {
      uint32_t lastIndex = openFiles_.size()-1;
      return openFile(lastIndex, fileNames_[lastIndex]);
   }

   /////////////////////////////////////////////////////////////////////////////
   uint32_t openFile(uint32_t fIndex, string filename)
   {

      // Make sure file exists
      if(BtcUtils::GetFileSize(filename) == UINT64_MAX)
         return UINT32_MAX;

      while(fIndex >= openFiles_.size())
      {
         openFiles_.push_back(NULL);
         fileSizes_.push_back((uint32_t)0);
         fileNames_.push_back(string(""));
         cumulSizes_.push_back((uint64_t)0);
      }

      
      ifstream* istrmPtr = openFiles_[fIndex];
      if(istrmPtr==NULL)
      {
         cout << "Opening file " << fIndex+1 << ": " << filename.c_str() << endl;
         openFiles_[fIndex] = new ifstream;
      }
      else
      {
         if(istrmPtr->is_open())
            istrmPtr->close();
      }


      istrmPtr = openFiles_[fIndex];
      istrmPtr->open(filename.c_str(), ios::in|ios::binary);

      if( !istrmPtr->is_open() )
      {
         cout << "***ERROR:  Could not open file! : " << filename << endl;
         return UINT32_MAX;
      }

      fileNames_[fIndex] = filename;

      // Get the filesize
      istrmPtr->seekg(0, ios::end);
      fileSizes_[fIndex] = istrmPtr->tellg();
      istrmPtr->seekg(0, ios::beg);

      // Update the cumulative filesize list
      uint64_t csize = 0;
      for(uint32_t i=0; i<openFiles_.size(); i++)
      {
         csize += fileSizes_[i];
         cumulSizes_[i] = csize;
      }

      // Return the size of the file we just opened
      return fileSizes_[fIndex];
   }
   

   /////////////////////////////////////////////////////////////////////////////
   void closeFile(uint32_t fidx)
   {
      
   }

   /////////////////////////////////////////////////////////////////////////////
   uint8_t* dataIsCached(FileDataPtr const & fdref)
   {
      static map<FileDataPtr, list<CacheData>::iterator>::iterator iter;

      // Retrieve one above the top.
      iter = cacheMap_.upper_bound(fdref);
      if(iter==cacheMap_.begin())
         return NULL;
      
      iter--;
      uint32_t cidx   = iter->first.getFileIndex();
      uint32_t cstart = iter->first.getStartByte();
      uint32_t crefsz = iter->second->second.getSize();

      if(cidx != fdref.getFileIndex())
         return NULL;

      // We have cached data in the same file, and starting before fdref...
      uint32_t coffset = fdref.getStartByte() - cstart;
      if(coffset + fdref.getNumBytes() > crefsz)
         return NULL;

      return iter->second->second.getPtr() + coffset;
   }


   /////////////////////////////////////////////////////////////////////////////
   uint8_t* getCachedDataPtr(FileDataPtr const & fdref)
   {
      uint8_t* ptr = dataIsCached(fdref);
      if(ptr != NULL || fdref.getNumBytes() > cacheSize_)
         return ptr;

      // Wasn't in the cache yet, let's get it into the cache...
      uint32_t cidx   = fdref.getFileIndex();
      uint32_t cstart = fdref.getStartByte();
      uint32_t cbytes = fdref.getNumBytes();

      clearExcessCacheData(cbytes);

      if( cidx >= openFiles_.size() || cstart + cbytes > fileSizes_[cidx] )
         return NULL;

      openFiles_[cidx]->seekg(cstart);
      cachedData_.push_back( CacheData(fdref, BinaryData(cbytes)) );
      list<CacheData>::iterator iter = cachedData_.end();
      iter--;
      uint8_t* newDataPtr = iter->second.getPtr();
      openFiles_[cidx]->read((char*)newDataPtr, cbytes);
      cacheMap_[fdref] = iter;
      cacheUsed_ += cbytes;

      return newDataPtr;
   }

   /////////////////////////////////////////////////////////////////////////////
   BinaryData getData(FileDataPtr const & fdref)
   {
      uint8_t* cachePtr = getCachedDataPtr(fdref);
      if(cachePtr==NULL)
      {
         cout << "***ERROR:  Could not retrieve cache!" << endl;
         return BinaryData(0);
      }

      return BinaryData(cachePtr, fdref.getNumBytes());
   }

   /////////////////////////////////////////////////////////////////////////////
   void clearExcessCacheData(uint64_t incomingBytes=0)
   {
      // TODO:  This turned out to be ridiculously slow!  
      //        every single one of these lines should
      //        be efficient, but I must've missed something!
      //while(cacheUsed_+incomingBytes > cacheSize_ )
      //{
         //list<CacheData>::iterator cIter = cachedData_.begin();
         //FileDataPtr & toRemove = cIter->first;
         //cacheUsed_ -= toRemove.getNumBytes();
         //cacheMap_.erase(toRemove);
         //cachedData_.erase(cIter);
      //}

      // This is a very "dumb" version that works great for pre-caching
      // which is the really important part.  If the cache is full, just
      // clear it completely!
      //
      if(cacheUsed_+incomingBytes > cacheSize_ )
      {
         cachedData_.clear();
         cacheMap_.clear();
         cacheUsed_ = 0;
      }
               
      
   }



   /////////////////////////////////////////////////////////////////////////////
   void pprintCacheState(void)
   {
      uint32_t nFile = fileSizes_.size();
      cout << "FileDataCache information:" << endl;
      cout << "   Cache Size: " << BtcUtils::numToStrWCommas(cacheSize_).c_str() << " bytes" << endl;
      cout << "   Cache Used: " << BtcUtils::numToStrWCommas(cacheUsed_).c_str() << " bytes" << endl;
      cout << "   Files Repr: " << BtcUtils::numToStrWCommas(cumulSizes_[nFile-1]).c_str() << " bytes" << endl;
      cout << "   Files" << endl;
      for(uint32_t i=0; i<nFile; i++)
      {
         cout << "      ";
         cout << fileNames_[i].c_str() << " : ";
         cout << BtcUtils::numToStrWCommas(fileSizes_[i]).c_str() << " (sum: ";
         cout << BtcUtils::numToStrWCommas(cumulSizes_[i]).c_str() << ")" << endl;
      }
      cout << endl;

      /*
      cout << "   Cached Data: " << cachedData_.size() << " cache chunks " << endl;

      map<FileDataPtr, list<CacheData>::iterator>::iterator mapIter;
      uint32_t i=0;
      for(mapIter = cacheMap_.begin(); mapIter != cacheMap_.end();  mapIter++)
      {
         cout << "       " << i++ << " : (";
         cout << mapIter->first.getFileIndex() << ", ";
         cout << mapIter->first.getStartByte() << ", ";
         cout << mapIter->first.getNumBytes() << ") ";
         cout << endl;
      }
      cout << endl;
      */
   }

   uint32_t getFileSize(uint32_t i) {return fileSizes_[i]; }
   uint32_t getLastFileSize(void) {return fileSizes_[fileSizes_.size()-1]; }
   uint64_t getCumulFileSize(uint32_t i=UINT32_MAX)
   {
      if(i==UINT32_MAX)
         return cumulSizes_[cumulSizes_.size()-1];
      else
         return cumulSizes_[i];
   }


private:
   typedef pair<FileDataPtr, BinaryData>   CacheData;


   vector<ifstream*>                             openFiles_;
   vector<uint32_t>                              fileSizes_;
   vector<uint64_t>                              cumulSizes_;
   vector<string>                                fileNames_;
   list<CacheData>                               cachedData_;
   map<FileDataPtr, list<CacheData>::iterator>   cacheMap_;
   uint64_t                                      cacheUsed_;
   uint64_t                                      cacheSize_;

};




#endif
