#ifndef _SSHHEADERS_H
#define _SSHHEADERS_H

#include <memory>
#include <thread>
#include "BinaryData.h"
#include "StoredBlockObj.h"

class BatchThreadContainer;
class ScrAddrFilter;

class SSHheaders
{
public:
   SSHheaders(uint32_t nThreads, uint32_t commitId)
      : nThreads_(nThreads), commitId_(commitId)
   {}

   shared_ptr<vector<StoredScriptHistory*>> 
      getSshHeaders(shared_ptr<BatchThreadContainer>,
                    unique_lock<mutex>&);
   void buildSshHeadersFromSAF(const ScrAddrFilter& SAF);
   void processSshHeaders(vector<BinaryData>& scrAddrs);
                        

private:
   shared_ptr<vector<StoredScriptHistory*>>
      processSshHeaders(
         shared_ptr<BatchThreadContainer>, 
         shared_ptr<SSHheaders>);

   void grabExistingSSHHeaders(vector<StoredScriptHistory*>& sshVec);
   void fetchExistingSshHeaders(map<BinaryData, StoredScriptHistory>& sshMap,
      const vector<StoredScriptHistory*>& saVec,
      uint32_t threadId);

   ///////
public:
   shared_ptr<map<BinaryData, StoredScriptHistory> > sshToModify_;
   mutex mu_;
   const uint32_t nThreads_;

private:
   const uint32_t commitId_;
};

#endif