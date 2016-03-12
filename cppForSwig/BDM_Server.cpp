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

      auto arg0 = args.get<int>();

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
   unique_lock<mutex> lock(mu_);
   auto iter = BDVs_.find(id);
   if (iter == BDVs_.end())
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
      = make_shared<BDV_Server_Object>(bdmT_, BDM_notifier_);

   string newID(newBDV->getID());

   {
      unique_lock<mutex> lock(mu_);
      BDVs_[newID] = newBDV;
   }
   
   LOGINFO << "registered bdv: " << newID;

   Arguments args;
   args.push_back(newID);
   return args;
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
   if (FCGX_Init())
      throw runtime_error("failed to initialize FCGI engine");

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

   //complete FCGI request
   FCGX_FPrintF(req->out, ss.str().c_str());
   FCGX_Finish_r(req);

   delete req;

   liveThreads_.fetch_sub(1, memory_order_relaxed);
}


///////////////////////////////////////////////////////////////////////////////
BDV_Server_Object::BDV_Server_Object(
   BlockDataManagerThread *bdmT, shared_ptr<BDV_Notifier> nf) :
   bdmT_(bdmT), BlockDataViewer(bdmT->bdm()), BDM_notifier_(nf)
{
   run_.store(false, std::memory_order_relaxed);

   bdvID_ = SecureBinaryData().GenerateRandom(10).toHexStr();
   buildMethodMap();
}

///////////////////////////////////////////////////////////////////////////////
void BDV_Server_Object::startThreads()
{
   auto thrLambda = [this](void)->void
   { this->maintenanceThread(); };

   auto listenerLambda = [this](void)->void
   { this->BDM_listener(); };

   tID_ = thread(thrLambda);

   thread listener(listenerLambda);
   if (listener.joinable())
      listener.detach();
}

///////////////////////////////////////////////////////////////////////////////
BDV_Action BDV_Server_Object::scan(void)
{
   bool scanAnyway = false;
   //check for ZC

   //check for newly registered wallets or addresses
   for (auto& grp : groups_)
   {
      ReadWriteLock::ReadLock rl(grp.lock_);
      for (auto& wlt : values(grp.wallets_))
      {
         if (wlt->getMergeFlag() == BtcWallet::MergeWallet::NeedsMerging)
         {
            scanAnyway = true;
            break;
         }
      }
   }

   BDV_refresh refresh = BDV_dontRefresh;
   vector<BinaryData> refreshIDVec;
   if (refresh_ != BDV_dontRefresh)
   {
      unique_lock<mutex> lock(refreshLock_);

      refresh = refresh_;
      refresh_ = BDV_dontRefresh;

      vector<BinaryData> refreshIDVec;
      for (const auto& refreshID : refreshIDSet_)
         refreshIDVec.push_back(refreshID);

      refreshIDSet_.clear();
      scanAnyway = true;
   }

   auto prev = top_;
   top_ = bdmT_->topBH();
   if (!scanAnyway)
   {
      if (top_ == prev)
         return BDV_NoAction;
   }

   scanWallets(prev->getBlockHeight(), top_->getBlockHeight(), refresh);

   if (prev == top_ && refresh != BDV_dontRefresh)
      return BDV_RefreshWallets;

   return BDV_NewBlock;
}

///////////////////////////////////////////////////////////////////////////////
void BDV_Server_Object::BDM_listener(void)
{
   mutex mu;
   unique_lock<mutex> lock(mu);
   while (run_)
   {
      BDM_notifier_->wait(&lock);
      localNotifier_.notify();
   }
}

///////////////////////////////////////////////////////////////////////////////
void BDV_Server_Object::maintenanceThread(void)
{
   run_.store(true, std::memory_order_relaxed);

   while (!isBDMReady())
   {
      //poll BDM state while it's still initializing
      usleep(1000);
   }

   /***Wait on wallet side scans if any. Usual registration process is:
   1) register wallets
   2) start BDV thread

   Wallets may still be in the side scan process when we get this far
   ***/

   {
      unique_lock<mutex> lock(registerWalletMutex_);
      for (auto& wltregstruct : wltRegMap_)
         wltregstruct.second.future_.wait();

      wltRegMap_.clear();
   }

   top_ = bdmT_->topBH();
   scanWallets(0, top_->getBlockHeight());
   Arguments args;
   args.push_back(move(string("BDM_Ready")));
   cb_.callback(move(args));

   mutex mu;
   unique_lock<mutex> lock(mu);

   while (run_)
   {
      auto action = scan();
      if (action == BDV_NoAction)
      {
         localNotifier_.wait(&lock);
         continue;
      }

      if (action == BDV_NewBlock)
      {
         Arguments args2;
         uint32_t blocknum = top_->getBlockHeight();
         args2.push_back(move(string("NewBlock")));
         args2.push_back(blocknum);
         cb_.callback(move(args2), OrderNewBlock);
      }
      else if (action == BDV_RefreshWallets)
      {
         Arguments args2;
         args2.push_back(move(string("BDV_Refresh")));
         cb_.callback(move(args2), OrderRefresh);
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

      //init future
      auto& wltregstruct = wltRegMap_[IDstr];
      wltregstruct.future_ = wltregstruct.promise_.get_future();

      //create lambda
      auto cbPromise = [&](void)->void
      {
         //fulfill promise
         wltregstruct.promise_.set_value(true);
      };

      auto wltPtr = createWallet(IDstr);

      if (wltPtr == nullptr)
         return false;

      //set lambda
      wltPtr->setRegistrationCallback(cbPromise);
   }

   //register wallet with BDV
   auto bdvPtr = (BlockDataViewer*)this;
   return bdvPtr->registerWallet(scrAddrVec, IDstr, wltIsNew) != nullptr;
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
