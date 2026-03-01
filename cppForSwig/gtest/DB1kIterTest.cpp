////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2016, goatpig                                               //            
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //                                   
//                                                                            //
////////////////////////////////////////////////////////////////////////////////
#include <limits.h>
#include <iostream>
#include <stdlib.h>
#include <stdint.h>
#include <thread>
#include "gtest.h"

#include "../log.h"
#include "../BinaryData.h"
#include "../BtcUtils.h"
#include "../BlockObj.h"
#include "../StoredBlockObj.h"
#include "../PartialMerkle.h"
#include "../EncryptionUtils.h"
#include "../lmdb_wrapper.h"
#include "../BlockUtils.h"
#include "../ScrAddrObj.h"
#include "../BtcWallet.h"
#include "../BlockDataViewer.h"
#include "../cryptopp/DetSign.h"
#include "../cryptopp/integer.h"
#include "../Progress.h"
#include "../reorgTest/blkdata.h"
#include "../BDM_seder.h"
#include "../BDM_Server.h"
#include "../TxClasses.h"
#include "../txio.h"
#include "../bdmenums.h"
#include "../SwigClient.h"


#ifdef _MSC_VER
#ifdef mlock
#undef mlock
#undef munlock
#endif
#include "win32_posix.h"
#undef close

#ifdef _DEBUG
//#define _CRTDBG_MAP_ALLOC
#include <stdlib.h>
#include <crtdbg.h>

#ifndef DBG_NEW
#define DBG_NEW new ( _NORMAL_BLOCK , __FILE__ , __LINE__ )
#define new DBG_NEW
#endif
#endif
#endif

#define READHEX BinaryData::CreateFromHex

static uint32_t getTopBlockHeightInDB(BlockDataManager &bdm, DB_SELECT db)
{
   StoredDBInfo sdbi;
   bdm.getIFace()->getStoredDBInfo(db, 0);
   return sdbi.topBlkHgt_;
}

static uint64_t getDBBalanceForHash160(
   BlockDataManager &bdm,
   BinaryDataRef addr160
   )
{
   StoredScriptHistory ssh;

   bdm.getIFace()->getStoredScriptHistory(ssh, HASH160PREFIX + addr160);
   if (!ssh.isInitialized())
      return 0;

   return ssh.getScriptBalance();
}

// Utility function - Clean up comments later
static int char2int(char input)
{
   if (input >= '0' && input <= '9')
      return input - '0';
   if (input >= 'A' && input <= 'F')
      return input - 'A' + 10;
   if (input >= 'a' && input <= 'f')
      return input - 'a' + 10;
   return 0;
}

// This function assumes src to be a zero terminated sanitized string with
// an even number of [0-9a-f] characters, and target to be sufficiently large
static void hex2bin(const char* src, unsigned char* target)
{
   while (*src && src[1])
   {
      *(target++) = char2int(*src) * 16 + char2int(src[1]);
      src += 2;
   }
}

#if ! defined(_MSC_VER) && ! defined(__MINGW32__)
/////////////////////////////////////////////////////////////////////////////
static void rmdir(string src)
{
   char* syscmd = new char[4096];
   sprintf(syscmd, "rm -rf %s", src.c_str());
   system(syscmd);
   delete[] syscmd;
}

/////////////////////////////////////////////////////////////////////////////
static void mkdir(string newdir)
{
   char* syscmd = new char[4096];
   sprintf(syscmd, "mkdir -p %s", newdir.c_str());
   system(syscmd);
   delete[] syscmd;
}
#endif

static void concatFile(const string &from, const string &to)
{
   std::ifstream i(from, ios::binary);
   std::ofstream o(to, ios::app | ios::binary);

   o << i.rdbuf();
}

static void appendBlocks(const std::vector<std::string> &files, const std::string &to)
{
   for (const std::string &f : files)
      concatFile("../reorgTest/blk_" + f + ".dat", to);
}

static void setBlocks(const std::vector<std::string> &files, const std::string &to)
{
   std::ofstream o(to, ios::trunc | ios::binary);
   o.close();

   for (const std::string &f : files)
      concatFile("../reorgTest/blk_" + f + ".dat", to);
}

static void nullProgress(unsigned, double, unsigned, unsigned)
{

}

