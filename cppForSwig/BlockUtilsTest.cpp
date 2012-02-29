#include <iostream>
#include <fstream>
#include <string>
#include <sstream>
#include "UniversalTimer.h"
#include "BinaryData.h"
#include "BtcUtils.h"
#include "BlockUtils.h"
#include "EncryptionUtils.h"


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


////////////////////////////////////////////////////////////////////////////////
void TestReadAndOrganizeChain(string blkfile);
void TestFindNonStdTx(string blkfile);
void TestScanForWalletTx(string blkfile);
void TestReorgBlockchain(string blkfile);
void TestZeroConf(void);
void TestCrypto(void);
void TestECDSA(void);
////////////////////////////////////////////////////////////////////////////////

void printTestHeader(string TestName)
{
   cout << endl;
   for(int i=0; i<80; i++) cout << "*";
   cout << endl << "Execute test: " << TestName << endl;
   for(int i=0; i<80; i++) cout << "*";
   cout << endl;
}

int main(void)
{
   BlockDataManager_FullRAM::GetInstance().SelectNetwork("Test");
   

   //string blkfile("/home/alan/.bitcoin/blk0001.dat");
   //string blkfile("/home/alan/.bitcoin/testnet/blk0001.dat");
   //string blkfile("C:/Documents and Settings/VBox/Application Data/Bitcoin/testnet/blk0001.dat");

   //printTestHeader("Read-and-Organize-Blockchain");
   //TestReadAndOrganizeChain(blkfile);

   //printTestHeader("Find-Non-Standard-Tx");
   //TestFindNonStdTx(blkfile);

   //printTestHeader("Wallet-Relevant-Tx-Scan");
   //TestScanForWalletTx(blkfile);

   //printTestHeader("Blockchain-Reorg-Unit-Test");
   //TestReorgBlockchain(blkfile);

   //printTestHeader("Testing Zero-conf handling");
   //TestZeroConf();

   //printTestHeader("Crypto-KDF-and-AES-methods");
   //TestCrypto();

   printTestHeader("Crypto-ECDSA-sign-verify");
   TestECDSA();

   /////////////////////////////////////////////////////////////////////////////
   // ***** Print out all timings to stdout and a csv file *****
   //       Any method, anywhere, that called UniversalTimer
   //       will end up having it's named timers printed out
   //       This file can be loaded into a spreadsheet,
   //       but it's not the prettiest thing...
   UniversalTimer::instance().print();
   UniversalTimer::instance().printCSV("timings.csv");
   cout << endl << endl;
   char pause[256];
   cout << "enter anything to exit" << endl;
   cin >> pause;
}







void TestReadAndOrganizeChain(string blkfile)
{
   BlockDataManager_FullRAM & bdm = BlockDataManager_FullRAM::GetInstance(); 
   /////////////////////////////////////////////////////////////////////////////
   cout << "Reading data from blockchain..." << endl;
   TIMER_START("BDM_Load_and_Scan_BlkChain");
   bdm.readBlkFile_FromScratch(blkfile, false);  // don't organize, just index
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
   // TESTNET has some 0.125-difficulty blocks which violates the assumption
   // that it never goes below 1.  So, need to comment this out for testnet
   /*  For whatever reason, this doesn't work on testnet...
   cout << "Verify integrity of blockchain file (merkleroots leading zeros on headers)" << endl;
   TIMER_START("Verify blk0001.dat integrity");
   bool isVerified = bdm.verifyBlkFileIntegrity();
   TIMER_STOP("Verify blk0001.dat integrity");
   cout << "Done!   Your blkfile " << (isVerified ? "is good!" : " HAS ERRORS") << endl;
   cout << endl << endl;
   */
}



void TestFindNonStdTx(string blkfile)
{
   BlockDataManager_FullRAM & bdm = BlockDataManager_FullRAM::GetInstance(); 
   bdm.readBlkFile_FromScratch(blkfile, false);  // don't organize, just index
   // This is mostly just for debugging...
   bdm.findAllNonStdTx();
   // At one point I had code to print out nonstd txinfo... not sure
   // what happened to it...
}



