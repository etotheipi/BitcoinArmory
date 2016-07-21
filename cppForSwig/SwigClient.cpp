////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2016, goatpig.                                              //
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //                                      
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#include "SwigClient.h"

///////////////////////////////////////////////////////////////////////////////
//
// BlockDataViewer
//
///////////////////////////////////////////////////////////////////////////////
bool BlockDataViewer::hasRemoteDB(void)
{
   return sock_->testConnection();
}

///////////////////////////////////////////////////////////////////////////////
BlockDataViewer BlockDataViewer::getNewBDV(const string& addr,
   const string& port, SocketType st)
{
   BinarySocket sock(addr, port);
   shared_ptr<BinarySocket> sockptr;
   
   if (st == SocketHttp)
      sockptr = make_shared<HttpSocket>(sock);
   else if (st == SocketFcgi)
      sockptr = make_shared<FcgiSocket>(HttpSocket(sock));

   BlockDataViewer bdv(sockptr);
   return bdv;
}

///////////////////////////////////////////////////////////////////////////////
void BlockDataViewer::registerWithDB(BinaryData magic_word)
{
   if (bdvID_.size() != 0)
      throw BDVAlreadyRegistered();

   //get bdvID
   try
   {
      Command cmd;
      cmd.method_ = "registerBDV";
      BinaryDataObject bdo(move(magic_word));
      cmd.args_.push_back(move(bdo));
      cmd.serialize();

      auto&& result = sock_->writeAndRead(cmd.command_);
      Arguments args(move(result));
      bdvID_ = args.get<string>();
   }
   catch (runtime_error &e)
   {
      LOGERR << e.what();
      throw e;
   }
}

///////////////////////////////////////////////////////////////////////////////
void BlockDataViewer::unregisterFromDB()
{
   Command cmd;
   cmd.method_ = "unregisterBDV";
   cmd.ids_.push_back(bdvID_);
   cmd.serialize();
   auto&& result = sock_->writeAndRead(cmd.command_);
}

///////////////////////////////////////////////////////////////////////////////
void BlockDataViewer::goOnline()
{
   Command cmd;
   cmd.method_ = "goOnline";
   cmd.ids_.push_back(bdvID_);
   cmd.serialize();
   auto&& result = sock_->writeAndRead(cmd.command_);
}

///////////////////////////////////////////////////////////////////////////////
BlockDataViewer::BlockDataViewer(const shared_ptr<BinarySocket> sock) :
   sock_(sock)
{
   DataMeta::initTypeMap();
}

///////////////////////////////////////////////////////////////////////////////
BlockDataViewer::~BlockDataViewer()
{
}

///////////////////////////////////////////////////////////////////////////////
void BlockDataViewer::shutdown(const string& spawnId)
{
   Command cmd;
   cmd.method_ = "shutdown";
   
   if (spawnId.size() > 0)
      cmd.args_.push_back(move(spawnId));

   cmd.serialize();
   auto&& result = sock_->writeAndRead(cmd.command_);
}

///////////////////////////////////////////////////////////////////////////////
BtcWallet BlockDataViewer::registerWallet(
   const string& id, const vector<BinaryData>& addrVec, bool isNew)
{
   Command cmd;
   unsigned isNewInt = (unsigned int)isNew;

   cmd.args_.push_back(id);
   cmd.args_.push_back(move(BinaryDataVector(addrVec)));
   cmd.args_.push_back(move(isNewInt));

   cmd.method_ = "registerWallet";
   cmd.ids_.push_back(bdvID_);
   cmd.serialize();
   auto&& result = sock_->writeAndRead(cmd.command_);

   //check result
   Arguments retval(result);
   auto retint = retval.get<unsigned int>();
   if (retint == 0)
      throw runtime_error("server returned false to registerWallet query");

   return BtcWallet(*this, id);
}