static BinaryData getTx(unsigned height, unsigned id)
{
   stringstream ss;
   ss << "../reorgTest/blk_" << height << ".dat";

   ifstream blkfile(ss.str(), ios::binary);
   blkfile.seekg(0, ios::end);
   auto size = blkfile.tellg();
   blkfile.seekg(0, ios::beg);

   vector<char> vec;
   vec.resize(size);
   blkfile.read(&vec[0], size);
   blkfile.close();

   BinaryRefReader brr((uint8_t*)&vec[0], size);
   StoredHeader sbh;
   sbh.unserializeFullBlock(brr, false, true);

   if (sbh.stxMap_.size() - 1 < id)
      throw range_error("invalid tx id");

   auto& stx = sbh.stxMap_[id];
   return stx.dataCopy_;
}

////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
string registerBDV(Clients* clients, const BinaryData& magic_word)
{
   Command cmd;
   cmd.method_ = "registerBDV";
   BinaryDataObject bdo(magic_word);
   cmd.args_.push_back(move(bdo));
   cmd.serialize();

   auto&& result = clients->runCommand(cmd.command_);

   auto& argVec = result.getArgVector();
   auto bdvId = dynamic_pointer_cast<DataObject<BinaryDataObject>>(argVec[0]);
   return bdvId->getObj().toStr();
}

void goOnline(Clients* clients, const string& id)
{
   Command cmd;
   cmd.method_ = "goOnline";
   cmd.ids_.push_back(id);
   cmd.serialize();
   clients->runCommand(cmd.command_);
}

const shared_ptr<BDV_Server_Object> getBDV(Clients* clients, const string& id)
{
   return clients->get(id);
}

void regWallet(Clients* clients, const string& bdvId,
   const vector<BinaryData>& scrAddrs, const string& wltName)
{
   Command cmd;
   BinaryDataObject bdo(wltName);
   cmd.args_.push_back(move(bdo));
   cmd.args_.push_back(move(BinaryDataVector(scrAddrs)));
   cmd.args_.push_back(move(IntType(false)));

   cmd.method_ = "registerWallet";
   cmd.ids_.push_back(bdvId);
   cmd.serialize();

   auto&& result = clients->runCommand(cmd.command_);

   //check result
   auto& argVec = result.getArgVector();
   auto retint = dynamic_pointer_cast<DataObject<IntType>>(argVec[0]);
   if (retint->getObj().getVal() == 0)
      throw runtime_error("server returned false to registerWallet query");
}

void regLockbox(Clients* clients, const string& bdvId,
   const vector<BinaryData>& scrAddrs, const string& wltName)
{
   Command cmd;

   BinaryDataObject bdo(wltName);
   cmd.args_.push_back(move(bdo));
   cmd.args_.push_back(move(BinaryDataVector(scrAddrs)));
   cmd.args_.push_back(move(IntType(false)));

   cmd.method_ = "registerLockbox";
   cmd.ids_.push_back(bdvId);
   cmd.serialize();

   auto&& result = clients->runCommand(cmd.command_);

   //check result
   auto& argVec = result.getArgVector();
   auto retint = dynamic_pointer_cast<DataObject<IntType>>(argVec[0]);
   if (retint->getObj().getVal() == 0)
      throw runtime_error("server returned false to registerWallet query");
}

void waitOnSignal(Clients* clients, const string& bdvId,
   string command, const string& signal)
{
   Command cmd;
   cmd.method_ = "registerCallback";
   cmd.ids_.push_back(bdvId);

   BinaryDataObject bdo(command);
   cmd.args_.push_back(move(bdo));
   cmd.serialize();

   auto processCallback = [&](Arguments args)->bool
   {
      auto& argVec = args.getArgVector();

      for (auto arg : argVec)
      {
         auto argstr = dynamic_pointer_cast<DataObject<BinaryDataObject>>(arg);
         if (argstr == nullptr)
            continue;

         auto&& cb = argstr->getObj().toStr();
         if (cb == signal)
            return true;
      }

      return false;
   };

   while (1)
   {
      auto&& result = clients->runCommand(cmd.command_);

      if (processCallback(move(result)))
         return;
   }
}

void waitOnBDMReady(Clients* clients, const string& bdvId)
{
   waitOnSignal(clients, bdvId, "waitOnBDV", "BDM_Ready");
}

void waitOnNewBlockSignal(Clients* clients, const string& bdvId)
{
   waitOnSignal(clients, bdvId, "getStatus", "NewBlock");
}

