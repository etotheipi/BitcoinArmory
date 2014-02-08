////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright(C) 2011-2013, Armory Technologies, Inc.                         //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE or http://www.gnu.org/licenses/agpl.html                      //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#include "BinaryData.h"
#include "BtcUtils.h"


/////////////////////////////////////////////////////////////////////////////
uint64_t BinaryReader::get_var_int(uint8_t* nRead)
{
   uint32_t nBytes;
   uint64_t varInt = BtcUtils::readVarInt( bdStr_.getPtr() + pos_, &nBytes);
   if(nRead != NULL)
      *nRead = nBytes;
   pos_ += nBytes;
   return varInt;
}

/////////////////////////////////////////////////////////////////////////////
uint64_t BinaryRefReader::get_var_int(uint8_t* nRead)
{
   uint32_t nBytes;
   uint64_t varInt = BtcUtils::readVarInt( bdRef_.getPtr() + pos_, &nBytes);
   if(nRead != NULL)
      *nRead = nBytes;
   pos_ += nBytes;
   return varInt;
}


/////////////////////////////////////////////////////////////////////////////



