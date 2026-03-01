////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2016, goatpig.                                              //
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //                                      
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#include "TransactionBatch.h"

////////////////////////////////////////////////////////////////////////////////
TransactionBatch::TransactionBatch()
{
   auto wallet_lbd = [this](
      const vector<string>& lines, pair<unsigned, unsigned>& bounds)->void
   {
      this->unserialize_wallet(lines, bounds);
   };

   auto recipient_lbd = [this](
      const vector<string>& lines, pair<unsigned, unsigned>& bounds)->void
   {
      this->unserialize_recipients(lines, bounds);
   };

   auto spender_lbd = [this](
      const vector<string>& lines, pair<unsigned, unsigned>& bounds)->void
   {
      this->unserialize_spenders(lines, bounds);
   };

   auto change_lbd = [this](
      const vector<string>& lines, pair<unsigned, unsigned>& bounds)->void
   {
      this->unserialize_change(lines, bounds);
   };

   auto fee_lbd = [this](
      const vector<string>& lines, pair<unsigned, unsigned>& bounds)->void
   {
      this->unserialize_fee(lines, bounds);
   };

   sections_.insert(make_pair(SECTION_WALLET, wallet_lbd));
   sections_.insert(make_pair(SECTION_RECIPIENTS, recipient_lbd));
   sections_.insert(make_pair(SECTION_SPENDERS, spender_lbd));
   sections_.insert(make_pair(SECTION_CHANGE, change_lbd));
   sections_.insert(make_pair(SECTION_FEE, fee_lbd));
}

////////////////////////////////////////////////////////////////////////////////
void TransactionBatch::processBatchStr(const string& batch)
{
   try
   {
      unserialize(batch);
      LOGINFO << "Processed transaction batch successfully";
   }
   catch (TransactionBatchException& e)
   {
      if (e.line() != UINT32_MAX)
         LOGERR << "TxBatch processing error at line " << e.line();
      LOGERR << "TxBatch error message: " << e.what();
   }
}

////////////////////////////////////////////////////////////////////////////////
void TransactionBatch::unserialize(const string& str)
{
   //break down into lines
   vector<string> lines;

   stringstream ss(str);
   while (ss.good())
   {
      string str;
      getline(ss, str);
      lines.push_back(move(str));
   }

   //break down into sections
   map<string, pair<unsigned, unsigned>> sectionMap;
   string currentSection;
   
   auto closeSection = [&](const string& sectionStr, unsigned end)->void
   {
      //grab section iter
      auto mapIter = sectionMap.find(sectionStr);
      if (mapIter == sectionMap.end())
         throw TransactionBatchException(
         "trying to a close section that was not opened", end);

      //cull empty lines
      for (int y = end; y >= int(mapIter->second.first); y--)
      {
         if (lines[y].size() != 0)
            break;

         --end;
      }

      mapIter->second.second = end;
   };


   for (unsigned i = 0; i < lines.size(); i++)
   {
      auto& thisLine = lines[i];

      auto sectionIter = sections_.find(thisLine);
      if (sectionIter == sections_.end())
         continue;

      //open new section
      sectionMap.insert(make_pair(
         thisLine, make_pair(i, UINT32_MAX)));

      //close previous one
      if (currentSection.size() != 0)
         closeSection(currentSection, i - 1);

      currentSection = thisLine;
   }

   //close last section
   closeSection(currentSection, lines.size() - 1);

   //make sure the mandatory sections are present
   auto mandatoryIter = sectionMap.find(SECTION_WALLET);
   if (mandatoryIter != sectionMap.end())
      haveWalletID_ = true;

   mandatoryIter = sectionMap.find(SECTION_RECIPIENTS);
   if (mandatoryIter == sectionMap.end())
      throw TransactionBatchException("missing Recipients section", UINT32_MAX);

   //run all sections against respective parser
   for (auto& sectionPair : sectionMap)
   {
      auto sectionIter = sections_.find(sectionPair.first);
      sectionIter->second(lines, sectionPair.second);
   }
}

////////////////////////////////////////////////////////////////////////////////
void TransactionBatch::unserialize_wallet(
   const vector<string>& lines, pair<unsigned, unsigned>& bounds)
{
   if (bounds.first > bounds.second)
      throw TransactionBatchException(
         "invalid section boundaries", bounds.first);

   auto lineCount = bounds.second - bounds.first + 1;
   if (lineCount != 2)
      throw TransactionBatchException(
         "Wallet section can only have one entry", bounds.first);

   auto& line = lines[bounds.first + 1];
   stringstream ss(line);
   getline(ss, walletID_, ';');
   if (!ss.good())
      throw TransactionBatchException(
         "Invalid entry termination", bounds.first + 1);
}

