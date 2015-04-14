#ifndef _SSHHEADERS_H
#define _SSHHEADERS_H

#include <memory>
#include "BinaryData.h"
#include "StoredBlockObj.h"

class BlockDataContainer;
class ScrAddrFilter;

class SSHheaders
{
public:
   SSHheaders(uint32_t nThreads)
      : nThreads_(nThreads)
   {}

   unique_lock<mutex>* getSshHeaders(shared_ptr<BlockDataContainer>);
   void buildSshHeadersFromSAF(const ScrAddrFilter& SAF);
   void processSshHeaders(vector<BinaryData>& scrAddrs);

private:
   void processSshHeaders(
      shared_ptr<BlockDataContainer>,
      const map<BinaryData, StoredScriptHistory>&);
   void computeDBKeys(vector<vector<const BinaryData*>>& saVec);
   void fetchSshHeaders(map<BinaryData, StoredScriptHistory>& sshMap,
      const vector<const BinaryData*>& saVec);
   void checkForSubKeyCollisions(void);

   ///////
public:
   shared_ptr<map<BinaryData, StoredScriptHistory> > sshToModify_;
   mutex mu_;

private:
   const uint32_t nThreads_;
};

#endif