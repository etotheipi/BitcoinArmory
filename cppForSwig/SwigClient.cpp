////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2016, goatpig.                                              //
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //                                      
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#include "SwigClient.h"

using namespace SwigClient;

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
      auto&& bdoID = args.get<BinaryDataObject>();
      bdvID_ = bdoID.toStr();
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
BlockDataViewer::BlockDataViewer(void)
{
   txMap_ = make_shared<map<BinaryData, Tx>>();
   rawHeaderMap_ = make_shared<map<BinaryData, BinaryData>>();
}


///////////////////////////////////////////////////////////////////////////////
BlockDataViewer::BlockDataViewer(const shared_ptr<BinarySocket> sock) :
   sock_(sock)
{
   txMap_ = make_shared<map<BinaryData, Tx>>();
   rawHeaderMap_ = make_shared<map<BinaryData, BinaryData>>();
}

///////////////////////////////////////////////////////////////////////////////
BlockDataViewer::~BlockDataViewer()
{
}

///////////////////////////////////////////////////////////////////////////////
void BlockDataViewer::shutdown(const string& cookie)
{
   Command cmd;
   cmd.method_ = "shutdown";
   
   if (cookie.size() > 0)
   {
      BinaryDataObject bdo(cookie);
      cmd.args_.push_back(move(bdo));
   }

   cmd.serialize();
   auto&& result = sock_->writeAndRead(cmd.command_);
}

///////////////////////////////////////////////////////////////////////////////
void BlockDataViewer::shutdownNode(const string& cookie)
{
   Command cmd;
   cmd.method_ = "shutdownNode";

   if (cookie.size() > 0)
   {
      BinaryDataObject bdo(cookie);
      cmd.args_.push_back(move(bdo));
   }

   cmd.serialize();
   sock_->writeAndRead(cmd.command_);
}

///////////////////////////////////////////////////////////////////////////////
SwigClient::BtcWallet BlockDataViewer::registerWallet(
   const string& id, const vector<BinaryData>& addrVec, bool isNew)
{
   Command cmd;

   BinaryDataObject bdo(id);
   cmd.args_.push_back(move(bdo));
   cmd.args_.push_back(move(BinaryDataVector(addrVec)));
   cmd.args_.push_back(move(IntType(isNew)));

   cmd.method_ = "registerWallet";
   cmd.ids_.push_back(bdvID_);
   cmd.serialize();
   auto&& result = sock_->writeAndRead(cmd.command_);

   //check result
   Arguments retval(result);
   auto retint = retval.get<IntType>().getVal();
   if (retint == 0)
      throw runtime_error("server returned false to registerWallet query");

   return BtcWallet(*this, id);
}

///////////////////////////////////////////////////////////////////////////////
Lockbox BlockDataViewer::registerLockbox(
   const string& id, const vector<BinaryData>& addrVec, bool isNew)
{
   Command cmd;

   BinaryDataObject bdo(id);
   cmd.args_.push_back(move(bdo));
   cmd.args_.push_back(BinaryDataVector(addrVec));
   cmd.args_.push_back(move(IntType(isNew)));

   cmd.method_ = "registerLockbox";
   cmd.ids_.push_back(bdvID_);
   cmd.serialize();
   auto&& result = sock_->writeAndRead(cmd.command_);

   //check result
   Arguments retval(result);
   auto retint = retval.get<IntType>().getVal();
   if (retint == 0)
      throw runtime_error("server returned false to registerLockbox query");

   return Lockbox(*this, id, addrVec);
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
   auto&& ldid = retval.get<BinaryDataObject>().toStr();
   
   LedgerDelegate ld(sock_, bdvID_, ldid);
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

   Arguments retval(move(result));
   auto&& ldid = retval.get<BinaryDataObject>().toStr();

   LedgerDelegate ld(sock_, bdvID_, ldid);
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
   auto&& txHash = BtcUtils::getHash256(rawTx.getRef());
   Tx tx(rawTx);
   txMap_->insert(make_pair(txHash, tx));

   Command cmd;

   cmd.method_ = "broadcastZC";
   cmd.ids_.push_back(bdvID_);
   cmd.args_.push_back(BinaryDataObject(rawTx));
   cmd.serialize();

   sock_->writeAndRead(cmd.command_);
}

