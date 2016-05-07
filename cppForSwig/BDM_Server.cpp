////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2016, goatpig.                                              //
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //                                      
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#include "BDM_Server.h"
#include "BDM_seder.h"


///////////////////////////////////////////////////////////////////////////////
void BDV_Server_Object::buildMethodMap()
{
   //registerCallback
   auto registerCallback = [this]
      (const vector<string>& ids, Arguments& args)->Arguments
   {
      return this->cb_.respond();
   };

   methodMap_["registerCallback"] = registerCallback;

   //goOnline
   auto goOnline = [this]
      (const vector<string>& ids, Arguments& args)->Arguments
   {
      this->startThreads();

      Arguments retarg;
      return retarg;
   };

   methodMap_["goOnline"] = goOnline;

   //getTopBlockHeight
   auto getTopBlockHeight = [this]
      (const vector<string>& ids, Arguments& args)->Arguments
   {
      auto retVal = this->getTopBlockHeight();
      Arguments retarg;
      retarg.push_back(retVal);
      return retarg;
   };

   methodMap_["getTopBlockHeight"] = getTopBlockHeight;

   //getHistoryPage
   auto getHistoryPage = [this]
      (const vector<string>& ids, Arguments& args)->Arguments
   {
      if (ids.size() != 2)
         throw runtime_error("unexpected id count");

      auto& delegateID = ids[1];

      auto delegateIter = delegateMap_.find(delegateID);
      if (delegateIter == delegateMap_.end())
         throw runtime_error("unknown delegateID");

      auto& delegateObject = delegateIter->second;

      auto arg0 = args.get<unsigned int>();

      auto&& retVal = delegateObject.getHistoryPage(arg0);

      LedgerEntryVector lev;
      for (auto& le : retVal)
      {
         LedgerEntryData led(le.getWalletID(),
            le.getValue(), le.getBlockNum(), le.getTxHash(),
            le.getIndex(), le.getTxTime(), le.isCoinbase(),
            le.isSentToSelf(), le.isChangeBack());
         lev.push_back(move(led));
      }

      Arguments retarg;
      retarg.push_back(move(lev));
      return retarg;
   };

   methodMap_["getHistoryPage"] = getHistoryPage;

   //registerWallet
   auto registerWallet = [this]
      (const vector<string>& ids, Arguments& args)->Arguments
   {
      auto&& id = args.get<string>();
      auto&& scrAddrVec = args.get<BinaryDataVector>();
      auto&& isNew = args.get<unsigned int>();

      uint32_t retVal = 
         this->registerWallet(scrAddrVec.get(), id, isNew);
      
      Arguments retarg;
      retarg.push_back(retVal);
      return retarg;
   };

   methodMap_["registerWallet"] = registerWallet;

   //registerLockbox
   auto registerLockbox = [this]
      (const vector<string>& ids, Arguments& args)->Arguments
   {
      auto&& id = args.get<string>();
      auto&& scrAddrVec = args.get<BinaryDataVector>();
      auto&& isNew = args.get<unsigned int>();

      uint32_t retVal =
         this->registerLockbox(scrAddrVec.get(), id, isNew) != nullptr;

      Arguments retarg;
      retarg.push_back(retVal);
      return retarg;
   };

   methodMap_["registerLockbox"] = registerLockbox;

   //getLedgerDelegateForWallets
   auto getLedgerDelegateForWallets = [this]
      (const vector<string>& ids, Arguments& args)->Arguments
   {
      auto&& ledgerdelegate = this->getLedgerDelegateForWallets();
      string id = SecureBinaryData().GenerateRandom(5).toHexStr();

      this->delegateMap_.insert(make_pair(id, ledgerdelegate));

      Arguments retarg;
      retarg.push_back(id);
      return retarg;
   };

   methodMap_["getLedgerDelegateForWallets"] = getLedgerDelegateForWallets;

   //getLedgerDelegateForLockboxes
   auto getLedgerDelegateForLockboxes = [this]
      (const vector<string>& ids, Arguments& args)->Arguments
   {
      auto&& ledgerdelegate = this->getLedgerDelegateForLockboxes();
      string id = SecureBinaryData().GenerateRandom(5).toHexStr();

      this->delegateMap_.insert(make_pair(id, ledgerdelegate));

      Arguments retarg;
      retarg.push_back(id);
      return retarg;
   };

   methodMap_["getLedgerDelegateForLockboxes"] = getLedgerDelegateForLockboxes;

   //getFullBalance
   auto getFullBalance = [this]
      (const vector<string>& ids, Arguments& args)->Arguments
   {
      if (ids.size() != 2)
         throw runtime_error("unexpected id count");

      auto& walletId = ids[1];
      BinaryData bdId((uint8_t*)walletId.c_str(), walletId.size());
      shared_ptr<BtcWallet> wltPtr = nullptr;
      for (int i = 0; i < this->groups_.size(); i++)
      {
         auto wltIter = this->groups_[i].wallets_.find(bdId);
         if (wltIter != this->groups_[i].wallets_.end())
            wltPtr = wltIter->second;
      }

      if (wltPtr == nullptr)
         throw runtime_error("unknown wallet/lockbox ID");

      auto balance = wltPtr->getFullBalance();

      Arguments retarg;
      retarg.push_back(balance);
      return retarg;
   };

   methodMap_["getFullBalance"] = getFullBalance;

   //getSpendableBalance
   auto getSpendableBalance = [this]
      (const vector<string>& ids, Arguments& args)->Arguments
   {
      if (ids.size() != 2)
         throw runtime_error("unexpected id count");

      auto& walletId = ids[1];
      BinaryData bdId((uint8_t*)walletId.c_str(), walletId.size());
      shared_ptr<BtcWallet> wltPtr = nullptr;
      for (int i = 0; i < this->groups_.size(); i++)
      {
         auto wltIter = this->groups_[i].wallets_.find(bdId);
         if (wltIter != this->groups_[i].wallets_.end())
            wltPtr = wltIter->second;
      }

      if (wltPtr == nullptr)
         throw runtime_error("unknown wallet/lockbox ID");

      auto height = args.get<uint32_t>();
      auto ignorezc = args.get<unsigned int>();

      auto balance = wltPtr->getSpendableBalance(height, ignorezc);

      Arguments retarg;
      retarg.push_back(balance);
      return retarg;
   };

   methodMap_["getSpendableBalance"] = getSpendableBalance;

   //getUnconfirmedBalance
   auto getUnconfirmedBalance = [this]
      (const vector<string>& ids, Arguments& args)->Arguments
   {
      if (ids.size() != 2)
         throw runtime_error("unexpected id count");

      auto& walletId = ids[1];
      BinaryData bdId((uint8_t*)walletId.c_str(), walletId.size());
      shared_ptr<BtcWallet> wltPtr = nullptr;
      for (int i = 0; i < this->groups_.size(); i++)
      {
         auto wltIter = this->groups_[i].wallets_.find(bdId);
         if (wltIter != this->groups_[i].wallets_.end())
            wltPtr = wltIter->second;
      }

      if (wltPtr == nullptr)
         throw runtime_error("unknown wallet/lockbox ID");

      auto height = args.get<uint32_t>();
      auto ignorezc = args.get<unsigned int>();

      auto balance = wltPtr->getUnconfirmedBalance(height, ignorezc);

      Arguments retarg;
      retarg.push_back(balance);
      return retarg;
   };

   methodMap_["getUnconfirmedBalance"] = getUnconfirmedBalance;

   //hasHeaderWithHash
   auto hasHeaderWithHash = [this]
      (const vector<string>& ids, Arguments& args)->Arguments
   {
      if (ids.size() != 1)
         throw runtime_error("unexpected id count");

      auto hash = args.get<BinaryDataObject>();

      unsigned int hasHash = 
         this->blockchain().hasHeaderWithHash(hash.get());

      Arguments retarg;
      retarg.push_back(hasHash);
      return retarg;
   };

   methodMap_["hasHeaderWithHash"] = hasHeaderWithHash;
}

