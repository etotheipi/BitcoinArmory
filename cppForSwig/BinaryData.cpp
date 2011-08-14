#include "BinaryData.h"


BinaryData::BinaryData(BinaryDataRef const & bdRef) 
{ 
   copyFrom(bdRef.getPtr(), bdRef.getSize());
}


inline void BinaryData::copyFrom(BinaryDataRef const & bdr)
{
   copyFrom( bdr.getPtr(), bdr.getSize() );
}


inline BinaryDataRef BinaryData::getRef(void) const
{
   return BinaryDataRef(getPtr(), nBytes_);
}



inline BinaryData & BinaryData::append(BinaryDataRef const & bd2)
{
   data_.insert(data_.end(), bd2.getPtr(), bd2.getPtr()+bd2.getSize());
   nBytes_ += bd2.getSize();
   return (*this);
}



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


int32_t BinaryData::find(BinaryData const & matchStr, uint32_t startPos)
{
   BinaryDataRef bdrmatch(matchStr);
   return find(bdrmatch, startPos);
}


bool BinaryData::contains(BinaryData const & matchStr, uint32_t startPos)
{
   return (find(matchStr, startPos) != -1);
}

bool BinaryData::contains(BinaryDataRef const & matchStr, uint32_t startPos)
{
   return (find(matchStr, startPos) != -1);
}
