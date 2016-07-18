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

struct BDVALreadyRegistered : public runtime_error
{
   BDVALreadyRegistered(void) : runtime_error("")
   {}
};

///////////////////////////////////////////////////////////////////////////////
class ScrAddrObj
{
private:
   const string walletID_;
   const BinaryData scrAddr_;
   const shared_ptr<BinarySocket> sock_;

public:
   ScrAddrObj(const BlockDataViewer&, const string&, const BinaryData&);
};

///////////////////////////////////////////////////////////////////////////////
class BtcWallet
{
private:
   const string walletID_;
   const string bdvID_;
   const shared_ptr<BinarySocket> sock_;

public:
   BtcWallet(const BlockDataViewer&, const string&);
   vector<uint64_t> getBalances(uint32_t topBlockHeight, bool IGNOREZC);

   vector<UTXO> getSpendableTxOutListForValue(uint64_t val, bool ignoreZC);
   map<BinaryData, uint32_t> getAddrTxnCountsFromDB(void);

   vector<LedgerEntryData> getHistoryPage(uint32_t id);
   LedgerEntryData getLedgerEntryForTxHash(
      const BinaryData& txhash);
};

///////////////////////////////////////////////////////////////////////////////
class LedgerDelegate
{
private:
   const string delegateID_;
   const string bdvID_;
   const shared_ptr<BinarySocket> sock_;

public:
   LedgerDelegate(BlockDataViewer&, const string&);

   vector<LedgerEntryData> getHistoryPage(uint32_t id);
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

   BtcWallet registerLockbox(const string& id,
      const vector<BinaryData>& addrVec,
      bool isNew);

   const string& getID(void) const { return bdvID_; }

   static BlockDataViewer getNewBDV(
      const string& addr, const string& port, SocketType);
   
   LedgerDelegate getLedgerDelegateForWallets(void);
   LedgerDelegate getLedgerDelegateForLockboxes(void);
   Blockchain blockchain(void);

   void goOnline(void);
   void registerWithDB(void);
   void unregisterFromDB(void);
   void shutdown(const string& spawnId);

   void broadcastZC(const BinaryData& rawTx);
   Tx getTxByHash(const BinaryData& txHash);

   bool hasRemoteDB(void);
};

#endif
