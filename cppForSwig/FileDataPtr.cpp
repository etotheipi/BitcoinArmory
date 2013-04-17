////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2013, Alan C. Reiner    <alan.reiner@gmail.com>        //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE or http://www.gnu.org/licenses/agpl.html                      //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////



#include "FileDataPtr.h"

FileDataCache FileDataPtr::globalCache_;



void FileDataPtr::SetupFileCaching(uint64_t maxCacheSize_)
{
   globalCache_.setCacheSize(maxCacheSize_);
}


uint8_t* FileDataPtr::getUnsafeDataPtr(void) const
{ 
   return globalCache_.getCachedDataPtr(*this); 
}

BinaryData FileDataPtr::getDataCopy(void) const
{ 
   return globalCache_.getData(*this); 
}

void FileDataPtr::preCacheThisChunk(void) const
{ 
   globalCache_.getCachedDataPtr(*this); 
}