///////////////////////////////////////////////////////////////////////////////
Tx BlockDataViewer::getTxByHash(const BinaryData& txHash)
{
   BinaryDataRef bdRef(txHash);
   BinaryData hash;

   if (txHash.getSize() != 32)
   {
      if (txHash.getSize() == 64)
      {
         string hashstr(txHash.toCharPtr(), txHash.getSize());
         hash = READHEX(hashstr);
         bdRef.setRef(hash);
      }
   }

   auto iter = txMap_->find(bdRef);
   if (iter != txMap_->end())
      return iter->second;

   Command cmd;

   cmd.method_ = "getTxByHash";
   cmd.ids_.push_back(bdvID_);
   cmd.args_.push_back(BinaryDataObject(bdRef));
   cmd.serialize();

   auto&& result = sock_->writeAndRead(cmd.command_);

   Arguments retval(result);
   auto&& rawtx = retval.get<BinaryDataObject>();

   Tx tx;
   tx.unserializeWithMetaData(rawtx.get());
   txMap_->insert(make_pair(txHash, tx));
   return tx;
}

///////////////////////////////////////////////////////////////////////////////
BinaryData BlockDataViewer::getRawHeaderForTxHash(const BinaryData& txHash)
{
   BinaryDataRef bdRef(txHash);
   BinaryData hash;

   if (txHash.getSize() != 32)
   {
      if (txHash.getSize() == 64)
      {
         string hashstr(txHash.toCharPtr(), txHash.getSize());
         hash = READHEX(hashstr);
         bdRef.setRef(hash);
      }
   }

   auto iter = rawHeaderMap_->find(bdRef);
   if (iter != rawHeaderMap_->end())
      return iter->second;

   Command cmd;

   cmd.method_ = "getRawHeaderForTxHash";
   cmd.ids_.push_back(bdvID_);
   cmd.args_.push_back(BinaryDataObject(bdRef));
   cmd.serialize();

   auto&& result = sock_->writeAndRead(cmd.command_);

   Arguments retval(result);
   auto&& rawheader = retval.get<BinaryDataObject>();

   rawHeaderMap_->insert(make_pair(bdRef, rawheader.get()));
   return rawheader.get();
}

///////////////////////////////////////////////////////////////////////////////
LedgerDelegate BlockDataViewer::getLedgerDelegateForScrAddr(
   const string& walletID, const BinaryData& scrAddr)
{
   Command cmd;

   cmd.method_ = "getLedgerDelegateForScrAddr";
   cmd.ids_.push_back(bdvID_);
   cmd.ids_.push_back(walletID);

   BinaryDataObject bdo(scrAddr);
   cmd.args_.push_back(move(bdo));

   cmd.serialize();

   auto&& result = sock_->writeAndRead(cmd.command_);

   Arguments retval(result);
   auto&& ldid = retval.get<BinaryDataObject>();

   LedgerDelegate ld(sock_, bdvID_, ldid.toStr());
   return ld;
}

///////////////////////////////////////////////////////////////////////////////
void BlockDataViewer::updateWalletsLedgerFilter(
   const vector<BinaryData>& wltIdVec)
{
   Command cmd;

   cmd.method_ = "updateWalletsLedgerFilter";
   cmd.ids_.push_back(bdvID_);

   BinaryDataVector bdVec;
   for (auto bd : wltIdVec)
      bdVec.push_back(move(bd));

   cmd.args_.push_back(move(bdVec));
   cmd.serialize();

   auto&& result = sock_->writeAndRead(cmd.command_);
}

///////////////////////////////////////////////////////////////////////////////
NodeStatusStruct BlockDataViewer::getNodeStatus()
{
   Command cmd;

   cmd.method_ = "getNodeStatus";
   cmd.ids_.push_back(bdvID_);

   cmd.serialize();
   auto&& result = sock_->writeAndRead(cmd.command_);

   Arguments retval(result);
   auto&& serData = retval.get<BinaryDataObject>();

   NodeStatusStruct nss;
   nss.deserialize(serData.get());

   return nss;
}

