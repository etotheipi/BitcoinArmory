#include "SSHheaders.h"
#include "BlockWriteBatcher.h"

////////////////////////////////////////////////////////////////////////////////
unique_lock<mutex>* SSHheaders::getSshHeaders(
   shared_ptr<BlockDataContainer> bdc)
{
   //TIMER_START("getParentSshToModify");
   unique_lock<mutex>* lock = nullptr;

   //if there is a parent SSHheader, we have to use that one
   if (bdc->processor_->sshHeaders_ != nullptr)
   {
      shared_ptr<SSHheaders> parent =
         bdc->processor_->sshHeaders_;
      lock = new unique_lock<mutex>(parent->mu_);
      sshToModify_ = parent->sshToModify_;
      return lock;
   }

   lock = new unique_lock<mutex>(mu_);

   //otherwise we may need to build one from scratch
   //but first let's make sure there isn't one available, in case
   //there is a writer running

   shared_ptr<SSHheaders> commitingHeaders = nullptr;
   unique_lock<mutex> parentWriterLock(bdc->processor_->writeMutex_, defer_lock);

   if (!parentWriterLock.try_lock())
   {
      //couldn't grab the parent writeMutex_, this means a write is under
      //process, which means there is a writer object referenced by parent_
      //with a valid SSHheaders. We will wait on the writer to complete
      //its serialization and grab that shared_ptr to serialize this
      //batch of data with. Otherwise, we'd have to wait on the write to
      //complete to get valid SSH balance and txio count.

      shared_ptr<BlockDataContainer> commitingObj = nullptr;
      if (bdc->processor_->writer_ != nullptr)
      {
         if (bdc->processor_->writer_->dataToCommit_.sshHeaders_ != nullptr)
         {
            //parent has a valid SSHheaders object, just use that
            commitingHeaders =
               bdc->processor_->writer_->dataToCommit_.sshHeaders_;
         }
         else commitingObj = bdc->processor_->writer_;
      }

      if (commitingObj != nullptr)
         commitingHeaders = commitingObj->dataToCommit_.sshHeaders_;
   }
   //TIMER_STOP("getParentSshToModify");

   if (commitingHeaders != nullptr && commitingHeaders.get() != this)
   {
      unique_lock<mutex> parentHeadersLock(commitingHeaders->mu_);
      processSshHeaders(
         bdc, *commitingHeaders->sshToModify_);
   }
   else
   {
      processSshHeaders(
         bdc, map<BinaryData, StoredScriptHistory>());
   }

   return lock;
}

////////////////////////////////////////////////////////////////////////////////
void SSHheaders::processSshHeaders(shared_ptr<BlockDataContainer> bdc,
   const map<BinaryData, StoredScriptHistory>& prevSshToModify)
{
   sshToModify_.reset(new map<BinaryData, StoredScriptHistory>());

   vector<vector<const BinaryData*>> saVec;
   saVec.resize(nThreads_);

   uint32_t i = 0;
   for (auto& threadData : bdc->threads_)
   {
      auto& subsshMap = threadData->subSshMap_;
      for (auto& subssh : subsshMap)
      {
         StoredScriptHistory& ssh = (*sshToModify_)[subssh.first];

         auto sshIter = prevSshToModify.find(subssh.first);
         if (sshIter != prevSshToModify.end())
            ssh = sshIter->second;

         saVec[i % nThreads_].push_back(&subssh.first);

         i++;
      }
   }

   computeDBKeys(saVec);
}

////////////////////////////////////////////////////////////////////////////////
void SSHheaders::processSshHeaders(vector<BinaryData>& scrAddrs)
{
   vector<vector<const BinaryData*>> saVec;
   saVec.resize(1);

   for (auto& sa : scrAddrs)
   {
      saVec[0].push_back(&sa);
      sshToModify_->insert(make_pair(sa, StoredScriptHistory()));
   }

   computeDBKeys(saVec);
}