///////////////////////////////////////////////////////////////////////////////
const shared_ptr<BDV_Server_Object>& Clients::get(const string& id) const
{
   auto bdvmap = BDVs_.get();
   auto iter = bdvmap->find(id);
   if (iter == bdvmap->end())
      throw runtime_error("unknown BDVid");

   return iter->second;
}

///////////////////////////////////////////////////////////////////////////////
Arguments Clients::runCommand(const string& cmdStr)
{
   Command cmdObj(cmdStr);
   cmdObj.deserialize();
   if (cmdObj.method_ == "registerBDV")
      return registerBDV();

   //find the BDV and method
   if (cmdObj.ids_.size() == 0)
      throw runtime_error("malformed command");

   auto bdv = get(cmdObj.ids_[0]);

   //execute command
   return bdv->executeCommand(cmdObj.method_, cmdObj.ids_, cmdObj.args_);
}

///////////////////////////////////////////////////////////////////////////////
Arguments Clients::registerBDV()
{
   shared_ptr<BDV_Server_Object> newBDV
      = make_shared<BDV_Server_Object>(bdmT_);

   string newID(newBDV->getID());

   BDVs_.addBdv(newID, newBDV);

   LOGINFO << "registered bdv: " << newID;

   Arguments args;
   args.push_back(newID);
   return args;
}

