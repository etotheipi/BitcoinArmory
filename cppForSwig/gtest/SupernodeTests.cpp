////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2015, Armory Technologies, Inc.                        //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE-ATI or http://www.gnu.org/licenses/agpl.html                  //
//                                                                            //
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
// TODO:  These tests were taken directly from the BlockUtilsSuper.cpp where 
//        they previously ran without issue.  After bringing them over to here,
//        they now seg-fault.  Disabled for now, since the PartialMerkleTrees 
//        are not actually in use anywhere yet.
class DISABLED_PartialMerkleTest : public ::testing::Test
{
protected:

   virtual void SetUp(void)
   {
      vector<BinaryData> txList_(7);
      // The "abcd" quartets are to trigger endianness errors -- without them,
      // these hashes are palindromes that work regardless of your endian-handling
      txList_[0] = READHEX("00000000000000000000000000000000"
         "000000000000000000000000abcd0000");
      txList_[1] = READHEX("11111111111111111111111111111111"
         "111111111111111111111111abcd1111");
      txList_[2] = READHEX("22222222222222222222222222222222"
         "222222222222222222222222abcd2222");
      txList_[3] = READHEX("33333333333333333333333333333333"
         "333333333333333333333333abcd3333");
      txList_[4] = READHEX("44444444444444444444444444444444"
         "444444444444444444444444abcd4444");
      txList_[5] = READHEX("55555555555555555555555555555555"
         "555555555555555555555555abcd5555");
      txList_[6] = READHEX("66666666666666666666666666666666"
         "666666666666666666666666abcd6666");

      vector<BinaryData> merkleTree_ = BtcUtils::calculateMerkleTree(txList_);

      /*
      cout << "Merkle Tree looks like the following (7 tx): " << endl;
      cout << "The ** indicates the nodes we care about for partial tree test" << endl;
      cout << "                                                    \n";
      cout << "                   _____0a10_____                   \n";
      cout << "                  /              \\                  \n";
      cout << "                _/                \\_                \n";
      cout << "            65df                    b4d6            \n";
      cout << "          /      \\                /      \\          \n";
      cout << "      6971        22dc        5675        d0b6      \n";
      cout << "     /    \\      /    \\      /    \\      /          \n";
      cout << "   0000  1111  2222  3333  4444  5555  6666         \n";
      cout << "    **                            **                \n";
      cout << "    " << endl;
      cout << endl;

      cout << "Full Merkle Tree (this one has been unit tested before):" << endl;
      for(uint32_t i=0; i<merkleTree_.size(); i++)
      cout << "    " << i << " " << merkleTree_[i].toHexStr() << endl;
      */
   }

   vector<BinaryData> txList_;
   vector<BinaryData> merkleTree_;
};



////////////////////////////////////////////////////////////////////////////////
TEST_F(DISABLED_PartialMerkleTest, FullTree)
{
   vector<bool> isOurs(7);
   isOurs[0] = true;
   isOurs[1] = true;
   isOurs[2] = true;
   isOurs[3] = true;
   isOurs[4] = true;
   isOurs[5] = true;
   isOurs[6] = true;

   //cout << "Start serializing a full tree" << endl;
   PartialMerkleTree pmtFull(7, &isOurs, &txList_);
   BinaryData pmtSerFull = pmtFull.serialize();

   //cout << "Finished serializing (full)" << endl;
   //cout << "Merkle Root: " << pmtFull.getMerkleRoot().toHexStr() << endl;

   //cout << "Starting unserialize (full):" << endl;
   //cout << "Serialized: " << pmtSerFull.toHexStr() << endl;
   PartialMerkleTree pmtFull2(7);
   pmtFull2.unserialize(pmtSerFull);
   BinaryData pmtSerFull2 = pmtFull2.serialize();
   //cout << "Reserializ: " << pmtSerFull2.toHexStr() << endl;
   //cout << "Equal? " << (pmtSerFull==pmtSerFull2 ? "True" : "False") << endl;

   //cout << "Print Tree:" << endl;
   //pmtFull2.pprintTree();
   EXPECT_EQ(pmtSerFull, pmtSerFull2);
}


////////////////////////////////////////////////////////////////////////////////
TEST_F(DISABLED_PartialMerkleTest, SingleLeaf)
{
   vector<bool> isOurs(7);
   /////////////////////////////////////////////////////////////////////////////
   // Test all 7 single-flagged trees
   for (uint32_t i = 0; i<7; i++)
   {
      for (uint32_t j = 0; j<7; j++)
         isOurs[j] = i == j;

      PartialMerkleTree pmt(7, &isOurs, &txList_);
      //cout << "Serializing (partial)" << endl;
      BinaryData pmtSer = pmt.serialize();
      PartialMerkleTree pmt2(7);
      //cout << "Unserializing (partial)" << endl;
      pmt2.unserialize(pmtSer);
      //cout << "Reserializing (partial)" << endl;
      BinaryData pmtSer2 = pmt2.serialize();
      //cout << "Serialized (Partial): " << pmtSer.toHexStr() << endl;
      //cout << "Reserializ (Partial): " << pmtSer.toHexStr() << endl;
      //cout << "Equal? " << (pmtSer==pmtSer2 ? "True" : "False") << endl;

      //cout << "Print Tree:" << endl;
      //pmt2.pprintTree();
      EXPECT_EQ(pmtSer, pmtSer2);
   }
}


////////////////////////////////////////////////////////////////////////////////
TEST_F(DISABLED_PartialMerkleTest, MultiLeaf)
{
   // Use deterministic seed
   srand(0);

   vector<bool> isOurs(7);

   /////////////////////////////////////////////////////////////////////////////
   // Test a variety of 3-flagged trees
   for (uint32_t i = 0; i<512; i++)
   {
      if (i<256)
      {
         // 2/3 of leaves will be selected
         for (uint32_t j = 0; j<7; j++)
            isOurs[j] = (rand() % 3 < 2);
      }
      else
      {
         // 1/3 of leaves will be selected
         for (uint32_t j = 0; j<7; j++)
            isOurs[j] = (rand() % 3 < 1);
      }

      PartialMerkleTree pmt(7, &isOurs, &txList_);
      //cout << "Serializing (partial)" << endl;
      BinaryData pmtSer = pmt.serialize();
      PartialMerkleTree pmt2(7);
      //cout << "Unserializing (partial)" << endl;
      pmt2.unserialize(pmtSer);
      //cout << "Reserializing (partial)" << endl;
      BinaryData pmtSer2 = pmt2.serialize();
      //cout << "Serialized (Partial): " << pmtSer.toHexStr() << endl;
      //cout << "Reserializ (Partial): " << pmtSer.toHexStr() << endl;
      cout << "Equal? " << (pmtSer == pmtSer2 ? "True" : "False") << endl;

      //cout << "Print Tree:" << endl;
      //pmt2.pprintTree();
      EXPECT_EQ(pmtSer, pmtSer2);
   }
}


////////////////////////////////////////////////////////////////////////////////
TEST_F(DISABLED_PartialMerkleTest, EmptyTree)
{
   vector<bool> isOurs(7);
   isOurs[0] = false;
   isOurs[1] = false;
   isOurs[2] = false;
   isOurs[3] = false;
   isOurs[4] = false;
   isOurs[5] = false;
   isOurs[6] = false;

   //cout << "Start serializing a full tree" << endl;
   PartialMerkleTree pmtFull(7, &isOurs, &txList_);
   BinaryData pmtSerFull = pmtFull.serialize();

   //cout << "Finished serializing (full)" << endl;
   //cout << "Merkle Root: " << pmtFull.getMerkleRoot().toHexStr() << endl;

   //cout << "Starting unserialize (full):" << endl;
   //cout << "Serialized: " << pmtSerFull.toHexStr() << endl;
   PartialMerkleTree pmtFull2(7);
   pmtFull2.unserialize(pmtSerFull);
   BinaryData pmtSerFull2 = pmtFull2.serialize();
   //cout << "Reserializ: " << pmtSerFull2.toHexStr() << endl;
   //cout << "Equal? " << (pmtSerFull==pmtSerFull2 ? "True" : "False") << endl;

   //cout << "Print Tree:" << endl;
   //pmtFull2.pprintTree();
   EXPECT_EQ(pmtSerFull, pmtSerFull2);

}


