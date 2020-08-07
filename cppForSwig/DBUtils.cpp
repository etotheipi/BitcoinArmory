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

#include "DBUtils.h"

////////////////////////////////////////////////////////////////////////////////
const BinaryData DBUtils::ZeroConfHeader_ = BinaryData::CreateFromHex("FFFF");

////////////////////////////////////////////////////////////////////////////////
BLKDATA_TYPE DBUtils::readBlkDataKey(BinaryRefReader & brr,
   uint32_t & height,
   uint8_t  & dupID)
{
   uint16_t tempTxIdx;
   uint16_t tempTxOutIdx;
   return readBlkDataKey(brr, height, dupID, tempTxIdx, tempTxOutIdx);
}

////////////////////////////////////////////////////////////////////////////////
BLKDATA_TYPE DBUtils::readBlkDataKey(BinaryRefReader & brr,
   uint32_t & height,
   uint8_t  & dupID,
   uint16_t & txIdx)
{
   uint16_t tempTxOutIdx;
   return readBlkDataKey(brr, height, dupID, txIdx, tempTxOutIdx);
}

////////////////////////////////////////////////////////////////////////////////
BLKDATA_TYPE DBUtils::readBlkDataKey(BinaryRefReader & brr,
   uint32_t & height,
   uint8_t  & dupID,
   uint16_t & txIdx,
   uint16_t & txOutIdx)
{
   uint8_t prefix = brr.get_uint8_t();
   if (prefix != (uint8_t)DB_PREFIX_TXDATA)
   {
      height = 0xffffffff;
      dupID = 0xff;
      txIdx = 0xffff;
      txOutIdx = 0xffff;
      return NOT_BLKDATA;
   }

   return readBlkDataKeyNoPrefix(brr, height, dupID, txIdx, txOutIdx);
}

////////////////////////////////////////////////////////////////////////////////
BLKDATA_TYPE DBUtils::readBlkDataKeyNoPrefix(
   BinaryRefReader & brr,
   uint32_t & height,
   uint8_t  & dupID)
{
   uint16_t tempTxIdx;
   uint16_t tempTxOutIdx;
   return readBlkDataKeyNoPrefix(brr, height, dupID, tempTxIdx, tempTxOutIdx);
}

////////////////////////////////////////////////////////////////////////////////
BLKDATA_TYPE DBUtils::readBlkDataKeyNoPrefix(
   BinaryRefReader & brr,
   uint32_t & height,
   uint8_t  & dupID,
   uint16_t & txIdx)
{
   uint16_t tempTxOutIdx;
   return readBlkDataKeyNoPrefix(brr, height, dupID, txIdx, tempTxOutIdx);
}

////////////////////////////////////////////////////////////////////////////////
BLKDATA_TYPE DBUtils::readBlkDataKeyNoPrefix(
   BinaryRefReader & brr,
   uint32_t & height,
   uint8_t  & dupID,
   uint16_t & txIdx,
   uint16_t & txOutIdx)
{
   BinaryData hgtx = brr.get_BinaryData(4);
   height = hgtxToHeight(hgtx);
   dupID = hgtxToDupID(hgtx);

   if (brr.getSizeRemaining() == 0)
   {
      txIdx = 0xffff;
      txOutIdx = 0xffff;
      return BLKDATA_HEADER;
   }
   else if (brr.getSizeRemaining() == 2)
   {
      txIdx = brr.get_uint16_t(BE);
      txOutIdx = 0xffff;
      return BLKDATA_TX;
   }
   else if (brr.getSizeRemaining() == 4)
   {
      txIdx = brr.get_uint16_t(BE);
      txOutIdx = brr.get_uint16_t(BE);
      return BLKDATA_TXOUT;
   }
   else
   {
      LOGERR << "Unexpected bytes remaining: " << brr.getSizeRemaining();
      return NOT_BLKDATA;
   }
}

////////////////////////////////////////////////////////////////////////////////
string DBUtils::getPrefixName(uint8_t prefixInt)
{
   return getPrefixName((DB_PREFIX)prefixInt);
}

////////////////////////////////////////////////////////////////////////////////
string DBUtils::getPrefixName(DB_PREFIX pref)
{
   switch (pref)
   {
   case DB_PREFIX_DBINFO:    return string("DBINFO");
   case DB_PREFIX_TXDATA:    return string("TXDATA");
   case DB_PREFIX_SCRIPT:    return string("SCRIPT");
   case DB_PREFIX_TXHINTS:   return string("TXHINTS");
   case DB_PREFIX_TRIENODES: return string("TRIENODES");
   case DB_PREFIX_HEADHASH:  return string("HEADHASH");
   case DB_PREFIX_HEADHGT:   return string("HEADHGT");
   case DB_PREFIX_UNDODATA:  return string("UNDODATA");
   default:                  return string("<unknown>");
   }
}

