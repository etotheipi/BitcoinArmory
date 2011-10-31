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
   bdm.readBlkFile_FromScratch("../../blk0001.dat");
   //bdm.readBlkFile_FromScratch("/home/alan/.bitcoin/blk0001.dat", false);
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

   /////////////////////////////////////////////////////////////////////////////
   cout << "Printing genesis block information:" << endl;
   bdm.getGenesisBlock().pprint(cout, 0, false);
   cout << endl << endl;

   cout << "Printing last block information:" << endl;
   bdm.getTopBlockHeader().pprint(cout, 0, false);
   cout << endl << endl;
   

   /////////////////////////////////////////////////////////////////////////////
   bdm.findAllNonStdTx();


   /////////////////////////////////////////////////////////////////////////////
   BinaryData myAddress;
   BtcWallet wlt;
   myAddress.createFromHex("604875c897a079f4db88e5d71145be2093cae194"); wlt.addAddress(myAddress);
   myAddress.createFromHex("8996182392d6f05e732410de4fc3fa273bac7ee6"); wlt.addAddress(myAddress);
   myAddress.createFromHex("b5e2331304bc6c541ffe81a66ab664159979125b"); wlt.addAddress(myAddress);
   myAddress.createFromHex("ebbfaaeedd97bc30df0d6887fd62021d768f5cb8"); wlt.addAddress(myAddress);
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

   /*
   vector< vector<UnspentTxOut> > sortedUTOs(4);
   sortedUTOs[0] = bdm.getUnspentTxOutsForWallet(myWallet, 0);
   sortedUTOs[1] = bdm.getUnspentTxOutsForWallet(myWallet, 1);
   sortedUTOs[2] = bdm.getUnspentTxOutsForWallet(myWallet, 2);
   sortedUTOs[3] = bdm.getUnspentTxOutsForWallet(myWallet, 3);

   for(int i=0; i<4; i++)
   {
      cout << "   Sorting Method: " << i << endl;
      cout << "   Value\t#Conf\tTxHash\tTxIdx" << endl;
      for(int j=0; j<sortedUTOs[i].size(); j++)
      {
         cout << "   "
              << sortedUTOs[i][j].getValue()/1.01e8 << "\t"
              << sortedUTOs[i][j].getNumConfirm() << "\t"
              << sortedUTOs[i][j].getTxHash().getSliceCopy(0,3).toHexStr() << "\t"
              << sortedUTOs[i][j].getTxOutIndex() << endl;
      }
      cout << endl;
   }
   */




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