///////////////////////////////////////////////////////////////////////////////
FeeEstimateStruct BlockDataViewer::estimateFee(
   unsigned blocksToConfirm, const string& strategy)
{
   Command cmd;

   cmd.method_ = "estimateFee";
   cmd.ids_.push_back(bdvID_);

   IntType inttype(blocksToConfirm);
   BinaryDataObject bdo(strategy);

   cmd.args_.push_back(move(inttype));
   cmd.args_.push_back(move(bdo));
   cmd.serialize();

   auto&& result = sock_->writeAndRead(cmd.command_);
   Arguments args(result);

   //fee/byte
   auto serData = args.get<BinaryDataObject>();
   BinaryRefReader brr(serData.get().getRef());
   auto val = brr.get_double();

   //issmart
   auto boolObj = args.get<IntType>();
   auto boolVal = bool(boolObj.getVal());

   //error msg
   string error;
   auto errorData = args.get<BinaryDataObject>().get();
   if (errorData.getSize() > 0)
      error = move(string(errorData.getCharPtr(), errorData.getSize()));

   return FeeEstimateStruct(val, boolVal, error);
}

///////////////////////////////////////////////////////////////////////////////
vector<LedgerEntryData> BlockDataViewer::getHistoryForWalletSelection(
   const vector<string>& wldIDs, const string& orderingStr)
{
   Command cmd;
   cmd.method_ = "getHistoryForWalletSelection";
   cmd.ids_.push_back(bdvID_);

   BinaryDataVector bdVec;
   for (auto& id : wldIDs)
   {
      BinaryData bd((uint8_t*)id.c_str(), id.size());
      bdVec.push_back(move(bd));
   }

   BinaryDataObject bdo(orderingStr);

   cmd.args_.push_back(move(bdVec));
   cmd.args_.push_back(move(bdo));
   cmd.serialize();

   auto&& result = sock_->writeAndRead(cmd.command_);
   Arguments args(result);

   auto&& lev = args.get<LedgerEntryVector>();
   return lev.toVector();
}

///////////////////////////////////////////////////////////////////////////////
uint64_t BlockDataViewer::getValueForTxOut(
   const BinaryData& txHash, unsigned inputId)
{
   Command cmd;
   cmd.method_ = "getValueForTxOut";
   cmd.ids_.push_back(bdvID_);

   BinaryDataObject bdo(txHash);
   IntType it_inputid(inputId);

   cmd.args_.push_back(move(bdo));
   cmd.args_.push_back(move(it_inputid));
   cmd.serialize();

   auto&& result = sock_->writeAndRead(cmd.command_);
   Arguments args(result);

   auto value = args.get<IntType>();
   return value.getVal();
}

///////////////////////////////////////////////////////////////////////////////
string BlockDataViewer::broadcastThroughRPC(const BinaryData& rawTx)
{
   Command cmd;
   cmd.method_ = "broadcastThroughRPC";
   cmd.ids_.push_back(bdvID_);

   BinaryDataObject bdo(rawTx);

   cmd.args_.push_back(move(bdo));
   cmd.serialize();

   auto&& result = sock_->writeAndRead(cmd.command_);
   Arguments args(result);

   auto result_bdo = args.get<BinaryDataObject>();
   auto& result_bd = result_bdo.get();
   string result_str(result_bd.getCharPtr(), result_bd.getSize());

   return result_str;
}

///////////////////////////////////////////////////////////////////////////////
void BlockDataViewer::registerAddrList(
   const BinaryData& id,
   const vector<BinaryData>& addrVec)
{
   Command cmd;

   cmd.method_ = "registerAddrList";
   cmd.ids_.push_back(bdvID_);

   BinaryDataObject bdo(id);
   BinaryDataVector bdVec;
   for (auto addr : addrVec)
      bdVec.push_back(move(addr));

   cmd.args_.push_back(move(bdo));
   cmd.args_.push_back(move(bdVec));
   cmd.serialize();

   auto&& result = sock_->writeAndRead(cmd.command_);
}

