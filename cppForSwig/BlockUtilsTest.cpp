////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2013, Alan C. Reiner    <alan.reiner@gmail.com>        //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE or http://www.gnu.org/licenses/agpl.html                      //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////
#include <iostream>
#include <stdio.h>
#include <fstream>
#include <string>
#include <sstream>
#include "UniversalTimer.h"
#include "BinaryData.h"
#include "BtcUtils.h"
#include "BlockUtils.h"
#include "EncryptionUtils.h"
#include "FileDataPtr.h"


using namespace std;



////////////////////////////////////////////////////////////////////////////////
void TestReadAndOrganizeChain(string blkdir);
void TestFindNonStdTx(string blkdir);
void TestReadAndOrganizeChainWithWallet(string blkdir);
void TestBalanceConstruction(string blkdir);
void TestReadAndUpdateBlkFile(string blkdir);
void TestScanForWalletTx(string blkdir);
void TestReorgBlockchain(string blkdir);
void TestZeroConf(void);
void TestCrypto(void);
void TestECDSA(void);
void TestPointCompression(void);
void TestFileCache(void);
void TestMemoryUsage_UseSystemMonitor(string blkdir);
void TestOutOfOrder(string blkdir);

void CreateMultiBlkFile(string blkdir);
////////////////////////////////////////////////////////////////////////////////

void printTestHeader(string TestName)
{
   cout << endl;
   for(int i=0; i<80; i++) cout << "*";
   cout << endl << "Execute test: " << TestName << endl;
   for(int i=0; i<80; i++) cout << "*";
   cout << endl;
}

bool copyFile(string src, string dst)
{
   uint32_t srcsz = BtcUtils::GetFileSize(src);
   if(srcsz == FILE_DOES_NOT_EXIST)
      return false;

   BinaryData temp(srcsz);
   ifstream is(src.c_str(), ios::in  | ios::binary);
   is.read((char*)temp.getPtr(), srcsz);
   is.close();

   ofstream os(dst.c_str(), ios::out | ios::binary);
   os.write((char*)temp.getPtr(), srcsz);
   os.close();
   return true;
}


string pathJoin(string dir, string file)
{
   int const TOTALSZ = dir.size() + file.size() + 10;
   char * path = new char[TOTALSZ];
   sprintf(path, "%s/%s", dir.c_str(), file.c_str());
   string ret(path);
   return ret;
}



