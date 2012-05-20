////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2012, Alan C. Reiner    <alan.reiner@gmail.com>        //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE or http://www.gnu.org/licenses/agpl.html                      //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////



#include "FileDataRef.h"

FileDataCache FileDataRef::globalCache_;



void FileDataRef::SetupFileCaching(uint64_t maxCacheSize_)
{
   globalCache_.setCacheSize(maxCacheSize_);
}


uint8_t* FileDataRef::getTempDataPtr(void) 
{ 
   return globalCache_.getCachedDataPtr(*this); 
}

BinaryData FileDataRef::getDataCopy(void) const
{ 
   return globalCache_.getData(*this); 
}