///////////////////////////////////////////////////////////////////////////////
vector<UTXO> BlockDataViewer::getUtxosForAddrVec(
   const vector<BinaryData>& addrVec)
{
   Command cmd;

   cmd.method_ = "getUTXOsForAddrList";
   cmd.ids_.push_back(bdvID_);

   BinaryDataVector bdVec;
   for (auto addr : addrVec)
      bdVec.push_back(move(addr));

   cmd.args_.push_back(move(bdVec));
   cmd.serialize();

   auto&& result = sock_->writeAndRead(cmd.command_);
   Arguments arg(move(result));
   auto count = arg.get<IntType>().getVal();

   vector<UTXO> utxovec;
   for (unsigned i = 0; i < count; i++)
   {
      auto&& bdo = arg.get<BinaryDataObject>();
      UTXO utxo;
      utxo.unserialize(bdo.get());

      utxovec.push_back(move(utxo));
   }

   return utxovec;
}

///////////////////////////////////////////////////////////////////////////////
//
// LedgerDelegate
//
///////////////////////////////////////////////////////////////////////////////
LedgerDelegate::LedgerDelegate(shared_ptr<BinarySocket> sock,
   const string& bdvid, const string& ldid) :
   sock_(sock), delegateID_(ldid), bdvID_(bdvid)
{}

