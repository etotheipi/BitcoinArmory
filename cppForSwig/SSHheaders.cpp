#include "SSHheaders.h"
#include "BlockWriteBatcher.h"

////////////////////////////////////////////////////////////////////////////////
shared_ptr<vector<StoredScriptHistory*>> SSHheaders::getSshHeaders(
   shared_ptr<BatchThreadContainer> btc, unique_lock<mutex>& lock)
{
   //if there is a parent SSHheader, we have to use that one
   if (btc->processor_->sshHeaders_ != nullptr)
   {
      shared_ptr<SSHheaders> parent =
         btc->processor_->sshHeaders_;
      TIMER_START("getSSHHeadersLock");
      lock = unique_lock<mutex>(parent->mu_);
      sshToModify_ = parent->sshToModify_;
      TIMER_STOP("getSSHHeadersLock");
      return nullptr;
   }

   sshToModify_.reset(new map<BinaryData, StoredScriptHistory>());
   shared_ptr<vector<StoredScriptHistory*>> sshVec =
      make_shared<vector<StoredScriptHistory*>>();

   return nullptr;

   lock = unique_lock<mutex>(mu_);

   //otherwise we may need to build one from scratch
   //but first let's make sure there isn't one available, in case
   //there is a writer running

   shared_ptr<SSHheaders> commitingHeaders = 
      btc->processor_->currentSSHheaders_;

   if (commitingHeaders != nullptr)
      unique_lock<mutex> parentHeadersLock(commitingHeaders->mu_);
      
   return processSshHeaders(btc, commitingHeaders);
}

////////////////////////////////////////////////////////////////////////////////
shared_ptr<vector<StoredScriptHistory*>> SSHheaders::processSshHeaders(
   shared_ptr<BatchThreadContainer> btc,
   shared_ptr<SSHheaders> prevHeaders)
{
   TIMER_START("prepareSSHheaders");
   sshToModify_.reset(new map<BinaryData, StoredScriptHistory>());
   shared_ptr<vector<StoredScriptHistory*>> sshVec = 
      make_shared<vector<StoredScriptHistory*>>();

   if (prevHeaders != nullptr)
   {
      for (auto& threadData : btc->threads_)
      {
         auto& subsshMap = threadData->subSshMap_;
         for (auto& subssh : subsshMap)
         {
            StoredScriptHistory& ssh = (*sshToModify_)[subssh.first];
            if (ssh.isInitialized())
               continue;

            //if the previous sshheader processed this ssh, let's take
            //that data as it is guaranteed to be up to date (may not have
            //been writen to db yet)
            auto sshIter = prevHeaders->sshToModify_->find(subssh.first);
            if (sshIter != prevHeaders->sshToModify_->end())
            {
               ssh = sshIter->second;
               continue;
            }

            ssh.uniqueKey_ = subssh.first;
            sshVec->push_back(&ssh);
         }
      }
   }
   else
   {
      for (auto& threadData : btc->threads_)
      {
         auto& subsshMap = threadData->subSshMap_;
         for (auto& subssh : subsshMap)
         {
            StoredScriptHistory& ssh = (*sshToModify_)[subssh.first];
            if (ssh.isInitialized())
               continue;

            ssh.uniqueKey_ = subssh.first;
            sshVec->push_back(&ssh);
         }
      }
   }

   grabExistingSSHHeaders(*sshVec);

   TIMER_STOP("prepareSSHheaders");

   return sshVec;
}

////////////////////////////////////////////////////////////////////////////////
void SSHheaders::processSshHeaders(vector<BinaryData>& scrAddrs)
{
   shared_ptr<vector<StoredScriptHistory*>> sshVec(
      new vector<StoredScriptHistory*>());

   for (auto& sa : scrAddrs)
   {
      auto sshIter = sshToModify_->insert(make_pair(sa, StoredScriptHistory()));
      sshIter.first->second.uniqueKey_ = sa;
      sshVec->push_back(&sshIter.first->second);
   }

   grabExistingSSHHeaders(*sshVec);
}

////////////////////////////////////////////////////////////////////////////////
void SSHheaders::grabExistingSSHHeaders(vector<StoredScriptHistory*>& sshVec)
{
   //fetch all relevant SSH headers already in DB
   uint32_t i;

   auto processExistingSshThread = [&sshVec, this](uint32_t tId)->void
   { this->fetchExistingSshHeaders(*sshToModify_, sshVec, tId); };

   uint32_t curNThreads = nThreads_;
   if (nThreads_ > 0)
      curNThreads--;

   TIMER_START("getExistingKeys");
   vector<thread> vecTh;
   for (i = 0; i < curNThreads; i++)
      vecTh.push_back(thread(processExistingSshThread, i + 1));

   processExistingSshThread(0);

   for (i = 0; i < curNThreads; i++)
      if (vecTh[i].joinable())
         vecTh[i].join();
   TIMER_STOP("getExistingKeys");

}

////////////////////////////////////////////////////////////////////////////////
void SSHheaders::fetchExistingSshHeaders(
   map<BinaryData, StoredScriptHistory>& sshMap,
   const vector<StoredScriptHistory*>& sshVec,
   uint32_t threadId)
{
   auto db = BlockWriteBatcher::iface_;
   for (uint32_t i = threadId; i < sshVec.size(); i+=nThreads_)
   {
      auto& ssh = *sshVec[i];
      {
         uint32_t shard = BlockWriteBatcher::iface_->getShard(ssh.uniqueKey_);
         LMDBEnv::Transaction tx;
         BlockWriteBatcher::iface_->beginShardTransaction(tx, shard, LMDB::ReadOnly);

         BinaryData sshKey = ssh.getDBKey(true);
         BinaryDataRef valRef = 
            db->getValueNoCopy(shard, sshKey);
         
         if (valRef.getSize() > 0)
            ssh.unserializeDBValue(valRef);
      }
   }
}

////////////////////////////////////////////////////////////////////////////////
void SSHheaders::buildSshHeadersFromSAF(const ScrAddrFilter& SAF)
{
   //for (auto saPair : sasd.getScrAddrMap())
   map<BinaryData, map<BinaryData, StoredSubHistory>> subsshMap;

   shared_ptr<vector<StoredScriptHistory*>> sshVec(
      new vector<StoredScriptHistory*>());
   auto& saMap = SAF.getScrAddrMap();


   sshToModify_.reset(new map<BinaryData, StoredScriptHistory>());
   for (auto& sa : saMap)
   {
      auto sshIter = sshToModify_->insert(make_pair(sa.first, StoredScriptHistory()));
      sshIter.first->second.uniqueKey_ = sa.first;
      sshVec->push_back(&sshIter.first->second);
   }

   grabExistingSSHHeaders(*sshVec);
}