///////////////////////////////////////////////////////////////////////////////
BtcWallet BlockDataViewer::registerLockbox(
   const string& id, const vector<BinaryData>& addrVec, bool isNew)
{
   Command cmd;
   uint32_t isNewInt = (uint32_t)isNew;

   cmd.args_.push_back(id);
   cmd.args_.push_back(BinaryDataVector(addrVec));
   cmd.args_.push_back(move(isNewInt));

   cmd.method_ = "registerLockbox";
   cmd.ids_.push_back(bdvID_);
   cmd.serialize();
   auto&& result = sock_->writeAndRead(cmd.command_);

   //check result
   Arguments retval(result);
   auto retint = retval.get<unsigned int>();
   if (retint == 0)
      throw runtime_error("server returned false to registerLockbox query");

   return BtcWallet(*this, id);
}

///////////////////////////////////////////////////////////////////////////////
LedgerDelegate BlockDataViewer::getLedgerDelegateForWallets()
{
   Command cmd;

   cmd.method_ = "getLedgerDelegateForWallets";
   cmd.ids_.push_back(bdvID_);
   cmd.serialize();

   auto&& result = sock_->writeAndRead(cmd.command_);

   Arguments retval(result);
   auto&& ldid = retval.get<string>();
   
   LedgerDelegate ld(*this, ldid);
   return ld;
}

///////////////////////////////////////////////////////////////////////////////
LedgerDelegate BlockDataViewer::getLedgerDelegateForLockboxes()
{
   Command cmd;

   cmd.method_ = "getLedgerDelegateForLockboxes";
   cmd.ids_.push_back(bdvID_);
   cmd.serialize();

   auto&& result = sock_->writeAndRead(cmd.command_);

   Arguments retval(result);
   auto&& ldid = retval.get<string>();

   LedgerDelegate ld(*this, ldid);
   return ld;
}

///////////////////////////////////////////////////////////////////////////////
Blockchain BlockDataViewer::blockchain(void)
{
   return Blockchain(*this);
}

///////////////////////////////////////////////////////////////////////////////
void BlockDataViewer::broadcastZC(const BinaryData& rawTx)
{
   Command cmd;

   cmd.method_ = "broadcastZC";
   cmd.ids_.push_back(bdvID_);
   cmd.args_.push_back(BinaryDataObject(rawTx));
   cmd.serialize();

   auto&& result = sock_->writeAndRead(cmd.command_);
}

///////////////////////////////////////////////////////////////////////////////
Tx BlockDataViewer::getTxByHash(const BinaryData& txHash)
{
   Command cmd;

   cmd.method_ = "getTxByHash";
   cmd.ids_.push_back(bdvID_);
   cmd.args_.push_back(BinaryDataObject(txHash));
   cmd.serialize();

   auto&& result = sock_->writeAndRead(cmd.command_);

   Arguments retval(result);
   auto&& rawtx = retval.get<BinaryDataObject>();

   Tx tx;
   tx.unserializeWithRBFFlag(rawtx.get());
   return tx;
}

///////////////////////////////////////////////////////////////////////////////
//
// LedgerDelegate
//
///////////////////////////////////////////////////////////////////////////////
LedgerDelegate::LedgerDelegate(BlockDataViewer& bdv, const string& id) :
   sock_(bdv.sock_), delegateID_(id), bdvID_(bdv.getID())
{}

///////////////////////////////////////////////////////////////////////////////
vector<LedgerEntryData> LedgerDelegate::getHistoryPage(uint32_t id)
{
   Command cmd;
   cmd.method_ = "getHistoryPage";
   cmd.ids_.push_back(bdvID_);
   cmd.ids_.push_back(delegateID_);

   cmd.args_.push_back(move(id));

   cmd.serialize();

   auto&& retval = sock_->writeAndRead(cmd.command_);
   Arguments arg(retval);
   auto&& lev = arg.get<LedgerEntryVector>();

   auto levData = lev.toVector();
   return levData;
}

///////////////////////////////////////////////////////////////////////////////
//
// BtcWallet
//
///////////////////////////////////////////////////////////////////////////////
BtcWallet::BtcWallet(const BlockDataViewer& bdv, const string& id) :
   sock_(bdv.sock_), walletID_(id), bdvID_(bdv.bdvID_)
{}