////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
class LMDBTest_Super : public ::testing::Test
{
protected:
   virtual void SetUp(void)
   {
#ifdef _MSC_VER
      rmdir("./ldbtestdir");
      mkdir("./ldbtestdir");
#else
      system("rm -rf ./ldbtestdir/*");
#endif

      magic_ = READHEX(MAINNET_MAGIC_BYTES);
      ghash_ = READHEX(MAINNET_GENESIS_HASH_HEX);
      gentx_ = READHEX(MAINNET_GENESIS_TX_HASH_HEX);
      zeros_ = READHEX("00000000");

      config_.armoryDbType_ = ARMORY_DB_SUPER;
      config_.dbDir_ = string("ldbtestdir");

      config_.genesisBlockHash_ = ghash_;
      config_.genesisTxHash_ = gentx_;
      config_.magicBytes_ = magic_;

      // Make sure the global DB type and prune type are reset for each test
      //iface_->openDatabases( ldbdir_, ghash_, gentx_, magic_, 
      //                        ARMORY_DB_BARE, DB_PRUNE_NONE);
      //       DBUtils::setArmoryDbType(ARMORY_DB_FULL);
      //       DBUtils::setDbPruneType(DB_PRUNE_NONE);

      rawHead_ = READHEX(
         "01000000"
         "1d8f4ec0443e1f19f305e488c1085c95de7cc3fd25e0d2c5bb5d000000000000"
         "9762547903d36881a86751f3f5049e23050113f779735ef82734ebf0b4450081"
         "d8c8c84d"
         "b3936a1a"
         "334b035b");
      headHashLE_ = READHEX(
         "1195e67a7a6d0674bbd28ae096d602e1f038c8254b49dfe79d47000000000000");
      headHashBE_ = READHEX(
         "000000000000479de7df494b25c838f0e102d696e08ad2bb74066d7a7ae69511");

      rawTx0_ = READHEX(
         "01000000016290dce984203b6a5032e543e9e272d8bce934c7de4d15fa0fe44d"
         "d49ae4ece9010000008b48304502204f2fa458d439f957308bca264689aa175e"
         "3b7c5f78a901cb450ebd20936b2c500221008ea3883a5b80128e55c9c6070aa6"
         "264e1e0ce3d18b7cd7e85108ce3d18b7419a0141044202550a5a6d3bb81549c4"
         "a7803b1ad59cdbba4770439a4923624a8acfc7d34900beb54a24188f7f0a4068"
         "9d905d4847cc7d6c8d808a457d833c2d44ef83f76bffffffff0242582c0a0000"
         "00001976a914c1b4695d53b6ee57a28647ce63e45665df6762c288ac80d1f008"
         "000000001976a9140e0aec36fe2545fb31a41164fb6954adcd96b34288ac0000"
         "0000");
      rawTx1_ = READHEX(
         "0100000001f658dbc28e703d86ee17c9a2d3b167a8508b082fa0745f55be5144"
         "a4369873aa010000008c49304602210041e1186ca9a41fdfe1569d5d807ca7ff"
         "6c5ffd19d2ad1be42f7f2a20cdc8f1cc0221003366b5d64fe81e53910e156914"
         "091d12646bc0d1d662b7a65ead3ebe4ab8f6c40141048d103d81ac9691cf13f3"
         "fc94e44968ef67b27f58b27372c13108552d24a6ee04785838f34624b294afee"
         "83749b64478bb8480c20b242c376e77eea2b3dc48b4bffffffff0200e1f50500"
         "0000001976a9141b00a2f6899335366f04b277e19d777559c35bc888ac40aeeb"
         "02000000001976a9140e0aec36fe2545fb31a41164fb6954adcd96b34288ac00"
         "000000");

      rawBlock_ = READHEX(
         // Header
         "01000000eb10c9a996a2340a4d74eaab41421ed8664aa49d18538bab59010000"
         "000000005a2f06efa9f2bd804f17877537f2080030cadbfa1eb50e02338117cc"
         "604d91b9b7541a4ecfbb0a1a64f1ade7"
         // 3 transactions
         "03"
         ///// Tx0, version
         "01000000"
         "01"
         // Tx0, Txin0
         "0000000000000000000000000000000000000000000000000000000000000000"
         "ffffffff"
         "08""04cfbb0a1a02360a""ffffffff"
         // Tx0, 1 TxOut
         "01"
         // Tx0, TxOut0
         "00f2052a01000000"
         "434104c2239c4eedb3beb26785753463be3ec62b82f6acd62efb65f452f8806f"
         "2ede0b338e31d1f69b1ce449558d7061aa1648ddc2bf680834d3986624006a27"
         "2dc21cac"
         // Tx0, Locktime
         "00000000"
         ///// Tx1, Version 
         "01000000"
         // Tx1, 3 txins
         "03"
         // Tx1, TxIn0
         "e8caa12bcb2e7e86499c9de49c45c5a1c6167ea4b894c8c83aebba1b6100f343"
         "01000000"
         "8c493046022100e2f5af5329d1244807f8347a2c8d9acc55a21a5db769e9274e"
         "7e7ba0bb605b26022100c34ca3350df5089f3415d8af82364d7f567a6a297fcc"
         "2c1d2034865633238b8c014104129e422ac490ddfcb7b1c405ab9fb42441246c"
         "4bca578de4f27b230de08408c64cad03af71ee8a3140b40408a7058a1984a9f2"
         "46492386113764c1ac132990d1""ffffffff"
         // Tx1, TxIn1
         "5b55c18864e16c08ef9989d31c7a343e34c27c30cd7caa759651b0e08cae0106"
         "00000000"
         "8c4930460221009ec9aa3e0caf7caa321723dea561e232603e00686d4bfadf46"
         "c5c7352b07eb00022100a4f18d937d1e2354b2e69e02b18d11620a6a9332d563"
         "e9e2bbcb01cee559680a014104411b35dd963028300e36e82ee8cf1b0c8d5bf1"
         "fc4273e970469f5cb931ee07759a2de5fef638961726d04bd5eb4e5072330b9b"
         "371e479733c942964bb86e2b22""ffffffff"
         // Tx1, TxIn2
         "3de0c1e913e6271769d8c0172cea2f00d6d3240afc3a20f9fa247ce58af30d2a"
         "01000000"
         "8c493046022100b610e169fd15ac9f60fe2b507529281cf2267673f4690ba428"
         "cbb2ba3c3811fd022100ffbe9e3d71b21977a8e97fde4c3ba47b896d08bc09ec"
         "b9d086bb59175b5b9f03014104ff07a1833fd8098b25f48c66dcf8fde34cbdbc"
         "c0f5f21a8c2005b160406cbf34cc432842c6b37b2590d16b165b36a3efc9908d"
         "65fb0e605314c9b278f40f3e1a""ffffffff"
         // Tx1, 2 TxOuts
         "02"
         // Tx1, TxOut0
         "40420f0000000000""19""76a914adfa66f57ded1b655eb4ccd96ee07ca62bc1ddfd88ac"
         // Tx1, TxOut1
         "007d6a7d04000000""19""76a914981a0c9ae61fa8f8c96ae6f8e383d6e07e77133e88ac"
         // Tx1 Locktime
         "00000000"
         ///// Tx2 Version
         "01000000"
         // Tx2 1 TxIn
         "01"
         "38e7586e0784280df58bd3dc5e3d350c9036b1ec4107951378f45881799c92a4"
         "00000000"
         "8a47304402207c945ae0bbdaf9dadba07bdf23faa676485a53817af975ddf85a"
         "104f764fb93b02201ac6af32ddf597e610b4002e41f2de46664587a379a01613"
         "23a85389b4f82dda014104ec8883d3e4f7a39d75c9f5bb9fd581dc9fb1b7cdf7"
         "d6b5a665e4db1fdb09281a74ab138a2dba25248b5be38bf80249601ae688c90c"
         "6e0ac8811cdb740fcec31d""ffffffff"
         // Tx2, 2 TxOuts
         "02"
         // Tx2, TxOut0
         "2f66ac6105000000""19""76a914964642290c194e3bfab661c1085e47d67786d2d388ac"
         // Tx2, TxOut1
         "2f77e20000000000""19""76a9141486a7046affd935919a3cb4b50a8a0c233c286c88ac"
         // Tx2 Locktime
         "00000000");

      rawTxUnfrag_ = READHEX(
         // Version
         "01000000"
         // NumTxIn
         "02"
         // Start TxIn0
         "0044fbc929d78e4203eed6f1d3d39c0157d8e5c100bbe0886779c0"
         "ebf6a69324010000008a47304402206568144ed5e7064d6176c74738b04c08ca"
         "19ca54ddeb480084b77f45eebfe57802207927d6975a5ac0e1bb36f5c05356dc"
         "da1f521770511ee5e03239c8e1eecf3aed0141045d74feae58c4c36d7c35beac"
         "05eddddc78b3ce4b02491a2eea72043978056a8bc439b99ddaad327207b09ef1"
         "6a8910828e805b0cc8c11fba5caea2ee939346d7ffffffff"
         // Start TxIn1
         "45c866b219b17695"
         "2508f8e5aea728f950186554fc4a5807e2186a8e1c4009e5000000008c493046"
         "022100bd5d41662f98cfddc46e86ea7e4a3bc8fe9f1dfc5c4836eaf7df582596"
         "cfe0e9022100fc459ae4f59b8279d679003b88935896acd10021b6e2e4619377"
         "e336b5296c5e014104c00bab76a708ba7064b2315420a1c533ca9945eeff9754"
         "cdc574224589e9113469b4e71752146a10028079e04948ecdf70609bf1b9801f"
         "6b73ab75947ac339e5ffffffff"
         // NumTxOut
         "02"
         // Start TxOut0
         "ac4c8bd5000000001976a9148dce8946f1c7763bb60ea5cf16ef514cbed0633b88ac"
         // Start TxOut1
         "002f6859000000001976a9146a59ac0e8f553f292dfe5e9f3aaa1da93499c15e88ac"
         // Locktime
         "00000000");

      rawTxFragged_ = READHEX(
         // Version
         "01000000"
         // NumTxIn
         "02"
         // Start TxIn0
         "0044fbc929d78e4203eed6f1d3d39c0157d8e5c100bbe0886779c0"
         "ebf6a69324010000008a47304402206568144ed5e7064d6176c74738b04c08ca"
         "19ca54ddeb480084b77f45eebfe57802207927d6975a5ac0e1bb36f5c05356dc"
         "da1f521770511ee5e03239c8e1eecf3aed0141045d74feae58c4c36d7c35beac"
         "05eddddc78b3ce4b02491a2eea72043978056a8bc439b99ddaad327207b09ef1"
         "6a8910828e805b0cc8c11fba5caea2ee939346d7ffffffff"
         // Start TxIn1
         "45c866b219b17695"
         "2508f8e5aea728f950186554fc4a5807e2186a8e1c4009e5000000008c493046"
         "022100bd5d41662f98cfddc46e86ea7e4a3bc8fe9f1dfc5c4836eaf7df582596"
         "cfe0e9022100fc459ae4f59b8279d679003b88935896acd10021b6e2e4619377"
         "e336b5296c5e014104c00bab76a708ba7064b2315420a1c533ca9945eeff9754"
         "cdc574224589e9113469b4e71752146a10028079e04948ecdf70609bf1b9801f"
         "6b73ab75947ac339e5ffffffff"
         // NumTxOut
         "02"
         // ... TxOuts fragged out 
         // Locktime
         "00000000");

      rawTxOut0_ = READHEX(
         // Value
         "ac4c8bd500000000"
         // Script size (var_int)
         "19"
         // Script
         "76""a9""14""8dce8946f1c7763bb60ea5cf16ef514cbed0633b""88""ac");
      rawTxOut1_ = READHEX(
         // Value 
         "002f685900000000"
         // Script size (var_int)
         "19"
         // Script
         "76""a9""14""6a59ac0e8f553f292dfe5e9f3aaa1da93499c15e""88""ac");

      bh_.unserialize(rawHead_);
      tx1_.unserialize(rawTx0_);
      tx2_.unserialize(rawTx1_);
      sbh_.setHeaderData(rawHead_);

      LOGDISABLESTDOUT();
   }

   /////
   virtual void TearDown(void)
   {
      // This seem to be the best way to remove a dir tree in C++ (in Linux)
      delete dbTx;
      iface_->closeDatabases();
      delete iface_;
      iface_ = NULL;

#ifdef _MSC_VER
      rmdir("./ldbtestdir/*");
#else
      system("rm -rf ./ldbtestdir/*");
#endif

      CLEANUP_ALL_TIMERS();
   }

   /////
   void addOutPairH(BinaryData key, BinaryData val)
   {
      expectOutH_.push_back(pair<BinaryData, BinaryData>(key, val));
   }

   /////
   void addOutPairB(BinaryData key, BinaryData val)
   {
      expectOutB_.push_back(pair<BinaryData, BinaryData>(key, val));
   }

   /////
   void replaceTopOutPairB(BinaryData key, BinaryData val)
   {
      uint32_t last = expectOutB_.size() - 1;
      expectOutB_[last] = pair<BinaryData, BinaryData>(key, val);
   }

   /////
   void printOutPairs(void)
   {
      cout << "Num Houts: " << expectOutH_.size() << endl;
      for (uint32_t i = 0; i<expectOutH_.size(); i++)
      {
         cout << "   \"" << expectOutH_[i].first.toHexStr() << "\"  ";
         cout << "   \"" << expectOutH_[i].second.toHexStr() << "\"    " << endl;
      }
      cout << "Num Bouts: " << expectOutB_.size() << endl;
      for (uint32_t i = 0; i<expectOutB_.size(); i++)
      {
         cout << "   \"" << expectOutB_[i].first.toHexStr() << "\"  ";
         cout << "   \"" << expectOutB_[i].second.toHexStr() << "\"    " << endl;
      }
   }

   /////
   bool compareKVListRange(uint32_t startH, uint32_t endplus1H,
      uint32_t startB, uint32_t endplus1B)
   {
      KVLIST fromDB = iface_->getAllDatabaseEntries(HEADERS);

      if (fromDB.size() < endplus1H || expectOutH_.size() < endplus1H)
      {
         LOGERR << "Headers DB not the correct size";
         LOGERR << "DB  size:  " << (int)fromDB.size();
         LOGERR << "Expected:  " << (int)expectOutH_.size();
         return false;
      }

      for (uint32_t i = startH; i<endplus1H; i++)
         if (fromDB[i].first != expectOutH_[i].first ||
            fromDB[i].second != expectOutH_[i].second)
         {
            LOGERR << "Mismatch of DB keys/values: " << i;
            LOGERR << "KEYS: ";
            LOGERR << "   Database:   " << fromDB[i].first.toHexStr();
            LOGERR << "   Expected:   " << expectOutH_[i].first.toHexStr();
            LOGERR << "VALUES: ";
            LOGERR << "   Database:   " << fromDB[i].second.toHexStr();
            LOGERR << "   Expected:   " << expectOutH_[i].second.toHexStr();
            return false;
         }

      fromDB = iface_->getAllDatabaseEntries(BLKDATA);
      if (fromDB.size() < endplus1B || expectOutB_.size() < endplus1B)
      {
         LOGERR << "BLKDATA DB not the correct size";
         LOGERR << "DB  size:  " << (int)fromDB.size();
         LOGERR << "Expected:  " << (int)expectOutB_.size();
         return false;
      }

      for (uint32_t i = startB; i<endplus1B; i++)
         if (fromDB[i].first != expectOutB_[i].first ||
            fromDB[i].second != expectOutB_[i].second)
         {
            LOGERR << "Mismatch of DB keys/values: " << i;
            LOGERR << "KEYS: ";
            LOGERR << "   Database:   " << fromDB[i].first.toHexStr();
            LOGERR << "   Expected:   " << expectOutB_[i].first.toHexStr();
            LOGERR << "VALUES: ";
            LOGERR << "   Database:   " << fromDB[i].second.toHexStr();
            LOGERR << "   Expected:   " << expectOutB_[i].second.toHexStr();
            return false;
         }

      return true;
   }


   /////
   bool standardOpenDBs(void)
   {
      iface_->openDatabases(
         config_.dbDir_,
         config_.genesisBlockHash_,
         config_.genesisTxHash_,
         config_.magicBytes_,
         config_.armoryDbType_);

      dbTx = new LMDBEnv::Transaction(iface_->dbEnv_[BLKDATA].get(), LMDB::ReadWrite);

      BinaryData DBINFO = StoredDBInfo().getDBKey();
      BinaryData flags = READHEX("04100000");
      BinaryData val0 = magic_ + flags + zeros_ + zeros_ + ghash_;
      addOutPairH(DBINFO, val0);
      addOutPairB(DBINFO, val0);

      return iface_->databasesAreOpen();
   }


   LMDBBlockDatabase* iface_;
   BlockDataManagerConfig config_;
   LMDBEnv::Transaction* dbTx = nullptr;
   vector<pair<BinaryData, BinaryData> > expectOutH_;
   vector<pair<BinaryData, BinaryData> > expectOutB_;

   BinaryData magic_;
   BinaryData ghash_;
   BinaryData gentx_;
   BinaryData zeros_;

   BinaryData rawHead_;
   BinaryData headHashLE_;
   BinaryData headHashBE_;
   BinaryData rawBlock_;
   BinaryData rawTx0_;
   BinaryData rawTx1_;
   BlockHeader bh_;
   Tx tx1_;
   Tx tx2_;
   StoredHeader sbh_;
   BinaryData rawTxUnfrag_;
   BinaryData rawTxFragged_;
   BinaryData rawTxOut0_;
   BinaryData rawTxOut1_;

};