void TestScanForWalletTx(string blkfile)
{
   BlockDataManager_FullRAM & bdm = BlockDataManager_FullRAM::GetInstance(); 
   bdm.readBlkFile_FromScratch(blkfile);
   /////////////////////////////////////////////////////////////////////////////
   BinaryData myAddress;
   BtcWallet wlt;
   
   // Main-network addresses
   myAddress.createFromHex("604875c897a079f4db88e5d71145be2093cae194"); wlt.addAddress(myAddress);
   myAddress.createFromHex("8996182392d6f05e732410de4fc3fa273bac7ee6"); wlt.addAddress(myAddress);
   myAddress.createFromHex("b5e2331304bc6c541ffe81a66ab664159979125b"); wlt.addAddress(myAddress);
   myAddress.createFromHex("ebbfaaeedd97bc30df0d6887fd62021d768f5cb8"); wlt.addAddress(myAddress);
   myAddress.createFromHex("11b366edfc0a8b66feebae5c2e25a7b6a5d1cf31"); wlt.addAddress(myAddress);
   // Test-network addresses
   //myAddress.createFromHex("5aa2b7e93537198ef969ad5fb63bea5e098ab0cc"); wlt.addAddress(myAddress);
   //myAddress.createFromHex("28b2eb2dc53cd15ab3dc6abf6c8ea3978523f948"); wlt.addAddress(myAddress);
   //myAddress.createFromHex("720fbde315f371f62c158b7353b3629e7fb071a8"); wlt.addAddress(myAddress);
   //myAddress.createFromHex("0cc51a562976a075b984c7215968d41af43be98f"); wlt.addAddress(myAddress);
   //myAddress.createFromHex("57ac7bfb77b1f678043ac6ea0fa67b4686c271e5"); wlt.addAddress(myAddress);
   //myAddress.createFromHex("b11bdcd6371e5b567b439cd95d928e869d1f546a"); wlt.addAddress(myAddress);
   //myAddress.createFromHex("2bb0974f6d43e3baa03d82610aac2b6ed017967d"); wlt.addAddress(myAddress);
   //myAddress.createFromHex("61d62799e52bc8ee514976a19d67478f25df2bb1"); wlt.addAddress(myAddress);

   // More testnet addresses, with only a few transactions
   myAddress.createFromHex("0c6b92101c7025643c346d9c3e23034a8a843e21"); wlt.addAddress(myAddress);
   myAddress.createFromHex("34c9f8dc91dfe1ae1c59e76cbe1aa39d0b7fc041"); wlt.addAddress(myAddress);
   myAddress.createFromHex("d77561813ca968270d5f63794ddb6aab3493605e"); wlt.addAddress(myAddress);
   myAddress.createFromHex("0e0aec36fe2545fb31a41164fb6954adcd96b342"); wlt.addAddress(myAddress);

   TIMER_WRAP(bdm.scanBlockchainForTx(wlt));
   TIMER_WRAP(bdm.scanBlockchainForTx(wlt));
   TIMER_WRAP(bdm.scanBlockchainForTx(wlt));
   
   cout << "Checking balance of all addresses: " << wlt.getNumAddr() << " addrs" << endl;
   for(uint32_t i=0; i<wlt.getNumAddr(); i++)
   {
      BinaryData addr20 = wlt.getAddrByIndex(i).getAddrStr20();
      cout << "  Addr: " << wlt.getAddrByIndex(i).getFullBalance() << ","
                         << wlt.getAddrByHash160(addr20).getFullBalance() << endl;
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

#ifndef TEST_NETWORK
   // TODO:  I somehow borked my list of test addresses.  Make sure I have some
   //        test addresses in here for each network that usually has lots of 
   //        unspent TxOuts
   
   // Main-network addresses
   myAddress.createFromHex("0e0aec36fe2545fb31a41164fb6954adcd96b342"); myWallet.addAddress(myAddress);
#else
   // Testnet addresses
   //myAddress.createFromHex("d184cea7e82c775d08edd288344bcd663c3f99a2"); myWallet.addAddress(myAddress);
   //myAddress.createFromHex("205fa00890e6898b987de6ff8c0912805416cf90"); myWallet.addAddress(myAddress);
   //myAddress.createFromHex("fc0ef58380e6d4bcb9599c5369ce82d0bc01a5c4"); myWallet.addAddress(myAddress);
#endif

   cout << "Rescanning the blockchain for new addresses." << endl;
   bdm.scanBlockchainForTx(myWallet);

   //vector<UnspentTxOut> sortedUTOs = bdm.getUnspentTxOutsForWallet(myWallet, 1);
   vector<UnspentTxOut> sortedUTOs = myWallet.getSpendableTxOutList();

   int i=1;
   cout << "   Sorting Method: " << i << endl;
   cout << "   Value\t#Conf\tTxHash\tTxIdx" << endl;
   for(int j=0; j<sortedUTOs.size(); j++)
   {
      cout << "   "
           << sortedUTOs[j].getValue()/1e8 << "\t"
           << sortedUTOs[j].getNumConfirm() << "\t"
           << sortedUTOs[j].getTxHash().toHexStr() << "\t"
           << sortedUTOs[j].getTxOutIndex() << endl;
   }
   cout << endl;


   // Test the zero-conf ledger-entry detection
   //le.pprint();

   //vector<LedgerEntry> levect = wlt.getAddrLedgerEntriesForTx(txSelf);
   //for(int i=0; i<levect.size(); i++)
   //{
      //levect[i].pprint();
   //}
   

}



void TestReorgBlockchain(string blkfile)
{
   BlockDataManager_FullRAM & bdm = BlockDataManager_FullRAM::GetInstance(); 
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

   // TODO: Let's look at the address ledger after the first chain
   //       Then look at it again after the reorg.  What we want
   //       to see is the presence of an invalidated tx, not just
   //       a disappearing tx -- the user must be informed that a 
   //       tx they previously thought they owned is now invalid.
   //       If the user is not informed, they could go crazy trying
   //       to figure out what happened to this money they thought
   //       they had.
   cout << "Constructing address ledger for the to-be-invalidated chain:" << endl;
   bdm.scanBlockchainForTx(wlt2);
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
   cout << "                          Balance: " << wlt2.getFullBalance()/1e8 << endl;
   for(uint32_t i=0; i<wlt2.getNumAddr(); i++)
   {
      BinaryData addr20 = wlt2.getAddrByIndex(i).getAddrStr20();
      cout << "  Addr: " << wlt2.getAddrByIndex(i).getFullBalance()/1e8 << ","
                         << wlt2.getAddrByHash160(addr20).getFullBalance() << endl;
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
      bdm.scanBlockchainForTx(wlt2);
      bdm.updateWalletAfterReorg(wlt2);
   }

   cout << "Checking balance of entire wallet: " << wlt2.getFullBalance()/1e8 << endl;
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
      cout << "  Addr: " << wlt2.getAddrByIndex(i).getFullBalance()/1e8 << ","
                         << wlt2.getAddrByHash160(addr20).getFullBalance()/1e8 << endl;
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
  

}


void TestZeroConf(void)
{

   BlockDataManager_FullRAM & bdm = BlockDataManager_FullRAM::GetInstance(); 
   BinaryData myAddress;
   BtcWallet wlt;
   /*
   bdm.Reset();
   bdm.readBlkFile_FromScratch("zctest/blk0001.dat");

   // More testnet addresses, with only a few transactions
   myAddress.createFromHex("4c98e1fb7aadce864b310b2e52b685c09bdfd5e7"); wlt.addAddress(myAddress);
   myAddress.createFromHex("08ccdf1ef9269b95f6ce93899ece9f68cd5afb22"); wlt.addAddress(myAddress);
   myAddress.createFromHex("edf6bbd7ba7aad222c2b28e6d8d5001178e3680c"); wlt.addAddress(myAddress);
   myAddress.createFromHex("18d9cae7ee0be5c6d58f02a992442d2cdb9914fa"); wlt.addAddress(myAddress);

   bdm.scanBlockchainForTx(wlt);

   bdm.enableZeroConf("zctest/mempool_new.bin");
   uint32_t currBlk = bdm.getTopBlockHeader().getBlockHeight();

   ifstream zcIn("zctest/mempool.bin", ios::in | ios::binary);
   zcIn.seekg(0, ios::end);
   uint64_t filesize = (size_t)zcIn.tellg();
   zcIn.seekg(0, ios::beg);

   BinaryData memPool(filesize);
   zcIn.read((char*)memPool.getPtr(), filesize);

   BinaryRefReader brr(memPool);
   cout << "Starting Wallet:" << endl;
   bdm.rescanWalletZeroConf(wlt);
   wlt.pprintLedger();
   while(brr.getSizeRemaining() > 8)
   {
      cout << endl << endl;
      cout << "Inserting another 0-conf tx..." << endl;
      uint64_t txtime = brr.get_uint64_t();
      TxRef zcTx(brr);
      bool wasAdded = bdm.addNewZeroConfTx(zcTx.serialize(), txtime, true);

      if(wasAdded)
         bdm.rescanWalletZeroConf(wlt);

      cout << "UltBal: " << wlt.getFullBalance() << endl;
      cout << "SpdBal: " << wlt.getSpendableBalance() << endl;
      cout << "UncBal: " << wlt.getUnconfirmedBalance(currBlk) << endl;
      wlt.pprintLedger();

      cout << "Unspent TxOuts:" << endl;
      vector<UnspentTxOut> utxoList = wlt.getSpendableTxOutList(currBlk);
      uint64_t bal = 0;
      for(uint32_t i=0; i<utxoList.size(); i++)
      {
         bal += utxoList[i].getValue();
         utxoList[i].pprintOneLine(currBlk);
      }
      cout << "Sum of TxOuts: " << bal/1e8 << endl;
   }
   */

   ifstream is("zctest/mempool_new.bin", ios::in  | ios::binary);
   ofstream os("zctest/mempool.bin",     ios::out | ios::binary);
   is.seekg(0, ios::end);
   uint64_t filesize = (size_t)is.tellg();
   is.seekg(0, ios::beg);
   BinaryData mempool(filesize);
   is.read ((char*)mempool.getPtr(), filesize);
   os.write((char*)mempool.getPtr(), filesize);
   is.close();
   os.close();

   ////////////////////////////////////////////////////////////////////////////
   ////////////////////////////////////////////////////////////////////////////
   // Start testing balance/wlt update after a new block comes in

   bdm.Reset();
   bdm.readBlkFile_FromScratch("zctest/blk0001.dat");
   // More testnet addresses, with only a few transactions
   wlt = BtcWallet();
   myAddress.createFromHex("4c98e1fb7aadce864b310b2e52b685c09bdfd5e7"); wlt.addAddress(myAddress);
   myAddress.createFromHex("08ccdf1ef9269b95f6ce93899ece9f68cd5afb22"); wlt.addAddress(myAddress);
   myAddress.createFromHex("edf6bbd7ba7aad222c2b28e6d8d5001178e3680c"); wlt.addAddress(myAddress);
   myAddress.createFromHex("18d9cae7ee0be5c6d58f02a992442d2cdb9914fa"); wlt.addAddress(myAddress);
   uint32_t topBlk = bdm.getTopBlockHeader().getBlockHeight();

   // This will load the memory pool into the zeroConfPool_ in BDM
   bdm.enableZeroConf("zctest/mempool.bin");

   // Now scan all transactions, which ends with scanning zero-conf
   bdm.scanBlockchainForTx(wlt);

   wlt.pprintAlot(topBlk, true);

   // The new blkfile has about 10 new blocks, one of which has these tx
   bdm.readBlkFileUpdate("zctest/blk0001_updated.dat");
   bdm.scanBlockchainForTx(wlt, topBlk);
   topBlk = bdm.getTopBlockHeader().getBlockHeight();
   wlt.pprintAlot(topBlk, true);

}


void TestCrypto(void)
{

   SecureBinaryData a("aaaaaaaaaa");
   SecureBinaryData b; b.resize(5);
   SecureBinaryData c; c.resize(0);

   a.copyFrom(b);
   b.copyFrom(c);
   c.copyFrom(a);

   a.resize(0);
   b = a;
   SecureBinaryData d(a); 

   cout << "a=" << a.toHexStr() << endl;
   cout << "b=" << b.toHexStr() << endl;
   cout << "c=" << c.toHexStr() << endl;
   cout << "d=" << d.toHexStr() << endl;

   SecureBinaryData e("eeeeeeeeeeeeeeee");
   SecureBinaryData f("ffffffff");
   SecureBinaryData g(0);

   e = g.copy();
   e = f.copy();

   cout << "e=" << e.toHexStr() << endl;
   cout << "f=" << f.toHexStr() << endl;
   cout << "g=" << g.toHexStr() << endl;
   
   

   /////////////////////////////////////////////////////////////////////////////
   // Start Key-Derivation-Function (KDF) Tests.  
   // ROMIX is the provably memory-hard (GPU-resistent) algorithm proposed by 
   // Colin Percival, who is the creator of Scrypt.  
   cout << endl << endl;
   cout << "Executing Key-Derivation-Function (KDF) tests" << endl;
   KdfRomix kdf;  
   kdf.computeKdfParams();
   kdf.printKdfParams();

   SecureBinaryData passwd1("This is my first password");
   SecureBinaryData passwd2("This is my first password.");
   SecureBinaryData passwd3("This is my first password");
   SecureBinaryData key;

   cout << "   Password1: '" << passwd1.toBinStr() << "'" << endl;
   key = kdf.DeriveKey(passwd1);
   cout << "   MasterKey: '" << key.toHexStr() << endl << endl;

   cout << "   Password2: '" << passwd2.toBinStr() << "'" << endl;
   key = kdf.DeriveKey(passwd2);
   cout << "   MasterKey: '" << key.toHexStr() << endl << endl;

   cout << "   Password1: '" << passwd3.toBinStr() << "'" << endl;
   key = kdf.DeriveKey(passwd3);
   cout << "   MasterKey: '" << key.toHexStr() << endl << endl;

   /////////////////////////////////////////////////////////////////////////////
   cout << "Executing KDF tests with longer compute time" << endl;
   kdf.computeKdfParams(1.0);
   kdf.printKdfParams();

   cout << "   Password1: '" << passwd1.toBinStr() << "'" << endl;
   key = kdf.DeriveKey(passwd1);
   cout << "   MasterKey: '" << key.toHexStr() << endl << endl;

   cout << "   Password2: '" << passwd2.toBinStr() << "'" << endl;
   key = kdf.DeriveKey(passwd2);
   cout << "   MasterKey: '" << key.toHexStr() << endl << endl;

   cout << "   Password1: '" << passwd3.toBinStr() << "'" << endl;
   key = kdf.DeriveKey(passwd3);
   cout << "   MasterKey: '" << key.toHexStr() << endl << endl;

   /////////////////////////////////////////////////////////////////////////////
   cout << "Executing KDF tests with limited memory target" << endl;
   kdf.computeKdfParams(1.0, 256*1024);
   kdf.printKdfParams();

   cout << "   Password1: '" << passwd1.toBinStr() << "'" << endl;
   key = kdf.DeriveKey(passwd1);
   cout << "   MasterKey: '" << key.toHexStr() << endl << endl;

   cout << "   Password2: '" << passwd2.toBinStr() << "'" << endl;
   key = kdf.DeriveKey(passwd2);
   cout << "   MasterKey: '" << key.toHexStr() << endl << endl;

   cout << "   Password1: '" << passwd3.toBinStr() << "'" << endl;
   key = kdf.DeriveKey(passwd3);
   cout << "   MasterKey: '" << key.toHexStr() << endl << endl;

   /////////////////////////////////////////////////////////////////////////////
   cout << "KDF with min memory requirement (1 kB)" << endl;
   kdf.computeKdfParams(1.0, 0);
   kdf.printKdfParams();

   cout << "   Password1: '" << passwd1.toBinStr() << "'" << endl;
   key = kdf.DeriveKey(passwd1);
   cout << "   MasterKey: '" << key.toHexStr() << endl << endl;

   cout << "   Password2: '" << passwd2.toBinStr() << "'" << endl;
   key = kdf.DeriveKey(passwd2);
   cout << "   MasterKey: '" << key.toHexStr() << endl << endl;

   cout << "   Password1: '" << passwd3.toBinStr() << "'" << endl;
   key = kdf.DeriveKey(passwd3);
   cout << "   MasterKey: '" << key.toHexStr() << endl << endl;

   /////////////////////////////////////////////////////////////////////////////
   cout << "KDF with 0 compute time" << endl;
   kdf.computeKdfParams(0, 0);
   kdf.printKdfParams();

   cout << "   Password1: '" << passwd1.toBinStr() << "'" << endl;
   key = kdf.DeriveKey(passwd1);
   cout << "   MasterKey: '" << key.toHexStr() << endl << endl;

   cout << "   Password2: '" << passwd2.toBinStr() << "'" << endl;
   key = kdf.DeriveKey(passwd2);
   cout << "   MasterKey: '" << key.toHexStr() << endl << endl;

   cout << "   Password1: '" << passwd3.toBinStr() << "'" << endl;
   key = kdf.DeriveKey(passwd3);
   cout << "   MasterKey: '" << key.toHexStr() << endl << endl;

   // Test AES code using NIST test vectors
   /// *** Test 1 *** ///
   cout << endl << endl;
   SecureBinaryData testIV, plaintext, cipherTarg, cipherComp, testKey, rtPlain;
   testKey.createFromHex   ("0000000000000000000000000000000000000000000000000000000000000000");
   testIV.createFromHex    ("80000000000000000000000000000000");
   plaintext.createFromHex ("00000000000000000000000000000000");
   cipherTarg.createFromHex("ddc6bf790c15760d8d9aeb6f9a75fd4e");

   cout << "   Plain        : " << plaintext.toHexStr() << endl;
   cipherComp = CryptoAES().Encrypt(plaintext, testKey, testIV);
   cout << "   CipherTarget : " << cipherComp.toHexStr() << endl;
   cout << "   CipherCompute: " << cipherComp.toHexStr() << endl;
   rtPlain = CryptoAES().Decrypt(cipherComp, testKey, testIV);
   cout << "   Plain        : " << rtPlain.toHexStr() << endl;


   /// *** Test 2 *** ///
   cout << endl << endl;
   testKey.createFromHex   ("0000000000000000000000000000000000000000000000000000000000000000");
   testIV.createFromHex    ("014730f80ac625fe84f026c60bfd547d");
   plaintext.createFromHex ("00000000000000000000000000000000");
   cipherTarg.createFromHex("5c9d844ed46f9885085e5d6a4f94c7d7");

   cout << "   Plain        : " << plaintext.toHexStr() << endl;
   cipherComp = CryptoAES().Encrypt(plaintext, testKey, testIV);
   cout << "   CipherTarget : " << cipherComp.toHexStr() << endl;
   cout << "   CipherCompute: " << cipherComp.toHexStr() << endl;
   rtPlain = CryptoAES().Decrypt(cipherComp, testKey, testIV);
   cout << "   Plain        : " << rtPlain.toHexStr() << endl;

   /// *** Test 3 *** ///
   cout << endl << endl;
   testKey.createFromHex   ("ffffffffffff0000000000000000000000000000000000000000000000000000");
   testIV.createFromHex    ("00000000000000000000000000000000");
   plaintext.createFromHex ("00000000000000000000000000000000");
   cipherTarg.createFromHex("225f068c28476605735ad671bb8f39f3");

   cout << "   Plain        : " << plaintext.toHexStr() << endl;
   cipherComp = CryptoAES().Encrypt(plaintext, testKey, testIV);
   cout << "   CipherTarget : " << cipherComp.toHexStr() << endl;
   cout << "   CipherCompute: " << cipherComp.toHexStr() << endl;
   rtPlain = CryptoAES().Decrypt(cipherComp, testKey, testIV);
   cout << "   Plain        : " << rtPlain.toHexStr() << endl;


   /// My own test, for sanity (can only check the roundtrip values)
   // This test is a lot more exciting with the couts uncommented in Encrypt/Decrypt
   cout << endl << endl;
   cout << "Starting some kdf-aes-combined tests..." << endl;
   kdf.printKdfParams();
   testKey = kdf.DeriveKey(SecureBinaryData("This passphrase is tough to guess"));
   SecureBinaryData secret, cipher;
   secret.createFromHex("ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff");
   SecureBinaryData randIV(0);  // tell the crypto to generate a random IV for me.

   cout << "Encrypting:" << endl;
   cipher = CryptoAES().Encrypt(secret, testKey, randIV);
   cout << endl << endl;
   cout << "Decrypting:" << endl;
   secret = CryptoAES().Decrypt(cipher, testKey, randIV);
   cout << endl << endl;

   // Now encrypting so I can store the encrypted data in file
   cout << "Encrypting again:" << endl;
   cipher = CryptoAES().Encrypt(secret, testKey, randIV);

   ofstream testfile("safefile.txt", ios::out);
   testfile << "KdfParams " << endl;
   testfile << "   MemReqts " << kdf.getMemoryReqtBytes() << endl;
   testfile << "   NumIters " << kdf.getNumIterations() << endl;
   testfile << "   HexSalt  " << kdf.getSalt().toHexStr() << endl;
   testfile << "EncryptedData" << endl;
   testfile << "   HexIV    " << randIV.toHexStr() << endl;
   testfile << "   Cipher   " << cipher.toHexStr() << endl;
   testfile.close();
   
   ifstream infile("safefile.txt", ios::in);
   uint32_t mem, nIters;
   SecureBinaryData salt, iv;
   char deadstr[256];
   char hexstr[256];

   infile >> deadstr;
   infile >> deadstr >> mem;
   infile >> deadstr >> nIters;
   infile >> deadstr >> hexstr;
   salt.copyFrom( SecureBinaryData::CreateFromHex(string(hexstr, 64)));
   infile >> deadstr;
   infile >> deadstr >> hexstr;
   iv.copyFrom( SecureBinaryData::CreateFromHex(string(hexstr, 64)));
   infile >> deadstr >> hexstr;
   cipher.copyFrom( SecureBinaryData::CreateFromHex(string(hexstr, 64)));
   infile.close();
   cout << endl << endl;

   // Will try this twice, once with correct passphrase, once without
   SecureBinaryData cipherTry1 = cipher;
   SecureBinaryData cipherTry2 = cipher;
   SecureBinaryData newKey;

   KdfRomix newKdf(mem, nIters, salt);
   newKdf.printKdfParams();

   // First test with the wrong passphrase
   cout << "Attempting to decrypt with wrong passphrase" << endl;
   SecureBinaryData passphrase = SecureBinaryData("This is the wrong passphrase");
   newKey = newKdf.DeriveKey( passphrase );
   CryptoAES().Decrypt(cipherTry1, newKey, iv);


   // Now try correct passphrase
   cout << "Attempting to decrypt with CORRECT passphrase" << endl;
   passphrase = SecureBinaryData("This passphrase is tough to guess");
   newKey = newKdf.DeriveKey( passphrase );
   CryptoAES().Decrypt(cipherTry2, newKey, iv);
}






void TestECDSA(void)
{
   SecureBinaryData msgToSign("This message came from me!");
   SecureBinaryData privData = SecureBinaryData().GenerateRandom(32);
   BTC_PRIVKEY privKey = CryptoECDSA().ParsePrivateKey(privData);
   BTC_PUBKEY  pubKey  = CryptoECDSA().ComputePublicKey(privKey);

   // Test key-match check
   cout << "Do the pub-priv keypair we just created match? ";
   cout << (CryptoECDSA().CheckPubPrivKeyMatch(privKey, pubKey) ? 1 : 0) << endl;
   cout << endl;
   
   SecureBinaryData signature = CryptoECDSA().SignData(msgToSign, privKey);
   cout << "Signature = " << signature.toHexStr() << endl;
   cout << endl;

   bool isValid = CryptoECDSA().VerifyData(msgToSign, signature, pubKey);
   cout << "SigValid? = " << (isValid ? 1 : 0) << endl;
   cout << endl;

   // Test signature from blockchain:
   SecureBinaryData msg = SecureBinaryData::CreateFromHex("0100000001bb664ff716b9dfc831bcc666c1767f362ad467fcfbaf4961de92e45547daab870100000062537a7652a269537a829178a91480677c5392220db736455533477d0bc2fba65502879b69537a829178a91402d7aa2e76d9066fb2b3c41ff8839a5c81bdca19879b69537a829178a91410039ce4fdb5d4ee56148fe3935b9bfbbe4ecc89879b6953aeffffffff0280969800000000001976a9140817482d2e97e4be877efe59f4bae108564549f188ac7015a7000000000062537a7652a269537a829178a91480677c5392220db736455533477d0bc2fba65502879b69537a829178a91402d7aa2e76d9066fb2b3c41ff8839a5c81bdca19879b69537a829178a91410039ce4fdb5d4ee56148fe3935b9bfbbe4ecc89879b6953ae0000000001000000");
   SecureBinaryData px  = SecureBinaryData::CreateFromHex("8c006ff0d2cfde86455086af5a25b88c2b81858aab67f6a3132c885a2cb9ec38");
   SecureBinaryData py  = SecureBinaryData::CreateFromHex("e700576fd46c7d72d7d22555eee3a14e2876c643cd70b1b0a77fbf46e62331ac");
   SecureBinaryData pub65  = SecureBinaryData::CreateFromHex("048c006ff0d2cfde86455086af5a25b88c2b81858aab67f6a3132c885a2cb9ec38e700576fd46c7d72d7d22555eee3a14e2876c643cd70b1b0a77fbf46e62331ac");
   //SecureBinaryData sig = SecureBinaryData::CreateFromHex("3046022100d73f633f114e0e0b324d87d38d34f22966a03b072803afa99c9408201f6d6dc6022100900e85be52ad2278d24e7edbb7269367f5f2d6f1bd338d017ca4600087766144");
   SecureBinaryData sig = SecureBinaryData::CreateFromHex("d73f633f114e0e0b324d87d38d34f22966a03b072803afa99c9408201f6d6dc6900e85be52ad2278d24e7edbb7269367f5f2d6f1bd338d017ca4600087766144");
   pubKey = CryptoECDSA().ParsePublicKey(px,py);
   isValid = CryptoECDSA().VerifyData(msg, sig, pubKey);
   cout << "SigValid? = " << (isValid ? 1 : 0) << endl;


   // Test speed on signature:
   uint32_t nTest = 50;
   cout << "Test signature and verification speeds"  << endl;
   cout << "\nTiming Signing";
   TIMER_START("SigningTime");
   for(uint32_t i=0; i<nTest; i++)
   {
      // This timing includes key parsing
      CryptoECDSA().SignData(msgToSign, privData);
   }
   TIMER_STOP("SigningTime");

   // Test speed of verification
   TIMER_START("VerifyTime");
   cout << "\nTiming Verify";
   for(uint32_t i=0; i<nTest; i++)
   {
      // This timing includes key parsing
      CryptoECDSA().VerifyData(msg, sig, pub65);
   }
   TIMER_STOP("VerifyTime");

   cout << endl;
   cout << "Timing (Signing): " << 1/(TIMER_READ_SEC("SigningTime")/nTest)
        << " signatures/sec" << endl;
   cout << "Timing (Verify):  " << 1/(TIMER_READ_SEC("VerifyTime")/nTest)
        << " verifies/sec" << endl;


   // Test deterministic key generation
   SecureBinaryData privDataOrig = SecureBinaryData().GenerateRandom(32);
   BTC_PRIVKEY privOrig = CryptoECDSA().ParsePrivateKey(privDataOrig);
   BTC_PUBKEY  pubOrig  = CryptoECDSA().ComputePublicKey(privOrig);
   cout << "Testing deterministic key generation" << endl;
   cout << "   Verify again that pub/priv objects pair match : ";
   cout << (CryptoECDSA().CheckPubPrivKeyMatch(privOrig, pubOrig) ? 1 : 0) << endl;

   SecureBinaryData binPriv = CryptoECDSA().SerializePrivateKey(privOrig);
   SecureBinaryData binPub  = CryptoECDSA().SerializePublicKey(pubOrig);
   cout << "   Verify again that binary pub/priv pair match  : ";
   cout << (CryptoECDSA().CheckPubPrivKeyMatch(binPriv, binPub) ? 1 : 0) << endl;
   cout << endl;

   SecureBinaryData chaincode = SecureBinaryData().GenerateRandom(32);
   cout << "   Starting privKey:" << binPriv.toHexStr() << endl;
   cout << "   Starting pubKey :" << binPub.toHexStr() << endl;
   cout << "   Chaincode       :" << chaincode.toHexStr() << endl;
   cout << endl;
   
   SecureBinaryData newBinPriv = CryptoECDSA().ComputeChainedPrivateKey(binPriv, chaincode);
   SecureBinaryData newBinPubA = CryptoECDSA().ComputePublicKey(newBinPriv);
   SecureBinaryData newBinPubB = CryptoECDSA().ComputeChainedPublicKey(binPub, chaincode);
   cout << "   Verify new binary pub/priv pair match: ";
   cout << (CryptoECDSA().CheckPubPrivKeyMatch(newBinPriv, newBinPubA) ? 1 : 0) << endl;
   cout << "   Verify new binary pub/priv pair match: ";
   cout << (CryptoECDSA().CheckPubPrivKeyMatch(newBinPriv, newBinPubB) ? 1 : 0) << endl;
   cout << "   New privKey:" << newBinPriv.toHexStr() << endl;
   cout << "   New pubKeyA:" << newBinPubA.getSliceCopy(0,30).toHexStr() << "..." << endl;
   cout << "   New pubKeyB:" << newBinPubB.getSliceCopy(0,30).toHexStr() << "..." << endl;
   cout << endl;


   // Test arbitrary scalar/point operations
   BinaryData a = BinaryData::CreateFromHex("8c006ff0d2cfde86455086af5a25b88c2b81858aab67f6a3132c885a2cb9ec38");
   BinaryData b = BinaryData::CreateFromHex("e700576fd46c7d72d7d22555eee3a14e2876c643cd70b1b0a77fbf46e62331ac");
   BinaryData c = BinaryData::CreateFromHex("f700576fd46c7d72d7d22555eee3a14e2876c643cd70b1b0a77fbf46e62331ac");
   BinaryData d = BinaryData::CreateFromHex("8130904787384d72d7d22555eee3a14e2876c643cd70b1b0a77fbf46e62331ac");
   BinaryData e = CryptoECDSA().ECMultiplyScalars(a,b);
   BinaryData f = CryptoECDSA().ECMultiplyPoint(a, b, c);
   BinaryData g = CryptoECDSA().ECAddPoints(a, b, c, d);
}






