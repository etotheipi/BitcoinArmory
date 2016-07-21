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
      auto cbPtr = this->cb_;
      if (cbPtr == nullptr || !cbPtr->isValid())
         return Arguments();

      auto&& retval = this->cb_->respond();

      if (!retval.hasArgs())
         LOGINFO << "returned empty callback packet";

      return retval;
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
      retarg.push_back(move(retVal));
      return retarg;
   };

   methodMap_["getTopBlockHeight"] = getTopBlockHeight;

   //getHistoryPage
   auto getHistoryPage = [this]
      (const vector<string>& ids, Arguments& args)->Arguments
   {
      if (ids.size() < 2)
         throw runtime_error("unexpected id count");

      auto toLedgerEntryVector = []
         (vector<LedgerEntry>& leVec)->LedgerEntryVector
      {
         LedgerEntryVector lev;
         for (auto& le : leVec)
         {
            LedgerEntryData led(le.getWalletID(),
               le.getValue(), le.getBlockNum(), le.getTxHash(),
               le.getIndex(), le.getTxTime(), le.isCoinbase(),
               le.isSentToSelf(), le.isChangeBack());
            lev.push_back(move(led));
         }

         return lev;
      };

      auto& nextID = ids[1];

      //is it a ledger from a delegate?
      auto delegateIter = delegateMap_.find(nextID);
      if (delegateIter != delegateMap_.end())
      {
         
         auto& delegateObject = delegateIter->second;

         auto arg0 = args.get<unsigned int>();

         auto&& retVal = delegateObject.getHistoryPage(arg0);

         Arguments retarg;
         retarg.push_back(move(toLedgerEntryVector(retVal)));
         return retarg;
      }
      
      //or a wallet?
      auto theWallet = getWalletOrLockbox(nextID);
      if (theWallet != nullptr)
      {
         //is it an address ledger?
         if (ids.size() == 3)
         {

         }

         unsigned pageId = UINT32_MAX;
         BinaryData txHash;

         //is a page or a hash
         try
         {
            pageId = args.get<unsigned int>();
         }
         catch (runtime_error&)
         {
            auto&& bdo = args.get<BinaryDataObject>();
            txHash = bdo.get();
         }
         
         LedgerEntryVector resultLev;
         if (pageId != UINT32_MAX)
         {
            auto&& retVal = theWallet->getHistoryPageAsVector(pageId);
            resultLev = move(toLedgerEntryVector(retVal));
         }
         else
         {
            pageId = 0;
            while (1)
            {
               auto&& ledgerMap = theWallet->getHistoryPage(pageId++);
               for (auto& lePair : ledgerMap)
               {
                  auto& leHash = lePair.second.getTxHash();
                  if (leHash == txHash)
                  {
                     auto& le = lePair.second;

                     LedgerEntryData led(le.getWalletID(),
                     le.getValue(), le.getBlockNum(), le.getTxHash(),
                     le.getIndex(), le.getTxTime(), le.isCoinbase(),
                     le.isSentToSelf(), le.isChangeBack());

                     LedgerEntryVector lev;
                     lev.push_back(move(led));

                     Arguments retarg;
                     retarg.push_back(move(lev));
                     return retarg;
                  }
               }

            }
         }
         
         Arguments retarg;
         retarg.push_back(move(resultLev));
         return retarg;
      }

      throw runtime_error("invalid id");
      return Arguments();
   };

   methodMap_["getHistoryPage"] = getHistoryPage;

   //registerWallet
   auto registerWallet = [this]
      (const vector<string>& ids, Arguments& args)->Arguments
   {
      if (ids.size() != 1)
         throw runtime_error("unexpected id count");

      auto&& id = args.get<string>();
      auto&& scrAddrVec = args.get<BinaryDataVector>();
      auto&& isNew = args.get<unsigned int>();

      uint32_t retVal = 
         this->registerWallet(scrAddrVec.get(), id, isNew);
      
      Arguments retarg;
      retarg.push_back(move(retVal));
      return retarg;
   };

   methodMap_["registerWallet"] = registerWallet;

   //registerLockbox
   auto registerLockbox = [this]
      (const vector<string>& ids, Arguments& args)->Arguments
   {
      if (ids.size() != 1)
         throw runtime_error("unexpected id count");

      auto&& id = args.get<string>();
      auto&& scrAddrVec = args.get<BinaryDataVector>();
      auto&& isNew = args.get<unsigned int>();

      uint32_t retVal = this->registerLockbox(scrAddrVec.get(), id, isNew);

      Arguments retarg;
      retarg.push_back(move(retVal));
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
      retarg.push_back(move(id));
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
      retarg.push_back(move(id));
      return retarg;
   };

   methodMap_["getLedgerDelegateForLockboxes"] = getLedgerDelegateForLockboxes;

   //getBalances
   auto getBalances = [this]
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

      auto balance_full = wltPtr->getFullBalance();
      auto balance_spen = wltPtr->getSpendableBalance(height, ignorezc);
      auto balance_unco = wltPtr->getUnconfirmedBalance(height, ignorezc);

      Arguments retarg;
      retarg.push_back(move(balance_full));
      retarg.push_back(move(balance_spen));
      retarg.push_back(move(balance_unco));
      return retarg;
   };

   methodMap_["getBalances"] = getBalances;

   //hasHeaderWithHash
   auto hasHeaderWithHash = [this]
      (const vector<string>& ids, Arguments& args)->Arguments
   {
      if (ids.size() != 1)
         throw runtime_error("unexpected id count");

      auto&& hash = args.get<BinaryDataObject>();

      unsigned int hasHash = 
         this->blockchain().hasHeaderWithHash(hash.get());

      Arguments retarg;
      retarg.push_back(move(hasHash));
      return retarg;
   };

   methodMap_["hasHeaderWithHash"] = hasHeaderWithHash;

   //getSpendableTxOutListForValue
   auto getSpendableTxOutListForValue = [this]
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
         throw runtime_error("unknown wallet or lockbox ID");

      auto value = args.get<uint64_t>();
      auto ignorezc = args.get<unsigned int>();

      auto&& utxoVec = wltPtr->getSpendableTxOutListForValue(value, ignorezc);

      UtxoVector retVec;
      for (auto& utxo : utxoVec)
      {
         UTXO entry(utxo.value_, utxo.txHeight_, utxo.txOutIndex_,
            move(utxo.txHash_), move(utxo.script_));

         retVec.push_back(move(entry));
      }

      Arguments retarg;
      retarg.push_back(move(retVec));
      return retarg;
   };

   methodMap_["getSpendableTxOutListForValue"] = getSpendableTxOutListForValue;

   //broadcastZC
   auto broadcastZC = [this]
      (const vector<string>& ids, Arguments& args)->Arguments
   {
      if (ids.size() != 1)
         throw runtime_error("unexpected id count");

      auto&& rawTx = args.get<BinaryDataObject>();

      this->zeroConfCont_->broadcastZC(rawTx.get());

      Arguments retarg;
      return retarg;
   };

   methodMap_["broadcastZC"] = broadcastZC;

   //getAddrTxnCounts
   auto getAddrTxnCounts = [this]
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
         throw runtime_error("unknown wallet or lockbox ID");

      auto&& countMap = wltPtr->getTotalTxnCount();

      Arguments retarg;
      auto&& mapSize = countMap.size();
      retarg.push_back(move(mapSize));

      for (auto count : countMap)
      {
         BinaryDataObject bdo(move(count.first));
         retarg.push_back(move(bdo));
         retarg.push_back(move(count.second));
      }

      return retarg;
   };

   methodMap_["getAddrTxnCounts"] = getAddrTxnCounts;

   //getTxByHash
   auto getTxByHash = [this]
      (const vector<string>& ids, Arguments& args)->Arguments
   {
      if (ids.size() != 1)
         throw runtime_error("unexpected id count");

      auto&& txHash = args.get<BinaryDataObject>();
      auto&& retval = this->getTxByHash(txHash.get());
      BinaryDataObject bdo(move(retval.serializeWithRBFFlag()));

      Arguments retarg;
      retarg.push_back(move(bdo));
      return move(retarg);
   };

   methodMap_["getTxByHash"] = getTxByHash;
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
   if (!run_.load(memory_order_relaxed))
      return Arguments();

   if (bdmT_->bdm()->hasException())
   {
      rethrow_exception(bdmT_->bdm()->getException());
   }

   Command cmdObj(cmdStr);
   cmdObj.deserialize();
   if (cmdObj.method_ == "registerBDV")
   {
      return registerBDV(cmdObj.args_);
   }
   else if (cmdObj.method_ == "unregisterBDV")
   {
      if (cmdObj.ids_.size() != 1)
         throw runtime_error("invalid arg count for unregisterBDV");

      unregisterBDV(cmdObj.ids_[0]);
      return Arguments();
   }
   else if (cmdObj.method_ == "shutdown")
   {
      auto& thisSpawnId = bdmT_->bdm()->config().spawnID_;
      if (thisSpawnId.size() == 0)
         return Arguments();

      //if thisSpawnId is empty, return
      //if the spawnId provided with the shutdown command is emtpy, 
      //mismatches, or is missing entirely (get() will throw), return

      try
      {
         auto&& spawnId = cmdObj.args_.get<string>();
         if ((spawnId.size() == 0) || (spawnId.compare(thisSpawnId) != 0))
            throw runtime_error("spawnId mismatch");
      }
      catch (...)
      {
         return Arguments();
      }

      auto shutdownLambda = [this](void)->void
      {
         this->exitRequestLoop();
      };

      //run shutdown sequence in its own thread so that the fcgi listen
      //loop can exit properly.
      thread shutdownThr(shutdownLambda);
      if (shutdownThr.joinable())
         shutdownThr.detach();

      return Arguments();
   }

   //find the BDV and method
   if (cmdObj.ids_.size() == 0)
      throw runtime_error("malformed command");

   auto bdv = get(cmdObj.ids_[0]);

   //execute command
   return bdv->executeCommand(cmdObj.method_, cmdObj.ids_, cmdObj.args_);
}

