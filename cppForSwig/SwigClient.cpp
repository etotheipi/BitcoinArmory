#include "SwigClient.h"

///////////////////////////////////////////////////////////////////////////////
//
// BlockDataViewer
//
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
void BlockDataViewer::goOnline()
{
   Command cmd;
   cmd.method_ = "goOnline";
   cmd.ids_.push_back(bdvID_);
   cmd.serialize();
   auto& result = sock_->writeAndRead(cmd.command_);
}

///////////////////////////////////////////////////////////////////////////////
BlockDataViewer::BlockDataViewer(const shared_ptr<BinarySocket> sock) :
   sock_(sock)
{

   //TODO: fix this
#ifdef _WIN33
   WORD wVersionRequested;
   WSADATA wsaData;
   int err;

   wVersionRequested = MAKEWORD(2, 2);

   err = WSAStartup(wVersionRequested, &wsaData);
   if (err != 0)
      throw runtime_error("WSAStartup failed with error: " + err);

   /* Confirm that the WinSock DLL supports 2.2.*/
   /* Note that if the DLL supports versions greater    */
   /* than 2.2 in addition to 2.2, it will still return */
   /* 2.2 in wVersion since that is the version we      */
   /* requested.                                        */

   if (LOBYTE(wsaData.wVersion) != 2 || HIBYTE(wsaData.wVersion) != 2) {
      WSACleanup();
      throw runtime_error("Could not find a usable version of Winsock.dll");
   }
#endif

   DataMeta::initTypeMap();

   auto&& result = sock_->writeAndRead(string("&registerBDV"));
   Arguments args(move(result));
   bdvID_ = args.get<string>();
}

///////////////////////////////////////////////////////////////////////////////
BlockDataViewer::~BlockDataViewer()
{
}

///////////////////////////////////////////////////////////////////////////////
BtcWallet BlockDataViewer::registerWallet(
   const string& id, const vector<BinaryData>& addrVec, bool isNew)
{
   Command cmd;
   uint32_t isNewInt = (uint32_t)isNew;

   cmd.args_.push_back(id);
   cmd.args_.push_back(BinaryDataVector(addrVec));
   cmd.args_.push_back(isNewInt);

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
   cmd.args_.push_back(isNewInt);

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

   cmd.args_.push_back(id);

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
int64_t BtcWallet::getFullBalance()
{
   Command cmd;
   cmd.method_ = "getFullBalance";
   cmd.ids_.push_back(bdvID_);
   cmd.ids_.push_back(walletID_);
   cmd.serialize();

   auto&& retval = sock_->writeAndRead(cmd.command_);
   Arguments arg(retval);
   auto&& balance = arg.get<uint64_t>();

   return balance;
}

///////////////////////////////////////////////////////////////////////////////
int64_t BtcWallet::getSpendableBalance(uint32_t blockheight, bool IGNOREZC)
{
   Command cmd;
   cmd.method_ = "getSpendableBalance";
   cmd.ids_.push_back(bdvID_);
   cmd.ids_.push_back(walletID_);

   unsigned int ignorezc = IGNOREZC;
   cmd.args_.push_back(blockheight);
   cmd.args_.push_back(unsigned int(ignorezc));

   cmd.serialize();

   auto&& retval = sock_->writeAndRead(cmd.command_);
   Arguments arg(retval);
   auto&& balance = arg.get<uint64_t>();

   return balance;
}

///////////////////////////////////////////////////////////////////////////////
int64_t BtcWallet::getUnconfirmedBalance(uint32_t blockheight, bool IGNOREZC)
{
   Command cmd;
   cmd.method_ = "getUnconfirmedBalance";
   cmd.ids_.push_back(bdvID_);
   cmd.ids_.push_back(walletID_);

   unsigned int ignorezc = IGNOREZC;
   cmd.args_.push_back(blockheight);
   cmd.args_.push_back(unsigned int(ignorezc));

   cmd.serialize();

   auto&& retval = sock_->writeAndRead(cmd.command_);
   Arguments arg(retval);
   auto&& balance = arg.get<uint64_t>();

   return balance;
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
   cmd.args_.push_back(val);
   cmd.args_.push_back(ignorezc);

   cmd.serialize();

   auto&& retval = sock_->writeAndRead(cmd.command_);
   Arguments arg(move(retval));
   auto&& utxoVec = arg.get<UtxoVector>();

   auto&& utxovec = utxoVec.toVec();
   return utxovec;
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
   cmd.args_.push_back(bdo);
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
void PythonCallback::remoteLoop(void)
{
   Command sendCmd;
   sendCmd.method_ = "registerCallback";
   sendCmd.ids_.push_back(bdvID_);
   sendCmd.serialize();

   while (run_)
   {
      auto&& retval = sock_->writeAndRead(sendCmd.command_);
      Arguments args(retval);

      auto&& cb = args.get<string>();

      if (cb == "NewBlock")
      {
         unsigned int newblock = args.get<unsigned int>();
         if (newblock != 0)
            run(BDMAction::BDMAction_NewBlock, &newblock, newblock);
      }
      else if (cb == "BDM_Ready")
      {
         unsigned int topblock = args.get<unsigned int>();
         run(BDMAction::BDMAction_Ready, nullptr, topblock);
      }
      else if (cb == "BDV_Refresh")
      {
         vector<BinaryData> bdVector;
         run(BDMAction::BDMAction_Refresh, &bdVector, 0);
      }
      else if (cb == "progress")
      {

      }
   }
}