///////////////////////////////////////////////////////////////////////////////
void Clients::maintenanceThread(void) const
{
   if (bdmT_ == nullptr)
      throw runtime_error("invalid BDM thread ptr");

   while (1)
   {
      try
      { 
         auto&& reorgState = bdmT_->bdm()->newBlocksStack_.get();
         auto bdvmap = BDVs_.get();

         for (auto& bdv : *bdvmap)
         {
            BDV_Action_Struct action;
            action.action_ = BDV_NewBlock;
            unique_ptr<BDV_Notification> bdvdata =
               make_unique<BDV_Notification_NewBlock>(reorgState);

            bdv.second->notificationStack_.push_back(move(action));
         }
      }
      catch (IsEmpty&)
      {
         break;
      }
   }
}

///////////////////////////////////////////////////////////////////////////////
Arguments BDV_Server_Object::executeCommand(const string& method,
   const vector<string>& ids, Arguments& args)
{
   //make sure the method exists
   auto iter = methodMap_.find(method);
   if (iter == methodMap_.end())
      throw runtime_error("error: unknown method");

   return iter->second(ids, args);
}

///////////////////////////////////////////////////////////////////////////////
void FCGI_Server::init()
{
   sockfd_ = FCGX_OpenSocket("localhost:9050", 10);
   if (sockfd_ == -1)
      throw runtime_error("failed to create FCGI listen socket");
}

///////////////////////////////////////////////////////////////////////////////
void FCGI_Server::enterLoop()
{
   while (run_)
   {
      FCGX_Request* request = new FCGX_Request;
      FCGX_InitRequest(request, sockfd_, 0);
      int rc = FCGX_Accept_r(request);

      auto processRequestLambda = [this](FCGX_Request* req)->void
      {
         this->processRequest(req);
      };

      liveThreads_.fetch_add(1, memory_order_relaxed);
      thread thr(processRequestLambda, request);
      if (thr.joinable())
         thr.detach();

      //implement a thread recycling chain later
   }
}

///////////////////////////////////////////////////////////////////////////////
void FCGI_Server::processRequest(FCGX_Request* req)
{
   //extract the string command from the fgci request
   stringstream ss;
   stringstream retStream;
   char* content = nullptr;

   //pass to clients_
   char* content_length = FCGX_GetParam("CONTENT_LENGTH", req->envp);
   if (content_length != nullptr)
   {
      auto a = atoi(content_length);
      content = new char[a + 1];
      FCGX_GetStr(content, a, req->in);
      content[a] = 0;

      string contentStr(content);

      try
      {
         auto&& retVal = clients_.runCommand(contentStr);
         retStream << retVal.serialize();

         //print HTML header
         ss << "HTTP/1.1 200 OK\r\n";
         ss << "Content-Type: text/html; charset=UTF-8\r\n";
         ss << "Content-Length: " << retStream.str().size();
         ss << "\r\n\r\n";
      }
      catch (exception& e)
      {
         retStream << "error: " << e.what();
      }
   }
   else
   {
      retStream << "Error: empty request";
   }

   delete[] content;
   
   //print serialized retVal
   ss << retStream.str();

   auto&& retStr = ss.str();
   vector<pair<size_t, size_t>> msgOffsetVec;
   auto totalsize = retStr.size();
   size_t delim = 8176; //8192 (max fcgi packet) - 16 (2x fcgi header)
   size_t start = 0;

   while (totalsize > 0)
   {
      auto chunk = delim;
      if (chunk > totalsize)
         chunk = totalsize;

      msgOffsetVec.push_back(make_pair(start, chunk));
      start += chunk;
      totalsize -= chunk;
   }

   //get non const ptr of the message string since we will set temp null bytes
   //for the purpose of breaking down the string into FCGI sized packets
   char* ptr = const_cast<char*>(retStr.c_str());
   char prevVal = ptr[0];

   //complete FCGI request
   for (auto& offsetPair : msgOffsetVec)
   {
      //reset previous last byte to its original value;
      ptr[offsetPair.first] = prevVal;

      //save current last byte
      prevVal = ptr[offsetPair.first + offsetPair.second];

      //null terminate for this packet
      ptr[offsetPair.first + offsetPair.second] = 0;

      FCGX_FPrintF(req->out, ptr + offsetPair.first);
   }

   FCGX_Finish_r(req);

   delete req;

   liveThreads_.fetch_sub(1, memory_order_relaxed);
}


///////////////////////////////////////////////////////////////////////////////
BDV_Server_Object::BDV_Server_Object(
   BlockDataManagerThread *bdmT) :
   bdmT_(bdmT), BlockDataViewer(bdmT->bdm())
{
   bdvID_ = SecureBinaryData().GenerateRandom(10).toHexStr();
   buildMethodMap();
}

///////////////////////////////////////////////////////////////////////////////
void BDV_Server_Object::startThreads()
{
   auto thrLambda = [this](void)->void
   { this->maintenanceThread(); };

   tID_ = thread(thrLambda);
}

