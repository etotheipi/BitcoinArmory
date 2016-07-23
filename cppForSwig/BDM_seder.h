////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2016, goatpig.                                              //
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //                                      
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#ifndef _BDM_SEDER_H
#define _BDM_SEDER_H

#include <condition_variable>
#include "BinaryData.h"
#include "DataObject.h"
#include "LedgerEntryData.h"
#include "TxClasses.h"

///////////////////////////////////////////////////////////////////////////////
class LedgerEntryVector
{
private:
   vector<LedgerEntryData> leVec_;

public:
   LedgerEntryVector(void)
   {}

   LedgerEntryVector(const vector<LedgerEntryData>& lev) :
      leVec_(lev)
   {}

   LedgerEntryVector(vector<LedgerEntryData>&& lev) :
      leVec_(move(lev))
   {}

   void push_back(LedgerEntryData&& led) { leVec_.push_back(move(led)); }

   friend ostream& operator << (ostream&, const LedgerEntryVector&);
   friend istream& operator >> (istream&, LedgerEntryVector&);

   const vector<LedgerEntryData>& toVector(void) const;
};

///////////////////////////////////////////////////////////////////////////////
class BinaryDataObject
{
private:
   BinaryData bd_;

public:
   BinaryDataObject(void)
   {}

   BinaryDataObject(const BinaryData& bd) :
      bd_(bd)
   {}

   friend ostream& operator << (ostream&, const BinaryDataObject&);
   friend istream& operator >> (istream&, BinaryDataObject&);

   const BinaryData& get(void) const
   {
      return bd_;
   }
};

///////////////////////////////////////////////////////////////////////////////
class BinaryDataVector
{
private:
   vector<BinaryData> bdVec_;

public:
   BinaryDataVector(void)
   {}

   BinaryDataVector(vector<BinaryData>&& bdvec) :
      bdVec_(move(bdvec))
   {}

   BinaryDataVector(const vector<BinaryData>& bdvec) :
      bdVec_(bdvec)
   {}

   const vector<BinaryData>& get(void) const { return bdVec_; }

   void push_back(BinaryData&& bd)
   { bdVec_.push_back(move(bd)); }

   friend ostream& operator << (ostream&, const BinaryDataVector&);
   friend istream& operator >> (istream&, BinaryDataVector&);
};

///////////////////////////////////////////////////////////////////////////////
class UtxoVector
{
private:
   vector<UTXO> vec_;

public:
   friend ostream& operator << (ostream&, const UtxoVector&);
   friend istream& operator >> (istream&, UtxoVector&);

   void push_back(UTXO utxo) { vec_.push_back(move(utxo)); }
   vector<UTXO> toVec(void) { return move(vec_); }
};

#endif
