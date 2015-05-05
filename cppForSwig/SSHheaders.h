#ifndef _SSHHEADERS_H
#define _SSHHEADERS_H

#include <memory>
#include <thread>
#include "BinaryData.h"
#include "StoredBlockObj.h"

class BlockDataContainer;
class ScrAddrFilter;

class SSHheaders
{
public:
   SSHheaders(uint32_t nThreads, uint32_t commitId)
      : nThreads_(nThreads), commitId_(commitId)
   {}

   thread getSshHeaders(shared_ptr<BlockDataContainer>,
      unique_lock<mutex>&);
   void buildSshHeadersFromSAF(const ScrAddrFilter& SAF);
   void processSshHeaders(vector<BinaryData>& scrAddrs);

private:
   thread processSshHeaders(
      shared_ptr<BlockDataContainer>,
      shared_ptr<SSHheaders>);
   void grabExistingSSHHeaders(vector<StoredScriptHistory*>& sshVec);
   void computeDBKeys(shared_ptr<vector<StoredScriptHistory*>> saVec);
   void fetchExistingSshHeaders(map<BinaryData, StoredScriptHistory>& sshMap,
      const vector<StoredScriptHistory*>& saVec,
      uint32_t threadId);
   void fetchSshHeaders(map<BinaryData, StoredScriptHistory>& sshMap,
      const vector<StoredScriptHistory*>& saVec,
      map<BinaryData, pair<uint8_t, uint32_t>>& prefixes,
      uint32_t tId) const;
   vector<StoredScriptHistory*> checkForSubKeyCollisions(
      vector<StoredScriptHistory*>&);

   ///////
public:
   shared_ptr<map<BinaryData, StoredScriptHistory> > sshToModify_;
   map<BinaryData, pair<uint8_t, uint32_t>> topPrefix_;
   mutex mu_;
   static int collisionCount;

private:
   const uint32_t nThreads_;
   const uint32_t commitId_;
};

#endif