///////////////////////////////////////////////////////////////////////////////
vector<uint64_t> BtcWallet::getBalances(uint32_t blockheight, bool IGNOREZC)
{
   Command cmd;
   cmd.method_ = "getBalances";
   cmd.ids_.push_back(bdvID_);
   cmd.ids_.push_back(walletID_);
   
   unsigned int ignorezc = IGNOREZC;
   cmd.args_.push_back(move(blockheight));
   cmd.args_.push_back(move(ignorezc));

   cmd.serialize();

   auto&& retval = sock_->writeAndRead(cmd.command_);
   Arguments arg(retval);
   
   auto&& balance_full = arg.get<uint64_t>();
   auto&& balance_spen = arg.get<uint64_t>();
   auto&& balance_unco = arg.get<uint64_t>();

   vector<uint64_t> balanceVec;
   balanceVec.push_back(balance_full);
   balanceVec.push_back(balance_spen);
   balanceVec.push_back(balance_unco);

   return balanceVec;
}

///////////////////////////////////////////////////////////////////////////////
vector<UTXO> BtcWallet::getSpendableTxOutListForValue(uint64_t val,
   bool ignoreZC)
{
   Command cmd;
   cmd.method_ = "getSpendableTxOutListForValue";
   cmd.ids_.push_back(bdvID_);
   cmd.ids_.push_back(walletID_);

   unsigned int ignorezc = ignoreZC;
   cmd.args_.push_back(move(val));
   cmd.args_.push_back(move(ignorezc));

   cmd.serialize();

   auto&& retval = sock_->writeAndRead(cmd.command_);
   Arguments arg(move(retval));
   auto&& utxoVec = arg.get<UtxoVector>();

   auto&& utxovec = utxoVec.toVec();
   return utxovec;
}

///////////////////////////////////////////////////////////////////////////////
map<BinaryData, uint32_t> BtcWallet::getAddrTxnCountsFromDB()
{
   Command cmd;
   cmd.method_ = "getAddrTxnCounts";
   cmd.ids_.push_back(bdvID_);
   cmd.ids_.push_back(walletID_);
   cmd.serialize();

   auto&& retval = sock_->writeAndRead(cmd.command_);
   Arguments arg(move(retval));

   map<BinaryData, uint32_t> countMap;

   auto&& count = arg.get<uint64_t>();
   for (unsigned i = 0; i < count; i++)
   {
      auto&& addr = arg.get<BinaryDataObject>();
      auto&& count = arg.get<uint32_t>();

      countMap[addr.get()] = count;
   }

   return countMap;
}

///////////////////////////////////////////////////////////////////////////////
vector<LedgerEntryData> BtcWallet::getHistoryPage(uint32_t id)
{
   Command cmd;
   cmd.method_ = "getHistoryPage";
   cmd.ids_.push_back(bdvID_);
   cmd.ids_.push_back(walletID_);

   cmd.args_.push_back(move(id));

   cmd.serialize();

   auto&& retval = sock_->writeAndRead(cmd.command_);
   Arguments arg(retval);
   auto&& lev = arg.get<LedgerEntryVector>();

   auto& levData = lev.toVector();
   return levData;
}

///////////////////////////////////////////////////////////////////////////////
LedgerEntryData BtcWallet::getLedgerEntryForTxHash(
   const BinaryData& txhash)
{
   Command cmd;
   cmd.method_ = "getHistoryPage";
   cmd.ids_.push_back(bdvID_);
   cmd.ids_.push_back(walletID_);

   //get history page with a hash as argument instead of an int will return 
   //the ledger entry for the tx instead of a page
   cmd.args_.push_back(move(BinaryDataObject(txhash)));

   cmd.serialize();

   auto&& retval = sock_->writeAndRead(cmd.command_);
   Arguments arg(retval);
   auto&& lev = arg.get<LedgerEntryVector>();

   auto& levData = lev.toVector();
   return levData[0];
}


