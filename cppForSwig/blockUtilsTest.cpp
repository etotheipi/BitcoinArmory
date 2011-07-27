#include <iostream>
#include <fstream>
#include "sha2.h"
#include "blockUtils.h"
#include "binaryData.h"



int main(void)
{
   binaryData bd(32);
   for(int i=0; i<32; i++) 
      bd[i] = i;

   cout << bd.toHex().c_str() << endl;

   BlockHeadersManager & bhm = BlockHeadersManager::GetInstance(); 

   binaryData genBlock;
   genBlock.createFromHex("0100000000000000000000000000000000000000000000000000000000000000000000003ba3edfd7a7b12b27ac72c3e67768f617fc81bc3888a51323a9fb8aa4b1e5e4a29ab5f49ffff001d1dac2b7c");
   cout << "The genesis block (hex): " << endl << "\t" << genBlock.toHex().c_str() << endl;

   binaryData theHash;   
   BlockHeadersManager::getHash(genBlock.getPtr(), theHash);
   cout << "The hash of the genesis block:" << endl << "\t" << theHash.toHex().c_str() << endl;

   bhm.importDataFromFile("../blkheaders.dat");


}
