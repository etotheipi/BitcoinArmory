#include <iostream>
#include <string>
#include <vector>
#include <map>
#include <cassert>
#include "BlockUtilsSWIG.h"

void SWIG_BlockchainManager::loadBlockchain(char* filename)
{
   BlockDataManager_FullRAM & bdm = BlockDataManager_FullRAM::GetInstance();

   bdm.readBlockchainFromBlkFile_FullRAM_FromScratch(string(filename));
   bdm.organizeChain();
   isBlockChainLoaded_ = true;
}

void SWIG_BlockchainManager::resetBlockchainData(void)
{
   BlockDataManager_FullRAM & bdm = BlockDataManager_FullRAM::GetInstance();

   bdm.Reset();
   isBlockChainLoaded_ = false;
}

SWIG_BlockHeader SWIG_BlockchainManager::getHeaderByHeight(uint32_t h)
{
   assert(isBlockChainLoaded_);
   BlockDataManager_FullRAM & bdm = BlockDataManager_FullRAM::GetInstance();

   return SWIG_BlockHeader(*bdm.getHeaderByHeight(h));
}

SWIG_BlockHeader SWIG_BlockchainManager::getHeaderByHash(char* hash)
{
   assert(isBlockChainLoaded_);
   BlockDataManager_FullRAM & bdm = BlockDataManager_FullRAM::GetInstance();

   BinaryData bdhash((uint8_t*)hash, 32);
   return SWIG_BlockHeader(*bdm.getHeaderByHash(bdhash));
}

SWIG_BlockHeader SWIG_BlockchainManager::getTopBlockHeader(void)
{
   assert(isBlockChainLoaded_);
   BlockDataManager_FullRAM & bdm = BlockDataManager_FullRAM::GetInstance();

   return SWIG_BlockHeader(bdm.getTopBlock());
}

uint32_t SWIG_BlockchainManager::getTopBlockHeight(void)
{
   assert(isBlockChainLoaded_);
   BlockDataManager_FullRAM & bdm = BlockDataManager_FullRAM::GetInstance();

   return bdm.getTopBlock().getBlockHeight();
}