///////////////////////////////////////////////////////////////////////////////
void Clients::shutdown()
{
   /*shutdown sequence*/
   
   //exit BDM maintenance thread
   bdmT_->shutdown();

   //shutdown ZC container
   bdmT_->bdm()->disableZeroConf();

   //terminate all ongoing scans
   bdmT_->bdm()->terminateAllScans();

   bdmT_->cleanUp();
}

///////////////////////////////////////////////////////////////////////////////
void Clients::exitRequestLoop()
{
   /*terminate request processing loop*/
   LOGINFO << "proceeding to shutdown";

   //shutdown node
   bdmT_->bdm()->shutdownNode();

   //prevent all new commands from running
   run_.store(false, memory_order_relaxed);

   //shutdown Clients gc thread
   gcCommands_.completed();

   //cleanup all BDVs
   unregisterAllBDVs();

   //shutdown loop on FcgiServer side
   fcgiShutdownCallback_();
}

///////////////////////////////////////////////////////////////////////////////
void Clients::unregisterAllBDVs()
{
   auto bdvs = BDVs_.get();
   BDVs_.clear();

   for (auto& bdv : *bdvs)
      bdv.second->haltThreads();
}

///////////////////////////////////////////////////////////////////////////////
Arguments Clients::registerBDV(Arguments& arg)
{
   try
   {
      auto&& magic_word = arg.get<BinaryDataObject>();
      auto& thisMagicWord = bdmT_->bdm()->config().magicBytes;

      if (thisMagicWord != magic_word.get())
         throw runtime_error("");
   }
   catch (...)
   {
      throw DbErrorMsg("invalid magic word");
   }


   shared_ptr<BDV_Server_Object> newBDV
      = make_shared<BDV_Server_Object>(bdmT_);

   string newID(newBDV->getID());

   //add to BDVs map
   BDVs_.insert(move(make_pair(newID, newBDV)));

   //register with ZC container
   bdmT_->bdm()->registerBDVwithZCcontainer(newBDV);

   LOGINFO << "registered bdv: " << newID;

   Arguments args;
   args.push_back(move(newID));
   return args;
}

