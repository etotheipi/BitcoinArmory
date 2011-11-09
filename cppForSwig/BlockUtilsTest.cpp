#include <iostream>
#include <fstream>
#include <string>
#include <sstream>
#include "UniversalTimer.h"
#include "BinaryData.h"
#include "BtcUtils.h"
#include "BlockUtils.h"


using namespace std;

void copyFile(string src, string dst)
{
   fstream fin(src.c_str(), ios::in | ios::binary);
   fstream fout(dst.c_str(), ios::out | ios::binary);
   if(fin == NULL || fout == NULL) { cout <<"error"; return; }
   // read from the first file then write to the second file
   char c;
   while(!fin.eof()) { fin.get(c); fout.put(c); }
}


int main(void)
{
   BlockDataManager_FullRAM & bdm = BlockDataManager_FullRAM::GetInstance(); 

   /////////////////////////////////////////////////////////////////////////////
   cout << "Reading data from blockchain..." << endl;
   TIMER_START("BDM_Load_and_Scan_BlkChain");
   bdm.readBlkFile_FromScratch("/home/alan/.bitcoin/blk0001.dat", false);
   //bdm.readBlkFile_FromScratch(
            //"C:/Documents and Settings/VBox/Application Data/Bitcoin/blk0001.dat",
            //false);  // false ~ don't organize blockchain, just create maps
   TIMER_STOP("BDM_Load_and_Scan_BlkChain");
   cout << endl << endl;

   /////////////////////////////////////////////////////////////////////////////
   cout << endl << "Organizing blockchain: " ;
   TIMER_START("BDM_Organize_Chain");
   bool isGenOnMainChain = bdm.organizeChain();
   TIMER_STOP("BDM_Organize_Chain");
   cout << (isGenOnMainChain ? "No Reorg!" : "Reorg Detected!") << endl;
   cout << endl << endl;

   /////////////////////////////////////////////////////////////////////////////
   //TESTNET has some 0.125-difficulty blocks which violates the assumption
   //that it never goes below 1
   //cout << "Verify integrity of blockchain file (merkleroots leading zeros on headers)" << endl;
   //TIMER_START("Verify blk0001.dat integrity");
   //bool isVerified = bdm.verifyBlkFileIntegrity();
   //TIMER_STOP("Verify blk0001.dat integrity");
   //cout << "Done!   Your blkfile " << (isVerified ? "is good!" : " HAS ERRORS") << endl;
   //cout << endl << endl;

/*
   /////////////////////////////////////////////////////////////////////////////
   cout << "Printing genesis block information:" << endl;
   bdm.getGenesisBlock().pprint(cout, 0, false);
   cout << endl << endl;

   cout << "Printing last block information:" << endl;
   bdm.getTopBlockHeader().pprint(cout, 0, false);
   cout << endl << endl;
   

   /////////////////////////////////////////////////////////////////////////////
   bdm.findAllNonStdTx();

*/

   /////////////////////////////////////////////////////////////////////////////
   BinaryData myAddress;
   BtcWallet wlt;
   
   // Test-network addresses
   //myAddress.createFromHex("abda0c878dd7b4197daa9622d96704a606d2cd14"); wlt.addAddress(myAddress);
   //myAddress.createFromHex("11b366edfc0a8b66feebae5c2e25a7b6a5d1cf31"); wlt.addAddress(myAddress);
   //myAddress.createFromHex("baa72d8650baec634cdc439c1b84a982b2e596b2"); wlt.addAddress(myAddress);
   //myAddress.createFromHex("fc0ef58380e6d4bcb9599c5369ce82d0bc01a5c4"); wlt.addAddress(myAddress);

   // Main-network addresses
   //myAddress.createFromHex("604875c897a079f4db88e5d71145be2093cae194"); wlt.addAddress(myAddress);
   //myAddress.createFromHex("8996182392d6f05e732410de4fc3fa273bac7ee6"); wlt.addAddress(myAddress);
   //myAddress.createFromHex("b5e2331304bc6c541ffe81a66ab664159979125b"); wlt.addAddress(myAddress);
   //myAddress.createFromHex("ebbfaaeedd97bc30df0d6887fd62021d768f5cb8"); wlt.addAddress(myAddress);

   myAddress.createFromHex("0e0aec36fe2545fb31a41164fb6954adcd96b342"); wlt.addAddress(myAddress);

   TIMER_WRAP(bdm.scanBlockchainForTx_FromScratch(wlt));
   
   cout << "Checking balance of all addresses: " << wlt.getNumAddr() << " addrs" << endl;
   for(uint32_t i=0; i<wlt.getNumAddr(); i++)
   {
      BinaryData addr20 = wlt.getAddrByIndex(i).getAddrStr20();
      cout << "  Addr: " << wlt.getAddrByIndex(i).getBalance() << ","
                         << wlt.getAddrByHash160(addr20).getBalance() << endl;
      vector<LedgerEntry> const & ledger = wlt.getAddrByIndex(i).getTxLedger();
      for(uint32_t j=0; j<ledger.size(); j++)
      {  
         cout << "    Tx: " 
           << ledger[j].getAddrStr20().getSliceCopy(0,4).toHexStr() << "  "
           << ledger[j].getValue()/(float)(CONVERTBTC) << " (" 
           << ledger[j].getBlockNum()
           << ")  TxHash: " << ledger[j].getTxHash().getSliceCopy(0,4).toHexStr() << endl;
      }

   }
   cout << endl << endl;

/*
   /////////////////////////////////////////////////////////////////////////////
   myAddress.createFromHex("f62242a747ec1cb02afd56aac978faf05b90462e");
   wlt.addAddress(myAddress);
   myAddress.createFromHex("6300bf4c5c2a724c280b893807afb976ec78a92b");
   wlt.addAddress(myAddress);
   TIMER_WRAP(bdm.scanBlockchainForTx_FromScratch(wlt));

   cout << "Checking balance of all addresses: " << wlt.getNumAddr() << "addrs" << endl;
   for(uint32_t i=0; i<wlt.getNumAddr(); i++)
   {
      BinaryData addr20 = wlt.getAddrByIndex(i).getAddrStr20();
      cout << "  Addr: " << wlt.getAddrByIndex(i).getBalance() << ","
                         << wlt.getAddrByHash160(addr20).getBalance() << endl;

   }
*/


   cout << "Printing SORTED allAddr ledger..." << endl;
   wlt.sortLedger();
   vector<LedgerEntry> const & ledgerAll = wlt.getTxLedger();
   for(uint32_t j=0; j<ledgerAll.size(); j++)
   {  
      cout << "    Tx: " 
           << ledgerAll[j].getAddrStr20().toHexStr() << "  "
           << ledgerAll[j].getValue()/1e8 << " (" 
           << ledgerAll[j].getBlockNum()
           << ")  TxHash: " << ledgerAll[j].getTxHash().getSliceCopy(0,4).toHexStr() << endl;
           
   }


   /////////////////////////////////////////////////////////////////////////////
   cout << "Test txout aggregation, with different prioritization schemes" << endl;

   BtcWallet myWallet;

   // Testnet addresses
   //myAddress.createFromHex("d184cea7e82c775d08edd288344bcd663c3f99a2"); myWallet.addAddress(myAddress);
   //myAddress.createFromHex("205fa00890e6898b987de6ff8c0912805416cf90"); myWallet.addAddress(myAddress);
   //myAddress.createFromHex("fc0ef58380e6d4bcb9599c5369ce82d0bc01a5c4"); myWallet.addAddress(myAddress);
   myAddress.createFromHex("0e0aec36fe2545fb31a41164fb6954adcd96b342"); myWallet.addAddress(myAddress);

   cout << "Rescanning the blockchain for new addresses." << endl;
   bdm.scanBlockchainForTx_FromScratch(myWallet);

   vector< vector<UnspentTxOut> > sortedUTOs(4);
   //sortedUTOs[0] = bdm.getUnspentTxOutsForWallet(myWallet, 0);
   sortedUTOs[1] = bdm.getUnspentTxOutsForWallet(myWallet, 1);
   //sortedUTOs[2] = bdm.getUnspentTxOutsForWallet(myWallet, 2);
   //sortedUTOs[3] = bdm.getUnspentTxOutsForWallet(myWallet, 3);

   //for(int i=0; i<4; i++)
   //{
      int i=1;
      cout << "   Sorting Method: " << i << endl;
      cout << "   Value\t#Conf\tTxHash\tTxIdx" << endl;
      for(int j=0; j<sortedUTOs[i].size(); j++)
      {
         cout << "   "
              << sortedUTOs[i][j].getValue()/1e8 << "\t"
              << sortedUTOs[i][j].getNumConfirm() << "\t"
              << sortedUTOs[i][j].getTxHash().toHexStr() << "\t"
              << sortedUTOs[i][j].getTxOutIndex() << endl;
      }
      cout << endl;


   /////////////////////////////////////////////////////////////////////////////
   //
   // BLOCKCHAIN REORGANIZATION UNIT-TEST
   //
   /////////////////////////////////////////////////////////////////////////////
   //
   // NOTE:  The unit-test files (blk_0_to_4, blk_3A, etc) are located in 
   //        cppForSwig/reorgTest.  These files represent a very small 
   //        blockchain with a double-spend and a couple invalidated 
   //        coinbase tx's.  All tx-hashes & OutPoints are consistent,
   //        all transactions have real ECDSA signatures, and blockheaders
   //        have four leading zero-bytes to be valid at difficulty=1
   //        
   //        If you were to set COINBASE_MATURITY=1 (not applicable here)
   //        this would be a *completely valid* blockchain--just a very 
   //        short blockchain.
   //
   //        FYI: The first block is the *actual* main-network genesis block
   //
   
   string blk04("reorgTest/blk_0_to_4.dat");
   string blk3A("reorgTest/blk_3A.dat");
   string blk4A("reorgTest/blk_4A.dat");
   string blk5A("reorgTest/blk_5A.dat");

   BtcWallet wlt2;
   wlt2.addAddress(BinaryData::CreateFromHex("62e907b15cbf27d5425399ebf6f0fb50ebb88f18"));
   wlt2.addAddress(BinaryData::CreateFromHex("ee26c56fc1d942be8d7a24b2a1001dd894693980"));
   wlt2.addAddress(BinaryData::CreateFromHex("cb2abde8bccacc32e893df3a054b9ef7f227a4ce"));
   wlt2.addAddress(BinaryData::CreateFromHex("c522664fb0e55cdc5c0cea73b4aad97ec8343232"));

                   
   cout << endl << endl;
   cout << "Preparing blockchain-reorganization test!" << endl;
   cout << "Resetting block-data mgr...";
   bdm.Reset();
   cout << "Done!" << endl;
   cout << "Reading in initial block chain (Blocks 0 through 4)..." ;
   bdm.readBlkFile_FromScratch("reorgTest/blk_0_to_4.dat");
   bdm.organizeChain();
   cout << "Done" << endl;

   //
   // TODO: Let's look at the address ledger after the first chain
   //       Then look at it again after the reorg.  What we want
   //       to see is the presence of an invalidated tx, not just
   //       a disappearing tx -- the user must be informed that a 
   //       tx they previously thought they owned is now invalid.
   //       If the user is not informed, they could go crazy trying
   //       to figure out what happened to this money they thought
   //       they had.
   cout << "Constructing address ledger for the to-be-invalidated chain:" << endl;
   bdm.scanBlockchainForTx_FromScratch(wlt2);
   vector<LedgerEntry> const & ledgerAll2 = wlt2.getTxLedger();
   for(uint32_t j=0; j<ledgerAll2.size(); j++)
   {  
      cout << "    Tx: " 
           << ledgerAll2[j].getValue()/1e8
           << " (" << ledgerAll2[j].getBlockNum() << ")"
           << "  TxHash: " << ledgerAll2[j].getTxHash().getSliceCopy(0,4).toHexStr();
      if(!ledgerAll2[j].isValid())      cout << " (INVALID) ";
      if( ledgerAll2[j].isSentToSelf()) cout << " (SENT_TO_SELF) ";
      if( ledgerAll2[j].isChangeBack()) cout << " (RETURNED CHANGE) ";
      cout << endl;
   }
   cout << "Checking balance of all addresses: " << wlt2.getNumAddr() << "addrs" << endl;
   cout << "                          Balance: " << wlt2.getBalance()/1e8 << endl;
   for(uint32_t i=0; i<wlt2.getNumAddr(); i++)
   {
      BinaryData addr20 = wlt2.getAddrByIndex(i).getAddrStr20();
      cout << "  Addr: " << wlt2.getAddrByIndex(i).getBalance()/1e8 << ","
                         << wlt2.getAddrByHash160(addr20).getBalance() << endl;
      vector<LedgerEntry> const & ledger = wlt2.getAddrByIndex(i).getTxLedger();
      for(uint32_t j=0; j<ledger.size(); j++)
      {  
         cout << "    Tx: " 
              << ledger[j].getAddrStr20().getSliceCopy(0,4).toHexStr() << "  "
              << ledger[j].getValue()/(float)(CONVERTBTC) << " (" 
              << ledger[j].getBlockNum()
              << ")  TxHash: " << ledger[j].getTxHash().getSliceCopy(0,4).toHexStr();
         if( ! ledger[j].isValid())  cout << " (INVALID) ";
         cout << endl;
      }

   }



   // prepare the other block to be read in
   ifstream is;
   BinaryData blk3a, blk4a, blk5a;
   assert(blk3a.readBinaryFile("reorgTest/blk_3A.dat") != -1);
   assert(blk4a.readBinaryFile("reorgTest/blk_4A.dat") != -1);
   assert(blk5a.readBinaryFile("reorgTest/blk_5A.dat") != -1);
   vector<bool> result;

   /////
   cout << "Pushing Block 3A into the BDM:" << endl;
   result = bdm.addNewBlockData(blk3a);

   /////
   cout << "Pushing Block 4A into the BDM:" << endl;
   result = bdm.addNewBlockData(blk4a);

   /////
   cout << "Pushing Block 5A into the BDM:" << endl;
   result = bdm.addNewBlockData(blk5a);
   if(result[ADD_BLOCK_CAUSED_REORG] == true)
   {
      cout << "Reorg happened after pushing block 5A" << endl;
      bdm.scanBlockchainForTx_FromScratch(wlt2);
      bdm.updateWalletAfterReorg(wlt2);
   }

   cout << "Checking balance of entire wallet: " << wlt2.getBalance()/1e8 << endl;
   vector<LedgerEntry> const & ledgerAll3 = wlt2.getTxLedger();
   for(uint32_t j=0; j<ledgerAll3.size(); j++)
   {  
      cout << "    Tx: " 
           << ledgerAll3[j].getValue()/1e8
           << " (" << ledgerAll3[j].getBlockNum() << ")"
           << "  TxHash: " << ledgerAll3[j].getTxHash().getSliceCopy(0,4).toHexStr();
      if(!ledgerAll3[j].isValid())      cout << " (INVALID) ";
      if( ledgerAll3[j].isSentToSelf()) cout << " (SENT_TO_SELF) ";
      if( ledgerAll3[j].isChangeBack()) cout << " (RETURNED CHANGE) ";
      cout << endl;
   }

   cout << "Checking balance of all addresses: " << wlt2.getNumAddr() << "addrs" << endl;
   for(uint32_t i=0; i<wlt2.getNumAddr(); i++)
   {
      BinaryData addr20 = wlt2.getAddrByIndex(i).getAddrStr20();
      cout << "  Addr: " << wlt2.getAddrByIndex(i).getBalance()/1e8 << ","
                         << wlt2.getAddrByHash160(addr20).getBalance()/1e8 << endl;
      vector<LedgerEntry> const & ledger = wlt2.getAddrByIndex(i).getTxLedger();
      for(uint32_t j=0; j<ledger.size(); j++)
      {  
         cout << "    Tx: " 
              << ledger[j].getAddrStr20().getSliceCopy(0,4).toHexStr() << "  "
              << ledger[j].getValue()/(float)(CONVERTBTC) << " (" 
              << ledger[j].getBlockNum()
              << ")  TxHash: " << ledger[j].getTxHash().getSliceCopy(0,4).toHexStr();
         if( ! ledger[j].isValid())
            cout << " (INVALID) ";
         cout << endl;
      }

   }
   /////////////////////////////////////////////////////////////////////////////
   //
   // END BLOCKCHAIN REORG UNIT-TEST
   //
   /////////////////////////////////////////////////////////////////////////////
  




   /////////////////////////////////////////////////////////////////////////////
   // ***** print out all timings to stdout and a csv file *****
   //       this file can be loaded into a spreadsheet,
   //       but it's not the prettiest thing...
   UniversalTimer::instance().print();
   UniversalTimer::instance().printCSV("timings.csv");
   cout << endl << endl;
   



   char pause[256];
   cout << "enter anything to exit" << endl;
   cin >> pause;


}