///////////////////////////////////////////////////////////////////////////////
void BDV_Server_Object::maintenanceThread(void)
{
   bdmPtr_->blockUntilReady();

   while (1)
   {
      bool isNew = false;
      set<BinaryData> scrAddrSet;
      map<string, walletRegStruct> wltMap;

      {
         unique_lock<mutex> lock(registerWalletMutex_);

         if (wltRegMap_.size() == 0)
            break;

         wltMap = move(wltRegMap_);
         wltRegMap_.clear();
      }

      //bundle addresses to register together
      for (auto& wlt : wltMap)
      {
         for (auto& scraddr : wlt.second.scrAddrVec)
            scrAddrSet.insert(scraddr);
      }

      //register address set with BDM
      auto&& waitOnFuture = bdmPtr_->registerAddressBatch(scrAddrSet, isNew);
      waitOnFuture.wait();

      //register actual wallets with BDV
      auto bdvPtr = (BlockDataViewer*)this;
      for (auto& wlt : wltMap)
      {
         //this should return when the wallet is registered, since all
         //underlying  addresses are already registered with the BDM
         bdvPtr->registerWallet(
            wlt.second.scrAddrVec, wlt.second.IDstr, wlt.second.isNew);
      }
   }

   BDV_Action_Struct firstScanAction;
   firstScanAction.action_ = BDV_Init;
   scanWallets(firstScanAction);

   Arguments args;
   args.push_back(move(string("BDM_Ready")));
   unsigned int topblock = blockchain().top().getBlockHeight();
   args.push_back(topblock);
   cb_.callback(move(args));

   while (1)
   {
      auto&& action_struct = notificationStack_.get();
      auto& action = action_struct.action_;

      scanWallets(action_struct);

      if (action == BDV_NewBlock)
      {
         //purge zc on new block

         Arguments args2;
         auto payload = 
            (BDV_Notification_NewBlock*)action_struct.payload_.get();
         uint32_t blocknum = 
            payload->reorgState_.newTop->getBlockHeight();

         args2.push_back(move(string("NewBlock")));
         args2.push_back(blocknum);
         cb_.callback(move(args2), OrderNewBlock);
      }
      else if (action == BDV_RefreshWallets)
      {
         //dont purge zc on refresh

         Arguments args2;
         args2.push_back(move(string("BDV_Refresh")));
         cb_.callback(move(args2), OrderRefresh);
      }
      else if (action == BDV_ZC)
      {
         //pass new zc to scan
      }
   }
}

///////////////////////////////////////////////////////////////////////////////
bool BDV_Server_Object::registerWallet(
   vector<BinaryData> const& scrAddrVec, string IDstr, bool wltIsNew)
{
   if (!run_.load(memory_order_relaxed))
   {
      //only run this code if the bdv maintenance thread hasn't started yet

      unique_lock<mutex> lock(registerWalletMutex_);

      //save data
      auto& wltregstruct = wltRegMap_[IDstr];

      wltregstruct.scrAddrVec = scrAddrVec;
      wltregstruct.IDstr = IDstr;
      wltregstruct.isNew = wltIsNew;

      return true;
   }
   else
   {
      //register wallet with BDV
      auto bdvPtr = (BlockDataViewer*)this;
      return bdvPtr->registerWallet(scrAddrVec, IDstr, wltIsNew) != nullptr;
   }
}

///////////////////////////////////////////////////////////////////////////////
void Callback::callback(Arguments&& cmd, OrderType type)
{
   {
      unique_lock<mutex> lock(mu_);
      //compress new block and refresh commands together
      cbOrder order(move(cmd), type);

      if (type != OrderOther)
      {
         deque<cbOrder> oldQueue = move(cbQueue_);
         cbQueue_.clear();
         for (auto& entry : oldQueue)
         {
            if (entry.otype_ != type)
               cbQueue_.push_back(move(entry));
         }
      }

      cbQueue_.push_back(move(order));
      if (cbQueue_.size() > maxQueue_)
         cbQueue_.pop_front();
   }

   emit();
}

///////////////////////////////////////////////////////////////////////////////
void SocketCallback::emit()
{
   cv_.notify_all();
}

///////////////////////////////////////////////////////////////////////////////
Arguments SocketCallback::respond()
{
   Arguments arg;

   {
      unique_lock<mutex> lock(mu_);

      if (cbQueue_.size() == 0)
         cv_.wait_for(lock, chrono::seconds(600));
      
      //TODO: deplete callback queue (instead of just pop the front)
      //consider just finishing the fcgi request in case there is no data
      //to push back to the client

      if (cbQueue_.size() == 0)
         return arg;

      arg = move(cbQueue_.front().order_);
      cbQueue_.pop_front();
   }

   //send it
   stringstream ss;
   return arg;
}