////////////////////////////////////////////////////////////////////////////////
TEST_F(LMDBTest_Super, DISABLED_OpenClose)
{
   iface_->openDatabases(
      config_.dbDir_,
      config_.genesisBlockHash_,
      config_.genesisTxHash_,
      config_.magicBytes_,
      config_.armoryDbType_);

   ASSERT_TRUE(iface_->databasesAreOpen());

   EXPECT_EQ(iface_->getTopBlockHeight(HEADERS), 0);
   EXPECT_EQ(READHEX(MAINNET_GENESIS_HASH_HEX), iface_->getTopBlockHash(HEADERS));

   KVLIST HList = iface_->getAllDatabaseEntries(HEADERS);
   KVLIST BList = iface_->getAllDatabaseEntries(BLKDATA);

   // 0123 4567 0123 4567
   // 0000 0010 0001 ---- ---- ---- ---- ----
   BinaryData flags = READHEX("04100000");

   for (uint32_t i = 0; i<HList.size(); i++)
   {
      EXPECT_EQ(HList[i].first, READHEX("00"));
      EXPECT_EQ(BList[i].second, magic_ + flags + zeros_ + zeros_ + ghash_);
   }

   for (uint32_t i = 0; i<BList.size(); i++)
   {
      EXPECT_EQ(HList[i].first, READHEX("00"));
      EXPECT_EQ(BList[i].second, magic_ + flags + zeros_ + zeros_ + ghash_);
   }

   iface_->closeDatabases();
}


////////////////////////////////////////////////////////////////////////////////
TEST_F(LMDBTest_Super, DISABLED_OpenCloseOpenNominal)
{
   // 0123 4567 0123 4567
   // 0000 0010 0001 ---- ---- ---- ---- ----
   BinaryData flags = READHEX("04100000");

   iface_->openDatabases(
      config_.dbDir_,
      config_.genesisBlockHash_,
      config_.genesisTxHash_,
      config_.magicBytes_,
      config_.armoryDbType_);


   iface_->closeDatabases();

   iface_->openDatabases(
      config_.dbDir_,
      config_.genesisBlockHash_,
      config_.genesisTxHash_,
      config_.magicBytes_,
      config_.armoryDbType_);

   ASSERT_TRUE(iface_->databasesAreOpen());

   KVLIST HList = iface_->getAllDatabaseEntries(HEADERS);
   KVLIST BList = iface_->getAllDatabaseEntries(BLKDATA);

   for (uint32_t i = 0; i<HList.size(); i++)
   {
      EXPECT_EQ(HList[i].first, READHEX("00"));
      EXPECT_EQ(BList[i].second, magic_ + flags + zeros_ + zeros_ + ghash_);
   }

   for (uint32_t i = 0; i<BList.size(); i++)
   {
      EXPECT_EQ(HList[i].first, READHEX("00"));
      EXPECT_EQ(BList[i].second, magic_ + flags + zeros_ + zeros_ + ghash_);
   }

   iface_->closeDatabases();
}


////////////////////////////////////////////////////////////////////////////////
TEST_F(LMDBTest_Super, DISABLED_OpenCloseOpenMismatch)
{
   LOGERR << "Expecting four error messages here:  this is normal";
   iface_->openDatabases(
      config_.dbDir_,
      config_.genesisBlockHash_,
      config_.genesisTxHash_,
      config_.magicBytes_,
      config_.armoryDbType_);

   EXPECT_TRUE(iface_->databasesAreOpen());
   iface_->closeDatabases();

   iface_->openDatabases(
      config_.dbDir_,
      config_.genesisBlockHash_,
      config_.genesisTxHash_,
      config_.magicBytes_,
      config_.armoryDbType_);

   EXPECT_TRUE(iface_->databasesAreOpen());
   iface_->closeDatabases();

   iface_->openDatabases(
      config_.dbDir_,
      config_.genesisBlockHash_,
      config_.genesisTxHash_,
      config_.magicBytes_,
      config_.armoryDbType_);

   EXPECT_FALSE(iface_->databasesAreOpen());

   iface_->openDatabases(
      config_.dbDir_,
      config_.genesisBlockHash_,
      config_.genesisTxHash_,
      config_.magicBytes_,
      config_.armoryDbType_);

   EXPECT_FALSE(iface_->databasesAreOpen());

   iface_->openDatabases(
      config_.dbDir_,
      config_.genesisBlockHash_,
      config_.genesisTxHash_,
      config_.magicBytes_,
      config_.armoryDbType_);

   ASSERT_TRUE(iface_->databasesAreOpen());

   KVLIST HList = iface_->getAllDatabaseEntries(HEADERS);
   KVLIST BList = iface_->getAllDatabaseEntries(BLKDATA);

   EXPECT_EQ(HList.begin()->first, READHEX("00"));
   EXPECT_EQ(BList.begin()->first, READHEX("00"));

   iface_->closeDatabases();
}


////////////////////////////////////////////////////////////////////////////////
TEST_F(LMDBTest_Super, DISABLED_PutGetDelete)
{
   BinaryData flags = READHEX("04100000");

   iface_->openDatabases(
      config_.dbDir_,
      config_.genesisBlockHash_,
      config_.genesisTxHash_,
      config_.magicBytes_,
      config_.armoryDbType_);

   ASSERT_TRUE(iface_->databasesAreOpen());
   LMDBEnv::Transaction tx(iface_->dbEnv_[BLKDATA].get(), LMDB::ReadWrite);

   DB_PREFIX TXDATA = DB_PREFIX_TXDATA;
   BinaryData DBINFO = StoredDBInfo().getDBKey();
   BinaryData PREFIX = WRITE_UINT8_BE((uint8_t)TXDATA);
   BinaryData val0 = magic_ + flags + zeros_ + zeros_ + ghash_;
   BinaryData commonValue = READHEX("abcd1234");
   BinaryData keyAB = READHEX("0000");
   BinaryData nothing = BinaryData(0);

   addOutPairH(DBINFO, val0);

   addOutPairB(DBINFO, val0);
   addOutPairB(keyAB, commonValue);
   addOutPairB(PREFIX + keyAB, commonValue);

   ASSERT_TRUE(compareKVListRange(0, 1, 0, 1));

   iface_->putValue(BLKDATA, keyAB, commonValue);
   ASSERT_TRUE(compareKVListRange(0, 1, 0, 2));

   iface_->putValue(BLKDATA, DB_PREFIX_TXDATA, keyAB, commonValue);
   ASSERT_TRUE(compareKVListRange(0, 1, 0, 3));

   // Now test a bunch of get* methods
   ASSERT_EQ(iface_->getValueRef(BLKDATA, PREFIX + keyAB), commonValue);
   ASSERT_EQ(iface_->getValueRef(BLKDATA, DB_PREFIX_DBINFO, nothing), val0);
   ASSERT_EQ(iface_->getValueRef(BLKDATA, DBINFO), val0);
   ASSERT_EQ(iface_->getValueRef(BLKDATA, PREFIX + keyAB), commonValue);
   ASSERT_EQ(iface_->getValueRef(BLKDATA, TXDATA, keyAB), commonValue);
   ASSERT_EQ(iface_->getValueReader(BLKDATA, PREFIX + keyAB).getRawRef(), commonValue);
   ASSERT_EQ(iface_->getValueReader(BLKDATA, TXDATA, keyAB).getRawRef(), commonValue);

   iface_->deleteValue(BLKDATA, DB_PREFIX_TXDATA, keyAB);
   ASSERT_TRUE(compareKVListRange(0, 1, 0, 2));

   iface_->deleteValue(BLKDATA, PREFIX + keyAB);
   ASSERT_TRUE(compareKVListRange(0, 1, 0, 1));

   iface_->deleteValue(BLKDATA, PREFIX + keyAB);
}

////////////////////////////////////////////////////////////////////////////////
TEST_F(LMDBTest_Super, DISABLED_STxOutPutGet)
{
   BinaryData TXP = WRITE_UINT8_BE((uint8_t)DB_PREFIX_TXDATA);
   BinaryData stxoVal = READHEX("0400") + rawTxOut0_;
   BinaryData stxoKey = TXP + READHEX("01e078""0f""0007""0001");

   ASSERT_TRUE(standardOpenDBs());

   StoredTxOut stxo0;
   stxo0.txVersion_ = 1;
   stxo0.spentness_ = TXOUT_UNSPENT;
   stxo0.blockHeight_ = 123000;
   stxo0.duplicateID_ = 15;
   stxo0.txIndex_ = 7;
   stxo0.txOutIndex_ = 1;
   stxo0.unserialize(rawTxOut0_);
   iface_->putStoredTxOut(stxo0);

   // Construct expected output
   addOutPairB(stxoKey, stxoVal);
   ASSERT_TRUE(compareKVListRange(0, 1, 0, 2));

   StoredTxOut stxoGet;
   iface_->getStoredTxOut(stxoGet, 123000, 15, 7, 1);
   EXPECT_EQ(
      serializeDBValue(stxoGet, ARMORY_DB_FULL),
      serializeDBValue(stxo0, ARMORY_DB_FULL)
      );

   StoredTxOut stxo1;
   stxo1.txVersion_ = 1;
   stxo1.spentness_ = TXOUT_UNSPENT;
   stxo1.blockHeight_ = 200333;
   stxo1.duplicateID_ = 3;
   stxo1.txIndex_ = 7;
   stxo1.txOutIndex_ = 1;
   stxo1.unserialize(rawTxOut1_);
   stxoVal = READHEX("0400") + rawTxOut1_;
   stxoKey = TXP + READHEX("030e8d""03""00070001");
   iface_->putStoredTxOut(stxo1);

   iface_->getStoredTxOut(stxoGet, 123000, 15, 7, 1);
   EXPECT_EQ(
      serializeDBValue(stxoGet, ARMORY_DB_FULL),
      serializeDBValue(stxo0, ARMORY_DB_FULL)
      );
   iface_->getStoredTxOut(stxoGet, 200333, 3, 7, 1);
   EXPECT_EQ(
      serializeDBValue(stxoGet, ARMORY_DB_FULL),
      serializeDBValue(stxo1, ARMORY_DB_FULL)
      );

   addOutPairB(stxoKey, stxoVal);
   ASSERT_TRUE(compareKVListRange(0, 1, 0, 3));

}

////////////////////////////////////////////////////////////////////////////////
TEST_F(LMDBTest_Super, DISABLED_PutFullTxNoOuts)
{
   //    DBUtils::setArmoryDbType(ARMORY_DB_FULL);
   //    DBUtils::setDbPruneType(DB_PRUNE_NONE);

   ASSERT_TRUE(standardOpenDBs());

   StoredTx stx;
   stx.createFromTx(rawTxUnfrag_);
   stx.setKeyData(123000, 15, 7);

   BinaryData TXP = WRITE_UINT8_BE((uint8_t)DB_PREFIX_TXDATA);
   BinaryData stxKey = TXP + READHEX("01e078""0f""0007");
   BinaryData stxVal = READHEX("0440") + stx.thisHash_ + rawTxFragged_;

   iface_->putStoredTx(stx, false);
   addOutPairB(stxKey, stxVal);
   EXPECT_TRUE(compareKVListRange(0, 1, 0, 2));
}

////////////////////////////////////////////////////////////////////////////////
TEST_F(LMDBTest_Super, DISABLED_PutFullTx)
{
   //    DBUtils::setArmoryDbType(ARMORY_DB_FULL);
   //    DBUtils::setDbPruneType(DB_PRUNE_NONE);

   BinaryData TXP = WRITE_UINT8_BE((uint8_t)DB_PREFIX_TXDATA);
   BinaryData stxoVal = READHEX("0400") + rawTxOut0_;
   BinaryData stxKey = TXP + READHEX("01e078""0f""0007");
   BinaryData stxo0Key = TXP + READHEX("01e078""0f""0007""0000");
   BinaryData stxo1Key = TXP + READHEX("01e078""0f""0007""0001");
   BinaryData stxo0raw = READHEX(
      "ac4c8bd5000000001976a9148dce8946f1c7763bb60ea5cf16ef514cbed0633b88ac");
   BinaryData stxo1raw = READHEX(
      "002f6859000000001976a9146a59ac0e8f553f292dfe5e9f3aaa1da93499c15e88ac");

   ASSERT_TRUE(standardOpenDBs());

   StoredTx stx;
   stx.createFromTx(rawTxUnfrag_);
   stx.setKeyData(123000, 15, 7);

   ASSERT_EQ(stx.stxoMap_.size(), 2);
   for (uint32_t i = 0; i<2; i++)
   {
      stx.stxoMap_[i].spentness_ = TXOUT_UNSPENT;
      stx.stxoMap_[i].isCoinbase_ = false;

      ASSERT_EQ(stx.stxoMap_[i].blockHeight_, 123000);
      ASSERT_EQ(stx.stxoMap_[i].duplicateID_, 15);
      ASSERT_EQ(stx.stxoMap_[i].txIndex_, 7);
      ASSERT_EQ(stx.stxoMap_[i].txOutIndex_, i);
      ASSERT_EQ(stx.stxoMap_[i].isCoinbase_, false);
   }

   BinaryData stxVal = READHEX("0440") + stx.thisHash_ + rawTxFragged_;
   BinaryData stxo0Val = READHEX("0400") + stxo0raw;
   BinaryData stxo1Val = READHEX("0400") + stxo1raw;

   iface_->putStoredTx(stx);
   addOutPairB(stxKey, stxVal);
   addOutPairB(stxo0Key, stxo0Val);
   addOutPairB(stxo1Key, stxo1Val);
   EXPECT_TRUE(compareKVListRange(0, 1, 0, 4));
}

