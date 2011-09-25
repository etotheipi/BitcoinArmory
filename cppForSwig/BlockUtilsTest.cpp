#include <iostream>
#include <fstream>
#include "UniversalTimer.h"
#include "BinaryData.h"
#include "BtcUtils.h"
#include "BlockUtils.h"


using namespace std;

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
   //cout << "Contains test (T): " << testContains.find(a) << endl;
   //cout << "Contains test (F): " << testContains.find(b) << endl;
   //cout << "Contains test (T): " << testContains.find(c) << endl;
   //cout << "Contains test (F): " << testContains.find(d) << endl;
   //cout << "Contains test (T): " << testContains.find(e) << endl;
   //cout << "Contains test (T): " << testContains.find(f) << endl;


   //cout << "Orig : " << strgenblk.c_str() << endl;
   //cout << "New  : " << strrndtrip.c_str() << endl;
   //cout << "Equal: " << (strrndtrip == strgenblk ? "EQUAL" : "NOT_EQUAL") << endl;

   BinaryData theHash;   
   for(int i=0; i<20000; i++)
   {
      TIMER_START("BinaryData::GetHash");
      BtcUtils::getHash256(genBlock, theHash);
      TIMER_STOP("BinaryData::GetHash");
   }
   cout << "The hash of the genesis block:" << endl << "\t" << theHash.toHex().c_str() << endl;
   cout << endl << endl;

   //TIMER_START("BDM_Import_Headers");
   //bdm.importFromBlockFile("../blk0001.dat", false);
   //bdm.importHeadersFromHeaderFile("../blkHeaders.dat");
   //TIMER_STOP("BDM_Import_Headers");
   
   // Reading data from blockchain
   cout << "Reading data from blockchain..." << endl;
   TIMER_START("BDM_Read_BlkChain_From_Scratch");
   bdm.readBlkFile_FromScratch("../blk0001.dat");
   TIMER_STOP("BDM_Read_BlkChain_From_Scratch");
   cout << endl << endl;

   cout << endl << "Organizing blockchain: " ;
   TIMER_START("BDM_Organize_Chain");
   bool isGenOnMainChain = bdm.organizeChain();
   TIMER_STOP("BDM_Organize_Chain");
   cout << (isGenOnMainChain ? "No Reorg!" : "Reorg Detected!") << endl;
   cout << endl << endl;

   //TIMER_START("BDM_Flag_Transactions");
   //bdm.flagMyTransactions();
   //TIMER_STOP("BDM_Flag_Transactions");


   cout << endl << endl;
   cout << "Printing genesis block information:" << endl;
   bdm.getGenesisBlock().getCopy().printBlockHeader(cout);

   cout << endl << endl;
   cout << "Printing last block information:" << endl;
   bdm.getTopBlock().getCopy().printBlockHeader(cout);


   BinaryData myAddress, myPubKey;
   BtcWallet wlt;
   //myAddress.createFromHex("abda0c878dd7b4197daa9622d96704a606d2cd1463794a22");
   myAddress.createFromHex("abda0c878dd7b4197daa9622d96704a606d2cd14");
   myPubKey.createFromHex("04e02e7826c63038fa3e6a416b74b85bc4db2b5125f039bb5b0139842655d0faec750ec639c380c0cbc070650037b17a1a6a101391422ff9827a27010990ae1acd");
   wlt.addAddress(myAddress, myPubKey);
   //myAddress.swapEndian();
   //myPubKey.swapEndian();

   myAddress.createFromHex("f62242a747ec1cb02afd56aac978faf05b90462e");
   wlt.addAddress(myAddress);

   myAddress.createFromHex("11b366edfc0a8b66feebae5c2e25a7b6a5d1cf31");
   wlt.addAddress(myAddress);

   TIMER_WRAP(bdm.scanBlockchainForTx_FromScratch(wlt));
   //TIMER_WRAP(bdm.scanBlockchainForTx_FromScratch_AllAddr());
   
   cout << "Checking balance of all addresses: " << wlt.getNumAddr() << "addrs" << endl;
   for(uint32_t i=0; i<wlt.getNumAddr(); i++)
   {
      BinaryData addr20 = wlt.getAddrByIndex(i).address20_;
      cout << "\tAddr: " << wlt.getAddrByIndex(i).getBalance() << ","
                         << wlt.getAddrByHash160(addr20).getBalance() << endl;

   }

   UniversalTimer::instance().print();
   UniversalTimer::instance().printCSV("timings.csv");

   bdm.Reset();



   char aa[256];
   cout << "Enter anything to exit" << endl;
   cin >> aa;
}
