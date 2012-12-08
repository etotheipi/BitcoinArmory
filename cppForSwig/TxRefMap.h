#ifndef _TXREFMAP_H_
#define _TXREFMAP_H_

#include <multimap>
#include "BinaryData.h"
#include "BlockObj.h"
#include "FileDataPtr.h"

////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
//
// TxRefMap:  Proxy class to replace std::map<BinaryData, TxRef> used in
//            BlockUtils.h/.cpp.  The map<> holds everything in RAM, which
//            has actually become prohibitive with the size of the blockchain.
//            However, I don't want to get rid of it entirely, I want to have
//            the option to switch between the RAM option (map<>) and the HDD
//            option (LevelDB).  
//
//            So I create this proxy class that defines the same functions,
//            regardless of which one is used behind the scenes.  The 
//            performance between them will differ drastically (and the HDD
//            one will create a new directory to store the data), but the 
//            operations on the data structure are the same.
//            
//            Btw, "map" is a misnomer here:  it's actually a multimap<> 
//            because we key the database only by the first 4 bytes of the
//            tx hash -- meaning there will occasionally be collisions 
//            (may be more than occasional in a couple years...).  Therefore,
//            each key actually points to a list of TxRef objects.  We 
//            implement equal_range the same way multimap does:  it returns
//            two iterators, one to the first element, and another one past 
//            the last element.  So you use the following construct:
//
//                pair<Iterator,Iterator> range = theMap_.equal_range(hash4B);
//                for(iter=range.first; iter!=range.second; iter++)
//                {
//                   // Do your stuff
//                }
//
//            We try to maintain a very similar interface to multimap<>, but 
//            it won't be exact.
//
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////


#ifdef TXREFMAP_IN_RAM


////////////////////////////////////////////////////////////////////////////////
class TxRefMap
{
public:
   TxRefMap(void)
   {
      
   }

   size_t size(void) {return theMap_.size();}
   size_t clear(void) {return theMap_.clear();}

   
   pair<TxRefMapIterator, TxRefMapIterator> equal_range(BinaryData key)
   {
      typedef multimap<BinaryData,TxRef>::iterator MapIter;
      pair<MapIter,MapIter> range = theMap_.equal_range(key.getSliceCopy(0,4))

      TxRefMapIterator iterLow(range.first);
      TxRefMapIterator iterHigh(range.second);
      return pair<TxRefMapIterator,TxRefMapIterator>(iterLow, iterHigh);
   }

   TxRefMapIterator begin(void) { return TxRefMapIterator(theMap_.begin());}
   TxRefMapIterator   end(void) { return TxRefMapIterator(theMap_.end());}


   TxRef insert(BinaryData const & txHash, FileDataPtr & fdp, BlockHeader * bhptr)
   {
      static multimap<HashString, TxRef>::iterator lowerBound;
      static multimap<HashString, TxRef>::iterator upperBound;
      static pair<HashString, TxRef>               txInputPair;
      static multimap<HashString, TxRef>::iterator txInsResult;

      txInputPair.first.copyFrom(txHash.getPtr(), 4);
      lowerBound = txHintMap_.lower_bound(txInputPair.first);
      upperBound = txHintMap_.upper_bound(txInputPair.first);

      bool needInsert = false;
      if(lowerBound!=upperBound)
      {
         multimap<HashString, TxRef>::iterator iter;
         for(iter = lowerBound; iter != upperBound; iter++)
            if(iter->second.getThisHash() == txHash)
               return &(iter->second);
      }
   
      // If we got here, the tx doesn't exist in the multimap yet,
      // and lowerBound is an appropriate hint for inserting the TxRef
      txInputPair.second.setBlkFilePtr(fdp);
      txInputPair.second.setHeaderPtr(bhptr);
      txInsResult = txHintMap_.insert(lowerBound, txInputPair);
      return &(txInsResult->second);

   }
   

private:
   
   multimap<BinaryData, TxRef> theMap_;

   
};



////////////////////////////////////////////////////////////////////////////////
class TxRefMapIterator
{
public:
   TxRefMapIterator(void) {}
   TxRefMapIterator(multimap<BinaryData,TxRef::iterator itr) : theIter_(itr) {}

   TxRefMapIterator & operator++(void)
   {
      theIter_++;
      return *this;
   }

   TxRefMapIterator operator++(int)
   {
      TxRefMapIterator out(*this);
      theIter_++;
      return out;
   }

   BinaryData key(void)
   {
      return theIter_->first;
   }


private:
   multimap<BinaryData, TxRef>::iterator theIter_;

   
};

#else

class TxRefMapIterator
{
public:

private:
   leveldb::Iterator* theIter_;
   uint32_t index_;
   
};

#endif
