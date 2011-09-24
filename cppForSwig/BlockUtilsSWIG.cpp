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

SWIG_BlockHeader SWIG_BlockchainManager::getHeaderByHash(BinaryData const & hash)
{
   assert(isBlockChainLoaded_);
   BlockDataManager_FullRAM & bdm = BlockDataManager_FullRAM::GetInstance();

   return SWIG_BlockHeader(*bdm.getHeaderByHash(hash));
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


vector<int> SWIG_BlockchainManager::getTop10BlockHeights(void)
{
   uint32_t topHeight = getTopBlockHeight();
   vector<int> out(10);
   for(int i=0; i<10; i++)
      out[i] = topHeight-i;

   return out;
}




vector<BinaryData> SWIG_BlockchainManager::getTop10BlockHashes(void)
{
   uint32_t topHeight = getTopBlockHeight();
   vector<BinaryData> out(10);
   for(int i=0; i<10; i++)
      out[i] = getHeaderByHeight(topHeight - i).getThisHash();

   return out;
}
