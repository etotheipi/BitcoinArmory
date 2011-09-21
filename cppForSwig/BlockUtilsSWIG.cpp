#include <iostream>
#include <string>
#include <vector>
#include <map>
#include <cassert>
#include "BlockUtilsSWIG.h"

void SWIG_BlockchainManager::loadBlockchain(string filename)
{
   BlockDataManager_FullRAM & bdm = BlockDataManager_FullRAM::GetInstance();

   bdm.readBlockchainFromBlkFile_FullRAM_FromScratch(filename);
   bdm.organizeChain();
   isBlockChainLoaded_ = true;
}

SWIG_BlockHeader SWIG_BlockchainManager::getHeaderByHeight(uint32_t h)
{
   assert(isBlockChainLoaded_);
   BlockDataManager_FullRAM & bdm = BlockDataManager_FullRAM::GetInstance();

   return SWIG_BlockHeader(*bdm.getHeaderByHeight(h));
}

SWIG_BlockHeader SWIG_BlockchainManager::getHeaderByHash(string hash)
{
   assert(isBlockChainLoaded_);
   BlockDataManager_FullRAM & bdm = BlockDataManager_FullRAM::GetInstance();

   return SWIG_BlockHeader(*bdm.getHeaderByHash(BinaryData(hash)));
}