void waitOnNewZcSignal(Clients* clients, const string& bdvId)
{
   waitOnSignal(clients, bdvId, "getStatus", "BDV_ZC");
}

void waitOnWalletRefresh(Clients* clients, const string& bdvId)
{
   waitOnSignal(clients, bdvId, "getStatus", "BDV_Refresh");
}

void triggerNewBlockNotification(BlockDataManagerThread* bdmt)
{
   auto nodePtr = bdmt->bdm()->networkNode_;
   auto nodeUnitTest = (NodeUnitTest*)nodePtr.get();

   nodeUnitTest->mockNewBlock();
}

struct ZcVector
{
   vector<Tx> zcVec_;

   void push_back(BinaryData rawZc, unsigned zcTime)
   {
      Tx zctx(rawZc);
      zctx.setTxTime(zcTime);

      zcVec_.push_back(move(zctx));
   }
};

void pushNewZc(BlockDataManagerThread* bdmt, const ZcVector& zcVec)
{
   auto zcConf = bdmt->bdm()->zeroConfCont_;

   ZeroConfContainer::ZcActionStruct newzcstruct;
   newzcstruct.action_ = Zc_NewTx;

   map<BinaryData, Tx> newzcmap;

   for (auto& newzc : zcVec.zcVec_)
   {
      auto&& zckey = zcConf->getNewZCkey();
      newzcmap[zckey] = newzc;
   }

   newzcstruct.setData(move(newzcmap));
   zcConf->newZcStack_.push_back(move(newzcstruct));
}


////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
class DB1kIter : public ::testing::Test
{
protected:
   BlockDataManagerThread *theBDMt_;
   Clients* clients_;

   void initBDM(void)
   {
      ScrAddrFilter::init();
      theBDMt_ = new BlockDataManagerThread(config);
      iface_ = theBDMt_->bdm()->getIFace();

      auto mockedShutdown = [](void)->void {};
      clients_ = new Clients(theBDMt_, mockedShutdown);
   }

   /////////////////////////////////////////////////////////////////////////////
   virtual void SetUp()
   {
      LOGDISABLESTDOUT();
      magic_ = READHEX(MAINNET_MAGIC_BYTES);
      ghash_ = READHEX(MAINNET_GENESIS_HASH_HEX);
      gentx_ = READHEX(MAINNET_GENESIS_TX_HASH_HEX);
      zeros_ = READHEX("00000000");

      blkdir_ = string("./blkfiletest");
      homedir_ = string("./fakehomedir");
      ldbdir_ = string("./ldbtestdir");

      rmdir(blkdir_);
      rmdir(homedir_);
      rmdir(ldbdir_);

      mkdir(blkdir_);
      mkdir(homedir_);
      mkdir(ldbdir_);

      // Put the first 5 blocks into the blkdir
      blk0dat_ = BtcUtils::getBlkFilename(blkdir_, 0);
      setBlocks({ "0", "1", "2", "3", "4", "5" }, blk0dat_);

      config.armoryDbType_ = ARMORY_DB_BARE;
      config.blkFileLocation_ = blkdir_;
      config.dbDir_ = ldbdir_;
      config.threadCount_ = 3;

      config.genesisBlockHash_ = ghash_;
      config.genesisTxHash_ = gentx_;
      config.magicBytes_ = magic_;
      config.nodeType_ = Node_UnitTest;

      wallet1id = BinaryData("wallet1");
      wallet2id = BinaryData("wallet2");
      LB1ID = BinaryData(TestChain::lb1B58ID);
      LB2ID = BinaryData(TestChain::lb2B58ID);

      initBDM();
   }

   /////////////////////////////////////////////////////////////////////////////
   virtual void TearDown(void)
   {
      if (clients_ != nullptr)
      {
         clients_->exitRequestLoop();
         clients_->shutdown();
      }

      delete clients_;
      delete theBDMt_;

      theBDMt_ = nullptr;
      clients_ = nullptr;

      rmdir(blkdir_);
      rmdir(homedir_);

#ifdef _MSC_VER
      rmdir("./ldbtestdir");
      mkdir("./ldbtestdir");
#else
      string delstr = ldbdir_ + "/*";
      rmdir(delstr);
#endif
      LOGENABLESTDOUT();
      CLEANUP_ALL_TIMERS();
   }

   BlockDataManagerConfig config;