int main(void)
{
   BlockDataManager_FileRefs::GetInstance().SelectNetwork("Main");
   

   string blkdir("/home/alan/.bitcoin");
   //string blkdir("/home/alan/.bitcoin/testnet/");
   //string blkdir("C:/Users/VBox/AppData/Roaming/Bitcoin");
   //string blkdir("C:/Users/VBox/AppData/Roaming/Bitcoin/testnet");
   //string multitest("./multiblktest");
   
   // ONLY USE THIS TO CREATE THE TEST BLOCKCHAIN -- then comment it out
   //CreateMultiBlkFile(blkdir); return 0;


   //printTestHeader("Read-and-Organize-Blockchain");
   //TestReadAndOrganizeChain(blkdir);

   //printTestHeader("Wallet-Relevant-Tx-Scan");
   //TestScanForWalletTx(blkdir);

   //printTestHeader("Find-Non-Standard-Tx");
   //TestFindNonStdTx(blkdir);

   //printTestHeader("Read-and-Organize-Blockchain-With-Wallet");
   //TestReadAndOrganizeChainWithWallet(blkdir);

   //printTestHeader("Test-Balance-Construction");
   //TestBalanceConstruction(blkdir);

   //printTestHeader("Read-and-Update-Blockchain");
   //TestReadAndUpdateBlkFile(multitest);

   //printTestHeader("Blockchain-Reorg-Unit-Test");
   //TestReorgBlockchain(blkdir);

   //printTestHeader("Test-Memory-Usage-With-System-Monitor");
   //TestMemoryUsage_UseSystemMonitor(blkdir);

   printTestHeader("Test-out-of-order calls");
   TestOutOfOrder(blkdir);

   //printTestHeader("Testing Zero-conf handling");
   //TestZeroConf();

   //printTestHeader("Crypto-KDF-and-AES-methods");
   //TestCrypto();

   //printTestHeader("Crypto-ECDSA-sign-verify");
   //TestECDSA();

   //printTestHeader("ECDSA Point Compression");
   //TestPointCompression();

   //printTestHeader("Testing file cache");
   //TestFileCache();
   
   
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







void TestReadAndOrganizeChain(string blkdir)
{
   BlockDataManager_FileRefs & bdm = BlockDataManager_FileRefs::GetInstance(); 
   /////////////////////////////////////////////////////////////////////////////
   cout << "Reading data from blockchain..." << endl;
   TIMER_START("BDM_Load_and_Scan_BlkChain");
   bdm.SetBlkFileLocation(blkdir, 4, 1);
   bdm.parseEntireBlockchain();  
   TIMER_STOP("BDM_Load_and_Scan_BlkChain");
   cout << endl << endl;

   /////////////////////////////////////////////////////////////////////////////
   // Organizing the chain is always really fast (sub-second), and has now been
   // removed as an OPTION to the "readBlkFile" methods.  It will be done 
   // automatically
   //cout << endl << "Organizing blockchain: " ;
   //TIMER_START("BDM_Organize_Chain");
   //bool isGenOnMainChain = bdm.organizeChain();
   //TIMER_STOP("BDM_Organize_Chain");
   //cout << (isGenOnMainChain ? "No Reorg!" : "Reorg Detected!") << endl;
   //cout << endl << endl;

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



void TestFindNonStdTx(string blkdir)
{
   /*
   // This is mostly just for debugging...
   BlockDataManager_FileRefs & bdm = BlockDataManager_FileRefs::GetInstance(); 
   bdm.SetBlkFileLocation(blkdir, 4, 1);
   bdm.parseEntireBlockchain(); 
   bdm.findAllNonStdTx();
   // At one point I had code to print out nonstd txinfo... not sure
   // what happened to it...
   */
}



void TestScanForWalletTx(string blkdir)
{
   BlockDataManager_FileRefs & bdm = BlockDataManager_FileRefs::GetInstance(); 
   bdm.SetBlkFileLocation(blkdir, 4, 1);
   bdm.parseEntireBlockchain();
   /////////////////////////////////////////////////////////////////////////////
   BinaryData myAddress;
   BtcWallet wlt;
   
   // Main-network addresses
   myAddress.createFromHex("604875c897a079f4db88e5d71145be2093cae194"); wlt.addAddress(myAddress);
   myAddress.createFromHex("8996182392d6f05e732410de4fc3fa273bac7ee6"); wlt.addAddress(myAddress);
   myAddress.createFromHex("b5e2331304bc6c541ffe81a66ab664159979125b"); wlt.addAddress(myAddress);
   myAddress.createFromHex("ebbfaaeedd97bc30df0d6887fd62021d768f5cb8"); wlt.addAddress(myAddress);
   myAddress.createFromHex("11b366edfc0a8b66feebae5c2e25a7b6a5d1cf31"); wlt.addAddress(myAddress);

   // This address contains a tx with a non-std TxOut, but the other TxOuts are valid
   myAddress.createFromHex("6c27c8e67b7376f3ab63553fe37a4481c4f951cf"); wlt.addAddress(myAddress);

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


void TestReadAndOrganizeChainWithWallet(string blkdir)
{
   cout << endl << "Starting blockchain loading with wallets..." << endl;
   /////////////////////////////////////////////////////////////////////////////
   BlockDataManager_FileRefs & bdm = BlockDataManager_FileRefs::GetInstance(); 
   BinaryData myAddress;
   BtcWallet wlt1;
   BtcWallet wlt2;
   
   // Main-network addresses
   myAddress.createFromHex("604875c897a079f4db88e5d71145be2093cae194"); wlt2.addAddress(myAddress);
   myAddress.createFromHex("8996182392d6f05e732410de4fc3fa273bac7ee6"); wlt2.addAddress(myAddress);
   myAddress.createFromHex("b5e2331304bc6c541ffe81a66ab664159979125b"); wlt2.addAddress(myAddress);
   myAddress.createFromHex("ebbfaaeedd97bc30df0d6887fd62021d768f5cb8"); wlt2.addAddress(myAddress);
   myAddress.createFromHex("11b366edfc0a8b66feebae5c2e25a7b6a5d1cf31"); wlt2.addAddress(myAddress);
   myAddress.createFromHex("e826f4a4381453dcdcf9bfeedffe95de7c86ccbd"); wlt2.addAddress(myAddress);

   // P2Pool Address
   myAddress.createFromHex("4975703dc910107e2cc1321e632d136803e218e8"); wlt1.addAddress(myAddress);
   
   // Add some relevant testnet addresses
   myAddress.createFromHex("0c6b92101c7025643c346d9c3e23034a8a843e21"); wlt2.addAddress(myAddress);
   myAddress.createFromHex("34c9f8dc91dfe1ae1c59e76cbe1aa39d0b7fc041"); wlt1.addAddress(myAddress);
   myAddress.createFromHex("d77561813ca968270d5f63794ddb6aab3493605e"); wlt1.addAddress(myAddress);
   myAddress.createFromHex("0e0aec36fe2545fb31a41164fb6954adcd96b342"); wlt1.addAddress(myAddress);

   vector<BtcWallet*> wltList;
   wltList.push_back(&wlt1);
   wltList.push_back(&wlt2);

   bdm.registerWallet(&wlt1);
   bdm.registerWallet(&wlt2);


   /////////////////////////////////////////////////////////////////////////////
   cout << "Reading data from blockchain... (with wallet scan)" << endl;
   TIMER_START("BDM_Load_Scan_Blockchain_With_Wallet");
   bdm.SetBlkFileLocation(blkdir, 4, 1);
   bdm.parseEntireBlockchain();  
   TIMER_STOP("BDM_Load_Scan_Blockchain_With_Wallet");
   cout << endl << endl;

   /////////////////////////////////////////////////////////////////////////////
   cout << endl << "Organizing blockchain: " ;
   TIMER_START("BDM_Organize_Chain");
   bool isGenOnMainChain = bdm.organizeChain();
   TIMER_STOP("BDM_Organize_Chain");
   cout << (isGenOnMainChain ? "No Reorg!" : "Reorg Detected!") << endl;
   cout << endl << endl;

   cout << endl << "Updating wallet (1) based on initial blockchain scan" << endl;
   TIMER_WRAP(bdm.scanBlockchainForTx(wlt1));
   cout << "Printing Wallet(1) Ledger" << endl;
   wlt1.pprintLedger();

   cout << endl << "Updating wallet (2) based on initial blockchain scan" << endl;
   TIMER_WRAP(bdm.scanBlockchainForTx(wlt2));
   cout << "Printing Wallet(2) Ledger" << endl;
   wlt2.pprintLedger();

   cout << endl << "Rescanning wlt2 multiple times" << endl;
   TIMER_WRAP(bdm.scanBlockchainForTx(wlt2));
   TIMER_WRAP(bdm.scanBlockchainForTx(wlt2));
   cout << "Printing Wallet(2) Ledger AGAIN" << endl;
   wlt2.pprintLedger();


   cout << endl << "ADD a new address to Wlt(1) requiring a blockchain rescan..." << endl;
   // This address contains a tx with a non-std TxOut, but the other TxOuts are valid
   myAddress.createFromHex("6c27c8e67b7376f3ab63553fe37a4481c4f951cf"); 
   wlt1.addAddress(myAddress);
   bdm.scanBlockchainForTx(wlt1);
   wlt1.pprintLedger();
   
   cout << endl << "ADD new address to wlt(2) but as a just-created addr not requiring rescan" << endl;
   myAddress.createFromHex("6c27c8e67b7376f3ab63553fe37a4481c4f951cf"); 
   wlt2.addNewAddress(myAddress);
   bdm.scanBlockchainForTx(wlt2);
   wlt2.pprintLedger();


   cout << endl << "Create new, unregistered wallet, scan it once (should rescan)..." << endl;
   BtcWallet wlt3;
   myAddress.createFromHex("72e20a94d6b2ed34a3b4d3757c1fed5152071993"); wlt3.addAddress(myAddress);
   wlt3.addAddress(myAddress);
   bdm.scanBlockchainForTx(wlt3);
   wlt3.pprintLedger();

   
   cout << endl << "Rescan unregistered wallet: addr should be registered, so no rescan..." << endl;
   bdm.scanBlockchainForTx(wlt3);
   wlt3.pprintLedger();


   cout << endl << endl;
   cout << "Getting Sent-To Address List for Wlt1:" << endl;
   vector<AddressBookEntry> targAddrVect = wlt1.createAddressBook();
   for(uint32_t i=0; i<targAddrVect.size(); i++)
   {
      vector<RegisteredTx> txList = targAddrVect[i].getTxList();

      cout << targAddrVect[i].getAddr160().toHexStr() << " " 
           << txList.size() << endl;
      
      for(uint32_t j=0; j<txList.size(); j++)
         cout << "   " << txList[j].txHash_.toHexStr()
              << "   " << txList[j].blkNum_
              << "   " << txList[j].txIndex_ << endl;
   }


   // Results for the sent-to address list, as of 09 Apr, 2012
   /*
   "13Tn1QkAcqnQvGA7kBiCBH7NbijNcr6GMs"
   "17ZqBkFgR6TWawd8rRKbyJAnpTWDWtok72"
   "12irKW1XFSnnu6v5FevcC3wZ6hfvPmaEDQ"
   "12Tg96ZPSYc3P2g5c9c4znFFH2whriN9NQ"
   "1PymCiNzubeTtJt47dqFdi31Zy9MAM1YZk"
   "1H3Jbv99F7Ng8oiadCovvda17CGZ9EFkPM"
   "16jN5NhB4eoUqFrSvuNnvDEc57oz6GRNi4"
   "17aLXn2XHKH7nhwdCPaWmkY6jgr36zSjyz"
   "1PjURhoxGr6cdK5YY5SyDDY2pQhEpbZdoK"
   "1NgBFTvqM6FsooFtkvFgf7VxzRBdXKnxpR"
   "176msrhhemi6q8DEdpBCoTQJvRCiGV5qEm"
   "16FSHWWyUv6wzT9qpbi7tCaovf6XX7T9xN"
   "1JiLbGTrVNmk6BsePVQWmBiD7DFUDmMYXw"
   "124DJWV7vYS8DUcVan4SXcGNAubopS1BHj"
   "1PESigPSLwsvaQAQfCDDPZM21i9m8Vqt21"
   "18i1rVZHMMXQwRxZuSrHZrpqUoejkV2Gh2"
   "1PZjRprkrM93GVXNdJ5zu7C1p84weTovWj"
   "14cKqt9e8QvgMaBrwbuykBjha1vXNtaj72"
   "1QJUzen8xL7EyBTGnkDUX6fnoMX9TL1fU7"
   "17iRBkToUTzDvVpXsNUT8usT6c6aEDe15R"
   "1NVJS8DWLdrte45rc5oGvWyjrAe9y1rtFt"
   "1MzxEf2Ck9XSC7U5y5DHQvMyPhL2UNcjSD"
   "1F7G4aq9fbAhqGb9jcnsVn6CRm6dqJf3sD"
   "15dYCgedoR1s4y1t5iiKNrRbgHNDize8VW"
   "15XopyBFQetJzyhE5BbM6WiuYDPeKPNfVP"
   "1SAD1wfvNCxz23WjEyQMG6fjKsiQx7FFK"
   "1TaintGh3cPFVGX9REbRk8FXSKTb1pcFZ"
   "1SAD2i96iGVQvsfhdhEhpi5GeFQpuP4Ye"
   "1SAD5qJu5UhhXdAZbW7zpjso4ay364W3B"
   "1SAD7gSBTkhMz5Qaf92SFjUdAsZiE6fq3"
   "13Sgmy78mfw7ToMiKQujyad9spmPGUZvCN"
   "1M7bd7iYNuJoFw8F7fGXvz2Fe9cGnhA3P6"
   */

   /* Here's the hash160 version of the above list
   "1b00a2f6899335366f04b277e19d777559c35bc8"
   "480649dc5fd4448f8c4bf75b3c84bb98ec40b45a"
   "12e259809932ee8fdab278946911dbd6c6e9e977"
   "10039ce4fdb5d4ee56148fe3935b9bfbbe4ecc89"
   "fc0ef58380e6d4bcb9599c5369ce82d0bc01a5c4"
   "aff189b24a36a1b93de2ea4d157c13d18251270a"
   "3edbb132f2cd894bc45fee76cfbf13d79fa87bbb"
   "481ec8e7d30c484ea664824fb7f52b5ae0a99d1d"
   "f95b21b39dbd7cfe9dd5ef81fe19777707b57f00"
   "edc36b7309fe440fea79e59c3b50d3969e7fa97d"
   "42e84bba78b26c2a8917f5cb48493316c3766f88"
   "39938f166521cbbef621f7c016308fbb428fd9e0"
   "c24b8bdcba3cb15a7fe95aa99b7ab6ceba5a4c2c"
   "0b93a48b5ebf29c0e6c7ce53d6701cb4495fc623"
   "f3dda4c01f89186a012c68607899a5cfd172e408"
   "548aa5b107b7a5d787c3b21db4fa07ec1cd7b1ec"
   "f7837ec1fccdbcb1c9848c271468aa9ddf12bf7a"
   "2796aa497bf2e3d8989319ceff88d1f30300ae36"
   "ff9955241d540b35fcd429b04e4f59fcfa34580d"
   "49a5ff7f45c3e2c256adf0615f45f2bbba7a33d3"
   "ebb4d74391893c08716988c5b9f684275be5966b"
   "e658556ebd5104f49ea88c27212e8fba71f38e3d"
   "9ac0d4663bae84fbccfb3f3d887551c075283d7b"
   "32c985fe4602556cef24b9fd1a35459a0d39e806"
   "31b4123c92a4aed2d7cfd08edced603dedefcfb7"
   "04c215b608229b1e71f6314d6973d235fe448c2e"
   "0506f6a7742b6b4c554ada6c780f7242c85bfdc2"
   "04c215c2800a1fb2a50f79865bd87a51ae9505c5"
   "04c215f54c237440e91ebc0e7ed01ecec18d09c0"
   "04c21613557ce112d0b95a37e08fabf3f8ec96b2"
   "1acbda75c997d00e2cef09389750708e75433357"
   "dca1e9baf8d970229f5efa269a15dd420ea7cfab"
   */

   BinaryData txHash1 = BinaryData::CreateFromHex("2ec3a745e032c8bcc1061ebf270afcee47318a43462ba57215174084775c794d");
   BinaryData txHash2 = BinaryData::CreateFromHex("b754fa89f7eb7f7c564611d9297dbcb471cf8d3cb0d235686323b6a5b263b094");

   if( bdm.getTxRefPtrByHash(txHash1) != NULL &&
       bdm.getTxRefPtrByHash(txHash2) != NULL)
   {
      cout << "Testing soft-scanning..." << endl;
      LedgerEntry le;
      le = wlt1.calcLedgerEntryForTx( *bdm.getTxRefPtrByHash(txHash1) ); le.pprintOneLine(); cout << endl;
      le = wlt2.calcLedgerEntryForTx( *bdm.getTxRefPtrByHash(txHash1) ); le.pprintOneLine(); cout << endl;
      le = wlt1.calcLedgerEntryForTx( *bdm.getTxRefPtrByHash(txHash2) ); le.pprintOneLine(); cout << endl;
      le = wlt2.calcLedgerEntryForTx( *bdm.getTxRefPtrByHash(txHash2) ); le.pprintOneLine(); cout << endl;
   }

   cout << "Num Headers: " << bdm.getNumHeaders() << endl;
   cout << "Num Tx:      " << bdm.getNumTx() << endl;
  
}

void TestBalanceConstruction(string blkdir)
{
   cout << endl << "Starting blockchain loading with wallets..." << endl;
   /////////////////////////////////////////////////////////////////////////////
   BlockDataManager_FileRefs & bdm = BlockDataManager_FileRefs::GetInstance(); 
   BinaryData myAddress;
   BtcWallet wlt;
   
   // Main-network addresses
   // I do not remember anymore what any of these addresses were for ...
   // All I know is they probably have some tx history..
   //myAddress.createFromHex("604875c897a079f4db88e5d71145be2093cae194"); wlt.addAddress(myAddress);
   //myAddress.createFromHex("8996182392d6f05e732410de4fc3fa273bac7ee6"); wlt.addAddress(myAddress);
   //myAddress.createFromHex("b5e2331304bc6c541ffe81a66ab664159979125b"); wlt.addAddress(myAddress);
   //myAddress.createFromHex("ebbfaaeedd97bc30df0d6887fd62021d768f5cb8"); wlt.addAddress(myAddress);
   //myAddress.createFromHex("11b366edfc0a8b66feebae5c2e25a7b6a5d1cf31"); wlt.addAddress(myAddress);
   //myAddress.createFromHex("e826f4a4381453dcdcf9bfeedffe95de7c86ccbd"); wlt.addAddress(myAddress);

   // P2Pool Address
   myAddress.createFromHex("4975703dc910107e2cc1321e632d136803e218e8"); wlt.addAddress(myAddress);

   // Add some relevant testnet addresses
   //myAddress.createFromHex("0c6b92101c7025643c346d9c3e23034a8a843e21"); wlt.addAddress(myAddress);
   //myAddress.createFromHex("34c9f8dc91dfe1ae1c59e76cbe1aa39d0b7fc041"); wlt.addAddress(myAddress);
   //myAddress.createFromHex("d77561813ca968270d5f63794ddb6aab3493605e"); wlt.addAddress(myAddress);
   //myAddress.createFromHex("0e0aec36fe2545fb31a41164fb6954adcd96b342"); wlt.addAddress(myAddress);

   // These two addresses were used at one point for testing unconfirmed balances
   myAddress.createFromHex("8c61f6a7558af399e404d82beddcc4692db7b30f"); wlt.addAddress(myAddress);
   myAddress.createFromHex("14445409283ef413f5fb004338377bf042064922"); wlt.addAddress(myAddress);

   bdm.registerWallet(&wlt);


   /////////////////////////////////////////////////////////////////////////////
   cout << "Reading data from blockchain... (with wallet scan)" << endl;
   TIMER_START("BDM_Load_Scan_Blockchain_With_Wallet");
   bdm.SetBlkFileLocation(blkdir, 4, 1);
   bdm.parseEntireBlockchain();  
   TIMER_STOP("BDM_Load_Scan_Blockchain_With_Wallet");
   cout << endl << endl;


   cout << endl << "Scanning wallet tx based on initial blockchain scan" << endl;
   TIMER_WRAP(bdm.scanBlockchainForTx(wlt));
   cout << "Printing Wallet Ledger" << endl;
   wlt.pprintLedger();


   // We want to check the memory pool transactions...
   string mempool("C:/Users/VBox/AppData/Roaming/Armory/mempool.bin");
   bdm.enableZeroConf(mempool);
   bdm.scanBlockchainForTx(wlt);

   uint32_t topBlk = bdm.getTopBlockHeight();
   uint64_t balFul = wlt.getFullBalance();
   uint64_t balSpd = wlt.getSpendableBalance(topBlk);
   uint64_t balUnc = wlt.getUnconfirmedBalance(topBlk);

   vector<UnspentTxOut> utxoF = wlt.getFullTxOutList(topBlk);
   vector<UnspentTxOut> utxoS = wlt.getSpendableTxOutList(topBlk);
   cout << "FULL:" << endl;
   for(uint32_t i=0; i<utxoF.size(); i++)
      utxoF[i].pprintOneLine(topBlk);

   cout << "SPENDABLE:" << endl;
   for(uint32_t i=0; i<utxoS.size(); i++)
      utxoS[i].pprintOneLine(topBlk);
}

void TestReadAndUpdateBlkFile(string tempBlkDir)
{

   string blk3  = pathJoin(tempBlkDir, "blk0003.dat");
   string blk3s = pathJoin(tempBlkDir, "blk0003sm.dat");
   string blk3b = pathJoin(tempBlkDir, "blk0003big.dat");
   string blk3g = pathJoin(tempBlkDir, "blk0003bigger.dat");
   string blk4  = pathJoin(tempBlkDir, "blk0004.dat");
   string blk4s = pathJoin(tempBlkDir, "blk0004sm.dat");
   string blk5  = pathJoin(tempBlkDir, "blk0005.dat");
   string blk5s = pathJoin(tempBlkDir, "blk0005sm.dat");
   uint32_t nblk;

   // Clean up from the previous run
   copyFile(blk3s,  blk3);
   if( BtcUtils::GetFileSize(blk4) != FILE_DOES_NOT_EXIST ) 
      remove(blk4.c_str());
   if( BtcUtils::GetFileSize(blk5) != FILE_DOES_NOT_EXIST ) 
      remove(blk5.c_str());


   // The newblk directory has a blk0003.dat file with one more block
   // and blk0004.dat file with 4 more blocks
   BlockDataManager_FileRefs & bdm = BlockDataManager_FileRefs::GetInstance(); 
   bdm.SetBlkFileLocation(tempBlkDir, 4, 1);
   bdm.parseEntireBlockchain();  

   // Test standard blkfile expansion
   copyFile(blk3b, blk3);
   nblk = bdm.readBlkFileUpdate();
   cout << "New Blocks Read: " << nblk << endl;

   // Test both blkfile expansion and splitting
   copyFile(blk3g, blk3);
   copyFile(blk4s, blk4);
   nblk = bdm.readBlkFileUpdate();
   cout << "New Blocks Read: " << nblk << endl;


   // Test just blockfile splitting
   copyFile(blk5s, blk5);
   nblk = bdm.readBlkFileUpdate();
   cout << "New Blocks Read: " << nblk << endl;

}

void TestReorgBlockchain(string blkdir)
{
   // June, 2012:  The reorg test compiled&worked up until I changed everything
   //              to FileDataPtrs, and now I don't have a good way to force 
   //              different blk files (because I auto-detect blkfiles...)
   //              Will revive this when I figure it out...
   /*
   BlockDataManager_FileRefs & bdm = BlockDataManager_FileRefs::GetInstance(); 
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
   bdm.SetBlkFileLocation("reorgTest/blk_0_to_4.dat", 4, 1);
   bdm.parseEntireBlockchain();
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
   */
  

}


void TestZeroConf(void)
{

   BlockDataManager_FileRefs & bdm = BlockDataManager_FileRefs::GetInstance(); 
   BinaryData myAddress;
   BtcWallet wlt;
   /*
   bdm.Reset();
   bdm.SetBlkFileLocation("zctest/blk0001.dat", 4, 1);
   bdm.parseEntireBlockchain();

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

   /*  Not only does this test not work anymore (due to FileDataPtr updates),
    *  I appear to have lost my carefully-constructed zctest directory since
    *  I ran this last... :(
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
   bdm.SetBlkFileLocation("zctest/blk0001.dat", 4, 1);
   bdm.parseEntireBlockchain();
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
   */

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
   cipherComp = CryptoAES().EncryptCFB(plaintext, testKey, testIV);
   cout << "   CipherTarget : " << cipherComp.toHexStr() << endl;
   cout << "   CipherCompute: " << cipherComp.toHexStr() << endl;
   rtPlain = CryptoAES().DecryptCFB(cipherComp, testKey, testIV);
   cout << "   Plain        : " << rtPlain.toHexStr() << endl;


   /// *** Test 2 *** ///
   cout << endl << endl;
   testKey.createFromHex   ("0000000000000000000000000000000000000000000000000000000000000000");
   testIV.createFromHex    ("014730f80ac625fe84f026c60bfd547d");
   plaintext.createFromHex ("00000000000000000000000000000000");
   cipherTarg.createFromHex("5c9d844ed46f9885085e5d6a4f94c7d7");

   cout << "   Plain        : " << plaintext.toHexStr() << endl;
   cipherComp = CryptoAES().EncryptCFB(plaintext, testKey, testIV);
   cout << "   CipherTarget : " << cipherComp.toHexStr() << endl;
   cout << "   CipherCompute: " << cipherComp.toHexStr() << endl;
   rtPlain = CryptoAES().DecryptCFB(cipherComp, testKey, testIV);
   cout << "   Plain        : " << rtPlain.toHexStr() << endl;

   /// *** Test 3 *** ///
   cout << endl << endl;
   testKey.createFromHex   ("ffffffffffff0000000000000000000000000000000000000000000000000000");
   testIV.createFromHex    ("00000000000000000000000000000000");
   plaintext.createFromHex ("00000000000000000000000000000000");
   cipherTarg.createFromHex("225f068c28476605735ad671bb8f39f3");

   cout << "   Plain        : " << plaintext.toHexStr() << endl;
   cipherComp = CryptoAES().EncryptCFB(plaintext, testKey, testIV);
   cout << "   CipherTarget : " << cipherComp.toHexStr() << endl;
   cout << "   CipherCompute: " << cipherComp.toHexStr() << endl;
   rtPlain = CryptoAES().DecryptCFB(cipherComp, testKey, testIV);
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
   cipher = CryptoAES().EncryptCFB(secret, testKey, randIV);
   cout << endl << endl;
   cout << "Decrypting:" << endl;
   secret = CryptoAES().DecryptCFB(cipher, testKey, randIV);
   cout << endl << endl;

   // Now encrypting so I can store the encrypted data in file
   cout << "Encrypting again:" << endl;
   cipher = CryptoAES().EncryptCFB(secret, testKey, randIV);

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
   CryptoAES().DecryptCFB(cipherTry1, newKey, iv);


   // Now try correct passphrase
   cout << "Attempting to decrypt with CORRECT passphrase" << endl;
   passphrase = SecureBinaryData("This passphrase is tough to guess");
   newKey = newKdf.DeriveKey( passphrase );
   CryptoAES().DecryptCFB(cipherTry2, newKey, iv);
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




void TestPointCompression(void)
{
   vector<BinaryData> testPubKey(3);
   testPubKey[0].createFromHex("044f355bdcb7cc0af728ef3cceb9615d90684bb5b2ca5f859ab0f0b704075871aa385b6b1b8ead809ca67454d9683fcf2ba03456d6fe2c4abe2b07f0fbdbb2f1c1");
   testPubKey[1].createFromHex("04ed83704c95d829046f1ac27806211132102c34e9ac7ffa1b71110658e5b9d1bdedc416f5cefc1db0625cd0c75de8192d2b592d7e3b00bcfb4a0e860d880fd1fc");
   testPubKey[2].createFromHex("042596957532fc37e40486b910802ff45eeaa924548c0e1c080ef804e523ec3ed3ed0a9004acf927666eee18b7f5e8ad72ff100a3bb710a577256fd7ec81eb1cb3");

   CryptoPP::ECP & ecp = CryptoECDSA::Get_secp256k1_ECP();
   for(uint32_t i=0; i<3; i++)
   {
      CryptoPP::Integer pubX, pubY;
      pubX.Decode(testPubKey[i].getPtr()+1,  32, UNSIGNED);
      pubY.Decode(testPubKey[i].getPtr()+33, 32, UNSIGNED);
      BTC_ECPOINT ptPub(pubX, pubY);

      BinaryData ptFlat(65);
      BinaryData ptComp(33);

      ecp.EncodePoint((byte*)ptFlat.getPtr(), ptPub, false);
      ecp.EncodePoint((byte*)ptComp.getPtr(), ptPub, true);

      cout << "Point (" << i << "): " << ptFlat.toHexStr() << endl;
      cout << "Point (" << i << "): " << ptComp.toHexStr() << endl;
      cout << "Point (" << i << "): " << CryptoECDSA().UncompressPoint(SecureBinaryData(ptComp)).toHexStr() << endl;
      cout << "Point (" << i << "): " << CryptoECDSA().CompressPoint(SecureBinaryData(testPubKey[i])).toHexStr() << endl;
   }



}



void TestFileCache(void)
{
   uint32_t nTestFiles = 3;
   vector<string> filenames(nTestFiles);

   // Create some test files
   for(uint32_t i=0; i<nTestFiles; i++)
   {
      char fn[256];
      sprintf(fn, "test_file_cache_%04d.dat", i);
      filenames[i] = string(fn);
      ofstream os(fn, ios::out | ios::binary);
      for(uint32_t j=0; j<(i+3)*1024; j++)
         os << (uint8_t)(j%256);
      os.close();
   }


   // Setup the file cache -- test with a cache of 1 kB
   FileDataPtr::SetupFileCaching(128);
   FileDataCache & fdcache = FileDataPtr::getGlobalCacheRef();
   
   for(uint32_t i=0; i<nTestFiles; i++)
   {
      fdcache.openFile(i, filenames[i]); 
      fdcache.pprintCacheState();
   }


   // Start testing only for a single file
   vector<FileDataPtr> fdrefs;
   //                           File  Start  Bytes
   fdrefs.push_back(FileDataPtr(   0,     0,    16  ));
   fdrefs.push_back(FileDataPtr(   0,     0,     8  ));
   fdrefs.push_back(FileDataPtr(   0,     8,     8  ));
   fdrefs.push_back(FileDataPtr(   0,     0,    32  ));
   fdrefs.push_back(FileDataPtr(   0,     8,     8  ));
   fdrefs.push_back(FileDataPtr(   0,     8,    16  ));
   fdrefs.push_back(FileDataPtr(   0,  3060,    12  ));
   fdrefs.push_back(FileDataPtr(   0,  3060,    13  ));
   fdrefs.push_back(FileDataPtr(   0,  3050,    22  ));
   fdrefs.push_back(FileDataPtr(   0,  1024,    64  ));
   fdrefs.push_back(FileDataPtr(   0,   512,    64  ));
   fdrefs.push_back(FileDataPtr(   0,   768,    64  ));
   fdrefs.push_back(FileDataPtr(   0,   768,   129  ));

   for(uint32_t i=0; i<fdrefs.size(); i++)
   {
      cout << fdrefs[i].getDataCopy().toHexStr() << endl;
   }


   FileDataPtr fdrHit(   0, 768,  16 );
   FileDataPtr fdrMiss1( 0,   0, 128 );
   FileDataPtr fdrMiss2( 0, 256, 128 );

   cout << "Testing Cache Hits" << endl;
   TIMER_START("CacheHit_50000");
   for(uint32_t i=0; i<50000; i++)
   {
      fdrHit.getUnsafeDataPtr();
   }
   TIMER_STOP("CacheHit_50000");


   cout << "Testing Cache Misses" << endl;
   TIMER_START("CacheMiss_50000");
   for(uint32_t i=0; i<50000; i++)
   {
      fdrMiss1.getUnsafeDataPtr();
      fdrMiss2.getUnsafeDataPtr();
   }
   TIMER_STOP("CacheMiss_50000");




   // Test multi-file caching
   fdrefs.clear();
   fdrefs.push_back(FileDataPtr(   0,     0,    16  ));
   fdrefs.push_back(FileDataPtr(   0,     0,     8  ));
   fdrefs.push_back(FileDataPtr(   0,     8,     8  ));
   fdrefs.push_back(FileDataPtr(   0,     0,    32  ));
   fdrefs.push_back(FileDataPtr(   0,     8,     8  ));
   fdrefs.push_back(FileDataPtr(   0,     8,    16  ));
   fdrefs.push_back(FileDataPtr(   0,  3060,    12  ));
   fdrefs.push_back(FileDataPtr(   0,  3060,    13  ));
   fdrefs.push_back(FileDataPtr(   0,  3050,    22  ));
   fdrefs.push_back(FileDataPtr(   0,  1024,    64  ));
   fdrefs.push_back(FileDataPtr(   0,   512,    64  ));
   fdrefs.push_back(FileDataPtr(   0,   768,    64  ));
   fdrefs.push_back(FileDataPtr(   0,   768,   129  ));
   fdrefs.push_back(FileDataPtr(   1,     0,    16  ));
   fdrefs.push_back(FileDataPtr(   1,     0,     8  ));
   fdrefs.push_back(FileDataPtr(   1,     8,     8  ));
   fdrefs.push_back(FileDataPtr(   1,     0,    32  ));
   fdrefs.push_back(FileDataPtr(   1,     8,     8  ));
   fdrefs.push_back(FileDataPtr(   1,     8,    16  ));
   fdrefs.push_back(FileDataPtr(   1,  3060,    12  ));
   fdrefs.push_back(FileDataPtr(   1,  3060,    13  ));
   fdrefs.push_back(FileDataPtr(   1,  3050,    22  ));
   fdrefs.push_back(FileDataPtr(   1,  1024,    64  ));
   fdrefs.push_back(FileDataPtr(   1,   512,    64  ));
   fdrefs.push_back(FileDataPtr(   1,   768,    64  ));
   fdrefs.push_back(FileDataPtr(   1,   768,   129  ));
   fdrefs.push_back(FileDataPtr(   2,     0,    16  ));
   fdrefs.push_back(FileDataPtr(   2,   129,    16  ));
   for(uint32_t i=0; i<fdrefs.size(); i++)
      cout << fdrefs[i].getDataCopy().toHexStr() << endl;


      


}


// This is not ever needed for anything, except to take an existing blk000X.dat
// file and split it into multiple pieces.  I need this for testing purposes...
void CreateMultiBlkFile(string blkdir)
{
   string targDir("multiblktest"); 

   BlockDataManager_FileRefs & bdm = BlockDataManager_FileRefs::GetInstance(); 
   bdm.SetBlkFileLocation(blkdir, 4, 1);
   bdm.parseEntireBlockchain();  

   uint32_t topBlk = bdm.getTopBlockHeight();
   uint32_t onethird = topBlk/3;
   uint32_t twothird = 2*topBlk/3;

   string fname;
   BinaryData magic = bdm.getMagicBytes();
   ofstream os;

   fname = pathJoin(targDir, "blk0001.dat");
   os.open(fname.c_str(), ios::out | ios::binary);
   for(uint32_t i=0; i<onethird; i++)
   {
      BlockHeader * bhp = bdm.getHeaderByHeight(i);
      os.write( bhp->serializeWholeBlock(magic, true).toBinStr().c_str(), bhp->getBlockSize()+8);
   }
   os.close();


   fname = pathJoin(targDir, "blk0002.dat");
   os.open(fname.c_str(), ios::out | ios::binary);
   for(uint32_t i=onethird; i<twothird; i++)
   {
      BlockHeader * bhp = bdm.getHeaderByHeight(i);
      os.write( bhp->serializeWholeBlock(magic, true).toBinStr().c_str(), bhp->getBlockSize()+8);
   }
   os.close();

   fname = pathJoin(targDir, "blk0003sm.dat");
   os.open(fname.c_str(), ios::out | ios::binary);
   for(uint32_t i=twothird; i<topBlk-8; i++)
   {
      BlockHeader * bhp = bdm.getHeaderByHeight(i);
      os.write( bhp->serializeWholeBlock(magic, true).toBinStr().c_str(), bhp->getBlockSize()+8);
   }
   os.close();

   fname = pathJoin(targDir, "blk0003big.dat");
   os.open(fname.c_str(), ios::out | ios::binary);
   for(uint32_t i=twothird; i<topBlk-6; i++)
   {
      BlockHeader * bhp = bdm.getHeaderByHeight(i);
      os.write( bhp->serializeWholeBlock(magic, true).toBinStr().c_str(), bhp->getBlockSize()+8);
   }
   os.close();

   fname = pathJoin(targDir, "blk0003bigger.dat");
   os.open(fname.c_str(), ios::out | ios::binary);
   for(uint32_t i=twothird; i<topBlk-4; i++)
   {
      BlockHeader * bhp = bdm.getHeaderByHeight(i);
      os.write( bhp->serializeWholeBlock(magic, true).toBinStr().c_str(), bhp->getBlockSize()+8);
   }
   os.close();
   
   fname = pathJoin(targDir, "blk0004sm.dat");
   os.open(fname.c_str(), ios::out | ios::binary);
   for(uint32_t i=topBlk-4; i<topBlk-2; i++)
   {
      BlockHeader * bhp = bdm.getHeaderByHeight(i);
      os.write( bhp->serializeWholeBlock(magic, true).toBinStr().c_str(), bhp->getBlockSize()+8);
   }
   os.close();

   fname = pathJoin(targDir, "blk0005sm.dat");
   os.open(fname.c_str(), ios::out | ios::binary);
   for(uint32_t i=topBlk-2; i<topBlk; i++)
   {
      BlockHeader * bhp = bdm.getHeaderByHeight(i);
      os.write( bhp->serializeWholeBlock(magic, true).toBinStr().c_str(), bhp->getBlockSize()+8);
   }
   os.close();
}




void TestMemoryUsage_UseSystemMonitor(string blkdir)
{
   BlockDataManager_FileRefs & bdm = BlockDataManager_FileRefs::GetInstance(); 
   bdm.SetBlkFileLocation(blkdir, 4, 1);
   bdm.parseEntireBlockchain();  

   char a[256];
   cout << "About to clear txHintMap" << endl;
   cin >> a;
   
   bdm.getTxHintMapRef().clear();

   cin >> a;
   cout << "About to clear txPtrs in headers" << endl;
   cin >> a;

   for(uint32_t i=0; i<bdm.getTopBlockHeight(); i++)
      bdm.getHeadersByHeightRef()[i]->getTxRefPtrList().clear();
      
   cin >> a;
   cout << "About to clear Headers datacopy" << endl;
   cin >> a;

   for(uint32_t i=0; i<bdm.getTopBlockHeight(); i++)
      bdm.getHeadersByHeightRef()[i]->clearDataCopy();

   cin >> a;
}




void TestOutOfOrder(string blkdir)
{
   /////////////////////////////////////////////////////////////////////////////
   BlockDataManager_FileRefs & bdm = BlockDataManager_FileRefs::GetInstance(); 
   BinaryData myAddress;
   BtcWallet wlt;
   
   // Main-network addresses
   // I do not remember anymore what any of these addresses were for ...
   // All I know is they probably have some tx history..
   myAddress.createFromHex("604875c897a079f4db88e5d71145be2093cae194"); wlt.addAddress(myAddress);
   myAddress.createFromHex("8996182392d6f05e732410de4fc3fa273bac7ee6"); wlt.addAddress(myAddress);
   myAddress.createFromHex("b5e2331304bc6c541ffe81a66ab664159979125b"); wlt.addAddress(myAddress);
   myAddress.createFromHex("ebbfaaeedd97bc30df0d6887fd62021d768f5cb8"); wlt.addAddress(myAddress);

   // P2Pool Address
   //myAddress.createFromHex("4975703dc910107e2cc1321e632d136803e218e8"); wlt.addAddress(myAddress);

   // Add some relevant testnet addresses
   //myAddress.createFromHex("0c6b92101c7025643c346d9c3e23034a8a843e21"); wlt.addAddress(myAddress);
   //myAddress.createFromHex("34c9f8dc91dfe1ae1c59e76cbe1aa39d0b7fc041"); wlt.addAddress(myAddress);
   //myAddress.createFromHex("d77561813ca968270d5f63794ddb6aab3493605e"); wlt.addAddress(myAddress);
   //myAddress.createFromHex("0e0aec36fe2545fb31a41164fb6954adcd96b342"); wlt.addAddress(myAddress);

   // These two addresses were used at one point for testing unconfirmed balances
   myAddress.createFromHex("8c61f6a7558af399e404d82beddcc4692db7b30f"); wlt.addAddress(myAddress);
   myAddress.createFromHex("14445409283ef413f5fb004338377bf042064922"); wlt.addAddress(myAddress);

   bdm.registerWallet(&wlt);


   /////////////////////////////////////////////////////////////////////////////
   cout << "Reading data from blockchain... (with wallet scan)" << endl;
   TIMER_START("BDM_Load_Scan_Blockchain_With_Wallet");
   bdm.SetBlkFileLocation(blkdir, 4, 1);
   bdm.parseEntireBlockchain();  
   TIMER_STOP("BDM_Load_Scan_Blockchain_With_Wallet");
   cout << endl << endl;

   myAddress.createFromHex("11b366edfc0a8b66feebae5c2e25a7b6a5d1cf31"); wlt.addAddress(myAddress);
   myAddress.createFromHex("e826f4a4381453dcdcf9bfeedffe95de7c86ccbd"); wlt.addAddress(myAddress);

   bdm.scanBlockchainForTx(wlt);
}