///////////////////////////////////////////////////////////////////////////////
vector<LedgerEntryData> LedgerDelegate::getHistoryPage(uint32_t id)
{
   Command cmd;
   cmd.method_ = "getHistoryPage";
   cmd.ids_.push_back(bdvID_);
   cmd.ids_.push_back(delegateID_);

   cmd.args_.push_back(move(IntType(id)));

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
SwigClient::BtcWallet::BtcWallet(const BlockDataViewer& bdv, const string& id) :
   sock_(bdv.sock_), walletID_(id), bdvID_(bdv.bdvID_)
{}

///////////////////////////////////////////////////////////////////////////////
vector<uint64_t> SwigClient::BtcWallet::getBalancesAndCount(
   uint32_t blockheight, bool IGNOREZC)
{
   Command cmd;
   cmd.method_ = "getBalancesAndCount";
   cmd.ids_.push_back(bdvID_);
   cmd.ids_.push_back(walletID_);
   
   unsigned int ignorezc = IGNOREZC;
   cmd.args_.push_back(move(IntType(blockheight)));

   cmd.serialize();

   auto&& retval = sock_->writeAndRead(cmd.command_);
   Arguments arg(retval);
   
   auto&& balance_full = arg.get<IntType>().getVal();
   auto&& balance_spen = arg.get<IntType>().getVal();
   auto&& balance_unco = arg.get<IntType>().getVal();
   auto&& count = arg.get<IntType>().getVal();

   vector<uint64_t> balanceVec;
   balanceVec.push_back(balance_full);
   balanceVec.push_back(balance_spen);
   balanceVec.push_back(balance_unco);
   balanceVec.push_back(count);

   return balanceVec;
}

///////////////////////////////////////////////////////////////////////////////
vector<UTXO> SwigClient::BtcWallet::getSpendableTxOutListForValue(uint64_t val)
{
   Command cmd;
   cmd.method_ = "getSpendableTxOutListForValue";
   cmd.ids_.push_back(bdvID_);
   cmd.ids_.push_back(walletID_);

   cmd.args_.push_back(move(IntType(val)));

   cmd.serialize();

   auto&& retval = sock_->writeAndRead(cmd.command_);
   Arguments arg(move(retval));
   auto count = arg.get<IntType>().getVal();

   vector<UTXO> utxovec;
   for (unsigned i = 0; i < count; i++)
   {
      auto&& bdo = arg.get<BinaryDataObject>();
      UTXO utxo;
      utxo.unserialize(bdo.get());

      utxovec.push_back(move(utxo));
   }

   return utxovec;
}

///////////////////////////////////////////////////////////////////////////////
vector<UTXO> SwigClient::BtcWallet::getSpendableZCList()
{
   Command cmd;
   cmd.method_ = "getSpendableZCList";
   cmd.ids_.push_back(bdvID_);
   cmd.ids_.push_back(walletID_);

   cmd.serialize();

   auto&& retval = sock_->writeAndRead(cmd.command_);
   Arguments arg(move(retval));
   auto count = arg.get<IntType>().getVal();

   vector<UTXO> utxovec;
   for (unsigned i = 0; i < count; i++)
   {
      auto&& bdo = arg.get<BinaryDataObject>();
      UTXO utxo;
      utxo.unserialize(bdo.get());
      utxovec.push_back(move(utxo));
   }

   return utxovec;
}

///////////////////////////////////////////////////////////////////////////////
vector<UTXO> SwigClient::BtcWallet::getRBFTxOutList()
{
   Command cmd;
   cmd.method_ = "getRBFTxOutList";
   cmd.ids_.push_back(bdvID_);
   cmd.ids_.push_back(walletID_);

   cmd.serialize();

   auto&& retval = sock_->writeAndRead(cmd.command_);
   Arguments arg(move(retval));
   auto count = arg.get<IntType>().getVal();

   vector<UTXO> utxovec;
   for (unsigned i = 0; i < count; i++)
   {
      auto&& bdo = arg.get<BinaryDataObject>();
      UTXO utxo;
      utxo.unserialize(bdo.get());
      utxovec.push_back(move(utxo));
   }

   return utxovec;
}

///////////////////////////////////////////////////////////////////////////////
map<BinaryData, uint32_t> SwigClient::BtcWallet::getAddrTxnCountsFromDB()
{
   Command cmd;
   cmd.method_ = "getAddrTxnCounts";
   cmd.ids_.push_back(bdvID_);
   cmd.ids_.push_back(walletID_);
   cmd.serialize();

   auto&& retval = sock_->writeAndRead(cmd.command_);
   Arguments arg(move(retval));

   map<BinaryData, uint32_t> countMap;

   auto&& count = arg.get<IntType>().getVal();
   for (unsigned i = 0; i < count; i++)
   {
      auto&& addr = arg.get<BinaryDataObject>();
      auto&& txcount = arg.get<IntType>().getVal();

      countMap[addr.get()] = txcount;
   }

   return countMap;
}

///////////////////////////////////////////////////////////////////////////////
map<BinaryData, vector<uint64_t>>
SwigClient::BtcWallet::getAddrBalancesFromDB(void)
{
   Command cmd;
   cmd.method_ = "getAddrBalances";
   cmd.ids_.push_back(bdvID_);
   cmd.ids_.push_back(walletID_);
   cmd.serialize();

   auto&& retval = sock_->writeAndRead(cmd.command_);
   Arguments arg(move(retval));

   map<BinaryData, vector<uint64_t>> balanceMap;

   auto&& count = arg.get<IntType>().getVal();
   for (unsigned i = 0; i < count; i++)
   {
      auto&& addr = arg.get<BinaryDataObject>();
      auto& balanceVec = balanceMap[addr.get()];

      balanceVec.push_back(arg.get<IntType>().getVal());
      balanceVec.push_back(arg.get<IntType>().getVal());
      balanceVec.push_back(arg.get<IntType>().getVal());
   }

   return balanceMap;
}


///////////////////////////////////////////////////////////////////////////////
vector<LedgerEntryData> SwigClient::BtcWallet::getHistoryPage(uint32_t id)
{
   Command cmd;
   cmd.method_ = "getHistoryPage";
   cmd.ids_.push_back(bdvID_);
   cmd.ids_.push_back(walletID_);

   cmd.args_.push_back(move(IntType(id)));

   cmd.serialize();

   auto&& retval = sock_->writeAndRead(cmd.command_);
   Arguments arg(retval);
   auto&& lev = arg.get<LedgerEntryVector>();

   auto& levData = lev.toVector();
   return levData;
}

///////////////////////////////////////////////////////////////////////////////
LedgerEntryData SwigClient::BtcWallet::getLedgerEntryForTxHash(
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
ScrAddrObj SwigClient::BtcWallet::getScrAddrObjByKey(const BinaryData& scrAddr,
   uint64_t full, uint64_t spendable, uint64_t unconf, uint32_t count)
{
   return ScrAddrObj(sock_, bdvID_, walletID_, scrAddr, INT32_MAX,
      full, spendable, unconf, count);
}

///////////////////////////////////////////////////////////////////////////////
vector<AddressBookEntry> SwigClient::BtcWallet::createAddressBook(void) const
{
   Command cmd;
   cmd.method_ = "createAddressBook";
   cmd.ids_.push_back(bdvID_);
   cmd.ids_.push_back(walletID_);

   cmd.serialize();

   auto&& retval = sock_->writeAndRead(cmd.command_);
   Arguments arg(move(retval));
   auto count = arg.get<IntType>().getVal();

   vector<AddressBookEntry> abVec;

   for (unsigned i = 0; i < count; i++)
   {
      auto&& bdo = arg.get<BinaryDataObject>();
      AddressBookEntry abe;
      abe.unserialize(bdo.get());

      abVec.push_back(move(abe));
   }

   return abVec;
}

///////////////////////////////////////////////////////////////////////////////
//
// Lockbox
//
///////////////////////////////////////////////////////////////////////////////
void Lockbox::getBalancesAndCountFromDB(uint32_t topBlockHeight, bool IGNOREZC)
{
   auto&& bVec = BtcWallet::getBalancesAndCount(topBlockHeight, IGNOREZC);

   fullBalance_ = bVec[0];
   spendableBalance_ = bVec[1];
   unconfirmedBalance_ = bVec[2];

   txnCount_ = bVec[3];
}

///////////////////////////////////////////////////////////////////////////////
bool Lockbox::hasScrAddr(const BinaryData& addr) const
{
   auto addrIter = scrAddrSet_.find(addr);
   return addrIter != scrAddrSet_.end();
}

///////////////////////////////////////////////////////////////////////////////
//
// ScrAddrObj
//
///////////////////////////////////////////////////////////////////////////////
ScrAddrObj::ScrAddrObj(shared_ptr<BinarySocket> sock, const string& bdvId,
   const string& walletID, const BinaryData& scrAddr, int index,
   uint64_t full, uint64_t spendabe, uint64_t unconf, uint32_t count) :
   sock_(sock), bdvID_(bdvId), walletID_(walletID), scrAddr_(scrAddr),
   index_(index), fullBalance_(full), spendableBalance_(spendabe), 
   unconfirmedBalance_(unconf), count_(count)
{}

///////////////////////////////////////////////////////////////////////////////
ScrAddrObj::ScrAddrObj(SwigClient::BtcWallet* wlt, const BinaryData& scrAddr,
   int index, uint64_t full, uint64_t spendabe, uint64_t unconf, uint32_t count) :
   sock_(wlt->sock_), bdvID_(wlt->bdvID_), walletID_(wlt->walletID_), 
   scrAddr_(scrAddr), index_(index),
   fullBalance_(full), spendableBalance_(spendabe),
   unconfirmedBalance_(unconf), count_(count)
{}

///////////////////////////////////////////////////////////////////////////////
vector<UTXO> ScrAddrObj::getSpendableTxOutList(bool ignoreZC)
{
   Command cmd;
   cmd.method_ = "getSpendableTxOutListForAddr";
   cmd.ids_.push_back(bdvID_);
   cmd.ids_.push_back(walletID_);

   BinaryDataObject bdo(scrAddr_);
   cmd.args_.push_back(move(bdo));
   cmd.args_.push_back(move(IntType(ignoreZC)));

   cmd.serialize();

   auto&& retval = sock_->writeAndRead(cmd.command_);
   Arguments arg(move(retval));
   auto count = arg.get<IntType>().getVal();

   vector<UTXO> utxovec;
   for (unsigned i = 0; i < count; i++)
   {
      auto&& _bdo = arg.get<BinaryDataObject>();
      UTXO utxo;
      utxo.unserialize(_bdo.get());

      utxovec.push_back(move(utxo));
   }

   return utxovec;
}

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
   auto&& hasHash = arg.get<IntType>().getVal();

   return hasHash;
}

///////////////////////////////////////////////////////////////////////////////
BlockHeader Blockchain::getHeaderByHeight(unsigned height)
{
   Command cmd;

   cmd.method_ = "getHeaderByHeight";
   cmd.ids_.push_back(bdvID_);
   cmd.args_.push_back(move(IntType(height)));
   cmd.serialize();

   auto&& result = sock_->writeAndRead(cmd.command_);

   Arguments retval(result);
   auto&& rawheader = retval.get<BinaryDataObject>();

   BlockHeader bh(rawheader.get(), height);
   return bh;
}

///////////////////////////////////////////////////////////////////////////////
//
// BlockHeader
//
///////////////////////////////////////////////////////////////////////////////
BlockHeader::BlockHeader(const BinaryData& rawheader, unsigned height)
{
   unserialize(rawheader.getRef());
   blockHeight_ = height;
}

////////////////////////////////////////////////////////////////////////////////
void BlockHeader::unserialize(uint8_t const * ptr, uint32_t size)
{
   if (size < HEADER_SIZE)
      throw BlockDeserializingException();
   dataCopy_.copyFrom(ptr, HEADER_SIZE);
   BtcUtils::getHash256(dataCopy_.getPtr(), HEADER_SIZE, thisHash_);
   difficultyDbl_ = BtcUtils::convertDiffBitsToDouble(
      BinaryDataRef(dataCopy_.getPtr() + 72, 4));
   isInitialized_ = true;
   blockHeight_ = UINT32_MAX;
}

///////////////////////////////////////////////////////////////////////////////
//
// PythonCallback
//
///////////////////////////////////////////////////////////////////////////////
PythonCallback::PythonCallback(const BlockDataViewer& bdv) :
   sock_(bdv.sock_), bdvID_(bdv.getID()), bdvPtr_(&bdv)
{
   orderMap_["continue"]         = CBO_continue;
   orderMap_["NewBlock"]         = CBO_NewBlock;
   orderMap_["BDV_ZC"]           = CBO_ZC;
   orderMap_["BDV_Refresh"]      = CBO_BDV_Refresh;
   orderMap_["BDM_Ready"]        = CBO_BDM_Ready;
   orderMap_["BDV_Progress"]     = CBO_progress;
   orderMap_["terminate"]        = CBO_terminate;
   orderMap_["BDV_NodeStatus"]   = CBO_NodeStatus;
   orderMap_["BDV_Error"]        = CBO_BDV_Error;
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
   BinarySocket::closeSocket(sockfd_);
   if (thr_.joinable())
      thr_.join();
}

///////////////////////////////////////////////////////////////////////////////
void PythonCallback::remoteLoop(void)
{
   Command sendCmd;
   sendCmd.method_ = "registerCallback";
   sendCmd.ids_.push_back(bdvID_);
   BinaryDataObject bdo("waitOnBDV");
   sendCmd.args_.push_back(move(bdo));
   sendCmd.serialize();

   bool isReady = false;

   auto processCallback = [&](Arguments args)->bool
   {
      //LOGINFO << "entering callback process lambda";

      while (args.hasArgs())
      {
         auto&& cb = args.get<BinaryDataObject>();

         auto orderIter = orderMap_.find(cb.toStr());
         if(orderIter == orderMap_.end())
         {
            continue;
         } 

         switch (orderIter->second)
         {
            case CBO_continue:
               break;

            case CBO_NewBlock:
            {
               unsigned int newblock = args.get<IntType>().getVal();
               bdvPtr_->setTopBlock(newblock);

               if (newblock != 0)
                  run(BDMAction::BDMAction_NewBlock, &newblock, newblock);

               break;
            }

            case CBO_ZC:
            {
               auto&& lev = args.get<LedgerEntryVector>();
               auto leVec = lev.toVector();

               run(BDMAction::BDMAction_ZC, &leVec, 0);

               break;
            }

            case CBO_BDV_Refresh:
            {
               auto&& refreshType = args.get<IntType>();
               auto&& idVec = args.get<BinaryDataVector>();

               auto refresh = BDV_refresh(refreshType.getVal());
   
               if (refresh != BDV_filterChanged)
                  run(BDMAction::BDMAction_Refresh, (void*)&idVec.get(), 0);
               else
               {
                  vector<BinaryData> bdvec;
                  bdvec.push_back(BinaryData("wallet_filter_changed"));
                  run(BDMAction::BDMAction_Refresh, (void*)&bdvec, 0);
               }

               break;
            }

            case CBO_BDM_Ready:
            {
               isReady = true;

               sendCmd.args_.clear();
               BinaryDataObject status("getStatus");
               sendCmd.args_.push_back(move(status));
               sendCmd.serialize();

               unsigned int topblock = args.get<IntType>().getVal();
               bdvPtr_->setTopBlock(topblock);

               run(BDMAction::BDMAction_Ready, nullptr, topblock);

               break;
            }

            case CBO_progress:
            {
               auto&& pd = args.get<ProgressData>();
               progress(pd.phase_, pd.wltIDs_, pd.progress_,
                  pd.time_, pd.numericProgress_);

               break;
            }

            case CBO_terminate:
            {
               //shut down command from server
               return false;
            }

            case CBO_NodeStatus:
            {
               auto&& serData = args.get<BinaryDataObject>();
               NodeStatusStruct nss;
               nss.deserialize(serData.get());

               run(BDMAction::BDMAction_NodeStatus, &nss, 0);
               break;
            }

            case CBO_BDV_Error:
            {
               auto&& serData = args.get<BinaryDataObject>();
               BDV_Error_Struct bdvErr;
               bdvErr.deserialize(serData.get());

               run(BDMAction::BDMAction_BDV_Error, &bdvErr, 0);
               break;
            }

            default:
               continue;
         }
      }

      return true;
   };

   while (run_)
   {
      try
      {
         auto&& retval = sock_->writeAndRead(sendCmd.command_);
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

///////////////////////////////////////////////////////////////////////////////
//
// ProcessMutex
//
///////////////////////////////////////////////////////////////////////////////
ProcessMutex::~ProcessMutex()
{}

///////////////////////////////////////////////////////////////////////////////
bool ProcessMutex::acquire()
{
   {
      string str;
      if (test(str))
         return false;
   }

   auto holdldb = [this]()
   {
      this->hodl();
   };

   holdThr_ = thread(holdldb);
   return true;
}

///////////////////////////////////////////////////////////////////////////////
bool ProcessMutex::test(const string& uriLink)
{
   auto sock = DedicatedBinarySocket(addr_, port_);

   if (!sock.openSocket(false))
      return false;

   try
   {
      BinaryWriter bw;
      BinaryDataRef bdr;
      bdr.setRef(uriLink);

      bw.put_var_int(uriLink.size());
      bw.put_BinaryDataRef(bdr);
      auto bwRef = bw.getDataRef();

      //serialize argv
      sock.writeToSocket((void*)bwRef.getPtr(), bwRef.getSize());
   }
   catch (...)
   {
      return false;
   }
   
   return true;
}

///////////////////////////////////////////////////////////////////////////////
void ProcessMutex::hodl()
{
   auto server = make_unique<ListenServer>(addr_, port_);
   
   auto readLdb = [this](vector<uint8_t> data, exception_ptr eptr)->bool
   {
      if (data.size() == 0 || eptr != nullptr)
         return false;

      //unserialize urilink
      string urilink;

      try
      {
         BinaryDataRef bdr(&data[0], data.size());
         BinaryRefReader brr(bdr);

         auto len = brr.get_var_int();
         auto uriRef = brr.get_BinaryDataRef(len);

         urilink = move(string((char*)uriRef.getPtr(), len));
      }
      catch (...)
      {
         return false;
      }

      //callback
      mutexCallback(urilink);

      //return false to close the socket
      return false;
   };

   server->start(readLdb);
   server->join();
}
