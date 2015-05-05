#include "SSHheaders.h"
#include "BlockWriteBatcher.h"

int SSHheaders::collisionCount = 0;

////////////////////////////////////////////////////////////////////////////////
thread SSHheaders::getSshHeaders(
   shared_ptr<BlockDataContainer> bdc, unique_lock<mutex>& lock)
{
   //if there is a parent SSHheader, we have to use that one
   if (bdc->processor_->sshHeaders_ != nullptr)
   {
      shared_ptr<SSHheaders> parent =
         bdc->processor_->sshHeaders_;
      TIMER_START("getSSHHeadersLock");
      lock = unique_lock<mutex>(parent->mu_);
      sshToModify_ = parent->sshToModify_;
      TIMER_STOP("getSSHHeadersLock");
      return thread();
   }

   lock = unique_lock<mutex>(mu_);

   //otherwise we may need to build one from scratch
   //but first let's make sure there isn't one available, in case
   //there is a writer running

   shared_ptr<SSHheaders> commitingHeaders = nullptr;
   if (bdc->processor_->writer_ != nullptr)
   {
      //previous writer has a valid SSHheaders object, just use that
      commitingHeaders =
         bdc->processor_->writer_->sshHeaders_;
   }

   if (commitingHeaders != nullptr && commitingHeaders.get() != this)
   {
      unique_lock<mutex> parentHeadersLock(commitingHeaders->mu_);
      return processSshHeaders(bdc, commitingHeaders);
   }
   else
   {
      //no ongoing serialization currently, let's not make the processing
      //thread wait any longer.
      {
         unique_lock<mutex> writerLock(bdc->waitOnWriterMutex_);
         bdc->waitOnWriterCV_.notify_all();
      }

      return processSshHeaders(bdc, nullptr);
   }
}

