#include <iostream>
#include <fstream>
#include "blockUtils.h"
#include "binaryData.h"
#include "UniversalTimer.h"



int main(void)
{
   binaryData bd(32);
   for(int i=0; i<32; i++) 
      bd[i] = i;

   cout << bd.toHex().c_str() << endl;

   BlockHeadersManager & bhm = BlockHeadersManager::GetInstance(); 

   binaryData genBlock;
   string strgenblk = "0100000000000000000000000000000000000000000000000000000000000000000000003ba3edfd7a7b12b27ac72c3e67768f617fc81bc3888a51323a9fb8aa4b1e5e4a29ab5f49ffff001d1dac2b7c";

   TIMER_START("Single_Hash_2x_SHA256");
   genBlock.createFromHex(strgenblk);
   TIMER_STOP("Single_Hash_2x_SHA256");
   //cout << "The genesis block (hex): " << endl << "\t" << genBlock.toHex().c_str() << endl;
   string strrndtrip = genBlock.toHex();

   //cout << "Orig : " << strgenblk.c_str() << endl;
   //cout << "New  : " << strrndtrip.c_str() << endl;
   //cout << "Equal: " << (strrndtrip == strgenblk ? "EQUAL" : "NOT_EQUAL") << endl;

   binaryData theHash;   
   for(int i=0; i<200000; i++)
   {
      TIMER_START("BHM_GetHash");
      BlockHeadersManager::getHash(genBlock.getPtr(), theHash);
      TIMER_STOP("BHM_GetHash");
   }
   cout << "The hash of the genesis block:" << endl << "\t" << theHash.toHex().c_str() << endl;

   TIMER_START("BHM_Import_Headers");
   //bhm.importHeadersFromBlockFile("../blk0001.dat");
   bhm.importHeadersFromHeaderFile("../blkHeaders.dat");
   TIMER_STOP("BHM_Import_Headers");

   TIMER_START("BHM_Organize_Chain");
   bool isGenOnMainChain = bhm.organizeChain();
   TIMER_STOP("BHM_Organize_Chain");

   cout << endl << endl;
   cout << "Printing genesis block information:" << endl;
   bhm.getGenesisBlock().printBlockHeader(cout);

   cout << endl << endl;
   cout << "Printing last block information:" << endl;
   bhm.getTopBlock().printBlockHeader(cout);

   UniversalTimer::instance().print();
   int i;
   cout << "Type something to exit";
   cin >> i;
}