////////////////////////////////////////////////////////////////////////////////
void SSHheaders::computeDBKeys(vector<vector<const BinaryData*>>& saVec)
{
   uint32_t i;

   auto processSshThread = [&saVec, this](uint32_t vecId)->void
   { this->fetchSshHeaders(*sshToModify_, saVec[vecId]); };

   uint32_t curNThreads = saVec.size() - 1;

   vector<thread> vecTh;
   for (i = 0; i < curNThreads; i++)
      vecTh.push_back(thread(processSshThread, i + 1));

   processSshThread(0);

   for (i = 0; i < curNThreads; i++)
      if (vecTh[i].joinable())
         vecTh[i].join();

   //check for key collisions
   checkForSubKeyCollisions();
}

////////////////////////////////////////////////////////////////////////////////
void SSHheaders::checkForSubKeyCollisions(void)
{
   uint32_t i;
   bool increasedKeySize = true;
   while (increasedKeySize)
   {
      /***
      Should check modified keys with DB (to cover for RAM to DB collision)
      ***/

      increasedKeySize = false;
      map<BinaryData, vector<StoredScriptHistory*> > collisionMap;

      for (auto& ssh : *sshToModify_)
         collisionMap[ssh.second.getSubKey()].push_back(&ssh.second);

      for (auto& subkey : collisionMap)
      {
         if (subkey.second.size())
         {
            //several new ssh are sharing the same key, let's fix that
            uint32_t previousPrefix = subkey.second[0]->dbPrefix_;
            uint32_t previousKeylen = subkey.second[0]->keyLength_;

            for (i = 1; i < subkey.second.size(); i++)
            {
               ++previousPrefix;
               if (previousPrefix > 0xFF)
               {
                  previousPrefix = 0;
                  ++previousKeylen;
                  increasedKeySize = true;
               }

               StoredScriptHistory& ssh = *subkey.second[i];
               ssh.dbPrefix_ = previousPrefix;
               ssh.keyLength_ = previousKeylen;
            }
         }
      }
   }
}

////////////////////////////////////////////////////////////////////////////////
void SSHheaders::fetchSshHeaders(
   map<BinaryData, StoredScriptHistory>& sshMap,
   const vector<const BinaryData*>& saVec)
{
   uint32_t distribute = 0;
   for (auto saPtr : saVec)
   {
      auto& ssh = sshMap.find(*saPtr)->second;
      if (ssh.keyLength_ == 0)
      {
         BlockWriteBatcher::iface_->getStoredScriptHistorySummary(
            ssh, *saPtr);
         if (!ssh.isInitialized())
         {
            BinaryData key =
               BlockWriteBatcher::iface_->getSubSSHKey(*saPtr);
            ssh.uniqueKey_ = *saPtr;
            ssh.dbPrefix_ = key.getPtr()[0];
            ssh.keyLength_ = key.getSize() + (distribute % nThreads_);
            distribute++;
         }
         else
         {
            if (ssh.keyLength_ == SUBSSHDB_PREFIX_MIN + (distribute % nThreads_))
               distribute++;
         }
      }
      else
      {
         if (ssh.keyLength_ == SUBSSHDB_PREFIX_MIN + (distribute % nThreads_))
            distribute++;
      }
   }
}

////////////////////////////////////////////////////////////////////////////////
void SSHheaders::buildSshHeadersFromSAF(const ScrAddrFilter& SAF)
{
   //for (auto saPair : sasd.getScrAddrMap())
   map<BinaryData, map<BinaryData, StoredSubHistory>> subsshMap;

   vector<const BinaryData*> saVec;
   auto& saMap = SAF.getScrAddrMap();


   sshToModify_.reset(new map<BinaryData, StoredScriptHistory>());
   for (auto& sa : saMap)
   {
      sshToModify_->insert(make_pair(sa.first, StoredScriptHistory()));
      saVec.push_back(&sa.first);
   }

   fetchSshHeaders(*sshToModify_, saVec);
   checkForSubKeyCollisions();
}
