////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2015, Armory Technologies, Inc.                        //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE-ATI or http://www.gnu.org/licenses/agpl.html                  //
//                                                                            //
//                                                                            //
//  Copyright (C) 2016, goatpig                                               //            
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //                                   
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#ifndef _H_DBUTILS
#define _H_DBUTILS

#include "BinaryData.h"

enum BLKDATA_TYPE
{
   NOT_BLKDATA,
   BLKDATA_HEADER,
   BLKDATA_TX,
   BLKDATA_TXOUT
};

enum DB_PREFIX
{
   DB_PREFIX_DBINFO,
   DB_PREFIX_HEADHASH,
   DB_PREFIX_HEADHGT,
   DB_PREFIX_TXDATA,
   DB_PREFIX_TXHINTS,
   DB_PREFIX_SCRIPT,
   DB_PREFIX_UNDODATA,
   DB_PREFIX_TRIENODES,
   DB_PREFIX_COUNT,
   DB_PREFIX_ZCDATA,
   DB_PREFIX_POOL,
   DB_PREFIX_MISSING_HASHES
};

class DBUtils
{
public:
   static const BinaryData ZeroConfHeader_;

public:

   static uint32_t   hgtxToHeight(const BinaryData& hgtx);
   static uint8_t    hgtxToDupID(const BinaryData& hgtx);
   static BinaryData heightAndDupToHgtx(uint32_t hgt, uint8_t dup);

   /////////////////////////////////////////////////////////////////////////////
   static BinaryData getBlkDataKey(uint32_t height,
      uint8_t  dup);

   /////////////////////////////////////////////////////////////////////////////
   static BinaryData getBlkDataKey(uint32_t height,
      uint8_t  dup,
      uint16_t txIdx);

   /////////////////////////////////////////////////////////////////////////////
   static BinaryData getBlkDataKey(uint32_t height,
      uint8_t  dup,
      uint16_t txIdx,
      uint16_t txOutIdx);

   /////////////////////////////////////////////////////////////////////////////
   static BinaryData getBlkDataKeyNoPrefix(uint32_t height,
      uint8_t  dup);

   /////////////////////////////////////////////////////////////////////////////
   static BinaryData getBlkDataKeyNoPrefix(uint32_t height,
      uint8_t  dup,
      uint16_t txIdx);

   /////////////////////////////////////////////////////////////////////////////
   static BinaryData getBlkDataKeyNoPrefix(uint32_t height,
      uint8_t  dup,
      uint16_t txIdx,
      uint16_t txOutIdx);



   /////////////////////////////////////////////////////////////////////////////
   static BLKDATA_TYPE readBlkDataKey(BinaryRefReader & brr,
      uint32_t & height,
      uint8_t  & dupID);

   /////////////////////////////////////////////////////////////////////////////
   static BLKDATA_TYPE readBlkDataKey(BinaryRefReader & brr,
      uint32_t & height,
      uint8_t  & dupID,
      uint16_t & txIdx);

   /////////////////////////////////////////////////////////////////////////////
   static BLKDATA_TYPE readBlkDataKey(BinaryRefReader & brr,
      uint32_t & height,
      uint8_t  & dupID,
      uint16_t & txIdx,
      uint16_t & txOutIdx);
   /////////////////////////////////////////////////////////////////////////////
   static BLKDATA_TYPE readBlkDataKeyNoPrefix(
      BinaryRefReader & brr,
      uint32_t & height,
      uint8_t  & dupID);

   /////////////////////////////////////////////////////////////////////////////
   static BLKDATA_TYPE readBlkDataKeyNoPrefix(
      BinaryRefReader & brr,
      uint32_t & height,
      uint8_t  & dupID,
      uint16_t & txIdx);

   /////////////////////////////////////////////////////////////////////////////
   static BLKDATA_TYPE readBlkDataKeyNoPrefix(
      BinaryRefReader & brr,
      uint32_t & height,
      uint8_t  & dupID,
      uint16_t & txIdx,
      uint16_t & txOutIdx);



   static string getPrefixName(uint8_t prefixInt);
   static string getPrefixName(DB_PREFIX pref);

   static bool checkPrefixByte(BinaryRefReader & brr,
      DB_PREFIX prefix,
      bool rewindWhenDone = false);
   static bool checkPrefixByteWError(BinaryRefReader & brr,
      DB_PREFIX prefix,
      bool rewindWhenDone = false);

   static BinaryData getFilterPoolKey(uint32_t filenum);
   static BinaryData getMissingHashesKey(uint32_t id);

   static bool fileExists(const string& path, int mode);
};
#endif