////////////////////////////////////////////////////////////////////////////////
void TransactionBatch::unserialize_recipients(
   const vector<string>& lines, pair<unsigned, unsigned>& bounds)
{
   if (bounds.first > bounds.second)
      throw TransactionBatchException(
         "invalid section boundaries", bounds.first);

   auto lineCount = bounds.second - bounds.first + 1;
   if (lineCount < 2)
      throw TransactionBatchException(
         "Recipients section needs at least 1 entry", bounds.first);

   for (unsigned i = bounds.first + 1; i <= bounds.second; i++)
   {
      auto& line = lines[i];
      stringstream ss(line);
      Recipient rcp;

      getline(ss, rcp.address_, ',');
      if (!ss.good())
         throw TransactionBatchException(
            "Invalid recipient address delimitation", i);

      string valueStr;
      getline(ss, valueStr, ',');
      if (!ss.good())
      {
         string valStr_ss(move(valueStr));
         stringstream ss2(valStr_ss); 
        
         getline(ss2, valueStr, ';');

         if (!ss2.good())
            throw TransactionBatchException(
               "Invalid entry termination", i);
      }
      else
      {
         getline(ss, rcp.comment_, ';');

         if (!ss.good())
            throw TransactionBatchException(
               "Invalid entry termination", i);
      }

      stringstream ssInteger(valueStr);
      ssInteger >> rcp.value_;

      recipients_.push_back(move(rcp));
   }
}

////////////////////////////////////////////////////////////////////////////////
void TransactionBatch::unserialize_spenders(
   const vector<string>& lines, pair<unsigned, unsigned>& bounds)
{
   if (!haveWalletID_)
      throw TransactionBatchException(
         "WalletID required for Spenders section", bounds.first);

   if (bounds.first > bounds.second)
      throw TransactionBatchException(
         "invalid section boundaries", bounds.first);

   auto lineCount = bounds.second - bounds.first + 1;
   if (lineCount < 2)
      throw TransactionBatchException(
      "Spenders section needs at least 1 entry", bounds.first);

   for (unsigned i = bounds.first + 1; i <= bounds.second; i++)
   {
      auto& line = lines[i];
      stringstream ss(line);
      Spender spd;

      getline(ss, spd.txHash_, ',');
      if (!ss.good())
         throw TransactionBatchException(
            "Invalid spender txhash delimitation", i);

      string idStr;
      string sequenceStr;
      getline(ss, idStr, ',');
      if (!ss.good())
      {
         string idstr_ss(move(idStr));
         stringstream ss2(idstr_ss);

         getline(ss2, idStr, ';');

         if (!ss2.good())
            throw TransactionBatchException(
               "Invalid entry termination", i);
      }
      else
      {
         getline(ss, sequenceStr, ';');

         if (!ss.good())
            throw TransactionBatchException(
               "Invalid entry termination", i);
      }

      stringstream ssId(idStr);
      ssId >> spd.index_;

      if (sequenceStr.size() != 0)
      {
         stringstream ssSeq(sequenceStr);
         ssSeq >> spd.sequence_;
      }

      spenders_.push_back(move(spd));
   }
}

////////////////////////////////////////////////////////////////////////////////
void TransactionBatch::unserialize_change(
   const vector<string>& lines, pair<unsigned, unsigned>& bounds)
{
   if (!haveWalletID_)
      throw TransactionBatchException(
         "WalletID required for Change section", bounds.first);

   if (bounds.first > bounds.second)
      throw TransactionBatchException(
         "invalid section boundaries", bounds.first);

   auto lineCount = bounds.second - bounds.first + 1;
   if (lineCount != 2)
      throw TransactionBatchException(
         "Change section can only have one entry", bounds.first);

   auto& line = lines[bounds.first + 1];
   stringstream ss(line);
   getline(ss, change_.address_, ';');
   if (!ss.good())
      throw TransactionBatchException(
         "Invalid entry termination", bounds.first + 1);
}

////////////////////////////////////////////////////////////////////////////////
void TransactionBatch::unserialize_fee(
   const vector<string>& lines, pair<unsigned, unsigned>& bounds)
{
   if (bounds.first > bounds.second)
      throw TransactionBatchException(
         "invalid section boundaries", bounds.first);

   auto lineCount = bounds.second - bounds.first + 1;
   if (lineCount != 2)
      throw TransactionBatchException(
         "Fee section can only have one entry", bounds.first);
   
   auto& line = lines[bounds.first + 1];
   stringstream ss(line);

   string feeTypeStr;
   getline(ss, feeTypeStr, ',');
   if (!ss.good())
      throw TransactionBatchException(
         "Invalid fee type delimitation", bounds.first + 1);

   string feeValStr;
   getline(ss, feeValStr, ';');
   if (!ss.good())
      throw TransactionBatchException(
         "Invalid entry termination", bounds.first + 1);

   if (feeTypeStr == "flat_fee")
   {
      float feeBTC;
      stringstream ssFlatFee(feeValStr);
      ssFlatFee >> feeBTC;

      fee_ = uint64_t(feeBTC * 100000000ULL);
   }
   else if (feeTypeStr == "fee_rate")
   {
      stringstream ssFeeRate(feeValStr);
      ssFeeRate >> fee_rate_;
   }
}