/////////////////////////////////////////////////////////////////////////////
bool DBUtils::checkPrefixByteWError(BinaryRefReader & brr,
   DB_PREFIX prefix,
   bool rewindWhenDone)
{
   uint8_t oneByte = brr.get_uint8_t();
   bool out;
   if (oneByte == (uint8_t)prefix)
      out = true;
   else
   {
      LOGERR << "Unexpected prefix byte: "
         << "Expected: " << getPrefixName(prefix)
         << "Received: " << getPrefixName(oneByte);
      out = false;
   }

   if (rewindWhenDone)
      brr.rewind(1);

   return out;
}

/////////////////////////////////////////////////////////////////////////////
bool DBUtils::checkPrefixByte(BinaryRefReader & brr,
   DB_PREFIX prefix,
   bool rewindWhenDone)
{
   uint8_t oneByte = brr.get_uint8_t();
   bool out = (oneByte == (uint8_t)prefix);

   if (rewindWhenDone)
      brr.rewind(1);

   return out;
}

/////////////////////////////////////////////////////////////////////////////
BinaryData DBUtils::getBlkDataKey(uint32_t height,
   uint8_t  dup)
{
   BinaryWriter bw(5);
   bw.put_uint8_t(DB_PREFIX_TXDATA);
   bw.put_BinaryData(heightAndDupToHgtx(height, dup));
   return bw.getData();
}

/////////////////////////////////////////////////////////////////////////////
BinaryData DBUtils::getBlkDataKey(uint32_t height,
   uint8_t  dup,
   uint16_t txIdx)
{
   BinaryWriter bw(7);
   bw.put_uint8_t(DB_PREFIX_TXDATA);
   bw.put_BinaryData(heightAndDupToHgtx(height, dup));
   bw.put_uint16_t(txIdx, BE);
   return bw.getData();
}

/////////////////////////////////////////////////////////////////////////////
BinaryData DBUtils::getBlkDataKey(uint32_t height,
   uint8_t  dup,
   uint16_t txIdx,
   uint16_t txOutIdx)
{
   BinaryWriter bw(9);
   bw.put_uint8_t(DB_PREFIX_TXDATA);
   bw.put_BinaryData(heightAndDupToHgtx(height, dup));
   bw.put_uint16_t(txIdx, BE);
   bw.put_uint16_t(txOutIdx, BE);
   return bw.getData();
}

/////////////////////////////////////////////////////////////////////////////
BinaryData DBUtils::getBlkDataKeyNoPrefix(uint32_t height,
   uint8_t  dup)
{
   return heightAndDupToHgtx(height, dup);
}

/////////////////////////////////////////////////////////////////////////////
BinaryData DBUtils::getBlkDataKeyNoPrefix(uint32_t height,
   uint8_t  dup,
   uint16_t txIdx)
{
   BinaryWriter bw(6);
   bw.put_BinaryData(heightAndDupToHgtx(height, dup));
   bw.put_uint16_t(txIdx, BE);
   return bw.getData();
}

/////////////////////////////////////////////////////////////////////////////
BinaryData DBUtils::getBlkDataKeyNoPrefix(uint32_t height,
   uint8_t  dup,
   uint16_t txIdx,
   uint16_t txOutIdx)
{
   BinaryWriter bw(8);
   bw.put_BinaryData(heightAndDupToHgtx(height, dup));
   bw.put_uint16_t(txIdx, BE);
   bw.put_uint16_t(txOutIdx, BE);
   return bw.getData();
}

/////////////////////////////////////////////////////////////////////////////
uint32_t DBUtils::hgtxToHeight(const BinaryData& hgtx)
{
   return (READ_UINT32_BE(hgtx) >> 8);

}

/////////////////////////////////////////////////////////////////////////////
uint8_t DBUtils::hgtxToDupID(const BinaryData& hgtx)
{
   return (READ_UINT32_BE(hgtx) & 0x7f);
}

/////////////////////////////////////////////////////////////////////////////
BinaryData DBUtils::heightAndDupToHgtx(uint32_t hgt, uint8_t dup)
{
   uint32_t hgtxInt = (hgt << 8) | (uint32_t)dup;
   return WRITE_UINT32_BE(hgtxInt);
}

/////////////////////////////////////////////////////////////////////////////
BinaryData DBUtils::getFilterPoolKey(uint32_t filenum)
{
   uint32_t bucketKey = (DB_PREFIX_POOL << 24) | (uint32_t)filenum;
   return WRITE_UINT32_BE(bucketKey);
}

/////////////////////////////////////////////////////////////////////////////
BinaryData DBUtils::getMissingHashesKey(uint32_t id)
{
   BinaryData bd;
   bd.resize(4);

   id &= 0x00FFFFFF; //24bit ids top
   id |= DB_PREFIX_MISSING_HASHES << 24;
   
   auto keyPtr = (uint32_t*)bd.getPtr();
   *keyPtr = id;

   return bd;
}

/////////////////////////////////////////////////////////////////////////////
bool DBUtils::fileExists(const string& path, int mode)
{
#ifdef _WIN32
   return _access(path.c_str(), mode) == 0;
#else
      auto nixmode = F_OK;
      if (mode & 2)
         nixmode |= R_OK;
      if (mode & 4)
         nixmode |= W_OK;
      return access(path.c_str(), nixmode) == 0;
#endif
}