////////////////////////////////////////////////////////////////////////////////
TEST_F(LMDBTest_Super, DISABLED_PutGetBareHeader)
{
   //    DBUtils::setArmoryDbType(ARMORY_DB_FULL);
   //    DBUtils::setDbPruneType(DB_PRUNE_NONE);

   StoredHeader sbh;
   BinaryRefReader brr(rawBlock_);
   sbh.unserializeFullBlock(brr);
   sbh.setKeyData(123000, UINT8_MAX);
   BinaryData header0 = sbh.thisHash_;

   ASSERT_TRUE(standardOpenDBs());

   uint8_t sdup = iface_->putBareHeader(sbh);
   EXPECT_EQ(sdup, 0);
   EXPECT_EQ(sbh.duplicateID_, 0);

   // Add a new header and make sure duplicate ID is done correctly
   BinaryData newHeader = READHEX(
      "0000000105d3571220ef5f87c6ac0bc8bf5b33c02a9e6edf83c84d840109592c"
      "0000000027523728e15f5fe1ac507bff92499eada4af8a0c485d5178e3f96568"
      "c18f84994e0e4efc1c0175d646a91ad4");
   BinaryData header1 = BtcUtils::getHash256(newHeader);

   StoredHeader sbh2;
   sbh2.setHeaderData(newHeader);
   sbh2.setKeyData(123000, UINT8_MAX);

   uint8_t newDup = iface_->putBareHeader(sbh2);
   EXPECT_EQ(newDup, 1);
   EXPECT_EQ(sbh2.duplicateID_, 1);

   // Now add a new, isMainBranch_ header
   StoredHeader sbh3;
   BinaryData anotherHead = READHEX(
      "010000001d8f4ec0443e1f19f305e488c1085c95de7cc3fd25e0d2c5bb5d0000"
      "000000009762547903d36881a86751f3f5049e23050113f779735ef82734ebf0"
      "b4450081d8c8c84db3936a1a334b035b");
   BinaryData header2 = BtcUtils::getHash256(anotherHead);

   sbh3.setHeaderData(anotherHead);
   sbh3.setKeyData(123000, UINT8_MAX);
   sbh3.isMainBranch_ = true;
   uint8_t anotherDup = iface_->putBareHeader(sbh3);
   EXPECT_EQ(anotherDup, 2);
   EXPECT_EQ(sbh3.duplicateID_, 2);
   EXPECT_EQ(iface_->getValidDupIDForHeight(123000), 2);

   // Now test getting bare headers
   StoredHeader sbh4;
   iface_->getBareHeader(sbh4, 123000);
   EXPECT_EQ(sbh4.thisHash_, header2);
   EXPECT_EQ(sbh4.duplicateID_, 2);

   iface_->getBareHeader(sbh4, 123000, 1);
   EXPECT_EQ(sbh4.thisHash_, header1);
   EXPECT_EQ(sbh4.duplicateID_, 1);

   // Re-add the same SBH3, make sure nothing changes
   iface_->putBareHeader(sbh3);
   EXPECT_EQ(sbh3.duplicateID_, 2);
   EXPECT_EQ(iface_->getValidDupIDForHeight(123000), 2);
}

////////////////////////////////////////////////////////////////////////////////
TEST_F(LMDBTest_Super, DISABLED_PutGetStoredTxHints)
{
   ASSERT_TRUE(standardOpenDBs());

   BinaryData prefix = READHEX("aabbccdd");

   StoredTxHints sths;
   EXPECT_FALSE(iface_->getStoredTxHints(sths, prefix));

   sths.txHashPrefix_ = prefix;

   ASSERT_TRUE(iface_->putStoredTxHints(sths));

   BinaryData THP = WRITE_UINT8_BE((uint8_t)DB_PREFIX_TXHINTS);
   addOutPairB(THP + prefix, READHEX("00"));

   compareKVListRange(0, 1, 0, 2);

   /////
   sths.dbKeyList_.push_back(READHEX("abcd1234ffff"));
   replaceTopOutPairB(THP + prefix, READHEX("01""abcd1234ffff"));
   EXPECT_TRUE(iface_->putStoredTxHints(sths));
   compareKVListRange(0, 1, 0, 2);

   /////
   sths.dbKeyList_.push_back(READHEX("00002222aaaa"));
   replaceTopOutPairB(THP + prefix, READHEX("02""abcd1234ffff""00002222aaaa"));
   EXPECT_TRUE(iface_->putStoredTxHints(sths));
   compareKVListRange(0, 1, 0, 2);

   /////
   sths.preferredDBKey_ = READHEX("00002222aaaa");
   replaceTopOutPairB(THP + prefix, READHEX("02""00002222aaaa""abcd1234ffff"));
   EXPECT_TRUE(iface_->putStoredTxHints(sths));
   compareKVListRange(0, 1, 0, 2);

   // Now test the get methods
   EXPECT_TRUE(iface_->getStoredTxHints(sths, prefix));
   EXPECT_EQ(sths.txHashPrefix_, prefix);
   EXPECT_EQ(sths.dbKeyList_.size(), 2);
   EXPECT_EQ(sths.preferredDBKey_, READHEX("00002222aaaa"));

   //
   sths.dbKeyList_.resize(0);
   sths.preferredDBKey_.resize(0);
   EXPECT_TRUE(iface_->putStoredTxHints(sths));
   EXPECT_TRUE(iface_->getStoredTxHints(sths, prefix));
   EXPECT_EQ(sths.txHashPrefix_, prefix);
   EXPECT_EQ(sths.dbKeyList_.size(), 0);
   EXPECT_EQ(sths.preferredDBKey_.getSize(), 0);
}


////////////////////////////////////////////////////////////////////////////////
TEST_F(LMDBTest_Super, DISABLED_PutGetStoredScriptHistory)
{
   ASSERT_TRUE(standardOpenDBs());

   ///////////////////////////////////////////////////////////////////////////
   // A whole bunch of setup stuff we need for ssh operations to work right
   LMDBBlockDatabase *const iface = iface_;
   iface->setValidDupIDForHeight(255, 0);
   iface->setValidDupIDForHeight(256, 0);

   BinaryData dbkey0 = READHEX("0000ff00""0001""0001");
   BinaryData dbkey1 = READHEX("0000ff00""0002""0002");
   BinaryData dbkey2 = READHEX("00010000""0004""0004");
   BinaryData dbkey3 = READHEX("00010000""0006""0006");
   uint64_t   val0 = READ_UINT64_HEX_LE("0100000000000000");
   uint64_t   val1 = READ_UINT64_HEX_LE("0002000000000000");
   uint64_t   val2 = READ_UINT64_HEX_LE("0000030000000000");
   uint64_t   val3 = READ_UINT64_HEX_LE("0000000400000000");

   BinaryData PREFIX = READHEX("03");
   BinaryData RAWTX = READHEX(
      "01000000016290dce984203b6a5032e543e9e272d8bce934c7de4d15fa0fe44d"
      "d49ae4ece9010000008b48304502204f2fa458d439f957308bca264689aa175e"
      "3b7c5f78a901cb450ebd20936b2c500221008ea3883a5b80128e55c9c6070aa6"
      "264e1e0ce3d18b7cd7e85108ce3d18b7419a0141044202550a5a6d3bb81549c4"
      "a7803b1ad59cdbba4770439a4923624a8acfc7d34900beb54a24188f7f0a4068"
      "9d905d4847cc7d6c8d808a457d833c2d44ef83f76bffffffff0242582c0a0000"
      "00001976a914c1b4695d53b6ee57a28647ce63e45665df6762c288ac80d1f008"
      "000000001976a9140e0aec36fe2545fb31a41164fb6954adcd96b34288ac0000"
      "0000");
   iface->putValue(BLKDATA, DB_PREFIX_TXDATA, dbkey0, RAWTX);
   iface->putValue(BLKDATA, DB_PREFIX_TXDATA, dbkey1, RAWTX);
   iface->putValue(BLKDATA, DB_PREFIX_TXDATA, dbkey2, RAWTX);
   iface->putValue(BLKDATA, DB_PREFIX_TXDATA, dbkey3, RAWTX);

   TxIOPair txio0(dbkey0, val0);
   TxIOPair txio1(dbkey1, val1);
   TxIOPair txio2(dbkey2, val2);
   TxIOPair txio3(dbkey3, val3);
   txio3.setMultisig(true);
   ///////////////////////////////////////////////////////////////////////////

   StoredSubHistory * subptr;
   TxIOPair * txioptr;

   StoredScriptHistory ssh, sshorig, sshtemp;
   BinaryData hgtX0 = READHEX("0000ff00");
   BinaryData hgtX1 = READHEX("00010000");
   BinaryData uniq = READHEX("00""0000ffff0000ffff0000ffff0000ffff0000ffff");
   sshorig.uniqueKey_ = uniq;
   uint32_t blk = READ_UINT32_HEX_LE("ffff0000");
   sshorig.alreadyScannedUpToBlk_ = blk;
   sshorig.version_ = 1;

   /////////////////////////////////////////////////////////////////////////////
   // Haven't actually done anything yet...
   ssh = sshorig;
   EXPECT_EQ(ssh.uniqueKey_, uniq);
   EXPECT_EQ(ssh.alreadyScannedUpToBlk_, blk);
   EXPECT_EQ(ssh.subHistMap_.size(), 0);

   /////////////////////////////////////////////////////////////////////////////
   // An empty ssh -- this shouldn't happen in production, but test it anyway
   iface_->putStoredScriptHistory(ssh);
   iface_->getStoredScriptHistory(sshtemp, uniq);

   EXPECT_EQ(sshtemp.uniqueKey_, uniq);
   EXPECT_EQ(sshtemp.alreadyScannedUpToBlk_, blk);
   EXPECT_EQ(sshtemp.subHistMap_.size(), 0);

   /////////////////////////////////////////////////////////////////////////////
   // A single txio
   ssh = sshorig;
   ssh.insertTxio(txio0);

   iface_->putStoredScriptHistory(ssh);
   iface_->getStoredScriptHistory(sshtemp, uniq);

   EXPECT_EQ(sshtemp.uniqueKey_, uniq);
   EXPECT_EQ(sshtemp.alreadyScannedUpToBlk_, blk);
   EXPECT_EQ(sshtemp.totalTxioCount_, 1);
   EXPECT_EQ(sshtemp.totalUnspent_, val0);
   EXPECT_EQ(sshtemp.subHistMap_.size(), 1);
   ASSERT_NE(sshtemp.subHistMap_.find(hgtX0), sshtemp.subHistMap_.end());
   subptr = &sshtemp.subHistMap_[hgtX0];
   EXPECT_EQ(subptr->uniqueKey_, uniq);
   EXPECT_EQ(subptr->hgtX_, hgtX0);
   ASSERT_EQ(subptr->txioMap_.size(), 1);
   ASSERT_NE(subptr->txioMap_.find(dbkey0), subptr->txioMap_.end());
   txioptr = &subptr->txioMap_[dbkey0];
   EXPECT_EQ(txioptr->getDBKeyOfOutput(), dbkey0);
   EXPECT_EQ(txioptr->getValue(), val0);
   EXPECT_FALSE(txioptr->isMultisig());

   /////////////////////////////////////////////////////////////////////////////
   // Two TxIOPairs in one sub history
   ssh = sshorig;
   sshtemp = StoredScriptHistory();
   ssh.insertTxio(txio0);
   ssh.insertTxio(txio1);

   iface_->putStoredScriptHistory(ssh);
   iface_->getStoredScriptHistory(sshtemp, uniq);

   EXPECT_EQ(sshtemp.uniqueKey_, uniq);
   EXPECT_EQ(sshtemp.alreadyScannedUpToBlk_, blk);
   EXPECT_EQ(sshtemp.totalTxioCount_, 2);
   EXPECT_EQ(sshtemp.totalUnspent_, val0 + val1);
   EXPECT_EQ(sshtemp.subHistMap_.size(), 1);
   ASSERT_NE(sshtemp.subHistMap_.find(hgtX0), sshtemp.subHistMap_.end());
   subptr = &sshtemp.subHistMap_[hgtX0];
   EXPECT_EQ(subptr->uniqueKey_, uniq);
   EXPECT_EQ(subptr->hgtX_, hgtX0);
   ASSERT_EQ(subptr->txioMap_.size(), 2);
   ASSERT_NE(subptr->txioMap_.find(dbkey0), subptr->txioMap_.end());
   txioptr = &subptr->txioMap_[dbkey0];
   EXPECT_EQ(txioptr->getDBKeyOfOutput(), dbkey0);
   EXPECT_EQ(txioptr->getValue(), val0);
   EXPECT_FALSE(txioptr->isMultisig());
   txioptr = &subptr->txioMap_[dbkey1];
   EXPECT_EQ(txioptr->getDBKeyOfOutput(), dbkey1);
   EXPECT_EQ(txioptr->getValue(), val1);
   EXPECT_FALSE(txioptr->isMultisig());


   /////////////////////////////////////////////////////////////////////////////
   // Add new sub-history with multisig
   ssh = sshorig;
   ssh.insertTxio(txio0);
   ssh.insertTxio(txio1);
   ssh.insertTxio(txio3);

   iface_->putStoredScriptHistory(ssh);
   iface_->getStoredScriptHistory(sshtemp, uniq);

   EXPECT_EQ(sshtemp.uniqueKey_, uniq);
   EXPECT_EQ(sshtemp.alreadyScannedUpToBlk_, blk);
   EXPECT_EQ(sshtemp.totalTxioCount_, 3);
   EXPECT_EQ(sshtemp.totalUnspent_, val0 + val1);
   EXPECT_EQ(sshtemp.subHistMap_.size(), 2);

   ASSERT_NE(sshtemp.subHistMap_.find(hgtX0), sshtemp.subHistMap_.end());
   subptr = &sshtemp.subHistMap_[hgtX0];
   EXPECT_EQ(subptr->uniqueKey_, uniq);
   EXPECT_EQ(subptr->hgtX_, hgtX0);
   ASSERT_EQ(subptr->txioMap_.size(), 2);
   ASSERT_NE(subptr->txioMap_.find(dbkey0), subptr->txioMap_.end());
   txioptr = &subptr->txioMap_[dbkey0];
   EXPECT_EQ(txioptr->getDBKeyOfOutput(), dbkey0);
   EXPECT_EQ(txioptr->getValue(), val0);
   txioptr = &subptr->txioMap_[dbkey1];
   EXPECT_EQ(txioptr->getDBKeyOfOutput(), dbkey1);
   EXPECT_EQ(txioptr->getValue(), val1);
   EXPECT_FALSE(txioptr->isMultisig());

   ASSERT_NE(sshtemp.subHistMap_.find(hgtX1), sshtemp.subHistMap_.end());
   subptr = &sshtemp.subHistMap_[hgtX1];
   EXPECT_EQ(subptr->uniqueKey_, uniq);
   EXPECT_EQ(subptr->hgtX_, hgtX1);
   ASSERT_EQ(subptr->txioMap_.size(), 1);
   ASSERT_NE(subptr->txioMap_.find(dbkey3), subptr->txioMap_.end());
   txioptr = &subptr->txioMap_[dbkey3];
   EXPECT_EQ(txioptr->getDBKeyOfOutput(), dbkey3);
   EXPECT_EQ(txioptr->getValue(), val3);
   EXPECT_TRUE(txioptr->isMultisig());
}

