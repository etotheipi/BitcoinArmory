////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2017, goatpig                                               //
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#include "TxEvalState.h"
#include "EncryptionUtils.h"

////////////////////////////////////////////////////////////////////////////////
bool TxInEvalState::isValid(void) const
{
   if (!validStack_)
      return false;

   unsigned count = 0;
   for (auto& state : pubKeyState_)
   {
      if (state.second)
         ++count;
   }

   return count >= m_;
}

////////////////////////////////////////////////////////////////////////////////
unsigned TxInEvalState::getSigCount(void) const
{
   unsigned count = 0;
   for (auto& state : pubKeyState_)
   {
      if (state.second)
         ++count;
   }

   return count;
}

////////////////////////////////////////////////////////////////////////////////
bool TxInEvalState::isSignedForPubKey(const BinaryData& pubkey)
{
   if (pubKeyState_.size() == 0)
      return false;

   auto type = getType();
   if (type == Type_Unkonwn)
      throw runtime_error("can't establish pub key type");

   if ((pubkey.getSize() == 65 && type == Type_Uncompressed) ||
      (pubkey.getSize() == 33 && type == Type_Compressed))
   {
      auto iter = pubKeyState_.find(pubkey);
      if (iter == pubKeyState_.end())
         return false;

      return iter->second;
   }
   else if (type != Type_Mixed)
   {
      BinaryData modified_key;
      if (type == Type_Compressed)
         modified_key = CryptoECDSA().CompressPoint(pubkey);
      else if (type == Type_Uncompressed)
         modified_key = CryptoECDSA().UncompressPoint(pubkey);

      auto iter = pubKeyState_.find(modified_key);
      if (iter == pubKeyState_.end())
         return false;

      return iter->second;
   }
   else
   { 
      BinaryData modified_key;
      if (type == Type_Compressed)
         modified_key = CryptoECDSA().CompressPoint(pubkey);
      else if (type == Type_Uncompressed)
         modified_key = CryptoECDSA().UncompressPoint(pubkey);

      auto iter = pubKeyState_.find(pubkey);
      if (iter == pubKeyState_.end())
      {
         auto iter2 = pubKeyState_.find(modified_key);
         if (iter2 == pubKeyState_.end())
            return false;

         return iter2->second;
      }

      return iter->second;
   }

   return false;
}

////////////////////////////////////////////////////////////////////////////////
PubKeyType TxInEvalState::getType() const
{
   if (keyType_ != Type_Unkonwn)
      return keyType_;

   bool isCompressed = false;
   bool isUncompressed = false;

   for (auto& key : pubKeyState_)
   {
      if (key.first.getSize() == 65)
         isUncompressed = true;
      else if (key.first.getSize() == 33)
         isCompressed = true;
   }

   if (isCompressed && isUncompressed)
      keyType_ = Type_Mixed;
   else if (isCompressed)
      keyType_ = Type_Compressed;
   else if (isUncompressed)
      keyType_ = Type_Uncompressed;

   return keyType_;
}

////////////////////////////////////////////////////////////////////////////////
void TxEvalState::updateState(unsigned id, TxInEvalState state)
{
   evalMap_.insert(make_pair(id, state));
}

////////////////////////////////////////////////////////////////////////////////
bool TxEvalState::isValid(void) const
{
   for (auto& state : evalMap_)
   {
      if (!state.second.isValid())
         return false;
   }

   return true;
}

////////////////////////////////////////////////////////////////////////////////
TxInEvalState TxEvalState::getSignedStateForInput(unsigned i)
{
   auto iter = evalMap_.find(i);
   if (iter == evalMap_.end())
      throw range_error("invalid input index");

   return iter->second;
}