///////////////////////////////////////////////////////////////////////////////
void Clients::unregisterBDV(const string& bdvId)
{
   shared_ptr<BDV_Server_Object> bdvPtr;

   //shutdown bdv threads
   {
      auto bdvMap = BDVs_.get();
      auto bdvIter = bdvMap->find(bdvId);
      if (bdvIter == bdvMap->end())
         return;

      //copy shared_ptr and unregister from bdv map
      bdvPtr = bdvIter->second;
      BDVs_.erase(bdvId);
   }

   //unregister from ZC container
   bdmT_->bdm()->unregisterBDVwithZCcontainer(bdvId);

   //shut down threads
   bdvPtr->haltThreads();

   //we are done
   LOGINFO << "unregistered bdv: " << bdvId;
}


///////////////////////////////////////////////////////////////////////////////
void Clients::maintenanceThread(void) const
{
   if (bdmT_ == nullptr)
      throw runtime_error("invalid BDM thread ptr");

   while (1)
   {
      bool hasNewTop = false;
      Blockchain::ReorganizationState reorgState;

      try
      {
         reorgState = move(bdmT_->bdm()->newBlocksStack_.get(chrono::seconds(120)));
         hasNewTop = true;
      }
      catch (StackTimedOutException&)
      {
         //nothing to do
      }
      catch (StopBlockingLoop&)
      {
         //shutdown gc thread
         gcCommands_.push_back(false);

         return;
      }

      //trigger gc thread
      gcCommands_.push_back(true);
      
      //don't go any futher if there is no new top
      if (!hasNewTop)
         continue;

      auto bdvmap = BDVs_.get();

      for (auto& bdv : *bdvmap)
      {
         auto bdvdata = make_unique<BDV_Notification_NewBlock>(reorgState);
         BDV_Action_Struct action(BDV_NewBlock, move(bdvdata));
         bdv.second->notificationStack_.push_back(move(action));
      }
   }
}

