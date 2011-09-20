#include <iostream>
#include <string>
#include <vector>
#include <map>
#include "BlockUtilsSWIG.h"

SWIG_BlockchainManager::SWIG_BlockchainManager(void)
{
   bdm_ = &(BlockDataManager_FullRAM.GetInstance());
}

void SWIG_BlockchainManager::addPublicKey(string binPubKey65Str)
{
   BinaryData binPubKey(binPubKeyStr);
      
}
