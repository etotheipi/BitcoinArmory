////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2015, Armory Technologies, Inc.                        //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE-ATI or http://www.gnu.org/licenses/agpl.html                  //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#include "BinaryData.h"
#include "BtcUtils.h"

BinaryData BinaryData::EmptyBinData_(0);

////////////////////////////////////////////////////////////////////////////////
BinaryData::BinaryData(BinaryDataRef const & bdRef) 
{ 
   copyFrom(bdRef.getPtr(), bdRef.getSize());
}


////////////////////////////////////////////////////////////////////////////////
void BinaryData::copyFrom(BinaryDataRef const & bdr)
{
   copyFrom( bdr.getPtr(), bdr.getSize() );
}


////////////////////////////////////////////////////////////////////////////////
BinaryDataRef BinaryData::getRef(void) const
{
   return BinaryDataRef(getPtr(), getSize());
}



////////////////////////////////////////////////////////////////////////////////
BinaryData & BinaryData::append(BinaryDataRef const & bd2)
{
   if(bd2.getSize()==0) 
      return (*this);
   
   if(getSize()==0) 
      copyFrom(bd2.getPtr(), bd2.getSize());
   else
      data_.insert(data_.end(), bd2.getPtr(), bd2.getPtr()+bd2.getSize());

   return (*this);
}


/////////////////////////////////////////////////////////////////////////////
BinaryData & BinaryData::append(uint8_t const * str, size_t sz)
{
   BinaryDataRef appStr(str, sz);
   return append(appStr);
}

////////////////////////////////////////////////////////////////////////////////
int32_t BinaryData::find(BinaryDataRef const & matchStr, uint32_t startPos)
{
   int32_t finalAnswer = -1;
   if(matchStr.getSize()==0)
      return startPos;

   for(int32_t i=startPos; i<=(int32_t)getSize()-(int32_t)matchStr.getSize(); i++)
   {
      if(matchStr[0] != data_[i])
         continue;

      for(uint32_t j=0; j<matchStr.getSize(); j++)
      {
         if(matchStr[j] != data_[i+j])
            break;

         // If we are at this instruction and is the last index, it's a match
         if(j==matchStr.getSize()-1)
            finalAnswer = i;
      }

      if(finalAnswer != -1)
         break;
   }

   return finalAnswer;
}


////////////////////////////////////////////////////////////////////////////////
int32_t BinaryData::find(BinaryData const & matchStr, uint32_t startPos)
{
   BinaryDataRef bdrmatch(matchStr);
   return find(bdrmatch, startPos);
}


////////////////////////////////////////////////////////////////////////////////
bool BinaryData::contains(BinaryData const & matchStr, uint32_t startPos)
{
   return (find(matchStr, startPos) != -1);
}

////////////////////////////////////////////////////////////////////////////////
bool BinaryData::contains(BinaryDataRef const & matchStr, uint32_t startPos)
{
   return (find(matchStr, startPos) != -1);
}



/////////////////////////////////////////////////////////////////////////////
bool BinaryData::startsWith(BinaryDataRef const & matchStr) const
{
   if(matchStr.getSize() > getSize())
      return false;

   for(uint32_t i=0; i<matchStr.getSize(); i++)
      if(matchStr[i] != (*this)[i])
         return false;

   return true;
}

/////////////////////////////////////////////////////////////////////////////
bool BinaryData::startsWith(BinaryData const & matchStr) const
{
   if(matchStr.getSize() > getSize())
      return false;

   for(uint32_t i=0; i<matchStr.getSize(); i++)
      if(matchStr[i] != (*this)[i])
         return false;

   return true;
}

/////////////////////////////////////////////////////////////////////////////
bool BinaryData::endsWith(BinaryDataRef const & matchStr) const
{
   size_t sz = matchStr.getSize();
   if(sz > getSize())
      return false;
   
   for(uint32_t i=0; i<sz; i++)
      if(matchStr[sz-(i+1)] != (*this)[getSize()-(i+1)])
         return false;

   return true;
}
/////////////////////////////////////////////////////////////////////////////
bool BinaryData::endsWith(BinaryData const & matchStr) const
{
   size_t sz = matchStr.getSize();
   if(sz > getSize())
      return false;
   
   for(uint32_t i=0; i<sz; i++)
      if(matchStr[sz-(i+1)] != (*this)[getSize()-(i+1)])
         return false;

   return true;
}

/////////////////////////////////////////////////////////////////////////////
BinaryDataRef BinaryData::getSliceRef(ssize_t start_pos, uint32_t nChar) const
{
   if(start_pos < 0) 
      start_pos = getSize() + start_pos;

   if((size_t)start_pos + nChar > getSize())
   {
      cerr << "getSliceRef: Invalid BinaryData access" << endl;
      return BinaryDataRef();
   }
   return BinaryDataRef( getPtr()+start_pos, nChar);
}

/////////////////////////////////////////////////////////////////////////////
BinaryData BinaryData::getSliceCopy(ssize_t start_pos, uint32_t nChar) const
{
   if(start_pos < 0) 
      start_pos = getSize() + start_pos;

   if((size_t)start_pos + nChar > getSize())
   {
      cerr << "getSliceCopy: Invalid BinaryData access" << endl;
      return BinaryData();
   }
   return BinaryData(getPtr()+start_pos, nChar);
}



/////////////////////////////////////////////////////////////////////////////
uint64_t BinaryReader::get_var_int(uint8_t* nRead)
{
   uint32_t nBytes;
   uint64_t varInt = BtcUtils::readVarInt( 
      bdStr_.getPtr() + pos_, bdStr_.getSize() - pos_, &nBytes);
   if(nRead != NULL)
      *nRead = nBytes;
   pos_ += nBytes;
   return varInt;
}

/////////////////////////////////////////////////////////////////////////////
uint64_t BinaryRefReader::get_var_int(uint8_t* nRead)
{
   uint32_t nBytes;
   uint64_t varInt = BtcUtils::readVarInt( bdRef_.getPtr() + pos_, getSizeRemaining(), &nBytes);
   if(nRead != NULL)
      *nRead = nBytes;
   pos_ += nBytes;
   return varInt;
}


/////////////////////////////////////////////////////////////////////////////
bool BinaryData::operator==(BinaryDataRef const & bd2) const
{
   if(getSize() != bd2.getSize())
      return false;

   return (memcmp(getPtr(), bd2.getPtr(), getSize()) == 0);
}

/////////////////////////////////////////////////////////////////////////////
bool BinaryData::operator<(BinaryDataRef const & bd2) const
{
   size_t minLen = min(getSize(), bd2.getSize());
   auto ref_ptr = bd2.getPtr();
   for (size_t i = 0; i<minLen; i++)
   {
      if (data_[i] == ref_ptr[i])
         continue;
      return data_[i] < ref_ptr[i];
   }
   return (getSize() < bd2.getSize());
}


