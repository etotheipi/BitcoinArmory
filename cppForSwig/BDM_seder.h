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
#include "bdmenums.h"

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
   const vector<LedgerEntryData>& toVector(void) const;

   void serialize(BinaryWriter &bw) const;
   static LedgerEntryVector deserialize(BinaryRefReader& bdr);
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

   BinaryDataObject(const BinaryDataRef& bdr) :
      bd_(bdr)
   {}

   BinaryDataObject(const string& str)
   {
      bd_ = move(BinaryData(str));
   }

   const BinaryData& get(void) const
   {
      return bd_;
   }

   string toStr(void) const
   {
      string str(bd_.toCharPtr(), bd_.getSize());
      return move(str);
   }

   void serialize(BinaryWriter& bw) const;
   static BinaryDataObject deserialize(BinaryRefReader& bdr);
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

   void serialize(BinaryWriter& bw) const;
   static BinaryDataVector deserialize(BinaryRefReader& bdr);
};

///////////////////////////////////////////////////////////////////////////////
struct ProgressData
{
   BDMPhase phase_; 
   double progress_;
   unsigned time_;
   unsigned numericProgress_;
   vector<string> wltIDs_;

   ProgressData(void)
   {}

   ProgressData(BDMPhase phase, double prog, 
      unsigned time, unsigned numProg, vector<string> wltIDs) :
      phase_(phase), progress_(prog), time_(time),
      numericProgress_(numProg), wltIDs_(wltIDs)
   {}

   void serialize(BinaryWriter& bw) const;
   static ProgressData deserialize(BinaryRefReader& bdr);
};

#endif
