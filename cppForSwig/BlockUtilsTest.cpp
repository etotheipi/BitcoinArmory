#include <iostream>
#include <fstream>
#include "UniversalTimer.h"
#include "BinaryData.h"
#include "BtcUtils.h"
#include "BlockUtils.h"


using namespace std;

int main(void)
{
   BlockDataManager_FullRAM & bdm = BlockDataManager_FullRAM::GetInstance(); 

   /////////////////////////////////////////////////////////////////////////////
   cout << "Reading data from blockchain..." << endl;
   TIMER_START("BDM_Load_and_Scan_BlkChain");
   bdm.readBlkFile_FromScratch("/home/alan/.bitcoin/blk0001.dat");
   //bdm.readBlkFile_FromScratch("C:/Documents and Settings/VBox/Application Data/Bitcoin/blk0001.dat");
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
   cout << "Verify integrity of blockchain file (merkleroots leading zeros on headers)" << endl;
   TIMER_START("Verify blk0001.dat integrity");
   bool isVerified = bdm.verifyBlkFileIntegrity();
   TIMER_STOP("Verify blk0001.dat integrity");
   cout << "Done!   Your blkfile " << (isVerified ? "is good!" : " HAS ERRORS") << endl;
   cout << endl << endl;

   /////////////////////////////////////////////////////////////////////////////
   cout << "Printing genesis block information:" << endl;
   bdm.getGenesisBlock().pprint(cout, 0, false);
   cout << endl << endl;

   cout << "Printing last block information:" << endl;
   bdm.getTopBlockHeader().pprint(cout, 0, false);
   cout << endl << endl;

   cout << "Next-to-top block:" << endl;
   BlockHeaderRef & topm1 = *(bdm.getHeaderByHash( bdm.getTopBlockHeader().getPrevHash()));
   topm1.pprint(cout, 0, false);
   cout << endl << endl;
   
   /////////////////////////////////////////////////////////////////////////////
   cout << "Verifying MerkleRoot of blk 100014" << endl;
   vector<BinaryData> merkletree(0);
   BlockHeaderRef & blk100k = *(bdm.getHeaderByHeight(100014));
   BinaryData merkroot = blk100k.calcMerkleRoot(&merkletree);
   isVerified = blk100k.verifyMerkleRoot();
   cout << (isVerified ? "Correct!" : "Incorrect!") 
        << "  ("  << merkroot.toHexStr() << ")" << endl;
   cout << endl << endl;



   /////////////////////////////////////////////////////////////////////////////
   uint32_t nTx = blk100k.getNumTx();
   vector<TxRef*> & txptrVect = blk100k.getTxRefPtrList();
   blk100k.pprint(cout, 0, false);
   cout << "Now print out the txinx/outs for this block:" << endl;
   for(uint32_t t=0; t<nTx; t++)
      txptrVect[t]->pprint(cout, 2, false);
   /*
   {
      TxRef & tx = *txrefVect[t]; 
      uint32_t nIn  = tx.getNumTxIn();
      uint32_t nOut = tx.getNumTxOut();
      for(uint32_t in=0; in<nIn; in++)
      {
         tx.getTxInRef(in).pprint();
      }
      for(uint32_t out=0; out<nOut; out++)
      {
         TxOutRef txout = tx.getTxOutRef(out);
         cout << "TxOut:" << endl;
         cout << "\tRecip: " << txout.getRecipientAddr().toHexStr() << endl;
         cout << "\tValue: " << txout.getValue() << endl;
      }
   }
   */
   cout << endl << endl;


   /////////////////////////////////////////////////////////////////////////////
   BinaryData myAddress, myPubKey;
   BtcWallet wlt;
   myAddress.createFromHex("abda0c878dd7b4197daa9622d96704a606d2cd14");
   wlt.addAddress(myAddress);
   myAddress.createFromHex("11b366edfc0a8b66feebae5c2e25a7b6a5d1cf31");
   wlt.addAddress(myAddress);
   myAddress.createFromHex("baa72d8650baec634cdc439c1b84a982b2e596b2");
   wlt.addAddress(myAddress);
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

   /////////////////////////////////////////////////////////////////////////////
   cout << "Printing unsorted allAddr ledger..." << endl;
   wlt.cleanLedger();
   vector<LedgerEntry> const & ledger = wlt.getTxLedger();
   for(uint32_t j=0; j<ledger.size(); j++)
   {  
      cout << "    Tx: " 
           << ledger[j].getAddrStr20().toHexStr() << "  "
           << ledger[j].getValue()/(float)(CONVERTBTC) << " (" 
           << ledger[j].getBlockNum()
           << ")  TxHash: " << ledger[j].getTxHash().getSliceCopy(0,4).toHexStr() << endl;
   }

   cout << "Printing SORTED allAddr ledger..." << endl;
   vector<LedgerEntry> const & ledger2 = wlt.getTxLedger();
   for(uint32_t j=0; j<ledger2.size(); j++)
   {  
      cout << "    Tx: " 
           << ledger2[j].getAddrStr20().toHexStr() << "  "
           << ledger2[j].getValue()/(float)(CONVERTBTC) << " (" 
           << ledger2[j].getBlockNum()
           << ")  TxHash: " << ledger2[j].getTxHash().getSliceCopy(0,4).toHexStr() << endl;
           
   }
   cout << endl << endl;

   /////////////////////////////////////////////////////////////////////////////
   /*
   cout << endl << endl;
   cout << "Scanning the blockchain for all non-std transactions..." << endl;
   TIMER_START("FindNonStdTx");
   vector<TxRef*> nonStdTxVect = bdm.findAllNonStdTx();
   TIMER_STOP("FindNonStdTx");
   cout << endl << "Found " << nonStdTxVect.size() << " such transactions:" << endl;
   for(uint32_t i=0; i<nonStdTxVect.size(); i++)
   {
      TxRef & tx = *(nonStdTxVect[i]);
      cout << "  Block:  " << tx.getHeaderPtr()->getBlockHeight() << endl;
      cout << "  TxHash: " << tx.getThisHash().copySwapEndian().toHexStr() << endl;
      cout << "  #TxIn:  " << tx.getNumTxIn() << endl;
      cout << "  #TxOut: " << tx.getNumTxOut() << endl;
      cout << endl << endl;
   }
   */
   cout << endl << endl;

   /////////////////////////////////////////////////////////////////////////////
   /*
   cout << "Resetting BlockDataManager..." << endl;
   TIMER_WRAP(bdm.Reset());

   bdm.readBlkFile_FromScratch("../blk0001.dat");
   cout << endl << endl;

   cout << endl << "Reading blockchain again" << endl;
   isGenOnMainChain = bdm.organizeChain();
   cout << (isGenOnMainChain ? "No Reorg!" : "Reorg Detected!") << endl;
   cout << endl << endl;

   cout << endl << endl;
   cout << "Printing genesis block information:" << endl;
   bdm.getGenesisBlock().pprint(cout, 0, false);
   */

   cout << endl << endl;
   cout << "Re-displaying top block information:" << endl;
   bdm.getTopBlockHeader().pprint(cout, 0, false);

   /////////////////////////////////////////////////////////////////////////////
   // ***** Print out all timings to stdout and a csv file *****
   //       This file can be loaded into a spreadsheet,
   //       but it's not the prettiest thing...
   UniversalTimer::instance().print();
   UniversalTimer::instance().printCSV("timings.csv");


   char aa[256];
   cout << "Wait a for your client to add a new block to the blk0001.dat " << endl
        << "file.  Then type a few characters and press enter -- will test" << endl
        << "the both BDM::readBlkFileUpdate and BDM::addBlockData()" << endl;
   cin >> aa;

   cout << "Checking blkfile for updates" << endl;
   bdm.readBlkFileUpdate();

   cout << endl << endl;
   cout << "Printing NEW top block information" << endl;
   bdm.getTopBlockHeader().pprint(cout, 0, false);

   cout << "Enter anything to exit" << endl;
   cin >> aa;
}
