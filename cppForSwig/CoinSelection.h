////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2017, goatpig                                               //
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#ifndef _H_COINSELECTION
#define _H_COINSELECTOIN

using namespace std;

#include <stdint.h>
#include <memory>
#include <functional>
#include <vector>
#include <string>
#include <set>

#include "TxClasses.h"
#include "ScriptRecipient.h"

#define DUST 10000
#define RANDOM_ITER_COUNT 10
#define ONE_BTC 100000000.0f

#define WEIGHT_NOZC     1000000.0f
#define WEIGHT_PRIORITY 50.0f
#define WEIGHT_NUMADDR  100000.0f
#define WEIGHT_TXSIZE   100.0f
#define WEIGHT_OUTANON  30.0f

class CoinSelectionException : public runtime_error
{
public:
   CoinSelectionException(const string& err) : runtime_error(err)
   {}
};

////////////////////////////////////////////////////////////////////////////////
struct PaymentStruct
{
   const map<unsigned, shared_ptr<ScriptRecipient>> recipients_;
   
   const uint64_t fee_;
   const float fee_byte_;
   
   uint64_t spendVal_;
   size_t size_;

   bool adjustFee_;

   PaymentStruct(map<unsigned, shared_ptr<ScriptRecipient>>& recipients,
      uint64_t fee, float fee_byte, bool adjust_fee) :
      recipients_(recipients), fee_(fee), fee_byte_(fee_byte),
      adjustFee_(adjust_fee)
   {
      init();
   }

   void init(void);
};

////////////////////////////////////////////////////////////////////////////////
struct UtxoSelection
{
   vector<UTXO> utxoVec_;

   uint64_t value_ = 0;
   uint64_t fee_ = 0;
   float fee_byte_ = 0.0f;

   size_t size_ = 0;
   size_t witnessSize_ = 0;
   float bumpPct_ = 0.0f;

   bool hasChange_ = false;

   UtxoSelection(void) 
   {}

   UtxoSelection(vector<UTXO>& utxovec) :
      utxoVec_(move(utxovec))
   {}

   void computeSizeAndFee(const PaymentStruct&);
};


////////////////////////////////////////////////////////////////////////////////
class CoinSelection
{
private:
   vector<UTXO> utxoVec_;
   uint64_t utxoVecValue_ = 0;
   const uint64_t spendableValue_;
   unsigned topHeight_ = UINT32_MAX;

   function<vector<UTXO>(uint64_t val)> getUTXOsForVal_;

protected:
   UtxoSelection getUtxoSelection(
      PaymentStruct&, const vector<UTXO>&, bool useExhaustiveList);

   void fleshOutSelection(const vector<UTXO>&, UtxoSelection& utxoSelect,
      PaymentStruct& payStruct);

   void updateUtxoVector(uint64_t value);
   static uint64_t tallyValue(const vector<UTXO>&);

public:
   CoinSelection(function<vector<UTXO>(uint64_t val)> func, 
      unsigned topHeight, uint64_t spendableValue)
      : getUTXOsForVal_(func), topHeight_(topHeight), 
      spendableValue_(spendableValue)
   {
      //for random shuffling
      srand(time(0));
   }

   UtxoSelection getUtxoSelectionForRecipients(
      PaymentStruct& payStruct, const vector<UTXO>&, bool useExhaustiveList);

   uint64_t getFeeForMaxVal(
      size_t txOutSize, float fee_byte, const vector<UTXO>&);
};

////////////////////////////////////////////////////////////////////////////////
struct CoinSorting
{
private:
   
   /////////////////////////////////////////////////////////////////////////////
   struct ScoredUtxo_Unsigned
   {
      const UTXO* utxo_;
      const unsigned score_;
      const unsigned order_;

      ScoredUtxo_Unsigned(const UTXO* utxo, unsigned score, 
         unsigned order) :
         utxo_(utxo), score_(score), order_(order)
      {}

      bool operator< (const ScoredUtxo_Unsigned& rhs) const
      {
         if (score_ != rhs.score_)
            return score_ > rhs.score_; //descending order
         else
            return order_ < rhs.order_; //respect order of appearnce
      }
   };

   /////////////////////////////////////////////////////////////////////////////
   struct ScoredUtxo_Float
   {
      const UTXO* utxo_;
      const float score_;
      const unsigned order_;

      ScoredUtxo_Float(const UTXO* utxo, float score, 
         unsigned order) :
         utxo_(utxo), score_(score), order_(order)
      {}

      bool operator< (const ScoredUtxo_Float& rhs) const
      {
         if (score_ != rhs.score_)
            return score_ > rhs.score_; //descending order
         else
            return order_ < rhs.order_; //respect order of appearnce
      }
   };

   /////////////////////////////////////////////////////////////////////////////
   struct ScoredUtxoVector_Float
   {
      const vector<UTXO> utxoVec_;
      const float score_;
      const unsigned order_;

      ScoredUtxoVector_Float(vector<UTXO> utxoVec, float score,
         unsigned order) :
         utxoVec_(move(utxoVec)), score_(score), order_(order)
      {}

      bool operator< (const ScoredUtxoVector_Float& rhs) const
      {
         if (score_ != rhs.score_)
            return score_ > rhs.score_; //descending order
         else
            return order_ < rhs.order_; //respect order of appearnce
      }
   };

private:

   /////////////////////////////////////////////////////////////////////////////
   static set<ScoredUtxo_Float> ruleset_1(const vector<UTXO>&, unsigned);

public:
   static vector<UTXO> sortCoins(
      const vector<UTXO>& utxoVec, unsigned topHeight, unsigned ruleset);
};

#endif

////////////////////////////////////////////////////////////////////////////////
struct CoinSubSelection
{
   //single spendval
   static vector<UTXO> selectOneUtxo_SingleSpendVal(
      const vector<UTXO>&, uint64_t spendVal, uint64_t fee);

   static vector<UTXO> selectManyUtxo_SingleSpendVal(
      const vector<UTXO>&, uint64_t spendVal, uint64_t fee);

   //double spendval
   static vector<UTXO> selectOneUtxo_DoubleSpendVal(
      const vector<UTXO>&, uint64_t spendVal, uint64_t fee);

   static vector<UTXO> selectManyUtxo_DoubleSpendVal(
      const vector<UTXO>&, uint64_t spendVal, uint64_t fee);
};

////////////////////////////////////////////////////////////////////////////////
struct SelectionScoring
{
   struct Scores
   {
      float hasZC_ = 0.0f;
      float priorityFactor_ = 0.0f;
      float numAddrFactor_ = 0.0f;
      float txSizeFactor_ = 0.0f;
      float outAnonFactor_ = 0.0f;

      float compileValue(void) const
      {
         float finalVal = 0.0f;

         finalVal += hasZC_ * WEIGHT_NOZC;
         finalVal += priorityFactor_ * WEIGHT_PRIORITY;
         finalVal += numAddrFactor_ * WEIGHT_NUMADDR;
         finalVal += txSizeFactor_ * WEIGHT_TXSIZE;
         finalVal += outAnonFactor_ * WEIGHT_OUTANON;

         return finalVal;
      }
   };

   static float computeScore(UtxoSelection&, const PaymentStruct&,
      unsigned topHeight);

   static unsigned getTrailingZeroCount(uint64_t);
};