   LMDBBlockDatabase* iface_;
   BinaryData magic_;
   BinaryData ghash_;
   BinaryData gentx_;
   BinaryData zeros_;

   string blkdir_;
   string homedir_;
   string ldbdir_;
   string blk0dat_;

   BinaryData wallet1id;
   BinaryData wallet2id;
   BinaryData LB1ID;
   BinaryData LB2ID;
};

////////////////////////////////////////////////////////////////////////////////
TEST_F(DB1kIter, DbInit1kIter)
{
   theBDMt_->start(config.initMode_);
   auto&& bdvID = registerBDV(clients_, magic_);

   vector<BinaryData> scrAddrVec;
   scrAddrVec.push_back(TestChain::scrAddrA);
   scrAddrVec.push_back(TestChain::scrAddrB);
   scrAddrVec.push_back(TestChain::scrAddrC);
   scrAddrVec.push_back(TestChain::scrAddrD);
   scrAddrVec.push_back(TestChain::scrAddrE);
   scrAddrVec.push_back(TestChain::scrAddrF);

   const vector<BinaryData> lb1ScrAddrs
   {
      TestChain::lb1ScrAddr,
      TestChain::lb1ScrAddrP2SH
   };
   const vector<BinaryData> lb2ScrAddrs
   {
      TestChain::lb2ScrAddr,
      TestChain::lb2ScrAddrP2SH
   };

   regWallet(clients_, bdvID, scrAddrVec, "wallet1");
   regLockbox(clients_, bdvID, lb1ScrAddrs, TestChain::lb1B58ID);
   regLockbox(clients_, bdvID, lb2ScrAddrs, TestChain::lb2B58ID);

   //wait on signals
   goOnline(clients_, bdvID);
   waitOnBDMReady(clients_, bdvID);

   clients_->exitRequestLoop();
   clients_->shutdown();

   delete clients_;
   delete theBDMt_;

   auto fakeprog = [](BDMPhase, double, unsigned, unsigned)->void
   {};

   for (unsigned i = 0; i<1000; i++)
   {
      cout << "iter: " << i << endl;
      initBDM();
      auto bdm = theBDMt_->bdm();
      bdm->doInitialSyncOnLoad_Rebuild(fakeprog);

      clients_->exitRequestLoop();
      clients_->shutdown();

      delete clients_;
      delete theBDMt_;
   }

   //one last init so that TearDown doesn't blow up
   initBDM();
}

