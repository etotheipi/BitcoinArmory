////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2012, Alan C. Reiner    <alan.reiner@gmail.com>        //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE or http://www.gnu.org/licenses/agpl.html                      //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#ifndef _FILEDATAREF_H_
#define _FILEDATAREF_H_


#include <fstream>
#include <vector>
#include <string>
#include "BinaryData.h"
#include "BtcUtils.h"


#define DEFAULT_CACHE_SIZE (16*1024*1024)

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
//       the individual FileDataRef objects, which is actually quite useful.
//
//
////////////////////////////////////////////////////////////////////////////////

class FileDataCache;

// All data will be stored as one of these sortable file references
class FileDataRef
{
public:
   FileDataRef(uint32_t fidx, uint32_t start, uint32_t nbytes) : 
      fileIndex_(fidx), 
      startByte_(start),
      numBytes_(nbytes) {}


   uint32_t getFileIndex(void) const {return fileIndex_;}
   uint32_t getStartByte(void) const {return startByte_;}
   uint32_t getNumBytes(void) const  {return numBytes_;}

   uint32_t setFileIndex(uint32_t i) {fileIndex_ = i;}
   uint32_t setStartByte(uint32_t b) {startByte_ = b;}
   uint32_t setNumBytes(uint32_t n)  {numBytes_  = n;}

   // We need to be able to sort these things...
   bool operator<(FileDataRef const & loc2) const
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
   bool operator==(FileDataRef const & loc2) const
   {
      if(startByte_ == loc2.startByte_ && 
         fileIndex_ == loc2.fileIndex_ && 
         numBytes_  == loc2.numBytes_)
         return true;
      return false;
   }


   uint8_t* getTempDataPtr(void); 
   BinaryData getDataCopy(void) const;  

   static void SetupFileCaching(uint64_t maxCacheSize_=DEFAULT_CACHE_SIZE);
   static FileDataCache & getGlobalCacheRef(void) { return globalCache_; }

private:
   uint32_t fileIndex_;
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
   uint32_t openFile(uint32_t fIndex, string filename)
   {
      // Make sure file exists
      if(BtcUtils::getFilesize(filename) == UINT64_MAX)
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
   uint8_t* dataIsCached(FileDataRef const & fdref)
   {
      static map<FileDataRef, list<CacheData>::iterator>::iterator iter;

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
   uint8_t* getCachedDataPtr(FileDataRef const & fdref)
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
   BinaryData getData(FileDataRef const & fdref)
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
      while(cacheUsed_+incomingBytes > cacheSize_ )
      {
         list<CacheData>::iterator cIter = cachedData_.begin();
         FileDataRef & toRemove = cIter->first;
         cacheUsed_ -= toRemove.getNumBytes();
         cacheMap_.erase(toRemove);
         cachedData_.erase(cIter);
      }
      
   }

   /////////////////////////////////////////////////////////////////////////////
   void pprintCacheState(void)
   {
      uint32_t nFile = fileSizes_.size();
      cout << "FileDataCache information:" << endl;
      cout << "   Cache Size: " << cacheSize_/1024.0 << " KiB" << endl;
      cout << "   Cache Used: " << cacheUsed_/1024.0 << " KiB" << endl;
      cout << "   Files Repr: " << cumulSizes_[nFile-1]/1024.0 << " KiB" << endl;
      cout << "   Files" << endl;
      for(uint32_t i=0; i<nFile; i++)
      {
         cout << "      ";
         cout << fileNames_[i].c_str() << " : ";
         cout << fileSizes_[i]/1024.0 << " KiB (sum: ";
         cout << cumulSizes_[i]/1024.0 << " KiB)" << endl;
      }
      cout << endl;

      cout << "   Cached Data: " << cachedData_.size() << " cache chunks " << endl;

      map<FileDataRef, list<CacheData>::iterator>::iterator mapIter;
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
   }



private:
   typedef pair<FileDataRef, BinaryData>   CacheData;


   vector<ifstream*>                             openFiles_;
   vector<uint32_t>                              fileSizes_;
   vector<uint64_t>                              cumulSizes_;
   vector<string>                                fileNames_;
   list<CacheData>                               cachedData_;
   map<FileDataRef, list<CacheData>::iterator>   cacheMap_;
   uint64_t                                      cacheUsed_;
   uint64_t                                      cacheSize_;

};



/*
class FileDataRef
{
private:



public:

   FileDataRef(void) : 
      fileLoc_(UINT32_MAX, UINT32_MAX),
      nBytes_(0),
      theData_(0) {} 

   FileDataRef(uint32_t fileIdx, uint32_t start, uint32_t nByte) : 
      fileIndex_(fileIdx),
      startByte_(start),
      nBytes_(nByte),
      theData_(0) 
   {
      if(fileIdx >= openFiles_.size())
         cout << "***ERROR: FileDataRef fileIndex_ out of range!" << endl;
   } 

   ~FileDataRef(void) { theData_.clear(); }

   uint8_t* getPtr()
   {
      // If the data is already here, return it.  
      if( nBytes_ == theData_.size() )
         return theData_.getPtr();

      //Otherwise, load from file.
      if( nBytes_    == 0                 ||
          fileIndex_ == UINT32_MAX        ||
          fileIndex_ >= openFiles_.size() ||
          ! openFiles_[fileIndex_].is_open())
         return NULL;
         
      theData_.resize(nBytes_); 
      uint32_t numRead = openFiles_[fileIndex_].read(theData_.getPtr(), nBytes_);
      if( numRead != nBytes_ )
      {
         cout << "***ERROR:  EOF reached before FileDataRef finished " << endl;
         return NULL;
      }
   }


   // Here's where we handle persistently-open files
   static uint32_t     getNumOpenFiles(void) { return openFiles_.size(); }
   static ifstream &   getOpenFileRef(uint32_t i) {return openFiles_[i]; }

   // This method will figure out if there is already a cached 
   static uint8_t*     refIsInCache(FileDataRef fdref) 
   {
      return openFiles_[i]; 
   }
   


private:
   FileDataRef  fileLoc_;
   uint32_t nBytes_;


};

*/






#endif
