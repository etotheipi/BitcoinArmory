#include "BinaryData.h"

////////////////////////////////////////////////////////////////////////////////
BinaryData::BinaryData(BinaryDataRef const & bdRef) 
{ 
   copyFrom(bdRef.getPtr(), bdRef.getSize());
}


////////////////////////////////////////////////////////////////////////////////
inline void BinaryData::copyFrom(BinaryDataRef const & bdr)
{
   copyFrom( bdr.getPtr(), bdr.getSize() );
}


////////////////////////////////////////////////////////////////////////////////
inline BinaryDataRef BinaryData::getRef(void) const
{
   return BinaryDataRef(getPtr(), nBytes_);
}



////////////////////////////////////////////////////////////////////////////////
inline BinaryData & BinaryData::append(BinaryDataRef const & bd2)
{
   data_.insert(data_.end(), bd2.getPtr(), bd2.getPtr()+bd2.getSize());
   nBytes_ += bd2.getSize();
   return (*this);
}



////////////////////////////////////////////////////////////////////////////////
int32_t BinaryData::find(BinaryDataRef const & matchStr, uint32_t startPos)
{
   int32_t finalAnswer = -1;
   for(int32_t i=startPos; i<=(int32_t)nBytes_-(int32_t)matchStr.getSize(); i++)
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
inline int32_t BinaryData::find(BinaryData const & matchStr, uint32_t startPos)
{
   BinaryDataRef bdrmatch(matchStr);
   return find(bdrmatch, startPos);
}


////////////////////////////////////////////////////////////////////////////////
inline bool BinaryData::contains(BinaryData const & matchStr, uint32_t startPos)
{
   return (find(matchStr, startPos) != -1);
}

////////////////////////////////////////////////////////////////////////////////
inline bool BinaryData::contains(BinaryDataRef const & matchStr, uint32_t startPos)
{
   return (find(matchStr, startPos) != -1);
}



/////////////////////////////////////////////////////////////////////////////
inline bool BinaryData::startsWith(BinaryDataRef const & matchStr)
{
   if(matchStr.getSize() > nBytes_)
      return false;

   for(uint32_t i=0; i<matchStr.getSize(); i++)
      if(matchStr[i] != (*this)[i])
         return false;

   return true;
}

/////////////////////////////////////////////////////////////////////////////
inline bool BinaryData::startsWith(BinaryData const & matchStr)
{
   if(matchStr.getSize() > nBytes_)
      return false;

   for(uint32_t i=0; i<matchStr.getSize(); i++)
      if(matchStr[i] != (*this)[i])
         return false;

   return true;
}

/////////////////////////////////////////////////////////////////////////////
inline bool BinaryData::endsWith(BinaryDataRef const & matchStr)
{
   uint32_t sz = matchStr.getSize();
   if(sz > nBytes_)
      return false;
   
   for(uint32_t i=0; i<sz; i++)
      if(matchStr[sz-(i+1)] != (*this)[nBytes_-(i+1)])
         return false;

   return true;
}
/////////////////////////////////////////////////////////////////////////////
bool BinaryData::endsWith(BinaryData const & matchStr)
{
   uint32_t sz = matchStr.getSize();
   if(sz > nBytes_)
      return false;
   
   for(uint32_t i=0; i<sz; i++)
      if(matchStr[sz-(i+1)] != (*this)[nBytes_-(i+1)])
         return false;

   return true;
}

/////////////////////////////////////////////////////////////////////////////
BinaryDataRef BinaryData::getSliceRef(uint32_t start_pos, uint32_t nChar)
{
   if(start_pos < 0) 
      start_pos = nBytes_ + start_pos;

   if(start_pos + nChar >= nBytes_)
   {
      cerr << "getSliceRef: Invalid BinaryData access" << endl;
      return BinaryDataRef();
   }
   return BinaryDataRef( getPtr()+start_pos, nChar);
}

/////////////////////////////////////////////////////////////////////////////
BinaryData    BinaryData::getSliceCopy(uint32_t start_pos, uint32_t nChar)
{
   if(start_pos < 0) 
      start_pos = nBytes_ + start_pos;

   if(start_pos + nChar >= nBytes_)
   {
      cerr << "getSliceCopy: Invalid BinaryData access" << endl;
      return BinaryData();
   }
   return BinaryData(getPtr()+start_pos, nChar);
}