////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
class BlockUtilsSuper : public ::testing::Test
{
protected:
   BlockDataManager TheBDM;
   BlockDataViewer*         theBDV;

   /////////////////////////////////////////////////////////////////////////////
   virtual void SetUp(void)
   {
      LOGDISABLESTDOUT();
      magic_ = READHEX(MAINNET_MAGIC_BYTES);
      ghash_ = READHEX(MAINNET_GENESIS_HASH_HEX);
      gentx_ = READHEX(MAINNET_GENESIS_TX_HASH_HEX);
      zeros_ = READHEX("00000000");

      blkdir_ = string("./blkfiletest");
      homedir_ = string("./fakehomedir");
      ldbdir_ = string("./ldbtestdir");

      mkdir(blkdir_);
      mkdir(homedir_);

      // Put the first 5 blocks into the blkdir
      blk0dat_ = BtcUtils::getBlkFilename(blkdir_, 0);
      setBlocks({ "0", "1", "2", "3", "4", "5" }, blk0dat_);

      config_.armoryDbType_ = ARMORY_DB_SUPER;
      config_.blkFileLocation_ = blkdir_;
      config_.dbDir_ = ldbdir_;

      config_.genesisBlockHash_ = ghash_;
      config_.genesisTxHash_ = gentx_;
      config_.magicBytes_ = magic_;

      theBDM = new BlockDataManager(config_);
      theBDM->openDatabase();
      theBDV = new BlockDataViewer(theBDM);

      iface_ = theBDM->getIFace();
   }


   /////////////////////////////////////////////////////////////////////////////
   virtual void TearDown(void)
   {
      delete theBDM;
      delete theBDV;

      theBDM = nullptr;
      theBDV = nullptr;

      rmdir(blkdir_);
      rmdir(homedir_);

#ifdef _MSC_VER
      rmdir(ldbdir_);
      mkdir(ldbdir_);
#else
      std::string d = ldbdir_ + "/*";
      rmdir(d);
#endif
      LOGENABLESTDOUT();
      CLEANUP_ALL_TIMERS();
   }


   // Run this before registering a BDM.
   void regWallet(const vector<BinaryData>& scrAddrs, const string& wltName,
      BlockDataViewer*& inBDV, shared_ptr<BtcWallet>* inWlt)
   {
      // Register the standalone address wallet. (All registrations should be
      // done before initializing the BDM. This is critical!)
      *inWlt = inBDV->registerWallet(scrAddrs, wltName, false);
   }


   // Run this before registering a BDM. (For now, just make the two lockboxes a
   // package deal. Code can be altered later if needed.)
   void regLockboxes(BlockDataViewer*& inBDV, shared_ptr<BtcWallet>* inLB1,
      shared_ptr<BtcWallet>* inLB2)
   {
      // Register the two lockboxes. Note that the lockbox data is pulled from
      // createTestChain.py, the script that built most of the blocks used in
      // these unit tests. Python, not C++, is where we find the code needed to
      // generate the data required by C++ lockboxes. If the lockboxes and/or
      // blocks are redone, this data's automatically redone.
      // LB1 = AddrB + AddrC
      // LB2 = AddrD + AddrE
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
      *inLB1 = inBDV->registerLockbox(lb1ScrAddrs, TestChain::lb1B58ID, false);
      *inLB2 = inBDV->registerLockbox(lb2ScrAddrs, TestChain::lb2B58ID, false);
   }


#if ! defined(_MSC_VER) && ! defined(__MINGW32__)
   /////////////////////////////////////////////////////////////////////////////
   void rmdir(string src)
   {
      char* syscmd = new char[4096];
      sprintf(syscmd, "rm -rf %s", src.c_str());
      system(syscmd);
      delete[] syscmd;
   }

   /////////////////////////////////////////////////////////////////////////////
   void mkdir(string newdir)
   {
      char* syscmd = new char[4096];
      sprintf(syscmd, "mkdir -p %s", newdir.c_str());
      system(syscmd);
      delete[] syscmd;
   }
#endif

   LMDBBlockDatabase* iface_;
   BinaryData magic_;
   BinaryData ghash_;
   BinaryData gentx_;
   BinaryData zeros_;
   BlockDataManagerConfig config_;

   string blkdir_;
   string homedir_;
   string ldbdir_;
   string blk0dat_;

   NullProgressReporter nullProg_;
};


////////////////////////////////////////////////////////////////////////////////
TEST_F(BlockUtilsSuper, DISABLED_HeadersOnly)
{
   EXPECT_EQ(&TheBDM.blockchain()->top(), &TheBDM.blockchain()->getGenesisBlock());
   TheBDM.readBlkFileUpdate();

   EXPECT_EQ(TheBDM.blockchain()->allHeaders().size(), 6);
   EXPECT_EQ(TheBDM.blockchain()->top().getBlockHeight(), 5);
   EXPECT_EQ(TheBDM.blockchain()->top().getThisHash(), TestChain::blkHash5);
   EXPECT_EQ(iface_->getTopBlockHeight(HEADERS), 5);
   //iface_->printAllDatabaseEntries(HEADERS);
}


////////////////////////////////////////////////////////////////////////////////
TEST_F(BlockUtilsSuper, DISABLED_HeadersOnly_Reorg)
{
   // this test is presently of dubious value. I think
   // at some point the alternate blocks (4A and 5A) had a higher difficulty
   setBlocks({ "0", "1", "2", "3", "4" }, blk0dat_);
   SETLOGLEVEL(LogLvlError);
   EXPECT_EQ(TheBDM.blockchain()->top(), TheBDM.blockchain()->getGenesisBlock());
   TheBDM.readBlkFileUpdate();

   EXPECT_EQ(TheBDM.blockchain()->allHeaders().size(), 5);
   EXPECT_EQ(TheBDM.blockchain()->top().getBlockHeight(), 4);

   EXPECT_EQ(iface_->getTopBlockHeight(HEADERS), 4);
   EXPECT_EQ(iface_->getTopBlockHash(HEADERS), TestChain::blkHash4);

   appendBlocks({ "4A" }, blk0dat_);
   TheBDM.readBlkFileUpdate();
   EXPECT_EQ(TheBDM.blockchain()->allHeaders().size(), 6);
   EXPECT_EQ(TheBDM.blockchain()->top().getBlockHeight(), 4);
   EXPECT_EQ(iface_->getTopBlockHeight(HEADERS), 4);
   EXPECT_EQ(iface_->getTopBlockHash(HEADERS), TestChain::blkHash4);
   EXPECT_FALSE(TheBDM.blockchain()->getHeaderByHash(TestChain::blkHash4A).isMainBranch());
   EXPECT_TRUE(TheBDM.blockchain()->getHeaderByHash(TestChain::blkHash4).isMainBranch());

   appendBlocks({ "5A" }, blk0dat_);
   TheBDM.readBlkFileUpdate();
   EXPECT_EQ(iface_->getTopBlockHeight(HEADERS), 5);
   EXPECT_EQ(iface_->getTopBlockHash(HEADERS), TestChain::blkHash5A);
   EXPECT_FALSE(TheBDM.blockchain()->getHeaderByHash(TestChain::blkHash4).isMainBranch());
   EXPECT_TRUE(TheBDM.blockchain()->getHeaderByHash(TestChain::blkHash4A).isMainBranch());
   EXPECT_TRUE(TheBDM.blockchain()->getHeaderByHash(TestChain::blkHash5A).isMainBranch());

   SETLOGLEVEL(LogLvlDebug2);
}


////////////////////////////////////////////////////////////////////////////////
TEST_F(BlockUtilsSuper, DISABLED_Load5Blocks)
{
   TheBDM.doInitialSyncOnLoad(nullProgress);

   StoredScriptHistory ssh;

   iface_->getStoredScriptHistory(ssh, TestChain::scrAddrA);
   EXPECT_EQ(ssh.getScriptBalance(), 50 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 50 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 1);

   iface_->getStoredScriptHistory(ssh, TestChain::scrAddrB);
   EXPECT_EQ(ssh.getScriptBalance(), 70 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 230 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 14);

   iface_->getStoredScriptHistory(ssh, TestChain::scrAddrC);
   EXPECT_EQ(ssh.getScriptBalance(), 20 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 75 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 8);

   iface_->getStoredScriptHistory(ssh, TestChain::scrAddrD);
   EXPECT_EQ(ssh.getScriptBalance(), 65 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 65 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 7);

   iface_->getStoredScriptHistory(ssh, TestChain::scrAddrE);
   EXPECT_EQ(ssh.getScriptBalance(), 30 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 30 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 5);

   iface_->getStoredScriptHistory(ssh, TestChain::scrAddrF);
   EXPECT_EQ(ssh.getScriptBalance(), 5 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 45 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 7);

   iface_->getStoredScriptHistory(ssh, TestChain::lb1ScrAddr);
   EXPECT_EQ(ssh.getScriptBalance(), 5 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 15 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 3);

   iface_->getStoredScriptHistory(ssh, TestChain::lb1ScrAddrP2SH);
   EXPECT_EQ(ssh.getScriptBalance(), 25 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 40 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 3);

   iface_->getStoredScriptHistory(ssh, TestChain::lb2ScrAddr);
   EXPECT_EQ(ssh.getScriptBalance(), 30 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 40 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 4);

   iface_->getStoredScriptHistory(ssh, TestChain::lb2ScrAddrP2SH);
   EXPECT_EQ(ssh.getScriptBalance(), 0 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 5 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 2);
}