////////////////////////////////////////////////////////////////////////////////
thread SSHheaders::processSshHeaders(shared_ptr<BlockDataContainer> bdc,
   shared_ptr<SSHheaders> prevHeaders)
{
   TIMER_START("prepareSSHheaders");
   sshToModify_.reset(new map<BinaryData, StoredScriptHistory>());
   shared_ptr<vector<StoredScriptHistory*>> sshVec(
      new vector<StoredScriptHistory*>());

   if (prevHeaders != nullptr)
   {
      uint32_t commitedId = bdc->processor_->getCommitedId();
      for (auto& prefix : prevHeaders->topPrefix_)
      {
         if (prefix.second.second >= commitedId)
            topPrefix_.insert(prefix);
      }

      for (auto& threadData : bdc->threads_)
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
            else
            {
               ssh.uniqueKey_ = subssh.first;
            }

            sshVec->push_back(&ssh);
         }
      }
   }
   else
   {
      for (auto& threadData : bdc->threads_)
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

   auto computeThread = [&sshVec, this](void)->void
   { 
      computeDBKeys(sshVec); 
   };

   return thread(computeThread);
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
   computeDBKeys(sshVec);
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
void SSHheaders::computeDBKeys(shared_ptr<vector<StoredScriptHistory*>> sshVec)
{
   TIMER_START("computeDBKeys");
   uint32_t i;
   vector<thread> vecTh;

   uint32_t curNThreads = nThreads_;
   if (nThreads_ > 0)
      curNThreads--;

   //Create keys for new SSH headers. We will run a loop on all remaining
   //new keys as long as they collide.

   vector<map<BinaryData, pair<uint8_t, uint32_t>>> topPrefixes;
   topPrefixes.resize(nThreads_);

   vector<StoredScriptHistory*> unknownSshVec;
   for (auto sshPtr : *sshVec)
   {
      if (sshPtr->keyLength_ == 0)
      {
         unknownSshVec.push_back(sshPtr);
      }
   }

   *sshVec = move(unknownSshVec);
   
   auto processNewSshThread = [&sshVec, &topPrefixes, this](uint32_t tId)->void
   { this->fetchSshHeaders(*sshToModify_, *sshVec, topPrefixes[tId], tId); };

   bool haveCollision = true;
   while (haveCollision)
   {
      TIMER_START("getNewKeys");
      haveCollision = false;
      topPrefixes.clear();
      topPrefixes.resize(nThreads_);

      vecTh.clear();
      for (i = 0; i < curNThreads; i++)
         vecTh.push_back(thread(processNewSshThread, i + 1));

      processNewSshThread(0);

      for (i = 0; i < curNThreads; i++)
         if (vecTh[i].joinable())
            vecTh[i].join();

      TIMER_STOP("getNewKeys");

      //check for key collisions
      auto newSshVec = checkForSubKeyCollisions(*sshVec);

      if (newSshVec.size() > 0)
      {
         haveCollision = true;
         *sshVec = move(newSshVec);
         collisionCount++;
      }

      //unify top prefixes
      for (auto& prefixMap : topPrefixes)
      {
         for (auto& prefix : prefixMap)
         {
            auto& pr = topPrefix_[prefix.first];
            if (pr.first < prefix.second.first)
            {
               pr = prefix.second;
            }
         }
      }
   }

   TIMER_STOP("computeDBKeys");
}

////////////////////////////////////////////////////////////////////////////////
vector<StoredScriptHistory*> SSHheaders::checkForSubKeyCollisions(
   vector<StoredScriptHistory*>& sshVec)
{
   TIMER_START("checkForCollisions");
   uint32_t i;

   map<BinaryData, vector<StoredScriptHistory*> > collisionMap;
   vector<StoredScriptHistory*> collidingSSH;

   for (auto ssh : sshVec)
      collisionMap[ssh->getSubKey()].push_back(ssh);

   for (auto& subkey : collisionMap)
   {
      if (subkey.second.size() > 1)
      {
         //several new ssh are sharing the same key, let's fix that
         for (i = 1; i < subkey.second.size(); i++)
         {
            StoredScriptHistory* ssh = subkey.second[i];
            ssh->dbPrefix_ = 0;
            ssh->keyLength_ = 0;
            collidingSSH.push_back(ssh);
         }
      }
   }

   TIMER_STOP("checkForCollisions");
   return collidingSSH;
}

////////////////////////////////////////////////////////////////////////////////
void SSHheaders::fetchExistingSshHeaders(
   map<BinaryData, StoredScriptHistory>& sshMap,
   const vector<StoredScriptHistory*>& sshVec,
   uint32_t threadId)
{
   LMDBEnv::Transaction tx;
   BlockWriteBatcher::iface_->beginDBTransaction(&tx, HISTORY, LMDB::ReadOnly);

   for (uint32_t i = threadId; i < sshVec.size(); i+=nThreads_)
   {
      auto& ssh = *sshVec[i];
      if (ssh.keyLength_ == 0)
      {
         BinaryData sshKey = ssh.getDBKey(true);
         BinaryDataRef valRef = 
            BlockWriteBatcher::iface_->getValueNoCopy(HISTORY, sshKey);
         
         if (valRef.getSize() > 0)
            ssh.unserializeDBValue(valRef);
      }
   }
}

////////////////////////////////////////////////////////////////////////////////
void SSHheaders::fetchSshHeaders(
   map<BinaryData, StoredScriptHistory>& sshMap,
   const vector<StoredScriptHistory*>& sshVec,
   map<BinaryData, pair<uint8_t, uint32_t>>& prefixes,
   uint32_t tId) const
{
   uint32_t distribute = 0;
   for (uint32_t i = tId; i < sshVec.size(); i+=nThreads_)
   {
      auto& ssh = *sshVec[i];
      if (ssh.keyLength_ > 0 && ssh.dbPrefix_ > 0)
         continue;

      ssh.keyLength_ = SUBSSHDB_PREFIX_MIN + (distribute % nThreads_);
      distribute++;

      auto checkForPrefix = [&ssh, &prefixes, this](BinaryData &key)->int
      {
         auto localPrefix = prefixes.find(key);
         if (localPrefix != prefixes.end())
         {
            if (localPrefix->second.first == 0xFF)
            {
               //we have this prefix but the address space is used up,
               //increment key size and try again
               ssh.keyLength_++;
               return 0;
            }
            else //(localPrefix->second.first != 0)
            {
               localPrefix->second.first++;
               localPrefix->second.second = commitId_;
               ssh.dbPrefix_ = localPrefix->second.first;
               ssh.keyLength_ = key.getSize();

               return 1;
            }
         }

         //else check if we have a top prefix for this key in SSHheaders
         auto mainPrefix = topPrefix_.find(key);
         if (mainPrefix != topPrefix_.end())
         {
            if (mainPrefix->second.first == 0xFF)
            {
               ssh.keyLength_++;
               return 0;
            }
            else//(mainPrefix->second.first != 0)
            {
               uint8_t newPrefix = mainPrefix->second.first + 1;
               ssh.dbPrefix_ = newPrefix;
               ssh.keyLength_ = key.getSize();

               prefixes[key] = make_pair(newPrefix, commitId_);
               return 1;
            }
         }

         return -1;
      };

      while (1)
      {
         BinaryData key = ssh.getSubKey();
         key.getPtr()[0] = 0;

         //check if we have a top prefix in local container
         int gotPrefix = checkForPrefix(key);
         if (gotPrefix == 1)
            break;
         else if (gotPrefix == 0)
            continue;

         //otherwise, grab it from the DB, update prefix 
         BinaryData keyFromDB =
            BlockWriteBatcher::iface_->getSubSSHKey(
               ssh.uniqueKey_, ssh.keyLength_);
         uint8_t newPrefix = keyFromDB.getPtr()[0] +1;
         keyFromDB.getPtr()[0] = 0;

         gotPrefix = checkForPrefix(keyFromDB);
         if (gotPrefix == 1)
            break;
         else if (gotPrefix == -1)
         {
            prefixes[keyFromDB] = make_pair(newPrefix, commitId_);
            ssh.dbPrefix_ = newPrefix;
            ssh.keyLength_ = keyFromDB.getSize();
            break;
         }
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

   //needs reworked for the new key fetch/CD
   grabExistingSSHHeaders(*sshVec);
   computeDBKeys(sshVec);
}