///////////////////////////////////////////////////////////////////////////////
void Clients::garbageCollectorThread(void)
{
   while (1)
   {
      try
      {
         bool command = gcCommands_.get();
         if(!command)
            return;
      }
      catch (IsEmpty&)
      {
         return;
      }

      vector<string> bdvToDelete;
      
      {
         auto bdvmap = BDVs_.get();

         for (auto& bdvPair : *bdvmap)
         {
            if (!bdvPair.second->cb_->isValid())
               bdvToDelete.push_back(bdvPair.first);
         }
      }

      for (auto& bdvID : bdvToDelete)
      {
         unregisterBDV(bdvID);
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
void FCGI_Server::haltFcgiLoop()
{
   /*** to exit the FCGI loop we need to shutdown the FCGI lib as a whole
   (otherwise accept will keep on blocking until a new fcgi request is 
   received. Shutting down the lib calls WSACleanUp in Windows, which will
   terminate all networking capacity for the process.

   This means the node P2P connection will crash if it isn't cleaned up first.
   ***/

   //shutdown loop
   run_ = 0;

   //spin lock until all requests are closed
   while (liveThreads_.load(memory_order_relaxed) != 0);

   //close the listening socket
   closesocket(sockfd_);
   OS_LibShutdown();
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

      //TODO: implement thread recycling
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

      //print HTML header
      ss << "HTTP/1.1 200 OK\r\n";
      ss << "Content-Type: text/html; charset=UTF-8\r\n";

      try
      {
         auto&& retVal = clients_.runCommand(contentStr);
         retStream << retVal.serialize();

      }
      catch (exception& e)
      {
         ErrorType err(e.what());
         Arguments arg;
         arg.push_back(move(err));

         retStream << arg.serialize();
      }
      catch (DbErrorMsg &e)
      {
         ErrorType err(e.what());
         Arguments arg;
         arg.push_back(move(err));

         retStream << arg.serialize();
      }
      catch (...)
      {
         ErrorType err("unknown error");
         Arguments arg;
         arg.push_back(move(err));
         
         retStream << arg.serialize();
      }
      
      //complete HTML header
      ss << "Content-Length: " << retStream.str().size();
      ss << "\r\n\r\n";
   }
   else
   {
      FCGX_Finish_r(req);
      delete req;

      liveThreads_.fetch_sub(1, memory_order_relaxed);
      return;
   }

   delete[] content;
   
   //print serialized retVal
   ss << retStream.str();

   auto&& retStr = ss.str();
   vector<pair<size_t, size_t>> msgOffsetVec;
   auto totalsize = retStr.size();
   //8192 (one memory page) - 8 (1 fcgi header), also a multiple of 8
   size_t delim = 8184; 
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

   //complete FCGI request
   for (auto& offsetPair : msgOffsetVec)
      FCGX_PutStr(ptr + offsetPair.first, offsetPair.second, req->out);

   FCGX_Finish_r(req);

   delete req;

   liveThreads_.fetch_sub(1, memory_order_relaxed);
}


///////////////////////////////////////////////////////////////////////////////
BDV_Server_Object::BDV_Server_Object(
   BlockDataManagerThread *bdmT) :
   bdmT_(bdmT), BlockDataViewer(bdmT->bdm())
{
   cb_ = make_shared<SocketCallback>();
   isReadyFuture_ = isReadyPromise_.get_future();

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
void BDV_Server_Object::haltThreads()
{
   notificationStack_.terminate();

   if (tID_.joinable())
      tID_.join();

   cb_.reset();
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
      waitOnFuture.get();

      //register actual wallets with BDV
      auto bdvPtr = (BlockDataViewer*)this;
      for (auto& wlt : wltMap)
      {
         //this should return when the wallet is registered, since all
         //underlying  addresses are already registered with the BDM
         if (wlt.second.type_ == TypeWallet)
            bdvPtr->registerWallet(
               wlt.second.scrAddrVec, wlt.second.IDstr, wlt.second.isNew);
         else
            bdvPtr->registerLockbox(
               wlt.second.scrAddrVec, wlt.second.IDstr, wlt.second.isNew);
      }
   }

   //could a wallet registration event get lost in between the init loop 
   //and setting the promise?
   isReadyPromise_.set_value(true);

   BDV_Action_Struct firstScanAction(BDV_Init, nullptr);
   scanWallets(move(firstScanAction));

   Arguments args;
   args.push_back(move(string("BDM_Ready")));
   unsigned int topblock = blockchain().top().getBlockHeight();
   args.push_back(move(topblock));
   cb_->callback(move(args));

   while (1)
   {
      BDV_Action_Struct action_struct;
      try
      {
         action_struct = move(notificationStack_.get());
      }
      catch (IsEmpty&)
      {
         cb_->callback(Arguments(), OrderTerminate);
         break;
      }

      auto& action = action_struct.action_;

      scanWallets(action_struct);

      if (action == BDV_NewBlock)
      {
         Arguments args2;
         auto payload = 
            (BDV_Notification_NewBlock*)action_struct.payload_.get();
         uint32_t blocknum = 
            payload->reorgState_.newTop->getBlockHeight();

         args2.push_back(move(string("NewBlock")));
         args2.push_back(move(blocknum));
         cb_->callback(move(args2), OrderNewBlock);
      }
      else if (action == BDV_RefreshWallets)
      {
         //ignore refresh type and refreshID for now

         Arguments args2;
         args2.push_back(move(string("BDV_Refresh")));
         cb_->callback(move(args2), OrderRefresh);
      }
      else if (action == BDV_ZC)
      {
         //TODO: upgrade to reporting actual ZC to trigger tooltip notification
         //in front end, instead simple refresh
         Arguments args2;
         args2.push_back(move(string("BDV_Refresh")));
         cb_->callback(move(args2), OrderRefresh);
      }
   }
}

///////////////////////////////////////////////////////////////////////////////
void BDV_Server_Object::zcCallback(
   map<BinaryData, shared_ptr<map<BinaryData, TxIOPair>>> zcMap)
{
   auto notificationPtr = make_unique<BDV_Notification_ZC>(
      move(zcMap));

   BDV_Action_Struct action(BDV_ZC, move(notificationPtr));

   notificationStack_.push_back(move(action));
}

///////////////////////////////////////////////////////////////////////////////
bool BDV_Server_Object::registerWallet(
   vector<BinaryData> const& scrAddrVec, string IDstr, bool wltIsNew)
{
   if (isReadyFuture_.wait_for(chrono::seconds(0)) != future_status::ready)
   {
      //only run this code if the bdv maintenance thread hasn't started yet

      unique_lock<mutex> lock(registerWalletMutex_);

      //save data
      auto& wltregstruct = wltRegMap_[IDstr];

      wltregstruct.scrAddrVec = scrAddrVec;
      wltregstruct.IDstr = IDstr;
      wltregstruct.isNew = wltIsNew;
      wltregstruct.type_ = TypeWallet;

      return true;
   }

   //register wallet with BDV
   auto bdvPtr = (BlockDataViewer*)this;
   return bdvPtr->registerWallet(scrAddrVec, IDstr, wltIsNew) != nullptr;
}

///////////////////////////////////////////////////////////////////////////////
bool BDV_Server_Object::registerLockbox(
   vector<BinaryData> const& scrAddrVec, string IDstr, bool wltIsNew)
{
   if (isReadyFuture_.wait_for(chrono::seconds(0)) != future_status::ready)
   {
      //only run this code if the bdv maintenance thread hasn't started yet

      unique_lock<mutex> lock(registerWalletMutex_);

      //save data
      auto& wltregstruct = wltRegMap_[IDstr];

      wltregstruct.scrAddrVec = scrAddrVec;
      wltregstruct.IDstr = IDstr;
      wltregstruct.isNew = wltIsNew;
      wltregstruct.type_ = TypeLockbox;

      return true;
   }

   //register wallet with BDV
   auto bdvPtr = (BlockDataViewer*)this;
   return bdvPtr->registerLockbox(scrAddrVec, IDstr, wltIsNew) != nullptr;
}

///////////////////////////////////////////////////////////////////////////////
Arguments SocketCallback::respond()
{
   unique_lock<mutex> lock(mu_, defer_lock);

   if (!lock.try_lock())
   {
      Arguments arg;
      arg.push_back(move(string("continue")));
      return arg;
   }
   
   count_ = 0;
   vector<Callback::OrderStruct> orderVec;

   try
   {
      orderVec = move(cbStack_.pop_all(std::chrono::seconds(50)));
   }
   catch (IsEmpty&)
   {
      Arguments arg;
      arg.push_back(move(string("continue")));
      return arg;
   }
   catch (StackTimedOutException&)
   {
      Arguments arg;
      arg.push_back(move(string("continue")));
      return arg;
   }
   catch (StopBlockingLoop&)
   {
      //return terminate packet
      Callback::OrderStruct terminateOrder;
      terminateOrder.order_.push_back(move(string("terminate")));
      terminateOrder.otype_ = OrderOther;
   }

   //consolidate NewBlock and Refresh notifications
   bool refreshNotification = false;
   int32_t newBlock = -1;

   Arguments arg;
   for (auto& order : orderVec)
   {
      switch (order.otype_)
      {
         case OrderNewBlock:
         {
            auto& argVector = order.order_.getArgVector();
            if (argVector.size() != 2)
               break;

            auto heightPtr = (DataObject<uint32_t>*)argVector[1].get();

            int blockheight = (int)heightPtr->getObj();
            if (blockheight > newBlock)
               newBlock = blockheight;

            break;
         }

         case OrderRefresh:
            refreshNotification = true;
            break;

         case OrderTerminate:
         {
            Arguments terminateArg;
            terminateArg.push_back(move(string("terminate")));
            return terminateArg;
         }

         default:
            arg.merge(order.order_);
      }
   }

   if (refreshNotification)
      arg.push_back(move(string("BDV_Refresh")));

   if (newBlock > -1)
   {
      arg.push_back(move(string("NewBlock")));
      arg.push_back(move((unsigned int)newBlock));
   }

   //send it
   return arg;
}