////////////////////////////////////////////////////////////////////////////////
TEST_F(BlockUtilsSuper, DISABLED_Load5Blocks_ReloadBDM)
{
   TheBDM.doInitialSyncOnLoad(nullProgress);

   StoredScriptHistory ssh;

   iface_->getStoredScriptHistory(ssh, TestChain::scrAddrA);
   EXPECT_EQ(ssh.getScriptBalance(), 50 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 50 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 1);

   iface_->getStoredScriptHistory(ssh, TestChain::scrAddrB);
   EXPECT_EQ(ssh.getScriptBalance(), 70 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 230 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 14);

   iface_->getStoredScriptHistory(ssh, TestChain::scrAddrC);
   EXPECT_EQ(ssh.getScriptBalance(), 20 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 75 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 8);

   iface_->getStoredScriptHistory(ssh, TestChain::scrAddrD);
   EXPECT_EQ(ssh.getScriptBalance(), 65 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 65 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 7);

   iface_->getStoredScriptHistory(ssh, TestChain::scrAddrE);
   EXPECT_EQ(ssh.getScriptBalance(), 30 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 30 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 5);

   iface_->getStoredScriptHistory(ssh, TestChain::scrAddrF);
   EXPECT_EQ(ssh.getScriptBalance(), 5 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 45 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 7);

   iface_->getStoredScriptHistory(ssh, TestChain::lb1ScrAddr);
   EXPECT_EQ(ssh.getScriptBalance(), 5 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 15 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 3);

   iface_->getStoredScriptHistory(ssh, TestChain::lb1ScrAddrP2SH);
   EXPECT_EQ(ssh.getScriptBalance(), 25 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 40 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 3);

   iface_->getStoredScriptHistory(ssh, TestChain::lb2ScrAddr);
   EXPECT_EQ(ssh.getScriptBalance(), 30 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 40 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 4);

   iface_->getStoredScriptHistory(ssh, TestChain::lb2ScrAddrP2SH);
   EXPECT_EQ(ssh.getScriptBalance(), 0 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 5 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 2);

   delete theBDM;
   theBDM = new BlockDataManager(config_);

   theBDM->openDatabase();
   iface_ = theBDM->getIFace();

   theBDM->doInitialSyncOnLoad(nullProgress);

   iface_->getStoredScriptHistory(ssh, TestChain::scrAddrA);
   EXPECT_EQ(ssh.getScriptBalance(), 50 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 50 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 1);

   iface_->getStoredScriptHistory(ssh, TestChain::scrAddrB);
   EXPECT_EQ(ssh.getScriptBalance(), 70 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 230 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 14);

   iface_->getStoredScriptHistory(ssh, TestChain::scrAddrC);
   EXPECT_EQ(ssh.getScriptBalance(), 20 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 75 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 8);

   iface_->getStoredScriptHistory(ssh, TestChain::scrAddrD);
   EXPECT_EQ(ssh.getScriptBalance(), 65 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 65 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 7);

   iface_->getStoredScriptHistory(ssh, TestChain::scrAddrE);
   EXPECT_EQ(ssh.getScriptBalance(), 30 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 30 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 5);

   iface_->getStoredScriptHistory(ssh, TestChain::scrAddrF);
   EXPECT_EQ(ssh.getScriptBalance(), 5 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 45 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 7);

   iface_->getStoredScriptHistory(ssh, TestChain::lb1ScrAddr);
   EXPECT_EQ(ssh.getScriptBalance(), 5 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 15 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 3);

   iface_->getStoredScriptHistory(ssh, TestChain::lb1ScrAddrP2SH);
   EXPECT_EQ(ssh.getScriptBalance(), 25 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 40 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 3);

   iface_->getStoredScriptHistory(ssh, TestChain::lb2ScrAddr);
   EXPECT_EQ(ssh.getScriptBalance(), 30 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 40 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 4);

   iface_->getStoredScriptHistory(ssh, TestChain::lb2ScrAddrP2SH);
   EXPECT_EQ(ssh.getScriptBalance(), 0 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 5 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 2);
}


////////////////////////////////////////////////////////////////////////////////
TEST_F(BlockUtilsSuper, DISABLED_Load3BlocksPlus3)
{
   // Copy only the first four blocks.  Will copy the full file next to test
   // readBlkFileUpdate method on non-reorg blocks.
   setBlocks({ "0", "1", "2" }, blk0dat_);
   TheBDM.doInitialSyncOnLoad(nullProgress);
   EXPECT_EQ(iface_->getTopBlockHeight(HEADERS), 2);
   EXPECT_EQ(iface_->getTopBlockHash(HEADERS), TestChain::blkHash2);
   EXPECT_TRUE(TheBDM.blockchain()->getHeaderByHash(TestChain::blkHash2).isMainBranch());

   appendBlocks({ "3" }, blk0dat_);
   TheBDM.readBlkFileUpdate();

   appendBlocks({ "5" }, blk0dat_);
   TheBDM.readBlkFileUpdate();

   delete theBDM;
   theBDM = new BlockDataManager(config_);

   theBDM->openDatabase();
   iface_ = theBDM->getIFace();

   theBDM->doInitialSyncOnLoad(nullProgress);

   appendBlocks({ "4" }, blk0dat_);

   TheBDM.readBlkFileUpdate();
   EXPECT_EQ(iface_->getTopBlockHeight(HEADERS), 5);
   EXPECT_EQ(iface_->getTopBlockHash(HEADERS), TestChain::blkHash5);
   EXPECT_TRUE(TheBDM.blockchain().getHeaderByHash(TestChain::blkHash5).isMainBranch());

   StoredScriptHistory ssh;

   iface_->getStoredScriptHistory(ssh, TestChain::scrAddrA);
   EXPECT_EQ(ssh.getScriptBalance(), 50 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 50 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 1);

   iface_->getStoredScriptHistory(ssh, TestChain::scrAddrB);
   EXPECT_EQ(ssh.getScriptBalance(), 70 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 230 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 14);

   iface_->getStoredScriptHistory(ssh, TestChain::scrAddrC);
   EXPECT_EQ(ssh.getScriptBalance(), 20 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 75 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 8);

   iface_->getStoredScriptHistory(ssh, TestChain::scrAddrD);
   EXPECT_EQ(ssh.getScriptBalance(), 65 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 65 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 7);

   iface_->getStoredScriptHistory(ssh, TestChain::scrAddrE);
   EXPECT_EQ(ssh.getScriptBalance(), 30 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 30 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 5);

   iface_->getStoredScriptHistory(ssh, TestChain::scrAddrF);
   EXPECT_EQ(ssh.getScriptBalance(), 5 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 45 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 7);

   iface_->getStoredScriptHistory(ssh, TestChain::lb1ScrAddr);
   EXPECT_EQ(ssh.getScriptBalance(), 5 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 15 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 3);

   iface_->getStoredScriptHistory(ssh, TestChain::lb1ScrAddrP2SH);
   EXPECT_EQ(ssh.getScriptBalance(), 25 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 40 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 3);

   iface_->getStoredScriptHistory(ssh, TestChain::lb2ScrAddr);
   EXPECT_EQ(ssh.getScriptBalance(), 30 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 40 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 4);

   iface_->getStoredScriptHistory(ssh, TestChain::lb2ScrAddrP2SH);
   EXPECT_EQ(ssh.getScriptBalance(), 0 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 5 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 2);

}

////////////////////////////////////////////////////////////////////////////////
TEST_F(BlockUtilsSuper, DISABLED_RepaidMissingTxio)
{
   // Copy only the first four blocks.  Will copy the full file next to test
   // readBlkFileUpdate method on non-reorg blocks.
   setBlocks({ "0", "1", "2" }, blk0dat_);
   TheBDM.doInitialSyncOnLoad(nullProgress);
   EXPECT_EQ(iface_->getTopBlockHeight(HEADERS), 2);
   EXPECT_EQ(iface_->getTopBlockHash(HEADERS), TestChain::blkHash2);
   EXPECT_TRUE(TheBDM.blockchain().getHeaderByHash(TestChain::blkHash2).isMainBranch());

   appendBlocks({ "3" }, blk0dat_);
   TheBDM.readBlkFileUpdate();

   //grab a ssh and delete some utxos
   StoredScriptHistory ssh;
   iface_->getStoredScriptHistory(ssh, TestChain::scrAddrB);

   for (auto& subssh : ssh.subHistMap_)
   {
      auto txioIter = subssh.second.txioMap_.begin();

      while (txioIter != subssh.second.txioMap_.end())
      {
         if (txioIter->second.isUTXO() &&
            !txioIter->second.isMultisig())
         {
            ssh.totalTxioCount_--;
            ssh.totalUnspent_ -= txioIter->second.getValue();
            subssh.second.txioMap_.erase(txioIter++);
         }
         else
            ++txioIter;
      }
   }

   //delete the keys
   auto delKeysThread = [&ssh, this](void)->void
   {
      LMDBEnv::Transaction tx(iface_->dbEnv_[BLKDATA].get(), LMDB::ReadWrite);

      iface_->putStoredScriptHistory(ssh);
   };

   thread delKeysTID(delKeysThread);
   delKeysTID.join();

   appendBlocks({ "5" }, blk0dat_);
   TheBDM.readBlkFileUpdate();

   appendBlocks({ "4" }, blk0dat_);
   TheBDM.readBlkFileUpdate();

   EXPECT_EQ(iface_->getTopBlockHeight(HEADERS), 5);
   EXPECT_EQ(iface_->getTopBlockHash(HEADERS), TestChain::blkHash5);
   EXPECT_TRUE(TheBDM.blockchain().getHeaderByHash(TestChain::blkHash5).isMainBranch());

   iface_->getStoredScriptHistory(ssh, TestChain::scrAddrA);
   EXPECT_EQ(ssh.getScriptBalance(), 50 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 50 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 1);

   iface_->getStoredScriptHistory(ssh, TestChain::scrAddrB);
   EXPECT_EQ(ssh.getScriptBalance(), 70 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 230 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 14);

   iface_->getStoredScriptHistory(ssh, TestChain::scrAddrC);
   EXPECT_EQ(ssh.getScriptBalance(), 20 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 75 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 8);

   iface_->getStoredScriptHistory(ssh, TestChain::scrAddrD);
   EXPECT_EQ(ssh.getScriptBalance(), 65 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 65 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 7);

   iface_->getStoredScriptHistory(ssh, TestChain::scrAddrE);
   EXPECT_EQ(ssh.getScriptBalance(), 30 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 30 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 5);

   iface_->getStoredScriptHistory(ssh, TestChain::scrAddrF);
   EXPECT_EQ(ssh.getScriptBalance(), 5 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 45 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 7);

   iface_->getStoredScriptHistory(ssh, TestChain::lb1ScrAddr);
   EXPECT_EQ(ssh.getScriptBalance(), 5 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 15 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 3);

   iface_->getStoredScriptHistory(ssh, TestChain::lb1ScrAddrP2SH);
   EXPECT_EQ(ssh.getScriptBalance(), 25 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 40 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 3);

   iface_->getStoredScriptHistory(ssh, TestChain::lb2ScrAddr);
   EXPECT_EQ(ssh.getScriptBalance(), 30 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 40 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 4);

   iface_->getStoredScriptHistory(ssh, TestChain::lb2ScrAddrP2SH);
   EXPECT_EQ(ssh.getScriptBalance(), 0 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 5 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 2);

}

////////////////////////////////////////////////////////////////////////////////
TEST_F(BlockUtilsSuper, DISABLED_Load5Blocks_Plus2NoReorg)
{
   //    DBUtils::setArmoryDbType(ARMORY_DB_SUPER);
   //    DBUtils::setDbPruneType(DB_PRUNE_NONE);
   TheBDM.doInitialSyncOnLoad(nullProgress);


   setBlocks({ "0", "1", "2", "3", "4", "5", "4A" }, blk0dat_);
   BtcUtils::copyFile("../reorgTest/blk_4A.dat", blk0dat_);
   TheBDM.readBlkFileUpdate();
   EXPECT_EQ(TheBDM.blockchain().top().getThisHash(), TestChain::blkHash5);
   EXPECT_EQ(TheBDM.blockchain().top().getBlockHeight(), 5);

   appendBlocks({ "5A" }, blk0dat_);
   TheBDM.readBlkFileUpdate();
   EXPECT_EQ(TheBDM.blockchain().top().getThisHash(), TestChain::blkHash5);
   EXPECT_EQ(TheBDM.blockchain().top().getBlockHeight(), 5);

   //BtcUtils::copyFile("../reorgTest/blk_5A.dat", blk0dat_);
   //iface_->pprintBlkDataDB(BLKDATA);
}


