////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2015, Armory Technologies, Inc.                        //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE-ATI or http://www.gnu.org/licenses/agpl.html                  //
//                                                                            //
//                                                                            //
//  Copyright (C) 2016, goatpig                                               //            
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //                                   
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#include "BDM_mainthread.h"
#include "BlockUtils.h"
#include "BlockDataViewer.h"

#include "nodeRPC.h"

#include <ctime>

////////////////////////////////////////////////////////////////////////////////
void BlockDataManager::registerBDVwithZCcontainer(
   BDV_Server_Object* bdvPtr)
{
   auto filter = [bdvPtr](const BinaryData& scrAddr)->bool
   {
      return bdvPtr->hasScrAddress(scrAddr);
   };

   auto newzc = [bdvPtr](
      map<BinaryData, shared_ptr<map<BinaryData, TxIOPair>>> zcMap)->void
   {
      bdvPtr->zcCallback(move(zcMap));
   };

   auto zcerror = [bdvPtr](string& error, string& id)->void
   {
      bdvPtr->zcErrorCallback(error, id);
   };

   ZeroConfContainer::BDV_Callbacks callbacks;
   callbacks.addressFilter_ = filter;
   callbacks.newZcCallback_ = newzc;
   callbacks.zcErrorCallback_ = zcerror;

   zeroConfCont_->insertBDVcallback(
      move(bdvPtr->getID()), move(callbacks));
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataManager::unregisterBDVwithZCcontainer(
   const string& bdvID)
{
   zeroConfCont_->eraseBDVcallback(bdvID);
}

BDM_CallBack::~BDM_CallBack()
{}

BlockDataManagerThread::BlockDataManagerThread(const BlockDataManagerConfig &config)
{
   pimpl = new BlockDataManagerThreadImpl;
   pimpl->bdm = new BlockDataManager(config);
}

BlockDataManagerThread::~BlockDataManagerThread()
{
   if (pimpl == nullptr)
      return;

   if (pimpl->run)
   {
      LOGERR << "Destroying BlockDataManagerThread without shutting down first";
   }
   else
   {
      delete pimpl;
      pimpl = nullptr;
   }
}


void BlockDataManagerThread::start(BDM_INIT_MODE mode)
{
   pimpl->mode = mode;
   pimpl->run = true;
   
   pimpl->tID = thread(thrun, this);
}

BlockDataManager *BlockDataManagerThread::bdm()
{
   return pimpl->bdm;
}

void BlockDataManagerThread::shutdown()
{
   if (pimpl->run)
   {
      pimpl->run = false;

      if (pimpl->tID.joinable())
         pimpl->tID.join();
   }
}

void BlockDataManagerThread::join()
{
   if (pimpl->run)
   {
      if (pimpl->tID.joinable())
         pimpl->tID.join();
   }
}


namespace
{
class OnFinish
{
   const function<void()> fn;
public:
   OnFinish(const function<void()> &_fn)
      : fn(_fn) { }
   ~OnFinish()
   {
      fn();
   }
};


}

void BlockDataManagerThread::run()
try
{
   BlockDataManager *const bdm = this->bdm();

   if (bdm->hasException())
      return;

   promise<bool> isReadyPromise;
   bdm->isReadyFuture_ = isReadyPromise.get_future();

   auto updateNodeStatusLambda = [bdm]()->void
   {
      try
      {
         auto&& nodeStatus = bdm->getNodeStatus();
         auto&& notifPtr =
            make_unique<BDV_Notification_NodeStatus>(move(nodeStatus));
         bdm->notificationStack_.push_back(move(notifPtr));
      }
      catch (exception&)
      {
      }
   };

   //connect to node as async, no need to wait for a succesful connection
   //to init the DB
   bdm->networkNode_->connectToNode(true);

   //if RPC is running, wait on node init
   try
   {
      bdm->nodeRPC_->waitOnChainSync(updateNodeStatusLambda);
   }
   catch (exception& e)
   {
      LOGINFO << "Error occured while querying the RPC for sync status";
      LOGINFO << "Message: " << e.what();
   }

   tuple<BDMPhase, double, unsigned, unsigned> lastvalues;
   time_t lastProgressTime = 0;

   class BDMStopRequest
   {
   public:
      virtual ~BDMStopRequest() { }
   };

   const auto loadProgress
      = [&](BDMPhase phase, double prog, unsigned time, unsigned numericProgress)
   {
      //pass empty walletID for main build&scan calls
      auto&& notifPtr = make_unique<BDV_Notification_Progress>(
         phase, prog, time, numericProgress, vector<string>());

      bdm->notificationStack_.push_back(move(notifPtr));

      if (!pimpl->run)
      {
         LOGINFO << "Stop requested detected";
         throw BDMStopRequest();
      }
   };

   try
   {
      unsigned mode = pimpl->mode & 0x00000003;
      bool clearZc = bdm->config().clearMempool_;

      if (mode == 0) bdm->doInitialSyncOnLoad(loadProgress);
      else if (mode == 1) bdm->doInitialSyncOnLoad_Rescan(loadProgress);
      else if (mode == 2) bdm->doInitialSyncOnLoad_Rebuild(loadProgress);
      else if (mode == 3) bdm->doInitialSyncOnLoad_RescanBalance(loadProgress);

      if (!bdm->config().checkChain_)
         bdm->enableZeroConf(clearZc);
   }
   catch (BDMStopRequest&)
   {
      LOGINFO << "UI asked build/scan thread to finish";
      return;
   }

   isReadyPromise.set_value(true);

   if (bdm->config().checkChain_)
      return;

   auto updateChainLambda = [bdm, this]()->bool
   {
      auto reorgState = bdm->readBlkFileUpdate();
      if (reorgState.hasNewTop_)
      {
         //purge zc container
         ZeroConfContainer::ZcActionStruct zcaction;
         zcaction.action_ = Zc_Purge;
         zcaction.finishedPromise_ = make_shared<promise<bool>>();
         auto purgeFuture = zcaction.finishedPromise_->get_future();

         bdm->zeroConfCont_->newZcStack_.push_back(move(zcaction));

         //wait on purge
         purgeFuture.get();

         //notify bdvs
         auto&& notifPtr =
            make_unique<BDV_Notification_NewBlock>(move(reorgState));
         bdm->notificationStack_.push_back(move(notifPtr));

         return true;
      }

      return false;
   };

   bdm->networkNode_->registerNodeStatusLambda(updateNodeStatusLambda);
   bdm->nodeRPC_->registerNodeStatusLambda(updateNodeStatusLambda);

   while (pimpl->run)
   {
      //register promise with p2p interface
      auto newBlocksPromise = make_shared<promise<bool>>();
      auto newBlocksFuture = newBlocksPromise->get_future();

      auto newBlocksCallback =
         [newBlocksPromise](const vector<InvEntry>& vecIE)->void
      {
         for (auto& ie : vecIE)
         {
            if (ie.invtype_ == Inv_Terminate)
            {
               try
               {
                  throw runtime_error("terminate");
               }
               catch (...)
               {
                  newBlocksPromise->set_exception(current_exception());
                  return;
               }
            }
         }

         newBlocksPromise->set_value(true);
      };

      try
      {
         bdm->networkNode_->registerInvBlockLambda(newBlocksCallback);

         //keep updating until there are no more new blocks
         while (updateChainLambda());

         //wait on future
         newBlocksFuture.get();
      }
      catch (exception &e)
      {
         LOGERR << "caught exception in main thread: " << e.what();
         break;
      }
      catch (...)
      {
         LOGERR << "caught unknown exception in main thread";
         break;
      }
   }
}
catch (std::exception &e)
{
   LOGERR << "BDM thread failed: " << e.what();
}
catch (...)
{
   LOGERR << "BDM thread failed: (unknown exception)";
}

void* BlockDataManagerThread::thrun(void *_self)
{
   BlockDataManagerThread *const self
      = static_cast<BlockDataManagerThread*>(_self);
   self->run();
   return 0;
}


// kate: indent-width 3; replace-tabs on;

