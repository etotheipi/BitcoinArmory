#include <iostream>
#include <fstream>
#include "blockUtils.h"
#include "BinaryData.h"
#include "BtcUtils.h"
#include "UniversalTimer.h"



int main(void)
{
   BinaryData bd(32);
   for(int i=0; i<32; i++) 
      bd[i] = i;

   cout << bd.toHex().c_str() << endl;

   BlockDataManager_FullRAM & bdm = BlockDataManager_FullRAM::GetInstance(); 

   BinaryData genBlock;
   string strgenblk = "0100000000000000000000000000000000000000000000000000000000000000000000003ba3edfd7a7b12b27ac72c3e67768f617fc81bc3888a51323a9fb8aa4b1e5e4a29ab5f49ffff001d1dac2b7c";

   TIMER_START("Single_Hash_2x_SHA256");
   genBlock.createFromHex(strgenblk);
   TIMER_STOP("Single_Hash_2x_SHA256");
   //cout << "The genesis block (hex): " << endl << "\t" << genBlock.toHex().c_str() << endl;
   string strrndtrip = genBlock.toHex();

   BinaryData testContains, a, b, c, d, e, f;
   testContains.createFromHex("00112233aabbccdd0000111122223333aaaabbbbccccdddd0000000001111111112222222233333333");
   a.createFromHex("0011");
   b.createFromHex("0012");
   c.createFromHex("2233");
   d.createFromHex("ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff");
   e.createFromHex("33333333");
   f.createFromHex("00112233aabbccdd0000111122223333aaaabbbbccccdddd0000000001111111112222222233333333");
   cout << "Contains test (T): " << testContains.find(a) << endl;
   cout << "Contains test (F): " << testContains.find(b) << endl;
   cout << "Contains test (T): " << testContains.find(c) << endl;
   cout << "Contains test (F): " << testContains.find(d) << endl;
   cout << "Contains test (T): " << testContains.find(e) << endl;
   cout << "Contains test (T): " << testContains.find(f) << endl;

   BinaryData myAddress, myPubKey;
   myAddress.createFromHex("abda0c878dd7b4197daa9622d96704a606d2cd1463794a22");
   myPubKey.createFromHex("e02e7826c63038fa3e6a416b74b85bc4db2b5125f039bb5b0139842655d0faec750ec639c380c0cbc070650037b17a1a6a101391422ff9827a27010990ae1acd");
   //myAddress.swapEndian();
   //myPubKey.swapEndian();

   bdm.addAccount(&myAddress, &myPubKey);

   //cout << "Orig : " << strgenblk.c_str() << endl;
   //cout << "New  : " << strrndtrip.c_str() << endl;
   //cout << "Equal: " << (strrndtrip == strgenblk ? "EQUAL" : "NOT_EQUAL") << endl;

   /*
   BinaryData theHash;   
   for(int i=0; i<20000; i++)
   {
      TIMER_START("BinaryData::GetHash");
      BinaryData::getHash256(genBlock, theHash);
      TIMER_STOP("BinaryData::GetHash");
   }
   cout << "The hash of the genesis block:" << endl << "\t" << theHash.toHex().c_str() << endl;

   TIMER_START("BDM_Import_Headers");
   bdm.importFromBlockFile("../blk0001.dat", false);
   //bdm.importHeadersFromHeaderFile("../blkHeaders.dat");
   TIMER_STOP("BDM_Import_Headers");

   TIMER_START("BDM_Organize_Chain");
   bool isGenOnMainChain = bdm.organizeChain();
   TIMER_STOP("BDM_Organize_Chain");
   */

   /*
   TIMER_START("BDM_Flag_Transactions");
   bdm.flagMyTransactions();
   TIMER_STOP("BDM_Flag_Transactions");
   */

   //cout << endl << endl;
   //cout << "Printing genesis block information:" << endl;
   //bdm.getGenesisBlock().printBlockHeader(cout);

   //cout << endl << endl;
   //cout << "Printing last block information:" << endl;
   //bdm.getTopBlock().printBlockHeader(cout);

   //UniversalTimer::instance().print();
   //UniversalTimer::instance().printCSV("timings.csv");

   //char aa[256];
   //cout << "Enter anything to exit" << endl;
   //cin >> aa;
}