////////////////////////////////////////////////////////////////////////////////
TEST_F(BlockUtilsSuper, DISABLED_Load5Blocks_FullReorg)
{
   TheBDM.doInitialSyncOnLoad(nullProgress);

   setBlocks({ "0", "1", "2", "3", "4", "5", "4A" }, blk0dat_);
   TheBDM.readBlkFileUpdate();
   appendBlocks({ "5A" }, blk0dat_);
   TheBDM.readBlkFileUpdate();

   StoredScriptHistory ssh;

   iface_->getStoredScriptHistory(ssh, TestChain::scrAddrA);
   EXPECT_EQ(ssh.getScriptBalance(), 50 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 50 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 1);

   iface_->getStoredScriptHistory(ssh, TestChain::scrAddrB);
   EXPECT_EQ(ssh.getScriptBalance(), 30 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 160 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 11);

   iface_->getStoredScriptHistory(ssh, TestChain::scrAddrC);
   EXPECT_EQ(ssh.getScriptBalance(), 55 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 55 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 4);

   iface_->getStoredScriptHistory(ssh, TestChain::scrAddrD);
   EXPECT_EQ(ssh.getScriptBalance(), 60 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 60 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 5);

   iface_->getStoredScriptHistory(ssh, TestChain::scrAddrE);
   EXPECT_EQ(ssh.getScriptBalance(), 30 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 30 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 4);

   iface_->getStoredScriptHistory(ssh, TestChain::scrAddrF);
   EXPECT_EQ(ssh.getScriptBalance(), 60 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 95 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 7);

   iface_->getStoredScriptHistory(ssh, TestChain::lb1ScrAddr);
   EXPECT_EQ(ssh.getScriptBalance(), 5 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 15 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 3);

   iface_->getStoredScriptHistory(ssh, TestChain::lb1ScrAddrP2SH);
   EXPECT_EQ(ssh.getScriptBalance(), 0 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 15 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 2);

   iface_->getStoredScriptHistory(ssh, TestChain::lb2ScrAddr);
   EXPECT_EQ(ssh.getScriptBalance(), 10 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 20 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 3);

   iface_->getStoredScriptHistory(ssh, TestChain::lb2ScrAddrP2SH);
   EXPECT_EQ(ssh.getScriptBalance(), 0 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 5 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 2);
}

////////////////////////////////////////////////////////////////////////////////
TEST_F(BlockUtilsSuper, DISABLED_Load5Blocks_ReloadBDM_Reorg)
{
   TheBDM.doInitialSyncOnLoad(nullProgress);

   //reload BDM
   delete theBDM;
   theBDM = new BlockDataManager(config_);
   theBDM->openDatabase();
   iface_ = theBDM->getIFace();

   setBlocks({ "0", "1", "2", "3", "4", "5", "4A", "5A" }, blk0dat_);
   TheBDM.doInitialSyncOnLoad(nullProgress);

   EXPECT_EQ(TheBDM.blockchain().top().getBlockHeight(), 5);

   StoredScriptHistory ssh;

   iface_->getStoredScriptHistory(ssh, TestChain::scrAddrA);
   EXPECT_EQ(ssh.getScriptBalance(), 50 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 50 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 1);

   iface_->getStoredScriptHistory(ssh, TestChain::scrAddrB);
   EXPECT_EQ(ssh.getScriptBalance(), 30 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 160 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 11);

   iface_->getStoredScriptHistory(ssh, TestChain::scrAddrC);
   EXPECT_EQ(ssh.getScriptBalance(), 55 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 55 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 4);

   iface_->getStoredScriptHistory(ssh, TestChain::scrAddrD);
   EXPECT_EQ(ssh.getScriptBalance(), 60 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 60 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 5);

   iface_->getStoredScriptHistory(ssh, TestChain::scrAddrE);
   EXPECT_EQ(ssh.getScriptBalance(), 30 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 30 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 4);

   iface_->getStoredScriptHistory(ssh, TestChain::scrAddrF);
   EXPECT_EQ(ssh.getScriptBalance(), 60 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 95 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 7);

   iface_->getStoredScriptHistory(ssh, TestChain::lb1ScrAddr);
   EXPECT_EQ(ssh.getScriptBalance(), 5 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 15 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 3);

   iface_->getStoredScriptHistory(ssh, TestChain::lb1ScrAddrP2SH);
   EXPECT_EQ(ssh.getScriptBalance(), 0 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 15 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 2);

   iface_->getStoredScriptHistory(ssh, TestChain::lb2ScrAddr);
   EXPECT_EQ(ssh.getScriptBalance(), 10 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 20 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 3);

   iface_->getStoredScriptHistory(ssh, TestChain::lb2ScrAddrP2SH);
   EXPECT_EQ(ssh.getScriptBalance(), 0 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 5 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 2);
}

////////////////////////////////////////////////////////////////////////////////
TEST_F(BlockUtilsSuper, DISABLED_Load5Blocks_DoubleReorg)
{
   StoredScriptHistory ssh;

   setBlocks({ "0", "1", "2", "3", "4A" }, blk0dat_);

   TheBDM.doInitialSyncOnLoad(nullProgress);

   //first reorg: up to 5
   setBlocks({ "0", "1", "2", "3", "4A", "4", "5" }, blk0dat_);
   uint32_t prevBlock = TheBDM.readBlkFileUpdate();

   iface_->getStoredScriptHistory(ssh, TestChain::scrAddrA);
   EXPECT_EQ(ssh.getScriptBalance(), 50 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 50 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 1);

   iface_->getStoredScriptHistory(ssh, TestChain::scrAddrB);
   EXPECT_EQ(ssh.getScriptBalance(), 70 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 230 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 14);

   iface_->getStoredScriptHistory(ssh, TestChain::scrAddrC);
   EXPECT_EQ(ssh.getScriptBalance(), 20 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 75 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 8);

   iface_->getStoredScriptHistory(ssh, TestChain::scrAddrD);
   EXPECT_EQ(ssh.getScriptBalance(), 65 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 65 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 7);

   iface_->getStoredScriptHistory(ssh, TestChain::scrAddrE);
   EXPECT_EQ(ssh.getScriptBalance(), 30 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 30 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 5);

   iface_->getStoredScriptHistory(ssh, TestChain::scrAddrF);
   EXPECT_EQ(ssh.getScriptBalance(), 5 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 45 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 7);

   iface_->getStoredScriptHistory(ssh, TestChain::lb1ScrAddr);
   EXPECT_EQ(ssh.getScriptBalance(), 5 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 15 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 3);

   iface_->getStoredScriptHistory(ssh, TestChain::lb1ScrAddrP2SH);
   EXPECT_EQ(ssh.getScriptBalance(), 25 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 40 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 3);

   iface_->getStoredScriptHistory(ssh, TestChain::lb2ScrAddr);
   EXPECT_EQ(ssh.getScriptBalance(), 30 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 40 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 4);

   iface_->getStoredScriptHistory(ssh, TestChain::lb2ScrAddrP2SH);
   EXPECT_EQ(ssh.getScriptBalance(), 0 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 5 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 2);

   //second reorg: up to 5A
   setBlocks({ "0", "1", "2", "3", "4A", "4", "5", "5A" }, blk0dat_);
   prevBlock = TheBDM.readBlkFileUpdate();

   iface_->getStoredScriptHistory(ssh, TestChain::scrAddrA);
   EXPECT_EQ(ssh.getScriptBalance(), 50 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 50 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 1);

   iface_->getStoredScriptHistory(ssh, TestChain::scrAddrB);
   EXPECT_EQ(ssh.getScriptBalance(), 30 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 160 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 11);

   iface_->getStoredScriptHistory(ssh, TestChain::scrAddrC);
   EXPECT_EQ(ssh.getScriptBalance(), 55 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 55 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 4);

   iface_->getStoredScriptHistory(ssh, TestChain::scrAddrD);
   EXPECT_EQ(ssh.getScriptBalance(), 60 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 60 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 5);

   iface_->getStoredScriptHistory(ssh, TestChain::scrAddrE);
   EXPECT_EQ(ssh.getScriptBalance(), 30 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 30 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 4);

   iface_->getStoredScriptHistory(ssh, TestChain::scrAddrF);
   EXPECT_EQ(ssh.getScriptBalance(), 60 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 95 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 7);

   iface_->getStoredScriptHistory(ssh, TestChain::lb1ScrAddr);
   EXPECT_EQ(ssh.getScriptBalance(), 5 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 15 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 3);

   iface_->getStoredScriptHistory(ssh, TestChain::lb1ScrAddrP2SH);
   EXPECT_EQ(ssh.getScriptBalance(), 0 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 15 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 2);

   iface_->getStoredScriptHistory(ssh, TestChain::lb2ScrAddr);
   EXPECT_EQ(ssh.getScriptBalance(), 10 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 20 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 3);

   iface_->getStoredScriptHistory(ssh, TestChain::lb2ScrAddrP2SH);
   EXPECT_EQ(ssh.getScriptBalance(), 0 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 5 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 2);
}

////////////////////////////////////////////////////////////////////////////////
// These next two tests disabled because they broke after ARMORY_DB_BARE impl
TEST_F(BlockUtilsSuper, DISABLED_RestartDBAfterBuild)
{
   // Copy only the first four blocks.  Will copy the full file next to test
   // readBlkFileUpdate method on non-reorg blocks.
   setBlocks({ "0", "1", "2", "3" }, blk0dat_);
   TheBDM.doInitialSyncOnLoad(nullProgress);
   EXPECT_EQ(iface_->getTopBlockHeight(HEADERS), 2);
   EXPECT_EQ(iface_->getTopBlockHash(HEADERS), TestChain::blkHash2);
   EXPECT_TRUE(TheBDM.blockchain().getHeaderByHash(TestChain::blkHash2).isMainBranch());

   // Add two more blocks
   appendBlocks({ "4", "5" }, blk0dat_);

   // Now reinitialize the DB and hopefully detect the new blocks and update

   TheBDM.doInitialSyncOnLoad(nullProgress);

   EXPECT_EQ(getTopBlockHeightInDB(TheBDM, HEADERS), 4);
   EXPECT_EQ(getTopBlockHeightInDB(TheBDM, BLKDATA), 4);
   EXPECT_TRUE(TheBDM.blockchain().getHeaderByHash(TestChain::blkHash4).isMainBranch());

   StoredScriptHistory ssh;

   iface_->getStoredScriptHistory(ssh, TestChain::scrAddrA);
   EXPECT_EQ(ssh.getScriptBalance(), 100 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 100 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 2);

   iface_->getStoredScriptHistory(ssh, TestChain::scrAddrB);
   EXPECT_EQ(ssh.getScriptBalance(), 0 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 140 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 3);

   iface_->getStoredScriptHistory(ssh, TestChain::scrAddrC);
   EXPECT_EQ(ssh.getScriptBalance(), 50 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 60 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 2);

   iface_->getStoredScriptHistory(ssh, TestChain::scrAddrD);
   EXPECT_EQ(ssh.getScriptBalance(), 100 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 100 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 3);
}


////////////////////////////////////////////////////////////////////////////////
TEST_F(BlockUtilsSuper, DISABLED_RestartDBAfterBuild_withReplay)
{
   // Copy only the first four blocks.  Will copy the full file next to test
   // readBlkFileUpdate method on non-reorg blocks.
   setBlocks({ "0", "1", "2", "3" }, blk0dat_);
   TheBDM.doInitialSyncOnLoad(nullProgress);
   EXPECT_EQ(iface_->getTopBlockHeight(HEADERS), 2);
   EXPECT_EQ(iface_->getTopBlockHash(HEADERS), TestChain::blkHash2);
   EXPECT_TRUE(TheBDM.blockchain().getHeaderByHash(TestChain::blkHash2).isMainBranch());

   // Add two more blocks
   appendBlocks({ "4", "5" }, blk0dat_);

   // Now reinitialize the DB and hopefully detect the new blocks and update

   uint32_t replayRewind = 700;

   TheBDM.doInitialSyncOnLoad(nullProgress);

   EXPECT_EQ(getTopBlockHeightInDB(TheBDM, HEADERS), 4);
   EXPECT_EQ(getTopBlockHeightInDB(TheBDM, BLKDATA), 4);
   EXPECT_TRUE(TheBDM.blockchain().getHeaderByHash(TestChain::blkHash4).isMainBranch());

   StoredScriptHistory ssh;

   iface_->getStoredScriptHistory(ssh, TestChain::scrAddrA);
   EXPECT_EQ(ssh.getScriptBalance(), 100 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 100 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 2);

   iface_->getStoredScriptHistory(ssh, TestChain::scrAddrB);
   EXPECT_EQ(ssh.getScriptBalance(), 0 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 140 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 3);

   iface_->getStoredScriptHistory(ssh, TestChain::scrAddrC);
   EXPECT_EQ(ssh.getScriptBalance(), 50 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 60 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 2);

   iface_->getStoredScriptHistory(ssh, TestChain::scrAddrD);
   EXPECT_EQ(ssh.getScriptBalance(), 100 * COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 100 * COIN);
   EXPECT_EQ(ssh.totalTxioCount_, 3);

   // Random note (since I just spent 2 hours trying to figure out why
   // I wasn't getting warnings about re-marking TxOuts spent that were
   // already marked spent):   We get three warnings about TxOuts that
   // already marked unspent in the ssh objects when we replay blocks 
   // 1 and 2 (but not 0). This is expected.  But, I also expected a 
   // warning about a TxOut already marked spent.  Turns out that 
   // we are replaying the previous block first which calls "markUnspent" 
   // before we hit this mark-spent logic.  So when we started the
   // method, we actually did have a already-marked-spent TxOut, but 
   // it was marked unspent before we got the point of trying to mark
   // it spent again.   In other words, all expected behavior.
}