////////////////////////////////////////////////////////////////////////////////
void TransactionBatch::unserialize_locktime(
   const vector<string>& lines, pair<unsigned, unsigned>& bounds)
{
   if (bounds.first > bounds.second)
      throw TransactionBatchException(
         "invalid section boundaries", bounds.first);

   auto lineCount = bounds.second - bounds.first + 1;
   if (lineCount != 2)
      throw TransactionBatchException(
         "Locktime section can only have one entry", bounds.first);

   auto& line = lines[bounds.first + 1];
   stringstream ss(line);

   string locktimeStr;
   getline(ss, locktimeStr, ';');
   if (!ss.good())
      throw TransactionBatchException(
         "Invalid entry termination", bounds.first + 1);

   if (locktimeStr.size() > 1 && locktimeStr.substr(0, 2) == "0x")
   {
      //convert to integer
      auto&& hexitStr = locktimeStr.substr(2);

      try
      {
         auto&& bd = READHEX(hexitStr);
         if (bd.getSize() > 4)
            throw TransactionBatchException(
               "hexit string out of bound", bounds.first + 1);

         locktime_ = 0;
         auto size = bd.getSize();
         auto offset = 4 - size;
         auto ltPtr = (uint8_t*)&locktime_;
         memcpy(ltPtr + offset, bd.getPtr(), size);
      }
      catch (runtime_error&)
      { 
         throw TransactionBatchException(
            "invalid hexit string", bounds.first + 1);
      }
   }
   else
   {
      stringstream locktimeSS(locktimeStr);
      ss >> locktime_;
   }
}

////////////////////////////////////////////////////////////////////////////////
string TransactionBatch::serialize(void) const
{
   stringstream ss;

   //wallet id
   if (walletID_.size() == 0)
      throw TransactionBatchException(
         "WalletID is required", UINT32_MAX);

   ss << SECTION_WALLET << endl;
   ss << walletID_ << ";" << endl << endl;

   //recipients
   if (recipients_.size() == 0)
      throw TransactionBatchException(
         "At least one recipient is required", UINT32_MAX);

   ss << SECTION_RECIPIENTS << endl;
   for (auto& rec : recipients_)
   {
      if (rec.address_.size() == 0)
         throw TransactionBatchException("Invalid address", UINT32_MAX);

      ss << rec.address_ << "," << rec.value_ << ";" << endl;
   }

   ss << endl;

   //spenders
   if (spenders_.size() > 0)
   {
      ss << SECTION_SPENDERS << endl;
      
      for (auto& spd : spenders_)
      {
         if (spd.txHash_.size() != 64)
            throw TransactionBatchException("Invalid hash", UINT32_MAX);

         ss << spd.txHash_ << "," 
            << spd.index_ << "," 
            << spd.sequence_ << ";" 
            << endl;
      }

      ss << endl;
   }

   //change
   if (change_.address_.size() > 0)
   {
      ss << SECTION_CHANGE << endl;
      ss << change_.address_ << ";" << endl << endl;
   }

   //fee
   if (fee_ > 0 || fee_rate_ > 0)
   {
      ss << SECTION_FEE << endl;
      
      if (fee_ > 0)
         ss << "flat_fee," << fee_ << endl;

      if (fee_rate_ > 0)
         ss << "fee_rate," << fee_rate_ << endl;
   }

   return ss.str();
}

////////////////////////////////////////////////////////////////////////////////
void TransactionBatch::addSpender(
   const string& txHash, unsigned txOutId, unsigned sequence)
{
   if (txHash.size() != 64)
      throw TransactionBatchException("invalid txhash size", UINT32_MAX);

   Spender spd;
   spd.txHash_ = txHash;
   spd.index_ = txOutId;
   spd.sequence_ = sequence;

   spenders_.push_back(move(spd));
}

////////////////////////////////////////////////////////////////////////////////
void TransactionBatch::addRecipient(const string& b58address, uint64_t value)
{
   Recipient rcp;
   rcp.address_ = b58address;
   rcp.value_ = value;

   recipients_.push_back(move(rcp));
}

////////////////////////////////////////////////////////////////////////////////
void TransactionBatch::setChange(const string& b58address)
{
   change_.address_ = b58address;
}
