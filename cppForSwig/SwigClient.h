////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2016, goatpig.                                              //
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //                                      
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

/***
Set of spoof classes that expose all BDV, wallet and address obj methods to SWIG
and handle the data transmission with the BDM server
***/

#ifndef _SWIGCLIENT_H
#define _SWIGCLIENT_H

#include "BDM_seder.h"
#include "StringSockets.h"
#include "bdmenums.h"
#include "log.h"
#include "TxClasses.h"

inline void StartCppLogging(string fname, int lvl) { STARTLOGGING(fname, (LogLevel)lvl); }
inline void ChangeCppLogLevel(int lvl) { SETLOGLEVEL((LogLevel)lvl); }
inline void DisableCppLogging() { SETLOGLEVEL(LogLvlDisabled); }
inline void EnableCppLogStdOut() { LOGENABLESTDOUT(); }
inline void DisableCppLogStdOut() { LOGDISABLESTDOUT(); }

#include <thread>

class BlockDataViewer;

struct NoArmoryDBExcept : public runtime_error
{
   NoArmoryDBExcept(void) : runtime_error("")
   {}
};

struct BDVAlreadyRegistered : public runtime_error
{
   BDVAlreadyRegistered(void) : runtime_error("")
   {}
};

///////////////////////////////////////////////////////////////////////////////
class LedgerDelegate
{
private:
   const string delegateID_;
   const string bdvID_;
   const shared_ptr<BinarySocket> sock_;

public:
   LedgerDelegate(shared_ptr<BinarySocket>, const string&, const string&);

   vector<LedgerEntryData> getHistoryPage(uint32_t id);
};

///////////////////////////////////////////////////////////////////////////////
class ScrAddrObj
{
private:
   const string bdvID_;
   const string walletID_;
   const BinaryData scrAddr_;
   const shared_ptr<BinarySocket> sock_;

   const uint64_t fullBalance_;
   const uint64_t spendableBalance_;
   const uint64_t unconfirmedBalance_;
   const uint32_t count_;

public:
   ScrAddrObj(shared_ptr<BinarySocket>, 
      const string&, const string&, const BinaryData&,
      uint64_t, uint64_t, uint64_t, uint32_t);

   uint64_t getFullBalance(void) const { return fullBalance_; }
   uint64_t getSpendableBalance(void) const { return spendableBalance_; }
   uint64_t getUnconfirmedBalance(void) const { return unconfirmedBalance_; }

   uint64_t getTxioCount(void) const { return count_; }

   vector<UTXO> getSpendableTxOutList(bool);
};

///////////////////////////////////////////////////////////////////////////////
class BtcWallet
{
protected:
   const string walletID_;
   const string bdvID_;
   const shared_ptr<BinarySocket> sock_;

public:
   BtcWallet(const BlockDataViewer&, const string&);
   vector<uint64_t> getBalancesAndCount(
      uint32_t topBlockHeight, bool IGNOREZC);

   vector<UTXO> getSpendableTxOutListForValue(
      uint64_t val = UINT64_MAX, bool ignoreZC = true);
   map<BinaryData, uint32_t> getAddrTxnCountsFromDB(void);
   map<BinaryData, vector<uint64_t> >
      getAddrBalancesFromDB(void);

   vector<LedgerEntryData> getHistoryPage(uint32_t id);
   LedgerEntryData getLedgerEntryForTxHash(
      const BinaryData& txhash);

   ScrAddrObj getScrAddrObjByKey(const BinaryData&, 
      uint64_t, uint64_t, uint64_t, uint32_t);

   vector<AddressBookEntry> createAddressBook(void) const;
};

///////////////////////////////////////////////////////////////////////////////
class Lockbox : public BtcWallet
{
private:
   uint64_t fullBalance_ = 0;
   uint64_t spendableBalance_ = 0;
   uint64_t unconfirmedBalance_ = 0;

   uint64_t txnCount_ = 0;

public:

   Lockbox(const BlockDataViewer& bdv, const string& id) :
      BtcWallet(bdv, id)
   {}

   void getBalancesAndCountFromDB(uint32_t topBlockHeight, bool IGNOREZC);

   uint64_t getFullBalance(void) const { return fullBalance_; }
   uint64_t getSpendableBalance(void) const { return spendableBalance_; }
   uint64_t getUnconfirmedBalance(void) const { return unconfirmedBalance_; }
   uint64_t getWltTotalTxnCount(void) const { return txnCount_; }
};

///////////////////////////////////////////////////////////////////////////////
class BlockHeader
{
   friend class Blockchain;
   friend class testBlockHeader;
   friend class BlockData;

private:
   
   void unserialize(uint8_t const * ptr, uint32_t size);
   void unserialize(BinaryDataRef const & str) 
   { unserialize(str.getPtr(), str.getSize()); }

public:

   BlockHeader(void) {}
   BlockHeader(const BinaryData&, unsigned);

   uint32_t           getVersion(void) const      { return READ_UINT32_LE(getPtr()); }
   BinaryData const & getThisHash(void) const     { return thisHash_; }
   BinaryData         getPrevHash(void) const     { return BinaryData(getPtr() + 4, 32); }
   BinaryData         getMerkleRoot(void) const   { return BinaryData(getPtr() + 36, 32); }
   BinaryData         getDiffBits(void) const     { return BinaryData(getPtr() + 72, 4); }
   uint32_t           getTimestamp(void) const    { return READ_UINT32_LE(getPtr() + 68); }
   uint32_t           getNonce(void) const        { return READ_UINT32_LE(getPtr() + 76); }
   uint32_t           getBlockHeight(void) const  { return blockHeight_; }

   /////////////////////////////////////////////////////////////////////////////
   BinaryDataRef  getThisHashRef(void) const   { return thisHash_.getRef(); }
   BinaryDataRef  getPrevHashRef(void) const   { return BinaryDataRef(getPtr() + 4, 32); }
   BinaryDataRef  getMerkleRootRef(void) const { return BinaryDataRef(getPtr() + 36, 32); }
   BinaryDataRef  getDiffBitsRef(void) const   { return BinaryDataRef(getPtr() + 72, 4); }

   /////////////////////////////////////////////////////////////////////////////
   uint8_t const * getPtr(void) const  {
      assert(isInitialized_);
      return dataCopy_.getPtr();
   }
   size_t        getSize(void) const {
      assert(isInitialized_);
      return dataCopy_.getSize();
   }
   bool            isInitialized(void) const { return isInitialized_; }

   void clearDataCopy() { dataCopy_.resize(0); }

private:
   BinaryData     dataCopy_;
   bool           isInitialized_ = false;
   // Specific to the DB storage
   uint32_t       blockHeight_ = UINT32_MAX;

   // Derived properties - we expect these to be set after construct/copy
   BinaryData     thisHash_;
   double         difficultyDbl_ = 0.0;
};


///////////////////////////////////////////////////////////////////////////////
class Blockchain
{
private:
   const shared_ptr<BinarySocket> sock_;
   const string bdvID_;

public:
   Blockchain(const BlockDataViewer&);
   bool hasHeaderWithHash(const BinaryData& hash);
   BlockHeader getHeaderByHeight(unsigned height);
};

///////////////////////////////////////////////////////////////////////////////
class PythonCallback
{   
private:

   enum CallbackOrder
   {
      CBO_continue,
      CBO_NewBlock,
      CBO_BDV_Refresh,
      CBO_BDM_Ready,
      CBO_progress,
      CBO_terminate
   };   

   bool run_ = true;
   thread thr_;

   const shared_ptr<BinarySocket> sock_;
   const string bdvID_;
   SOCKET sockfd_;

   map<string, CallbackOrder> orderMap_;

public:
   PythonCallback(const BlockDataViewer& bdv);
   virtual ~PythonCallback(void) = 0;

   virtual void run(BDMAction action, void* ptr, int block = 0) = 0;
   virtual void progress(
      BDMPhase phase,
      const vector<string> &walletIdVec,
      float progress, unsigned secondsRem,
      unsigned progressNumeric
      ) = 0;   
   
   void startLoop(void);
   void remoteLoop(void);

   void shutdown(void);
};

///////////////////////////////////////////////////////////////////////////////
class BlockDataViewer
{
   friend class ScrAddrObj;
   friend class BtcWallet;
   friend class PythonCallback;
   friend class LedgerDelegate;
   friend class Blockchain;

private:
   string bdvID_;
   const shared_ptr<BinarySocket> sock_;

private:
   BlockDataViewer(const shared_ptr<BinarySocket> sock);

public:
   ~BlockDataViewer(void);
   BtcWallet registerWallet(const string& id, 
      const vector<BinaryData>& addrVec,
      bool isNew);

   Lockbox registerLockbox(const string& id,
      const vector<BinaryData>& addrVec,
      bool isNew);

   const string& getID(void) const { return bdvID_; }

   static BlockDataViewer getNewBDV(
      const string& addr, const string& port, SocketType);
   
   LedgerDelegate getLedgerDelegateForWallets(void);
   LedgerDelegate getLedgerDelegateForLockboxes(void);
   LedgerDelegate getLedgerDelegateForScrAddr(
      const string&, const BinaryData&);
   Blockchain blockchain(void);

   void goOnline(void);
   void registerWithDB(BinaryData magic_word);
   void unregisterFromDB(void);
   void shutdown(const string& spawnId);

   void broadcastZC(const BinaryData& rawTx);
   Tx getTxByHash(const BinaryData& txHash);

   bool hasRemoteDB(void);
};

#endif
