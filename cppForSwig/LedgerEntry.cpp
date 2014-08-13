#include "LedgerEntry.h"

////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
//
// LedgerEntry
//
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
bool LedgerEntry::operator<(LedgerEntry const & le2) const
{
   // TODO: I wanted to update this with txTime_, but I didn't want to c
   //       complicate the mess of changes going in, yet.  Do this later
   //       once everything is stable again.
   //if(       blockNum_ != le2.blockNum_)
      //return blockNum_  < le2.blockNum_;
   //else if(  index_    != le2.index_)
      //return index_     < le2.index_;
   //else if(  txTime_   != le2.txTime_)
      //return txTime_    < le2.txTime_;
   //else
      //return false;
   
   if( blockNum_ != le2.blockNum_)
      return blockNum_ < le2.blockNum_;
   else if( index_ != le2.index_)
      return index_ < le2.index_;
   else
      return false;
   
}

//////////////////////////////////////////////////////////////////////////////
bool LedgerEntry::operator==(LedgerEntry const & le2) const
{
   //TODO
   //return (blockNum_ == le2.blockNum_ && 
           //index_    == le2.index_ && 
           //txTime_   == le2.txTime_);
   return (blockNum_ == le2.blockNum_ && index_ == le2.index_);
}

//////////////////////////////////////////////////////////////////////////////
void LedgerEntry::pprint(void)
{
   cout << "LedgerEntry: " << endl;
   cout << "   ScrAddr : " << getScrAddr().toHexStr() << endl;
   cout << "   Value   : " << getValue()/1e8 << endl;
   cout << "   BlkNum  : " << getBlockNum() << endl;
   cout << "   TxHash  : " << getTxHash().toHexStr() << endl;
   cout << "   TxIndex : " << getIndex() << endl;
   cout << "   isValid : " << (isValid() ? 1 : 0) << endl;
   cout << "   Coinbase: " << (isCoinbase() ? 1 : 0) << endl;
   cout << "   sentSelf: " << (isSentToSelf() ? 1 : 0) << endl;
   cout << "   isChange: " << (isChangeBack() ? 1 : 0) << endl;
   cout << endl;
}

//////////////////////////////////////////////////////////////////////////////
void LedgerEntry::pprintOneLine(void) const
{
   printf("   Addr:%s Tx:%s:%02d   BTC:%0.3f   Blk:%06d\n", 
                           "   ",
                           getTxHash().getSliceCopy(0,8).toHexStr().c_str(),
                           getIndex(),
                           getValue()/1e8,
                           getBlockNum());
}

//////////////////////////////////////////////////////////////////////////////
bool LedgerEntry::operator>(LedgerEntry const & le2) const
{
   if (blockNum_ != le2.blockNum_)
      return blockNum_ > le2.blockNum_;
   else if (index_ != le2.index_)
      return index_ > le2.index_;
   else
      return false;

}
