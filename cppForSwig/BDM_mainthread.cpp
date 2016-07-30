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

#include <ctime>

////////////////////////////////////////////////////////////////////////////////
void BlockDataManager::registerBDVwithZCcontainer(
   shared_ptr<BDV_Server_Object> bdvPtr)
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

   ZeroConfContainer::BDV_Callbacks callbacks;
   callbacks.addressFilter_ = filter;
   callbacks.newZcCallback_ = newzc;

   zeroConfCont_->insertBDVcallback(move(bdvPtr->getID()), move(callbacks));
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

namespace
{
class OnFinish
{
   const function<void()> fn;
public:
   OnFinish(const function<void()> &fn)
      : fn(fn) { }
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
   
   {
      //connect to node as async, no need to wait for a succesful connection
      //to init the DB
      bdm->networkNode_->connectToNode(true);

      tuple<BDMPhase, double, unsigned, unsigned> lastvalues;
      time_t lastProgressTime=0;
      
      class BDMStopRequest
      {
      public:
         virtual ~BDMStopRequest() { }
      };
     
      const auto loadProgress
         = [&] (BDMPhase phase, double prog,unsigned time, unsigned numericProgress)
      {
         const tuple<BDMPhase, double, unsigned, unsigned> currentvalues
            { phase, prog, time, numericProgress };
         if (currentvalues == lastvalues)
            return; // don't go to python if nothing's changed
         
         // also, don't go to the python if the phase is the same and it's been
         // less than 1 second since the last time this has been called
         // python is a lot slower than C++, so we don't want to invoke
         // the python interpreter to frequently
         const time_t currentProgressTime = std::time(nullptr);
         if (phase == get<0>(lastvalues)
            && currentProgressTime <= lastProgressTime+1
            && fabs(get<1>(lastvalues)-get<1>(currentvalues)) <= .01 )
            return;
            
         lastProgressTime = currentProgressTime;
         
         lastvalues = currentvalues;
         
         //pass empty walletID for main build&scan calls
         //callback->progress(phase, vector<string>(), prog, time, numericProgress);

         if (!pimpl->run)
         {
            LOGINFO << "Stop requested detected";
            throw BDMStopRequest();
         }
      };
      
      try
      {
         unsigned mode = pimpl->mode & 0x00000003;
         bool clearZc = pimpl->mode & 0x00000004;

         if (mode == 0) bdm->doInitialSyncOnLoad(loadProgress);
         else if (mode == 1) bdm->doInitialSyncOnLoad_Rescan(loadProgress);
         else if (mode == 2) bdm->doInitialSyncOnLoad_Rebuild(loadProgress);
         else if (mode == 3) bdm->doInitialSyncOnLoad_RescanBalance(loadProgress);

         bdm->enableZeroConf(clearZc);
      }
      catch (BDMStopRequest&)
      {
         LOGINFO << "UI asked build/scan thread to finish";
         return;
      }
   }

   isReadyPromise.set_value(true);
   
   auto updateChainLambda = [bdm, this]()->bool
   {
      auto reorgState = bdm->readBlkFileUpdate();
      if (reorgState.hasNewTop)
      {
         bdm->newBlocksStack_.push_back(move(reorgState));
         
         ZeroConfContainer::ZcActionStruct zcaction;
         zcaction.action_ = Zc_Purge;

         bdm->zeroConfCont_->newZcStack_.push_back(move(zcaction));
         return true;
      }

      return false;
   };

   while(pimpl->run)
   {
      //register promise with p2p interface
      promise<bool> newBlocksPromise;
      auto newBlocksFuture = newBlocksPromise.get_future();
      
      auto newBlocksCallback = 
         [&newBlocksPromise](const vector<InvEntry>& vecIE)->void
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
                  newBlocksPromise.set_exception(current_exception());
                  return;
               }
            }
         }

         newBlocksPromise.set_value(true);
      };

      try
      {
         bdm->networkNode_->registerInvBlockLambda(newBlocksCallback);

         //keep updating until there are no more new blocks
         while (updateChainLambda());

         //wait on future
         newBlocksFuture.get();
      }
      catch (...)
      {
         break;
      }
   }

   //bdm->newBlocksStack_.terminate();
}
catch (std::exception &e)
{
   LOGERR << "BDM thread failed: " << e.what();
   string errstr(e.what());
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