////////////////////////////////////////////////////////////////////////////////
TEST_F(BlockUtilsSuper, DISABLED_TimeAndSpaceTest_usuallydisabled)
{
   //    DBUtils::setArmoryDbType(ARMORY_DB_SUPER);
   //    DBUtils::setDbPruneType(DB_PRUNE_NONE);

   string oldblkdir = blkdir_;
   //blkdir_  = string("/home/alan/.bitcoin/blks3");
   //blkdir_  = string("/home/alan/.bitcoin/blocks");
   //TheBDM.SelectNetwork("Main");
   blkdir_ = string("/home/alan/.bitcoin/testnet3/blocks");

   StoredScriptHistory ssh;
   TheBDM.doInitialSyncOnLoad(nullProgress);
   BinaryData scrAddr = READHEX("11b366edfc0a8b66feebae5c2e25a7b6a5d1cf31");
   BinaryData scrAddr2 = READHEX("39aa3d569e06a1d7926dc4be1193c99bf2eb9ee0");
   BinaryData scrAddr3 = READHEX("758e51b5e398a32c6abd091b3fde383291267cfa");
   BinaryData scrAddr4 = READHEX("6c22eb00e3f93acac5ae5d81a9db78a645dfc9c7");
   EXPECT_EQ(getDBBalanceForHash160(TheBDM, scrAddr), 18 * COIN);
   /*TheBDM.pprintSSHInfoAboutHash160(scrAddr);
   TheBDM.pprintSSHInfoAboutHash160(scrAddr2);
   TheBDM.pprintSSHInfoAboutHash160(scrAddr3);
   TheBDM.pprintSSHInfoAboutHash160(scrAddr4);*/
   blkdir_ = oldblkdir;
   LOGINFO << "waiting... (please copy the DB dir...)";
   int pause;
   cin >> pause;
}


////////////////////////////////////////////////////////////////////////////////
// I thought I was going to do something different with this set of tests,
// but I ended up with an exact copy of the BlockUtilsSuper fixture.  Oh well.
class BlockUtilsWithWalletTest : public ::testing::Test
{
protected:
   BlockDataManager *theBDM;
   BlockDataViewer*          theBDV;
   /////////////////////////////////////////////////////////////////////////////
   virtual void SetUp(void)
   {
      LOGDISABLESTDOUT();
      magic_ = READHEX(MAINNET_MAGIC_BYTES);
      ghash_ = READHEX(MAINNET_GENESIS_HASH_HEX);
      gentx_ = READHEX(MAINNET_GENESIS_TX_HASH_HEX);
      zeros_ = READHEX("00000000");

      blkdir_ = string("./blkfiletest");
      homedir_ = string("./fakehomedir");
      ldbdir_ = string("./ldbtestdir");

      mkdir(blkdir_);
      mkdir(homedir_);

      // Put the first 5 blocks into the blkdir
      blk0dat_ = BtcUtils::getBlkFilename(blkdir_, 0);
      setBlocks({ "0", "1", "2", "3", "4", "5" }, blk0dat_);

      BlockDataManagerConfig config;
      config.armoryDbType_ = ARMORY_DB_SUPER;
      config.blkFileLocation_ = blkdir_;
      config.dbLocation_ = ldbdir_;

      config.genesisBlockHash = ghash_;
      config.genesisTxHash = gentx_;
      config.magicBytes = magic_;

      theBDM = new BlockDataManager(config);
      theBDM->openDatabase();
      theBDV = new BlockDataViewer(theBDM);
      iface_ = theBDM->getIFace();

   }


   /////////////////////////////////////////////////////////////////////////////
   virtual void TearDown(void)
   {
      delete theBDM;
      delete theBDV;

      theBDM = nullptr;
      theBDV = nullptr;

      rmdir(blkdir_);
      rmdir(homedir_);

#ifdef _MSC_VER
      rmdir(ldbdir_);
      mkdir(ldbdir_);
#else

      char* delstr = new char[4096];
      sprintf(delstr, "%s/*", ldbdir_.c_str());
      rmdir(delstr);
      delete[] delstr;
#endif

      LOGENABLESTDOUT();
      CLEANUP_ALL_TIMERS();
   }


#if ! defined(_MSC_VER) && ! defined(__MINGW32__)

   /////////////////////////////////////////////////////////////////////////////
   void rmdir(string src)
   {
      char* syscmd = new char[4096];
      sprintf(syscmd, "rm -rf %s", src.c_str());
      system(syscmd);
      delete[] syscmd;
   }

   /////////////////////////////////////////////////////////////////////////////
   void mkdir(string newdir)
   {
      char* syscmd = new char[4096];
      sprintf(syscmd, "mkdir -p %s", newdir.c_str());
      system(syscmd);
      delete[] syscmd;
   }
#endif

   LMDBBlockDatabase* iface_;
   BinaryData magic_;
   BinaryData ghash_;
   BinaryData gentx_;
   BinaryData zeros_;

   string blkdir_;
   string homedir_;
   string ldbdir_;
   string blk0dat_;

};


////////////////////////////////////////////////////////////////////////////////
TEST_F(BlockUtilsWithWalletTest, DISABLED_PreRegisterScrAddrs)
{
   vector<BinaryData> scrAddrVec;
   scrAddrVec.push_back(TestChain::scrAddrA);
   scrAddrVec.push_back(TestChain::scrAddrB);
   scrAddrVec.push_back(TestChain::scrAddrC);

   BtcWallet& wlt = *theBDV->registerWallet(scrAddrVec, "wallet1", false);
   wlt.addScrAddress(TestChain::scrAddrD);

   setBlocks({ "0", "1", "2", "3", "4", "5" }, blk0dat_);

   TheBDM.doInitialSyncOnLoad(nullProgress);

   theBDV->scanWallets();

   uint64_t balanceWlt;
   uint64_t balanceDB;

   balanceWlt = wlt.getScrAddrObjByKey(TestChain::scrAddrA)->getFullBalance();
   balanceDB = iface_->getBalanceForScrAddr(TestChain::scrAddrA);
   EXPECT_EQ(balanceWlt, 50 * COIN);
   EXPECT_EQ(balanceDB, 50 * COIN);

   balanceWlt = wlt.getScrAddrObjByKey(TestChain::scrAddrB)->getFullBalance();
   balanceDB = iface_->getBalanceForScrAddr(TestChain::scrAddrB);
   EXPECT_EQ(balanceWlt, 70 * COIN);
   EXPECT_EQ(balanceDB, 70 * COIN);

   balanceWlt = wlt.getScrAddrObjByKey(TestChain::scrAddrC)->getFullBalance();
   balanceDB = iface_->getBalanceForScrAddr(TestChain::scrAddrC);
   EXPECT_EQ(balanceWlt, 20 * COIN);
   EXPECT_EQ(balanceDB, 20 * COIN);

   balanceDB = iface_->getBalanceForScrAddr(TestChain::scrAddrD);
   EXPECT_EQ(balanceDB, 65 * COIN);
   balanceDB = iface_->getBalanceForScrAddr(TestChain::scrAddrE);
   EXPECT_EQ(balanceDB, 30 * COIN);
   balanceDB = iface_->getBalanceForScrAddr(TestChain::scrAddrF);
   EXPECT_EQ(balanceDB, 5 * COIN);
}

////////////////////////////////////////////////////////////////////////////////
TEST_F(BlockUtilsWithWalletTest, DISABLED_PostRegisterScrAddr)
{
   setBlocks({ "0", "1", "2", "3", "4", "5" }, blk0dat_);
   TheBDM.doInitialSyncOnLoad(nullProgress);

   // We do all the database stuff first, THEN load the addresses
   vector<BinaryData> scrAddrVec;
   scrAddrVec.push_back(TestChain::scrAddrA);
   scrAddrVec.push_back(TestChain::scrAddrB);
   scrAddrVec.push_back(TestChain::scrAddrC);

   BtcWallet& wlt = *theBDV->registerWallet(scrAddrVec, "wallet1", false);
   wlt.addScrAddress(TestChain::scrAddrD);

   theBDV->scanWallets();

   uint64_t balanceWlt;
   uint64_t balanceDB;

   balanceWlt = wlt.getScrAddrObjByKey(TestChain::scrAddrA)->getFullBalance();
   balanceDB = iface_->getBalanceForScrAddr(TestChain::scrAddrA);
   EXPECT_EQ(balanceWlt, 50 * COIN);
   EXPECT_EQ(balanceDB, 50 * COIN);

   balanceWlt = wlt.getScrAddrObjByKey(TestChain::scrAddrB)->getFullBalance();
   balanceDB = iface_->getBalanceForScrAddr(TestChain::scrAddrB);
   EXPECT_EQ(balanceWlt, 70 * COIN);
   EXPECT_EQ(balanceDB, 70 * COIN);

   balanceWlt = wlt.getScrAddrObjByKey(TestChain::scrAddrC)->getFullBalance();
   balanceDB = iface_->getBalanceForScrAddr(TestChain::scrAddrC);
   EXPECT_EQ(balanceWlt, 20 * COIN);
   EXPECT_EQ(balanceDB, 20 * COIN);

   balanceDB = iface_->getBalanceForScrAddr(TestChain::scrAddrD);
   EXPECT_EQ(balanceDB, 65 * COIN);
   balanceDB = iface_->getBalanceForScrAddr(TestChain::scrAddrE);
   EXPECT_EQ(balanceDB, 30 * COIN);
   balanceDB = iface_->getBalanceForScrAddr(TestChain::scrAddrF);
   EXPECT_EQ(balanceDB, 5 * COIN);
}

////////////////////////////////////////////////////////////////////////////////
TEST_F(BlockUtilsWithWalletTest, DISABLED_ZeroConfUpdate)
{
   // Copy only the first two blocks
   setBlocks({ "0", "1" }, blk0dat_);

   vector<BinaryData> scrAddrVec;
   scrAddrVec.push_back(TestChain::scrAddrA);
   scrAddrVec.push_back(TestChain::scrAddrB);
   scrAddrVec.push_back(TestChain::scrAddrC);

   BtcWallet& wlt = *theBDV->registerWallet(scrAddrVec, "wallet1", false);
   wlt.addScrAddress(TestChain::scrAddrD);

   TheBDM.doInitialSyncOnLoad(nullProgress);
   theBDV->enableZeroConf();
   theBDV->scanWallets();

   BinaryData ZChash = READHEX(
      "b6b6f145742a9072fd85f96772e63a00eb4101709aa34ec5dd59e8fc904191a7");
   BinaryData rawZC(259);
   FILE *ff = fopen("../reorgTest/ZCtx.tx", "rb");
   fread(rawZC.getPtr(), 259, 1, ff);
   fclose(ff);

   theBDV->addNewZeroConfTx(rawZC, 1300000000, false);
   theBDV->parseNewZeroConfTx();
   theBDV->scanWallets();

   EXPECT_EQ(wlt.getScrAddrObjByKey(TestChain::scrAddrA)->getFullBalance(), 50 * COIN);
   EXPECT_EQ(wlt.getScrAddrObjByKey(TestChain::scrAddrB)->getFullBalance(), 70 * COIN);
   EXPECT_EQ(wlt.getScrAddrObjByKey(TestChain::scrAddrC)->getFullBalance(), 10 * COIN);
   EXPECT_EQ(wlt.getScrAddrObjByKey(TestChain::scrAddrD)->getFullBalance(), 0 * COIN);

   //test ledger entry
   LedgerEntry le = wlt.getLedgerEntryForTx(ZChash);

   EXPECT_EQ(le.getTxTime(), 1300000000);
   EXPECT_EQ(le.isSentToSelf(), false);
   EXPECT_EQ(le.getValue(), 30 * COIN);

   //check ZChash in DB
   BinaryData zcKey = WRITE_UINT16_BE(0xFFFF);
   zcKey.append(WRITE_UINT32_LE(0));
   EXPECT_EQ(iface_->getTxHashForLdbKey(zcKey), ZChash);
}

////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
// Now actually execute all the tests
////////////////////////////////////////////////////////////////////////////////
GTEST_API_ int main(int argc, char **argv)
{
#ifdef _MSC_VER
   _CrtSetDbgFlag(_CRTDBG_ALLOC_MEM_DF | _CRTDBG_LEAK_CHECK_DF);
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