///////////////////////////////////////////////////////////////////////////////
//
// ScrAddrObj
//
///////////////////////////////////////////////////////////////////////////////
ScrAddrObj::ScrAddrObj(const BlockDataViewer& bdv, const string& walletID,
   const BinaryData& scrAddr) :
   sock_(bdv.sock_), walletID_(walletID), scrAddr_(scrAddr)
{}

///////////////////////////////////////////////////////////////////////////////
//
// Blockchain
//
///////////////////////////////////////////////////////////////////////////////
Blockchain::Blockchain(const BlockDataViewer& bdv) :
   sock_(bdv.sock_), bdvID_(bdv.bdvID_)
{
}

///////////////////////////////////////////////////////////////////////////////
bool Blockchain::hasHeaderWithHash(const BinaryData& hash)
{
   Command cmd;
   cmd.method_ = "hasHeaderWithHash";
   cmd.ids_.push_back(bdvID_);

   BinaryDataObject bdo(hash);
   cmd.args_.push_back(move(bdo));
   cmd.serialize();

   auto&& retval = sock_->writeAndRead(cmd.command_);
   Arguments arg(retval);
   auto&& hasHash = arg.get<unsigned int>();

   return hasHash;
}

///////////////////////////////////////////////////////////////////////////////
//
// PythonCallback
//
///////////////////////////////////////////////////////////////////////////////
PythonCallback::PythonCallback(const BlockDataViewer& bdv) :
   sock_(bdv.sock_), bdvID_(bdv.getID())
{
   orderMap_["continue"] = CBO_continue;
   orderMap_["NewBlock"] = CBO_NewBlock;
   orderMap_["BDV_Refresh"] = CBO_BDV_Refresh;
   orderMap_["BDM_Ready"] = CBO_BDM_Ready;
   orderMap_["progress"] = CBO_progress;
   orderMap_["terminate"] = CBO_terminate;
}

///////////////////////////////////////////////////////////////////////////////
void PythonCallback::startLoop(void)
{
   auto loop = [this](void)->void
   { this->remoteLoop(); };

   thr_ = thread(loop);
}

///////////////////////////////////////////////////////////////////////////////
PythonCallback::~PythonCallback(void)
{
   run_ = false;
   if (thr_.joinable())
      thr_.join();
}

///////////////////////////////////////////////////////////////////////////////
void PythonCallback::shutdown()
{
   run_ = false;
   closesocket(sockfd_);
   if (thr_.joinable())
      thr_.join();
}

///////////////////////////////////////////////////////////////////////////////
void PythonCallback::remoteLoop(void)
{
   Command sendCmd;
   sendCmd.method_ = "registerCallback";
   sendCmd.ids_.push_back(bdvID_);
   sendCmd.serialize();

   auto processCallback = [this](Arguments args)->bool
   {
      //LOGINFO << "entering callback process lambda";

      while (args.hasArgs())
      {
         auto&& cb = args.get<string>();

         auto orderIter = orderMap_.find(cb);
         if(orderIter == orderMap_.end())
         {
            continue;
         } 

         switch(orderIter->second)
         {
         case CBO_continue:
            break;
       
         case CBO_NewBlock:
         {
            unsigned int newblock = args.get<unsigned int>();
            if (newblock != 0)
               run(BDMAction::BDMAction_NewBlock, &newblock, newblock);
            break;
         }

         case CBO_BDV_Refresh:
         {
            vector<BinaryData> bdVector;
            run(BDMAction::BDMAction_Refresh, &bdVector, 0);
            break;
         }

         case CBO_BDM_Ready:
         {
            unsigned int topblock = args.get<unsigned int>();
            run(BDMAction::BDMAction_Ready, nullptr, topblock);
            //return false;
            break;
         }

         case CBO_progress:
         {
            break;
         }

         case CBO_terminate:
         {
            //shut down command from server
            return false;
         }
         }
      }

      return true;
   };

   while (run_)
   {
      try
      {
         sockfd_ = sock_->openSocket(true);
         auto&& retval = sock_->writeAndRead(sendCmd.command_, sockfd_);
         Arguments args(move(retval));

         if (!processCallback(move(args)))
            return;
      }
      catch (runtime_error&)
      {
         continue;
      }
   }
}
