////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2017, goatpig                                               //
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#ifndef _H_TXEVALSTATE
#define _H_TXEVALSTATE

#include <map>
#include "BinaryData.h"

enum PubKeyType
{
   Type_Compressed,
   Type_Uncompressed,
   Type_Mixed,
   Type_Unkonwn
};


////////////////////////////////////////////////////////////////////////////////
class TxInEvalState
{
   friend class StackInterpreter;

private:
   bool validStack_ = false;

   unsigned n_ = 0;
   unsigned m_ = 0;

   map<BinaryData, bool> pubKeyState_;

   mutable PubKeyType keyType_ = Type_Unkonwn;

private:
   PubKeyType getType(void) const;

public:
   bool isValid(void) const;
   unsigned getSigCount(void) const;
   bool isSignedForPubKey(const BinaryData& pubkey);
   const map<BinaryData, bool> getPubKeyMap(void) const { return pubKeyState_; }
};

////////////////////////////////////////////////////////////////////////////////
class TxEvalState
{
private:
   map<unsigned, TxInEvalState> evalMap_;

public:
   size_t getEvalMapSize(void) const { return evalMap_.size(); }
   void reset(void) { evalMap_.clear(); }
   void updateState(unsigned id, TxInEvalState state);
   bool isValid(void) const;
   TxInEvalState getSignedStateForInput(unsigned i);
};

#endif