////////////////////////////////////////////////////////////////////////////////
TEST_F(DB1kIter, DbInit1kIter_WithSignals)
{

   vector<BinaryData> scrAddrVec;

   const vector<BinaryData> lb1ScrAddrs
   {
      TestChain::lb1ScrAddr,
      TestChain::lb1ScrAddrP2SH
   };
   const vector<BinaryData> lb2ScrAddrs
   {
      TestChain::lb2ScrAddr,
      TestChain::lb2ScrAddrP2SH
   };

   for (unsigned i = 0; i < 1000; i++)
   {
      scrAddrVec.clear();

      scrAddrVec.push_back(TestChain::scrAddrA);
      scrAddrVec.push_back(TestChain::scrAddrB);
      scrAddrVec.push_back(TestChain::scrAddrC);
      scrAddrVec.push_back(TestChain::scrAddrE);

      setBlocks({ "0", "1", "2" }, blk0dat_);

      theBDMt_->start(config.initMode_);
      auto&& bdvID = registerBDV(clients_, magic_);

      regWallet(clients_, bdvID, scrAddrVec, "wallet1");
      regLockbox(clients_, bdvID, lb1ScrAddrs, TestChain::lb1B58ID);
      regLockbox(clients_, bdvID, lb2ScrAddrs, TestChain::lb2B58ID);

      auto bdvPtr = getBDV(clients_, bdvID);

      //wait on signals
      goOnline(clients_, bdvID);
      waitOnBDMReady(clients_, bdvID);
      auto wlt = bdvPtr->getWalletOrLockbox(wallet1id);
      auto wltLB1 = bdvPtr->getWalletOrLockbox(LB1ID);
      auto wltLB2 = bdvPtr->getWalletOrLockbox(LB2ID);

      EXPECT_EQ(iface_->getTopBlockHeight(HEADERS), 2);
      EXPECT_EQ(iface_->getTopBlockHash(HEADERS), TestChain::blkHash2);
      EXPECT_TRUE(theBDMt_->bdm()->blockchain()->getHeaderByHash(TestChain::blkHash2)->isMainBranch());

      const ScrAddrObj* scrObj;
      scrObj = wlt->getScrAddrObjByKey(TestChain::scrAddrA);
      EXPECT_EQ(scrObj->getFullBalance(), 50 * COIN);
      scrObj = wlt->getScrAddrObjByKey(TestChain::scrAddrB);
      EXPECT_EQ(scrObj->getFullBalance(), 55 * COIN);
      scrObj = wlt->getScrAddrObjByKey(TestChain::scrAddrC);
      EXPECT_EQ(scrObj->getFullBalance(), 0 * COIN);

      uint64_t fullBalance = wlt->getFullBalance();
      uint64_t spendableBalance = wlt->getSpendableBalance(3);
      uint64_t unconfirmedBalance = wlt->getUnconfirmedBalance(3);
      EXPECT_EQ(fullBalance, 105 * COIN);
      EXPECT_EQ(spendableBalance, 5 * COIN);
      EXPECT_EQ(unconfirmedBalance, 105 * COIN);

      //add ZC
      BinaryData rawZC(259);
      FILE *ff = fopen("../reorgTest/ZCtx.tx", "rb");
      fread(rawZC.getPtr(), 259, 1, ff);
      fclose(ff);
      ZcVector rawZcVec;
      rawZcVec.push_back(move(rawZC), 1300000000);

      BinaryData ZChash = READHEX(TestChain::zcTxHash256);

      pushNewZc(theBDMt_, rawZcVec);
      waitOnNewZcSignal(clients_, bdvID);

      scrObj = wlt->getScrAddrObjByKey(TestChain::scrAddrA);
      EXPECT_EQ(scrObj->getFullBalance(), 50 * COIN);
      scrObj = wlt->getScrAddrObjByKey(TestChain::scrAddrB);
      EXPECT_EQ(scrObj->getFullBalance(), 75 * COIN);
      scrObj = wlt->getScrAddrObjByKey(TestChain::scrAddrC);
      EXPECT_EQ(scrObj->getFullBalance(), 10 * COIN);

      fullBalance = wlt->getFullBalance();
      spendableBalance = wlt->getSpendableBalance(4);
      unconfirmedBalance = wlt->getUnconfirmedBalance(4);
      EXPECT_EQ(fullBalance, 135 * COIN);
      EXPECT_EQ(spendableBalance, 5 * COIN);
      EXPECT_EQ(unconfirmedBalance, 135 * COIN);

      //check ledger for ZC
      LedgerEntry le = wlt->getLedgerEntryForTx(ZChash);
      EXPECT_EQ(le.getTxTime(), 1300000000);
      EXPECT_EQ(le.getValue(), 3000000000);
      EXPECT_EQ(le.getBlockNum(), UINT32_MAX);

      //pull ZC from DB, verify it's carrying the proper data
      LMDBEnv::Transaction *dbtx =
         new LMDBEnv::Transaction(iface_->dbEnv_[ZERO_CONF].get(), LMDB::ReadOnly);
      StoredTx zcStx;
      BinaryData zcKey = WRITE_UINT16_BE(0xFFFF);
      zcKey.append(WRITE_UINT32_LE(0));

      EXPECT_EQ(iface_->getStoredZcTx(zcStx, zcKey), true);
      EXPECT_EQ(zcStx.thisHash_, ZChash);
      EXPECT_EQ(zcStx.numBytes_, TestChain::zcTxSize);
      EXPECT_EQ(zcStx.fragBytes_, 190);
      EXPECT_EQ(zcStx.numTxOut_, 2);
      EXPECT_EQ(zcStx.stxoMap_.begin()->second.getValue(), 10 * COIN);

      //check ZChash in DB
      EXPECT_EQ(iface_->getTxHashForLdbKey(zcKey), ZChash);
      delete dbtx;

      //restart bdm
      bdvPtr.reset();
      wlt.reset();
      wltLB1.reset();
      wltLB2.reset();

      clients_->exitRequestLoop();
      clients_->shutdown();

      delete clients_;
      delete theBDMt_;

      initBDM();

      theBDMt_->start(config.initMode_);
      bdvID = registerBDV(clients_, magic_);

      scrAddrVec.pop_back();
      regWallet(clients_, bdvID, scrAddrVec, "wallet1");
      regLockbox(clients_, bdvID, lb1ScrAddrs, TestChain::lb1B58ID);
      regLockbox(clients_, bdvID, lb2ScrAddrs, TestChain::lb2B58ID);

      bdvPtr = getBDV(clients_, bdvID);

      //wait on signals
      goOnline(clients_, bdvID);
      waitOnBDMReady(clients_, bdvID);
      wlt = bdvPtr->getWalletOrLockbox(wallet1id);
      wltLB1 = bdvPtr->getWalletOrLockbox(LB1ID);
      wltLB2 = bdvPtr->getWalletOrLockbox(LB2ID);

      //add 4th block
      setBlocks({ "0", "1", "2", "3" }, blk0dat_);
      triggerNewBlockNotification(theBDMt_);
      waitOnNewBlockSignal(clients_, bdvID);

      EXPECT_EQ(iface_->getTopBlockHeight(HEADERS), 3);
      EXPECT_EQ(iface_->getTopBlockHash(HEADERS), TestChain::blkHash3);
      EXPECT_TRUE(theBDMt_->bdm()->blockchain()->getHeaderByHash(TestChain::blkHash3)->isMainBranch());

      scrObj = wlt->getScrAddrObjByKey(TestChain::scrAddrA);
      EXPECT_EQ(scrObj->getFullBalance(), 50 * COIN);
      scrObj = wlt->getScrAddrObjByKey(TestChain::scrAddrB);
      EXPECT_EQ(scrObj->getFullBalance(), 20 * COIN);
      scrObj = wlt->getScrAddrObjByKey(TestChain::scrAddrC);
      EXPECT_EQ(scrObj->getFullBalance(), 65 * COIN);

      fullBalance = wlt->getFullBalance();
      spendableBalance = wlt->getSpendableBalance(5);
      unconfirmedBalance = wlt->getUnconfirmedBalance(5);
      EXPECT_EQ(fullBalance, 135 * COIN);
      EXPECT_EQ(spendableBalance, 5 * COIN);
      EXPECT_EQ(unconfirmedBalance, 105 * COIN);

      le = wlt->getLedgerEntryForTx(ZChash);
      EXPECT_EQ(le.getTxTime(), 1300000000);
      EXPECT_EQ(le.getValue(), 3000000000);
      EXPECT_EQ(le.getBlockNum(), UINT32_MAX);

      //The BDM was recycled, but the ZC is still live, and the mempool should 
      //have reloaded it. Pull from DB and verify
      dbtx = new LMDBEnv::Transaction(iface_->dbEnv_[ZERO_CONF].get(), LMDB::ReadOnly);
      StoredTx zcStx2;

      EXPECT_EQ(iface_->getStoredZcTx(zcStx2, zcKey), true);
      EXPECT_EQ(zcStx2.thisHash_, ZChash);
      EXPECT_EQ(zcStx2.numBytes_, TestChain::zcTxSize);
      EXPECT_EQ(zcStx2.fragBytes_, 190);
      EXPECT_EQ(zcStx2.numTxOut_, 2);
      EXPECT_EQ(zcStx2.stxoMap_.begin()->second.getValue(), 10 * COIN);

      delete dbtx;

      //add 5th block
      setBlocks({ "0", "1", "2", "3", "4" }, blk0dat_);
      triggerNewBlockNotification(theBDMt_);
      waitOnNewBlockSignal(clients_, bdvID);

      EXPECT_EQ(iface_->getTopBlockHeight(HEADERS), 4);
      EXPECT_EQ(iface_->getTopBlockHash(HEADERS), TestChain::blkHash4);
      EXPECT_TRUE(theBDMt_->bdm()->blockchain()->getHeaderByHash(TestChain::blkHash4)->isMainBranch());

      scrObj = wlt->getScrAddrObjByKey(TestChain::scrAddrA);
      EXPECT_EQ(scrObj->getFullBalance(), 50 * COIN);
      scrObj = wlt->getScrAddrObjByKey(TestChain::scrAddrB);
      EXPECT_EQ(scrObj->getFullBalance(), 20 * COIN);
      scrObj = wlt->getScrAddrObjByKey(TestChain::scrAddrC);
      EXPECT_EQ(scrObj->getFullBalance(), 20 * COIN);

      fullBalance = wlt->getFullBalance();
      spendableBalance = wlt->getSpendableBalance(5);
      unconfirmedBalance = wlt->getUnconfirmedBalance(5);
      EXPECT_EQ(fullBalance, 90 * COIN);
      EXPECT_EQ(spendableBalance, 10 * COIN);
      EXPECT_EQ(unconfirmedBalance, 60 * COIN);

      dbtx = new LMDBEnv::Transaction(iface_->dbEnv_[ZERO_CONF].get(), LMDB::ReadOnly);
      StoredTx zcStx3;

      EXPECT_EQ(iface_->getStoredZcTx(zcStx3, zcKey), true);
      EXPECT_EQ(zcStx3.thisHash_, ZChash);
      EXPECT_EQ(zcStx3.numBytes_, TestChain::zcTxSize);
      EXPECT_EQ(zcStx3.fragBytes_, 190); // Not sure how Python can get this value
      EXPECT_EQ(zcStx3.numTxOut_, 2);
      EXPECT_EQ(zcStx3.stxoMap_.begin()->second.getValue(), 10 * COIN);

      delete dbtx;

      //add 6th block
      setBlocks({ "0", "1", "2", "3", "4", "5" }, blk0dat_);
      triggerNewBlockNotification(theBDMt_);
      waitOnNewBlockSignal(clients_, bdvID);

      EXPECT_EQ(iface_->getTopBlockHeight(HEADERS), 5);
      EXPECT_EQ(iface_->getTopBlockHash(HEADERS), TestChain::blkHash5);
      EXPECT_TRUE(theBDMt_->bdm()->blockchain()->getHeaderByHash(TestChain::blkHash5)->isMainBranch());

      scrObj = wlt->getScrAddrObjByKey(TestChain::scrAddrA);
      EXPECT_EQ(scrObj->getFullBalance(), 50 * COIN);
      scrObj = wlt->getScrAddrObjByKey(TestChain::scrAddrB);
      EXPECT_EQ(scrObj->getFullBalance(), 70 * COIN);
      scrObj = wlt->getScrAddrObjByKey(TestChain::scrAddrC);
      EXPECT_EQ(scrObj->getFullBalance(), 20 * COIN);

      fullBalance = wlt->getFullBalance();
      spendableBalance = wlt->getSpendableBalance(5);
      unconfirmedBalance = wlt->getUnconfirmedBalance(5);
      EXPECT_EQ(fullBalance, 140 * COIN);
      EXPECT_EQ(spendableBalance, 40 * COIN);
      EXPECT_EQ(unconfirmedBalance, 140 * COIN);

      le = wlt->getLedgerEntryForTx(ZChash);
      EXPECT_EQ(le.getTxTime(), 1231009513);
      EXPECT_EQ(le.getValue(), 3000000000);
      EXPECT_EQ(le.getBlockNum(), 5);

      //Tx is now in a block, ZC should be gone from DB
      dbtx = new LMDBEnv::Transaction(iface_->dbEnv_[ZERO_CONF].get(), LMDB::ReadWrite);
      StoredTx zcStx4;

      EXPECT_EQ(iface_->getStoredZcTx(zcStx4, zcKey), false);

      delete dbtx;

      bdvPtr.reset();
      wlt.reset();
      wltLB1.reset();
      wltLB2.reset();

      clients_->exitRequestLoop();
      clients_->shutdown();

      delete clients_;
      delete theBDMt_;

      cout << i << endl;

      rmdir(blkdir_);
      rmdir(homedir_);
      rmdir(ldbdir_);

      mkdir(blkdir_);
      mkdir(homedir_);
      mkdir(ldbdir_);

      initBDM();
   }
}

////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
// Now actually execute all the tests
////////////////////////////////////////////////////////////////////////////////
GTEST_API_ int main(int argc, char **argv)
{
#ifdef _MSC_VER
   _CrtSetDbgFlag(_CRTDBG_ALLOC_MEM_DF | _CRTDBG_LEAK_CHECK_DF);

   WSADATA wsaData;
   WORD wVersion = MAKEWORD(2, 0);
   WSAStartup(wVersion, &wsaData);
#endif

   std::cout << "Running main() from gtest_main.cc\n";

   // Setup the log file 
   STARTLOGGING("cppTestsLog.txt", LogLvlDebug2);
   //LOGDISABLESTDOUT();

   testing::InitGoogleTest(&argc, argv);
   int exitCode = RUN_ALL_TESTS();

   FLUSHLOG();
   CLEANUPLOG();

   return exitCode;
}
