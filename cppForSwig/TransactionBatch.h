////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2016, goatpig.                                              //
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //                                      
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

/***
Transaction batching format:

1) Syntax and formating:

   Sections are delimited by colons (:)
   Entries are delimited by semi colons (;)
   Values within an entry are delimited by commas (,)

   Sections and Entries are single lines (line breaks 
   before the delimiting character are not tolerated).
   
   Syntax is case sensitive.
   
   All data on a given line (prior to a line break) after 
   a delimiting colon (:) or semi colon (;) is ignored.

   White space and empty line breaks are ignored.
   All lines starting with # are ignored.

2) Data types:
   
   string: ascii text
   hexit: a-f A-F 0-9, in pairs. Hexit strings (one
      or more hexit pairs) must be prefixed with 0x
   integer: 0-9
   float: 0-9.0-9

3) List of sections
   Mandatory sections:

      Recipients

   Optional sections:

      WalletID
      Spenders
      Change
      Fee
      Locktime

      Change and Spenders require the presence of a WalletID section

4) Encoding (per section):
   a) WalletID: (mandatory)
      The id of the wallet coins are being spent from. Only one wallet 
      per batch is allowed.

   b) Spenders:
      A spender is an outpoint and a sequence. The outpoint is mandatory.
      the sequence is optional. Spenders as a section is optional. In the 
      absence of spenders, the wallet will fallback to its coin selection
      algorythm. In the presence of Spenders, no coin selection logic is
      applied.
      
      The outpoint is a 32 bytes hash represented as hexits followed by 
      the txid as an integer and the sequence as hexits. 
      
      Sequence will defaults to 0xFFFFFFFF.

      Example:

      Spenders:
      0xabcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789,11,0xFDFFFFFF;
      0xabcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789,5;

   c) Recipients:
      A recipient is a base58 address as a string and value as an integer
      representing an amonut of satoshis. Supports 1 optional comment as 
      a string

      Example:

      Recipients:
      1randomaddressstringforp2pkh,100000000;
      3somep2shaddressformultisig,200000000,This is a comment;

   d) Change:
      Change is a single base58 address as a string, no value. If a change
      address is not specified, the wallet will create one if applicable.

      Example:

      Change:
      1myenforcedchangeaddressexample;

   e) Fee:
      Fee can either be a flat_fee amount in BTC as a float or a fee_rate
      satoshi per byte integer. The two are mutually exclusive. In the 
      absence of a fee, the wallet will use its default fee setup instead

      Example:

      (as flat fee of 0.0005 BTC)
      Fee:
      flat_fee,0.0005;

      (as fee rate of 150 sat/B)
      Fee:
      fee_rate,150;

   f) Locktime
      4 hexit pairs or an integer

      Example:

      Locktime:
      0x00FE58A1

      or

      Locktime:
      450631
***/

#ifndef _H_TRANSACTION_BATCH
#define _H_TRANSACTION_BATCH

using namespace std;

#include <vector>
#include <map>
#include <stdint.h>
#include <functional>

#include "BinaryData.h"
#include "log.h"

#define SECTION_WALLET     "WalletID:"
#define SECTION_RECIPIENTS "Recipients:"
#define SECTION_SPENDERS   "Spenders:"
#define SECTION_CHANGE     "Change:"
#define SECTION_FEE        "Fee:"
#define SECTION_LOCKTIME   "Locktime:"

////////////////////////////////////////////////////////////////////////////////
class TransactionBatchException : public runtime_error
{
private:
   const unsigned lineId_;

public:
   TransactionBatchException(const string& err, unsigned lineId) :
      runtime_error(err), lineId_(lineId)
   {}

   unsigned line(void) const { return lineId_; }
};

////////////////////////////////////////////////////////////////////////////////
struct Spender
{
   string txHash_;
   uint32_t index_;
   uint32_t sequence_ = UINT32_MAX;
};

////////////////////////////////////////////////////////////////////////////////
struct Recipient
{
   string address_;
   uint64_t value_;
   string comment_;
};

////////////////////////////////////////////////////////////////////////////////
class TransactionBatch
{
private:
   vector<Spender> spenders_;
   vector<Recipient> recipients_;
  
   Recipient change_;
   
   unsigned locktime_ = 0;
   uint64_t fee_rate_ = 0;
   float fee_ = 0;

   string walletID_;
   bool haveWalletID_ = false;

private:
   map<string, function<
      void(const vector<string>&, pair<unsigned, unsigned>&)> > sections_;

private:
   void unserialize_wallet(const vector<string>&, pair<unsigned, unsigned>&);
   void unserialize_recipients(const vector<string>&, pair<unsigned, unsigned>&);
   void unserialize_spenders(const vector<string>&, pair<unsigned, unsigned>&);
   void unserialize_change(const vector<string>&, pair<unsigned, unsigned>&);
   void unserialize_fee(const vector<string>&, pair<unsigned, unsigned>&);
   void unserialize_locktime(const vector<string>&, pair <unsigned, unsigned>&);

   void unserialize(const string& str);

public:
   TransactionBatch(void);

   //add/set
   void addSpender(
      const string& txHashStr, unsigned txOutIndex, unsigned sequence);
   void addRecipient(const string& b58Address, uint64_t value);
   void setChange(const string& b58Address);
   
   void setWalletID(const string& ID) { walletID_ = ID; }

   //ser/deser
   void processBatchStr(const string& batch);
   string serialize(void) const;

   //get
   const string& getWalletID(void) const { return walletID_; }
   vector<Recipient> getRecipients(void) const { return recipients_; }
   vector<Spender> getSpenders(void) const { return spenders_; }
   const Recipient& getChange(void) const { return change_; }
   const uint64_t getFeeRate(void) const { return fee_rate_; }
   const float getFlatFee(void) const { return fee_; }
   unsigned getLockTime(void) const { return locktime_; }
};

#endif