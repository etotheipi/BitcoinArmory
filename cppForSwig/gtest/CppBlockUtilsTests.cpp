#include <limits.h>
#include <iostream>
#include <stdlib.h>
#include "gtest/gtest.h"

#include "../log.h"
#include "../BinaryData.h"
#include "../BtcUtils.h"
#include "../BlockObj.h"
#include "../StoredBlockObj.h"
#include "../PartialMerkle.h"
#include "../leveldb_wrapper.h"
#include "../BlockUtils.h"

#define READHEX BinaryData::CreateFromHex
#define TheBDM BlockDataManager_LevelDB::GetInstance()


/* This didn't work at all
class BitcoinEnvironment : public ::testing::Environment 
{
public:
   // Override this to define how to set up the environment.
   virtual void SetUp() 
   {
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
         "01000000eb10c9a996a2340a4d74eaab41421ed8664aa49d18538bab59010000"
         "000000005a2f06efa9f2bd804f17877537f2080030cadbfa1eb50e02338117cc"
         "604d91b9b7541a4ecfbb0a1a64f1ade703010000000100000000000000000000"
         "00000000000000000000000000000000000000000000ffffffff0804cfbb0a1a"
         "02360affffffff0100f2052a01000000434104c2239c4eedb3beb26785753463"
         "be3ec62b82f6acd62efb65f452f8806f2ede0b338e31d1f69b1ce449558d7061"
         "aa1648ddc2bf680834d3986624006a272dc21cac000000000100000003e8caa1"
         "2bcb2e7e86499c9de49c45c5a1c6167ea4b894c8c83aebba1b6100f343010000"
         "008c493046022100e2f5af5329d1244807f8347a2c8d9acc55a21a5db769e927"
         "4e7e7ba0bb605b26022100c34ca3350df5089f3415d8af82364d7f567a6a297f"
         "cc2c1d2034865633238b8c014104129e422ac490ddfcb7b1c405ab9fb4244124"
         "6c4bca578de4f27b230de08408c64cad03af71ee8a3140b40408a7058a1984a9"
         "f246492386113764c1ac132990d1ffffffff5b55c18864e16c08ef9989d31c7a"
         "343e34c27c30cd7caa759651b0e08cae0106000000008c4930460221009ec9aa"
         "3e0caf7caa321723dea561e232603e00686d4bfadf46c5c7352b07eb00022100"
         "a4f18d937d1e2354b2e69e02b18d11620a6a9332d563e9e2bbcb01cee559680a"
         "014104411b35dd963028300e36e82ee8cf1b0c8d5bf1fc4273e970469f5cb931"
         "ee07759a2de5fef638961726d04bd5eb4e5072330b9b371e479733c942964bb8"
         "6e2b22ffffffff3de0c1e913e6271769d8c0172cea2f00d6d3240afc3a20f9fa"
         "247ce58af30d2a010000008c493046022100b610e169fd15ac9f60fe2b507529"
         "281cf2267673f4690ba428cbb2ba3c3811fd022100ffbe9e3d71b21977a8e97f"
         "de4c3ba47b896d08bc09ecb9d086bb59175b5b9f03014104ff07a1833fd8098b"
         "25f48c66dcf8fde34cbdbcc0f5f21a8c2005b160406cbf34cc432842c6b37b25"
         "90d16b165b36a3efc9908d65fb0e605314c9b278f40f3e1affffffff0240420f"
         "00000000001976a914adfa66f57ded1b655eb4ccd96ee07ca62bc1ddfd88ac00"
         "7d6a7d040000001976a914981a0c9ae61fa8f8c96ae6f8e383d6e07e77133e88"
         "ac00000000010000000138e7586e0784280df58bd3dc5e3d350c9036b1ec4107"
         "951378f45881799c92a4000000008a47304402207c945ae0bbdaf9dadba07bdf"
         "23faa676485a53817af975ddf85a104f764fb93b02201ac6af32ddf597e610b4"
         "002e41f2de46664587a379a0161323a85389b4f82dda014104ec8883d3e4f7a3"
         "9d75c9f5bb9fd581dc9fb1b7cdf7d6b5a665e4db1fdb09281a74ab138a2dba25"
         "248b5be38bf80249601ae688c90c6e0ac8811cdb740fcec31dffffffff022f66"
         "ac61050000001976a914964642290c194e3bfab661c1085e47d67786d2d388ac"
         "2f77e200000000001976a9141486a7046affd935919a3cb4b50a8a0c233c286c"
         "88ac00000000");

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
         //"01000000020044fbc929d78e4203eed6f1d3d39c0157d8e5c100bbe0886779c0"
         //"ebf6a69324010000008a47304402206568144ed5e7064d6176c74738b04c08ca"
         //"19ca54ddeb480084b77f45eebfe57802207927d6975a5ac0e1bb36f5c05356dc"
         //"da1f521770511ee5e03239c8e1eecf3aed0141045d74feae58c4c36d7c35beac"
         //"05eddddc78b3ce4b02491a2eea72043978056a8bc439b99ddaad327207b09ef1"
         //"6a8910828e805b0cc8c11fba5caea2ee939346d7ffffffff45c866b219b17695"
         //"2508f8e5aea728f950186554fc4a5807e2186a8e1c4009e5000000008c493046"
         //"022100bd5d41662f98cfddc46e86ea7e4a3bc8fe9f1dfc5c4836eaf7df582596"
         //"cfe0e9022100fc459ae4f59b8279d679003b88935896acd10021b6e2e4619377"
         //"e336b5296c5e014104c00bab76a708ba7064b2315420a1c533ca9945eeff9754"
         //"cdc574224589e9113469b4e71752146a10028079e04948ecdf70609bf1b9801f"
         //"6b73ab75947ac339e5ffffffff0200000000");
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


      sbh_.unserialize(rawHead_);

      // Make sure the global DB type and prune type are reset for each test
      DBUtils.setArmoryDbType(ARMORY_DB_FULL);
      DBUtils.setDbPruneType(DB_PRUNE_NONE);
   }

   BinaryData rawHead_;
   BinaryData headHashLE_;
   BinaryData headHashBE_;

   BinaryData rawBlock_;

   BinaryData rawTx0_;
   BinaryData rawTx1_;

   BlockHeader bh_;
   Tx tx1_;
   Tx tx2_;

   BinaryData rawTxUnfrag_;
   BinaryData rawTxFragged_;
   BinaryData rawTxOut0_;
   BinaryData rawTxOut1_;

   StoredHeader sbh_;

};


::testing::Environment* const btcenv = 
               ::testing::AddGlobalTestEnvironment(new BitcoinEnvironment);
*/




////////////////////////////////////////////////////////////////////////////////
class BinaryDataTest : public ::testing::Test
{
protected:
   virtual void SetUp(void) 
   {
      str0_ = "";
      str4_ = "1234abcd";
      str5_ = "1234abcdef";

      bd0_ = READHEX(str0_);
      bd4_ = READHEX(str4_);
      bd5_ = READHEX(str5_);
   }

   string str0_;
   string str4_;
   string str5_;

   BinaryData bd0_;
   BinaryData bd4_;
   BinaryData bd5_;

};


////////////////////////////////////////////////////////////////////////////////
TEST_F(BinaryDataTest, Constructor)
{
   uint8_t* ptr = new uint8_t[4];

   BinaryData a;
   BinaryData b(4);
   BinaryData c(ptr, 2);
   BinaryData d(ptr, 4);
   BinaryData e(b);
   BinaryData f(string("xyza"));

   EXPECT_EQ(a.getSize(), 0);
   EXPECT_EQ(b.getSize(), 4);
   EXPECT_EQ(c.getSize(), 2);
   EXPECT_EQ(d.getSize(), 4);
   EXPECT_EQ(e.getSize(), 4);
   EXPECT_EQ(f.getSize(), 4);

   EXPECT_TRUE( a.isNull());
   EXPECT_FALSE(b.isNull());
   EXPECT_FALSE(c.isNull());
   EXPECT_FALSE(d.isNull());
   EXPECT_FALSE(e.isNull());

   BinaryDataRef g(f);
   BinaryDataRef h(d);
   BinaryData    i(g);

   EXPECT_EQ(   g.getSize(), 4);
   EXPECT_EQ(   i.getSize(), 4);
   EXPECT_TRUE( g==f);
   EXPECT_FALSE(g==h);
   EXPECT_TRUE( i==g);

   delete[] ptr;
}


////////////////////////////////////////////////////////////////////////////////
TEST_F(BinaryDataTest, CopyFrom)
{
   BinaryData a,b,c,d,e,f;
   a.copyFrom((uint8_t*)bd0_.getPtr(), bd0_.getSize());
   b.copyFrom((uint8_t*)bd4_.getPtr(), (uint8_t*)bd4_.getPtr()+4);
   c.copyFrom((uint8_t*)bd4_.getPtr(), bd4_.getSize());
   d.copyFrom(str5_);
   e.copyFrom(a);

   BinaryDataRef i(b);
   f.copyFrom(i);

   EXPECT_EQ(a.getSize(), 0);
   EXPECT_EQ(b.getSize(), 4);
   EXPECT_EQ(c.getSize(), 4);
   EXPECT_EQ(a,e);
   EXPECT_EQ(b,c);
}


////////////////////////////////////////////////////////////////////////////////
TEST_F(BinaryDataTest, CopyTo)
{
   BinaryData a,b,c,d,e,f,g,h;
   bd0_.copyTo(a);
   bd4_.copyTo(b);

   c.resize(bd5_.getSize());
   bd5_.copyTo(c.getPtr());

   size_t sz = 2;
   d.resize(sz);
   e.resize(sz);
   bd5_.copyTo(d.getPtr(), sz);
   bd5_.copyTo(e.getPtr(), bd5_.getSize()-sz, sz);

   f.copyFrom(bd5_.getPtr(), bd5_.getPtr()+sz);

   EXPECT_TRUE(a==bd0_);
   EXPECT_TRUE(b==bd4_);
   EXPECT_TRUE(c==bd5_);
   EXPECT_TRUE(bd5_.startsWith(d));
   EXPECT_TRUE(bd5_.endsWith(e));
   EXPECT_TRUE(d==f);

   EXPECT_EQ(a.getSize(), 0);
   EXPECT_EQ(b.getSize(), 4);
   EXPECT_EQ(c.getSize(), 5);
   EXPECT_EQ(d.getSize(), 2);
   EXPECT_NE(b,c);
}

////////////////////////////////////////////////////////////////////////////////
TEST_F(BinaryDataTest, Fill)
{
   BinaryData a(0), b(1), c(4);
   BinaryData aAns = READHEX("");
   BinaryData bAns = READHEX("aa");
   BinaryData cAns = READHEX("aaaaaaaa");

   a.fill(0xaa);
   b.fill(0xaa);
   c.fill(0xaa);

   EXPECT_EQ(a, aAns);
   EXPECT_EQ(b, bAns);
   EXPECT_EQ(c, cAns);
}

////////////////////////////////////////////////////////////////////////////////
TEST_F(BinaryDataTest, IndexOp)
{
   EXPECT_EQ(bd4_[0], 0x12);
   EXPECT_EQ(bd4_[1], 0x34);
   EXPECT_EQ(bd4_[2], 0xab);
   EXPECT_EQ(bd4_[3], 0xcd);

   EXPECT_EQ(bd4_[-4], 0x12);
   EXPECT_EQ(bd4_[-3], 0x34);
   EXPECT_EQ(bd4_[-2], 0xab);
   EXPECT_EQ(bd4_[-1], 0xcd);

   bd4_[1] = 0xff;
   EXPECT_EQ(bd4_[0], 0x12);
   EXPECT_EQ(bd4_[1], 0xff);
   EXPECT_EQ(bd4_[2], 0xab);
   EXPECT_EQ(bd4_[3], 0xcd);

   EXPECT_EQ(bd4_[-4], 0x12);
   EXPECT_EQ(bd4_[-3], 0xff);
   EXPECT_EQ(bd4_[-2], 0xab);
   EXPECT_EQ(bd4_[-1], 0xcd);

   EXPECT_EQ(bd4_.toHexStr(), string("12ffabcd"));
}

////////////////////////////////////////////////////////////////////////////////
TEST_F(BinaryDataTest, StartsEndsWith)
{
   BinaryData a = READHEX("abcd");
   EXPECT_TRUE( bd0_.startsWith(bd0_));
   EXPECT_TRUE( bd4_.startsWith(bd0_));
   EXPECT_TRUE( bd5_.startsWith(bd4_));
   EXPECT_TRUE( bd5_.startsWith(bd5_));
   EXPECT_FALSE(bd4_.startsWith(bd5_));
   EXPECT_TRUE( bd0_.startsWith(bd0_));
   EXPECT_FALSE(bd0_.startsWith(bd4_));
   EXPECT_FALSE(bd5_.endsWith(a));
   EXPECT_TRUE( bd4_.endsWith(a));
   EXPECT_FALSE(bd0_.endsWith(a));
}


////////////////////////////////////////////////////////////////////////////////
TEST_F(BinaryDataTest, Append)
{
   BinaryData a = READHEX("ef");

   BinaryData static4 = bd4_;

   BinaryData b = bd4_ + a;
   BinaryData c = bd4_.append(a);

   BinaryDataRef d(a);
   bd4_.copyFrom(static4);
   BinaryData e = bd4_.append(d);
   bd4_.copyFrom(static4);
   BinaryData f = bd4_.append(a.getPtr(), 1);
   bd4_.copyFrom(static4);
   BinaryData g = bd4_.append(0xef);

   BinaryData h = bd0_ + a;
   BinaryData i = bd0_.append(a);
   bd0_.resize(0);
   BinaryData j = bd0_.append(a.getPtr(), 1);
   bd0_.resize(0);
   BinaryData k = bd0_.append(0xef);
   
   EXPECT_EQ(bd5_, b);
   EXPECT_EQ(bd5_, c);
   EXPECT_EQ(bd5_, e);
   EXPECT_EQ(bd5_, f);
   EXPECT_EQ(bd5_, g);

   EXPECT_NE(bd5_, h);
   EXPECT_EQ(a, h);
   EXPECT_EQ(a, i);
   EXPECT_EQ(a, j);
   EXPECT_EQ(a, k);
}


////////////////////////////////////////////////////////////////////////////////
TEST_F(BinaryDataTest, Inequality)
{
   EXPECT_FALSE(bd0_ < bd0_);
   EXPECT_TRUE( bd0_ < bd4_);
   EXPECT_TRUE( bd0_ < bd5_);

   EXPECT_FALSE(bd4_ < bd0_);
   EXPECT_FALSE(bd4_ < bd4_);
   EXPECT_TRUE( bd4_ < bd5_);

   EXPECT_FALSE(bd5_ < bd0_);
   EXPECT_FALSE(bd5_ < bd4_);
   EXPECT_FALSE(bd5_ < bd5_);
}

////////////////////////////////////////////////////////////////////////////////
TEST_F(BinaryDataTest, Equality)
{
   EXPECT_TRUE( bd0_==bd0_);
   EXPECT_TRUE( bd4_==bd4_);
   EXPECT_FALSE(bd4_==bd5_);
   EXPECT_TRUE( bd0_!=bd4_);
   EXPECT_TRUE( bd0_!=bd5_);
   EXPECT_TRUE( bd4_!=bd5_);
   EXPECT_FALSE(bd4_!=bd4_);
}


////////////////////////////////////////////////////////////////////////////////
TEST_F(BinaryDataTest, ToString)
{
   EXPECT_EQ(bd0_.toHexStr(), str0_);
   EXPECT_EQ(bd4_.toHexStr(), str4_);
   EXPECT_EQ(bd4_.toHexStr(), str4_);

   string a,b;
   bd0_.copyTo(a);
   bd4_.copyTo(b);
   EXPECT_EQ(bd0_.toBinStr(), a);
   EXPECT_EQ(bd4_.toBinStr(), b);

   string stra("cdab3412");
   BinaryData bda = READHEX(stra);

   EXPECT_EQ(bd4_.toHexStr(true), stra);
   EXPECT_EQ(bd4_.toBinStr(true), bda.toBinStr());

}


////////////////////////////////////////////////////////////////////////////////
TEST_F(BinaryDataTest, Endianness)
{
   BinaryData a = READHEX("cdab3412");
   BinaryData b = READHEX("1234cdab");

   BinaryData static4 = bd4_;

   EXPECT_EQ(   a.copySwapEndian(), bd4_);
   EXPECT_EQ(bd4_.copySwapEndian(),    a);
   EXPECT_EQ(bd0_.copySwapEndian(), bd0_);


   bd4_ = static4;
   bd4_.swapEndian();
   EXPECT_EQ(bd4_, a);

   bd4_ = static4;
   bd4_.swapEndian(2);
   EXPECT_EQ(bd4_, b);

   bd4_ = static4;
   bd4_.swapEndian(2,2);
   EXPECT_EQ(bd4_, b);

   bd4_ = static4;
   bd4_.swapEndian(2,4);
   EXPECT_EQ(bd4_, b);
}


TEST_F(BinaryDataTest, IntToBinData)
{
   // 0x1234 in src code is always interpreted by the compiler as
   // big-endian, regardless of the underlying architecture.  So 
   // writing 0x1234 will be interpretted as an integer with value
   // 4660 on all architectures.  
   BinaryData a,b;

   a = BinaryData::IntToStrLE<uint8_t>(0xab);
   b = BinaryData::IntToStrBE<uint8_t>(0xab);
   EXPECT_EQ(a, READHEX("ab"));
   EXPECT_EQ(b, READHEX("ab"));

   a = BinaryData::IntToStrLE<uint16_t>(0xabcd);
   b = BinaryData::IntToStrBE<uint16_t>(0xabcd);
   EXPECT_EQ(a, READHEX("cdab"));
   EXPECT_EQ(b, READHEX("abcd"));

   a = BinaryData::IntToStrLE((uint16_t)0xabcd);
   b = BinaryData::IntToStrBE((uint16_t)0xabcd);
   EXPECT_EQ(a, READHEX("cdab"));
   EXPECT_EQ(b, READHEX("abcd"));

   // This fails b/c it auto "promotes" non-suffix literals to 4-byte ints
   a = BinaryData::IntToStrLE(0xabcd);
   b = BinaryData::IntToStrBE(0xabcd);
   EXPECT_NE(a, READHEX("cdab"));
   EXPECT_NE(b, READHEX("abcd"));

   a = BinaryData::IntToStrLE(0xfec38a11);
   b = BinaryData::IntToStrBE(0xfec38a11);
   EXPECT_EQ(a, READHEX("118ac3fe"));
   EXPECT_EQ(b, READHEX("fec38a11"));

   a = BinaryData::IntToStrLE(0x00000000fec38a11ULL);
   b = BinaryData::IntToStrBE(0x00000000fec38a11ULL);
   EXPECT_EQ(a, READHEX("118ac3fe00000000"));
   EXPECT_EQ(b, READHEX("00000000fec38a11"));

}

TEST_F(BinaryDataTest, BinDataToInt)
{
   uint8_t   a8,  b8;
   uint16_t a16, b16;
   uint32_t a32, b32;
   uint64_t a64, b64;

   a8 = BinaryData::StrToIntBE<uint8_t>(READHEX("ab"));
   b8 = BinaryData::StrToIntLE<uint8_t>(READHEX("ab"));
   EXPECT_EQ(a8, 0xab);
   EXPECT_EQ(b8, 0xab);

   a16 = BinaryData::StrToIntBE<uint16_t>(READHEX("abcd"));
   b16 = BinaryData::StrToIntLE<uint16_t>(READHEX("abcd"));
   EXPECT_EQ(a16, 0xabcd);
   EXPECT_EQ(b16, 0xcdab);

   a32 = BinaryData::StrToIntBE<uint32_t>(READHEX("fec38a11"));
   b32 = BinaryData::StrToIntLE<uint32_t>(READHEX("fec38a11"));
   EXPECT_EQ(a32, 0xfec38a11);
   EXPECT_EQ(b32, 0x118ac3fe);

   a64 = BinaryData::StrToIntBE<uint64_t>(READHEX("00000000fec38a11"));
   b64 = BinaryData::StrToIntLE<uint64_t>(READHEX("00000000fec38a11"));
   EXPECT_EQ(a64, 0x00000000fec38a11);
   EXPECT_EQ(b64, 0x118ac3fe00000000);
    
   // These are really just identical tests, I have no idea whether it
   // was worth spending the time to write these, and even this comment
   // here explaining how it was probably a waste of time...
   a8 = READ_UINT8_BE(READHEX("ab"));
   b8 = READ_UINT8_LE(READHEX("ab"));
   EXPECT_EQ(a8, 0xab);
   EXPECT_EQ(b8, 0xab);

   a16 = READ_UINT16_BE(READHEX("abcd"));
   b16 = READ_UINT16_LE(READHEX("abcd"));
   EXPECT_EQ(a16, 0xabcd);
   EXPECT_EQ(b16, 0xcdab);

   a32 = READ_UINT32_BE(READHEX("fec38a11"));
   b32 = READ_UINT32_LE(READHEX("fec38a11"));
   EXPECT_EQ(a32, 0xfec38a11);
   EXPECT_EQ(b32, 0x118ac3fe);

   a64 = READ_UINT64_BE(READHEX("00000000fec38a11"));
   b64 = READ_UINT64_LE(READHEX("00000000fec38a11"));
   EXPECT_EQ(a64, 0x00000000fec38a11);
   EXPECT_EQ(b64, 0x118ac3fe00000000);

   // Test the all-on-one read-int macros
   a8 = READ_UINT8_HEX_BE("ab");
   b8 = READ_UINT8_HEX_LE("ab");
   EXPECT_EQ(a8, 0xab);
   EXPECT_EQ(b8, 0xab);

   a16 = READ_UINT16_HEX_BE("abcd");
   b16 = READ_UINT16_HEX_LE("abcd");
   EXPECT_EQ(a16, 0xabcd);
   EXPECT_EQ(b16, 0xcdab);

   a32 = READ_UINT32_HEX_BE("fec38a11");
   b32 = READ_UINT32_HEX_LE("fec38a11");
   EXPECT_EQ(a32, 0xfec38a11);
   EXPECT_EQ(b32, 0x118ac3fe);

   a64 = READ_UINT64_HEX_BE("00000000fec38a11");
   b64 = READ_UINT64_HEX_LE("00000000fec38a11");
   EXPECT_EQ(a64, 0x00000000fec38a11);
   EXPECT_EQ(b64, 0x118ac3fe00000000);
}

////////////////////////////////////////////////////////////////////////////////
TEST_F(BinaryDataTest, Find)
{
   BinaryData a = READHEX("12");
   BinaryData b = READHEX("34");
   BinaryData c = READHEX("abcd");
   BinaryData d = READHEX("ff");

   EXPECT_EQ(bd0_.find(bd0_),     0);
   EXPECT_EQ(bd0_.find(bd4_),    -1);
   EXPECT_EQ(bd0_.find(bd4_, 2), -1);
   EXPECT_EQ(bd4_.find(bd0_),     0);
   EXPECT_EQ(bd4_.find(bd0_, 2),  2);

   EXPECT_EQ(bd4_.find(a),  0);
   EXPECT_EQ(bd4_.find(b),  1);
   EXPECT_EQ(bd4_.find(c),  2);
   EXPECT_EQ(bd4_.find(d), -1);

   EXPECT_EQ(bd4_.find(a, 0),  0);
   EXPECT_EQ(bd4_.find(b, 0),  1);
   EXPECT_EQ(bd4_.find(c, 0),  2);
   EXPECT_EQ(bd4_.find(d, 0), -1);

   EXPECT_EQ(bd4_.find(a, 1), -1);
   EXPECT_EQ(bd4_.find(b, 1),  1);
   EXPECT_EQ(bd4_.find(c, 1),  2);
   EXPECT_EQ(bd4_.find(d, 1), -1);

   EXPECT_EQ(bd4_.find(a, 4), -1);
   EXPECT_EQ(bd4_.find(b, 4), -1);
   EXPECT_EQ(bd4_.find(c, 4), -1);
   EXPECT_EQ(bd4_.find(d, 4), -1);

   EXPECT_EQ(bd4_.find(a, 8), -1);
   EXPECT_EQ(bd4_.find(b, 8), -1);
   EXPECT_EQ(bd4_.find(c, 8), -1);
   EXPECT_EQ(bd4_.find(d, 8), -1);
}
    

TEST_F(BinaryDataTest, Contains)
{
   BinaryData a = READHEX("12");
   BinaryData b = READHEX("34");
   BinaryData c = READHEX("abcd");
   BinaryData d = READHEX("ff");

   EXPECT_TRUE( bd0_.contains(bd0_));
   EXPECT_FALSE(bd0_.contains(bd4_));
   EXPECT_FALSE(bd0_.contains(bd4_, 2));

   EXPECT_TRUE( bd4_.contains(a));
   EXPECT_TRUE( bd4_.contains(b));
   EXPECT_TRUE( bd4_.contains(c));
   EXPECT_FALSE(bd4_.contains(d));

   EXPECT_TRUE( bd4_.contains(a, 0));
   EXPECT_TRUE( bd4_.contains(b, 0));
   EXPECT_TRUE( bd4_.contains(c, 0));
   EXPECT_FALSE(bd4_.contains(d, 0));

   EXPECT_FALSE(bd4_.contains(a, 1));
   EXPECT_TRUE( bd4_.contains(b, 1));
   EXPECT_TRUE( bd4_.contains(c, 1));
   EXPECT_FALSE(bd4_.contains(d, 1));

   EXPECT_FALSE(bd4_.contains(a, 4));
   EXPECT_FALSE(bd4_.contains(b, 4));
   EXPECT_FALSE(bd4_.contains(c, 4));
   EXPECT_FALSE(bd4_.contains(d, 4));

   EXPECT_FALSE(bd4_.contains(a, 8));
   EXPECT_FALSE(bd4_.contains(b, 8));
   EXPECT_FALSE(bd4_.contains(c, 8));
   EXPECT_FALSE(bd4_.contains(d, 8));
}

////////////////////////////////////////////////////////////////////////////////
//TEST_F(BinaryDataTest, GenerateRandom)
//{
    // Yeah, this would be a fun one to try to test...
//}


////////////////////////////////////////////////////////////////////////////////
//TEST_F(BinaryDataTest, ReadFile)
//{
   //ofstream os("test
//}



////////////////////////////////////////////////////////////////////////////////
class BinaryDataRefTest : public ::testing::Test
{
protected:
   virtual void SetUp(void) 
   {
      str0_ = "";
      str4_ = "1234abcd";
      str5_ = "1234abcdef";

      bd0_ = READHEX(str0_);
      bd4_ = READHEX(str4_);
      bd5_ = READHEX(str5_);

      bdr__ = BinaryDataRef();
      bdr0_ = BinaryDataRef(bd0_);
      bdr4_ = BinaryDataRef(bd4_);
      bdr5_ = BinaryDataRef(bd5_);
   }

   string str0_;
   string str4_;
   string str5_;

   BinaryData bd0_;
   BinaryData bd4_;
   BinaryData bd5_;

   BinaryDataRef bdr__;
   BinaryDataRef bdr0_;
   BinaryDataRef bdr4_;
   BinaryDataRef bdr5_;
};



////////////////////////////////////////////////////////////////////////////////
TEST_F(BinaryDataRefTest, Constructor)
{
   BinaryDataRef a;
   BinaryDataRef b((uint8_t*)bd0_.getPtr(), bd0_.getSize());
   BinaryDataRef c((uint8_t*)bd0_.getPtr(), (uint8_t*)bd0_.getPtr());
   BinaryDataRef d((uint8_t*)bd4_.getPtr(), bd4_.getSize());
   BinaryDataRef e((uint8_t*)bd4_.getPtr(), (uint8_t*)bd4_.getPtr()+4);
   BinaryDataRef f(bd0_);
   BinaryDataRef g(bd4_);
   BinaryDataRef h(str0_);
   BinaryDataRef i(str4_);

   EXPECT_TRUE(a.getPtr()==NULL);
   EXPECT_EQ(a.getSize(), 0);

   EXPECT_TRUE(b.getPtr()==NULL);
   EXPECT_EQ(b.getSize(), 0);

   EXPECT_TRUE(c.getPtr()==NULL);
   EXPECT_EQ(c.getSize(), 0);

   EXPECT_FALSE(d.getPtr()==NULL);
   EXPECT_EQ(d.getSize(), 4);

   EXPECT_FALSE(e.getPtr()==NULL);
   EXPECT_EQ(e.getSize(), 4);

   EXPECT_TRUE(f.getPtr()==NULL);
   EXPECT_EQ(f.getSize(), 0);

   EXPECT_FALSE(g.getPtr()==NULL);
   EXPECT_EQ(g.getSize(), 4);

   EXPECT_TRUE(h.getPtr()==NULL);
   EXPECT_EQ(h.getSize(), 0);

   EXPECT_FALSE(i.getPtr()==NULL);
   EXPECT_EQ(i.getSize(), 8);

   EXPECT_TRUE( a.isNull());
   EXPECT_TRUE( b.isNull());
   EXPECT_TRUE( c.isNull());
   EXPECT_FALSE(d.isNull());
   EXPECT_FALSE(e.isNull());
   EXPECT_TRUE( f.isNull());
   EXPECT_FALSE(g.isNull());
   EXPECT_TRUE( h.isNull());
   EXPECT_FALSE(i.isNull());
}



////////////////////////////////////////////////////////////////////////////////
TEST_F(BinaryDataRefTest, PostConstruct)
{
   BinaryDataRef a,b,c,d,e,f,g,h,i;

   b.setRef((uint8_t*)bd0_.getPtr(), bd0_.getSize());
   c.setRef((uint8_t*)bd0_.getPtr(), (uint8_t*)bd0_.getPtr());
   d.setRef((uint8_t*)bd4_.getPtr(), bd4_.getSize());
   e.setRef((uint8_t*)bd4_.getPtr(), (uint8_t*)bd4_.getPtr()+4);
   f.setRef(bd0_);
   g.setRef(bd4_);
   h.setRef(str0_);
   i.setRef(str4_);

   EXPECT_TRUE(a.getPtr()==NULL);
   EXPECT_EQ(a.getSize(), 0);

   EXPECT_TRUE(b.getPtr()==NULL);
   EXPECT_EQ(b.getSize(), 0);

   EXPECT_TRUE(c.getPtr()==NULL);
   EXPECT_EQ(c.getSize(), 0);

   EXPECT_FALSE(d.getPtr()==NULL);
   EXPECT_EQ(d.getSize(), 4);

   EXPECT_FALSE(e.getPtr()==NULL);
   EXPECT_EQ(e.getSize(), 4);

   EXPECT_TRUE(f.getPtr()==NULL);
   EXPECT_EQ(f.getSize(), 0);

   EXPECT_FALSE(g.getPtr()==NULL);
   EXPECT_EQ(g.getSize(), 4);

   EXPECT_FALSE(h.getPtr()==NULL);
   EXPECT_EQ(h.getSize(), 0);

   EXPECT_FALSE(i.getPtr()==NULL);
   EXPECT_EQ(i.getSize(), 8);

   EXPECT_TRUE( a.isNull());
   EXPECT_TRUE( b.isNull());
   EXPECT_TRUE( c.isNull());
   EXPECT_FALSE(d.isNull());
   EXPECT_FALSE(e.isNull());
   EXPECT_TRUE( f.isNull());
   EXPECT_FALSE(g.isNull());
   EXPECT_FALSE(h.isNull());
   EXPECT_FALSE(i.isNull());
}



////////////////////////////////////////////////////////////////////////////////
TEST_F(BinaryDataRefTest, CopyTo)
{
   BinaryData a,b,c,d,e,f,g,h;
   bdr0_.copyTo(a);
   bdr4_.copyTo(b);

   c.resize(bdr5_.getSize());
   bdr5_.copyTo(c.getPtr());

   size_t sz = 2;
   d.resize(sz);
   e.resize(sz);
   bdr5_.copyTo(d.getPtr(), sz);
   bdr5_.copyTo(e.getPtr(), bdr5_.getSize()-sz, sz);

   f.copyFrom(bdr5_.getPtr(), bdr5_.getPtr()+sz);

   EXPECT_TRUE(a==bdr0_);
   EXPECT_TRUE(b==bdr4_);
   EXPECT_TRUE(c==bdr5_);
   EXPECT_TRUE(bdr5_.startsWith(d));
   EXPECT_TRUE(bdr5_.endsWith(e));
   EXPECT_TRUE(d==f);

   EXPECT_EQ(a.getSize(), 0);
   EXPECT_EQ(b.getSize(), 4);
   EXPECT_EQ(c.getSize(), 5);
   EXPECT_EQ(d.getSize(), 2);
   EXPECT_NE(b,c);

   g = bdr0_.copy();
   h = bdr4_.copy();

   EXPECT_EQ(g, bdr0_);
   EXPECT_EQ(h, bdr4_);
   EXPECT_EQ(g, bdr0_.copy());
   EXPECT_EQ(h, bdr4_.copy());

   EXPECT_EQ(bdr0_, g);
   EXPECT_EQ(bdr4_, h);
   EXPECT_EQ(bdr0_.copy(), g);
   EXPECT_EQ(bdr4_.copy(), h);
}



////////////////////////////////////////////////////////////////////////////////
TEST_F(BinaryDataRefTest, ToString)
{
   EXPECT_EQ(bdr0_.toHexStr(), str0_);
   EXPECT_EQ(bdr4_.toHexStr(), str4_);
   EXPECT_EQ(bdr4_.toHexStr(), str4_);

   string a,b;
   bdr0_.copyTo(a);
   bdr4_.copyTo(b);
   EXPECT_EQ(bd0_.toBinStr(), a);
   EXPECT_EQ(bd4_.toBinStr(), b);

   string stra("cdab3412");
   BinaryData bda = READHEX(stra);

   EXPECT_EQ(bdr4_.toHexStr(true), stra);
   EXPECT_EQ(bdr4_.toBinStr(true), bda.toBinStr());

}


////////////////////////////////////////////////////////////////////////////////
TEST_F(BinaryDataRefTest, Find)
{
   BinaryData a = READHEX("12");
   BinaryData b = READHEX("34");
   BinaryData c = READHEX("abcd");
   BinaryData d = READHEX("ff");

   EXPECT_EQ(bdr0_.find(bdr0_),     0);
   EXPECT_EQ(bdr0_.find(bdr4_),    -1);
   EXPECT_EQ(bdr0_.find(bdr4_, 2), -1);
   EXPECT_EQ(bdr4_.find(bdr0_),     0);
   EXPECT_EQ(bdr4_.find(bdr0_, 2),  2);

   EXPECT_EQ(bdr4_.find(a),  0);
   EXPECT_EQ(bdr4_.find(b),  1);
   EXPECT_EQ(bdr4_.find(c),  2);
   EXPECT_EQ(bdr4_.find(d), -1);

   EXPECT_EQ(bdr4_.find(a, 0),  0);
   EXPECT_EQ(bdr4_.find(b, 0),  1);
   EXPECT_EQ(bdr4_.find(c, 0),  2);
   EXPECT_EQ(bdr4_.find(d, 0), -1);

   EXPECT_EQ(bdr4_.find(a, 1), -1);
   EXPECT_EQ(bdr4_.find(b, 1),  1);
   EXPECT_EQ(bdr4_.find(c, 1),  2);
   EXPECT_EQ(bdr4_.find(d, 1), -1);

   EXPECT_EQ(bdr4_.find(a, 4), -1);
   EXPECT_EQ(bdr4_.find(b, 4), -1);
   EXPECT_EQ(bdr4_.find(c, 4), -1);
   EXPECT_EQ(bdr4_.find(d, 4), -1);

   EXPECT_EQ(bdr4_.find(a, 8), -1);
   EXPECT_EQ(bdr4_.find(b, 8), -1);
   EXPECT_EQ(bdr4_.find(c, 8), -1);
   EXPECT_EQ(bdr4_.find(d, 8), -1);

   EXPECT_EQ(bdr4_.find(a.getRef(), 0),  0);
   EXPECT_EQ(bdr4_.find(b.getRef(), 0),  1);
   EXPECT_EQ(bdr4_.find(c.getRef(), 0),  2);
   EXPECT_EQ(bdr4_.find(d.getRef(), 0), -1);
}


TEST_F(BinaryDataRefTest, Contains)
{
   BinaryData a = READHEX("12");
   BinaryData b = READHEX("34");
   BinaryData c = READHEX("abcd");
   BinaryData d = READHEX("ff");

   EXPECT_TRUE( bdr0_.contains(bdr0_));
   EXPECT_FALSE(bdr0_.contains(bdr4_));
   EXPECT_FALSE(bdr0_.contains(bdr4_, 2));

   EXPECT_TRUE( bdr4_.contains(a));
   EXPECT_TRUE( bdr4_.contains(b));
   EXPECT_TRUE( bdr4_.contains(c));
   EXPECT_FALSE(bdr4_.contains(d));

   EXPECT_TRUE( bdr4_.contains(a, 0));
   EXPECT_TRUE( bdr4_.contains(b, 0));
   EXPECT_TRUE( bdr4_.contains(c, 0));
   EXPECT_FALSE(bdr4_.contains(d, 0));

   EXPECT_FALSE(bdr4_.contains(a, 1));
   EXPECT_TRUE( bdr4_.contains(b, 1));
   EXPECT_TRUE( bdr4_.contains(c, 1));
   EXPECT_FALSE(bdr4_.contains(d, 1));

   EXPECT_FALSE(bdr4_.contains(a, 4));
   EXPECT_FALSE(bdr4_.contains(b, 4));
   EXPECT_FALSE(bdr4_.contains(c, 4));
   EXPECT_FALSE(bdr4_.contains(d, 4));

   EXPECT_FALSE(bdr4_.contains(a, 8));
   EXPECT_FALSE(bdr4_.contains(b, 8));
   EXPECT_FALSE(bdr4_.contains(c, 8));
   EXPECT_FALSE(bdr4_.contains(d, 8));

   EXPECT_TRUE( bdr4_.contains(a.getRef(), 0));
   EXPECT_TRUE( bdr4_.contains(b.getRef(), 0));
   EXPECT_TRUE( bdr4_.contains(c.getRef(), 0));
   EXPECT_FALSE(bdr4_.contains(d.getRef(), 0));
}


////////////////////////////////////////////////////////////////////////////////
TEST_F(BinaryDataRefTest, StartsEndsWith)
{
   BinaryData a = READHEX("abcd");
   EXPECT_TRUE( bdr0_.startsWith(bdr0_));
   EXPECT_TRUE( bdr4_.startsWith(bdr0_));
   EXPECT_TRUE( bdr5_.startsWith(bdr4_));
   EXPECT_TRUE( bdr5_.startsWith(bdr5_));
   EXPECT_FALSE(bdr4_.startsWith(bdr5_));
   EXPECT_TRUE( bdr0_.startsWith(bdr0_));
   EXPECT_FALSE(bdr0_.startsWith(bdr4_));

   EXPECT_TRUE( bdr0_.startsWith(bd0_));
   EXPECT_TRUE( bdr4_.startsWith(bd0_));
   EXPECT_TRUE( bdr5_.startsWith(bd4_));
   EXPECT_TRUE( bdr5_.startsWith(bd5_));
   EXPECT_FALSE(bdr4_.startsWith(bd5_));
   EXPECT_TRUE( bdr0_.startsWith(bd0_));
   EXPECT_FALSE(bdr0_.startsWith(bd4_));
   EXPECT_FALSE(bdr5_.endsWith(a));
   EXPECT_TRUE( bdr4_.endsWith(a));
   EXPECT_FALSE(bdr0_.endsWith(a));
}


////////////////////////////////////////////////////////////////////////////////
TEST_F(BinaryDataRefTest, Inequality)
{
   EXPECT_FALSE(bdr0_ < bdr0_);
   EXPECT_TRUE( bdr0_ < bdr4_);
   EXPECT_TRUE( bdr0_ < bdr5_);

   EXPECT_FALSE(bdr4_ < bdr0_);
   EXPECT_FALSE(bdr4_ < bdr4_);
   EXPECT_TRUE( bdr4_ < bdr5_);

   EXPECT_FALSE(bdr5_ < bdr0_);
   EXPECT_FALSE(bdr5_ < bdr4_);
   EXPECT_FALSE(bdr5_ < bdr5_);

   EXPECT_FALSE(bdr0_ < bd0_);
   EXPECT_TRUE( bdr0_ < bd4_);
   EXPECT_TRUE( bdr0_ < bd5_);

   EXPECT_FALSE(bdr4_ < bd0_);
   EXPECT_FALSE(bdr4_ < bd4_);
   EXPECT_TRUE( bdr4_ < bd5_);

   EXPECT_FALSE(bdr5_ < bd0_);
   EXPECT_FALSE(bdr5_ < bd4_);
   EXPECT_FALSE(bdr5_ < bd5_);

   EXPECT_FALSE(bdr0_ > bdr0_);
   EXPECT_TRUE( bdr4_ > bdr0_);
   EXPECT_TRUE( bdr5_ > bdr0_);

   EXPECT_FALSE(bdr0_ > bdr4_);
   EXPECT_FALSE(bdr4_ > bdr4_);
   EXPECT_TRUE( bdr5_ > bdr4_);

   EXPECT_FALSE(bdr0_ > bdr5_);
   EXPECT_FALSE(bdr4_ > bdr5_);
   EXPECT_FALSE(bdr5_ > bdr5_);
}

////////////////////////////////////////////////////////////////////////////////
TEST_F(BinaryDataRefTest, Equality)
{
   EXPECT_TRUE( bdr0_==bdr0_);
   EXPECT_TRUE( bdr4_==bdr4_);
   EXPECT_FALSE(bdr4_==bdr5_);
   EXPECT_TRUE( bdr0_!=bdr4_);
   EXPECT_TRUE( bdr0_!=bdr5_);
   EXPECT_TRUE( bdr4_!=bdr5_);
   EXPECT_FALSE(bdr4_!=bdr4_);

   EXPECT_TRUE( bdr0_==bd0_);
   EXPECT_TRUE( bdr4_==bd4_);
   EXPECT_FALSE(bdr4_==bd5_);
   EXPECT_TRUE( bdr0_!=bd4_);
   EXPECT_TRUE( bdr0_!=bd5_);
   EXPECT_TRUE( bdr4_!=bd5_);
   EXPECT_FALSE(bdr4_!=bd4_);
}


////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
TEST(BitReadWriteTest, Writer8)
{
   BitPacker<uint8_t> bitp;
   
   //EXPECT_EQ( bitp.getValue(), 0);
   EXPECT_EQ( bitp.getBitsUsed(), 0);
   EXPECT_EQ( bitp.getBinaryData(), READHEX("00"));

   bitp.putBit(true);
   //EXPECT_EQ( bitp.getValue(), 128);
   EXPECT_EQ( bitp.getBitsUsed(), 1);
   EXPECT_EQ( bitp.getBinaryData(), READHEX("80"));

   bitp.putBit(false);
   //EXPECT_EQ( bitp.getValue(), 128);
   EXPECT_EQ( bitp.getBitsUsed(), 2);
   EXPECT_EQ( bitp.getBinaryData(), READHEX("80"));

   bitp.putBit(true);
   //EXPECT_EQ( bitp.getValue(), 160);
   EXPECT_EQ( bitp.getBitsUsed(), 3);
   EXPECT_EQ( bitp.getBinaryData(), READHEX("a0"));

   bitp.putBits(0, 2);
   //EXPECT_EQ( bitp.getValue(),  160);
   EXPECT_EQ( bitp.getBitsUsed(), 5);
   EXPECT_EQ( bitp.getBinaryData(), READHEX("a0"));

   bitp.putBits(3, 3);
   //EXPECT_EQ( bitp.getValue(),  163);
   EXPECT_EQ( bitp.getBitsUsed(), 8);
   EXPECT_EQ( bitp.getBinaryData(), READHEX("a3"));
}

////////////////////////////////////////////////////////////////////////////////
TEST(BitReadWriteTest, Writer16)
{
   BitPacker<uint16_t> bitp;
   
   //EXPECT_EQ( bitp.getValue(), 0);
   EXPECT_EQ( bitp.getBitsUsed(), 0);
   EXPECT_EQ( bitp.getBinaryData(), READHEX("0000"));

   bitp.putBit(true);
   //EXPECT_EQ( bitp.getValue(), 0x8000);
   EXPECT_EQ( bitp.getBitsUsed(), 1);
   EXPECT_EQ( bitp.getBinaryData(), READHEX("8000"));

   bitp.putBit(false);
   //EXPECT_EQ( bitp.getValue(), 0x8000);
   EXPECT_EQ( bitp.getBitsUsed(), 2);
   EXPECT_EQ( bitp.getBinaryData(), READHEX("8000"));

   bitp.putBit(true);
   //EXPECT_EQ( bitp.getValue(), 0xa000);
   EXPECT_EQ( bitp.getBitsUsed(), 3);
   EXPECT_EQ( bitp.getBinaryData(), READHEX("a000"));

   bitp.putBits(0, 2);
   //EXPECT_EQ( bitp.getValue(),  0xa000);
   EXPECT_EQ( bitp.getBitsUsed(), 5);
   EXPECT_EQ( bitp.getBinaryData(), READHEX("a000"));

   bitp.putBits(3, 3);
   //EXPECT_EQ( bitp.getValue(),  0xa300);
   EXPECT_EQ( bitp.getBitsUsed(), 8);
   EXPECT_EQ( bitp.getBinaryData(), READHEX("a300"));

   bitp.putBits(3, 8);
   //EXPECT_EQ( bitp.getValue(),  0xa303);
   EXPECT_EQ( bitp.getBitsUsed(), 16);
   EXPECT_EQ( bitp.getBinaryData(), READHEX("a303"));
}


////////////////////////////////////////////////////////////////////////////////
TEST(BitReadWriteTest, Writer32)
{
   BitPacker<uint32_t> bitp;
   
   bitp.putBits(0xffffff00, 32);
   //EXPECT_EQ( bitp.getValue(),  0xffffff00);
   EXPECT_EQ( bitp.getBitsUsed(), 32);
   EXPECT_EQ( bitp.getBinaryData(), READHEX("ffffff00"));
}

////////////////////////////////////////////////////////////////////////////////
TEST(BitReadWriteTest, Writer64)
{
   BitPacker<uint64_t> bitp;
   
   bitp.putBits(0xffffff00ffffffaaULL, 64);
   //EXPECT_EQ( bitp.getValue(),  0xffffff00ffffffaaULL);
   EXPECT_EQ( bitp.getBitsUsed(), 64);
   EXPECT_EQ( bitp.getBinaryData(), READHEX("ffffff00ffffffaa"));

   BitPacker<uint64_t> bitp2;
   bitp2.putBits(0xff, 32);
   bitp2.putBits(0xff, 32);
   //EXPECT_EQ( bitp2.getValue(),  0x000000ff000000ffULL);
   EXPECT_EQ( bitp2.getBitsUsed(), 64);
   EXPECT_EQ( bitp2.getBinaryData(), READHEX("000000ff000000ff"));
}

////////////////////////////////////////////////////////////////////////////////
TEST(BitReadWriteTest, Reader8)
{
   BitUnpacker<uint8_t> bitu;
   
   bitu.setValue(0xa3);
   EXPECT_TRUE( bitu.getBit());
   EXPECT_FALSE(bitu.getBit());
   EXPECT_TRUE( bitu.getBit());
   EXPECT_EQ(   bitu.getBits(2), 0);
   EXPECT_EQ(   bitu.getBits(3), 3);
}

////////////////////////////////////////////////////////////////////////////////
TEST(BitReadWriteTest, Reader16)
{
   BitUnpacker<uint16_t> bitu;
   
   bitu.setValue(0xa303);
   
   EXPECT_TRUE( bitu.getBit());
   EXPECT_FALSE(bitu.getBit());
   EXPECT_TRUE( bitu.getBit());
   EXPECT_EQ(   bitu.getBits(2), 0);
   EXPECT_EQ(   bitu.getBits(3), 3);
   EXPECT_EQ(   bitu.getBits(8), 3);
}


////////////////////////////////////////////////////////////////////////////////
TEST(BitReadWriteTest, Reader32)
{
   BitUnpacker<uint32_t> bitu(0xffffff00);
   EXPECT_EQ(bitu.getBits(32), 0xffffff00);
}

////////////////////////////////////////////////////////////////////////////////
TEST(BitReadWriteTest, Reader64)
{
   BitUnpacker<uint64_t> bitu(0xffffff00ffffffaaULL);
   EXPECT_EQ( bitu.getBits(64),  0xffffff00ffffffaaULL);
}

////////////////////////////////////////////////////////////////////////////////
TEST(BinaryReadWriteTest, Writer)
{
   BinaryData out = READHEX("01""0100""013200aa""ff00ff00ff00ff00"
                            "ab""fdffff""fe013200aa""ffff00ff00ff00ff00");

   BinaryWriter bw;
   bw.put_uint8_t(1);                       EXPECT_EQ(bw.getSize(), 1);
   bw.put_uint16_t(1);                      EXPECT_EQ(bw.getSize(), 3);
   bw.put_uint32_t(0xaa003201);             EXPECT_EQ(bw.getSize(), 7);
   bw.put_uint64_t(0x00ff00ff00ff00ffULL);  EXPECT_EQ(bw.getSize(), 15);
   bw.put_var_int(0xab);                    EXPECT_EQ(bw.getSize(), 16);
   bw.put_var_int(0xffff);                  EXPECT_EQ(bw.getSize(), 19);
   bw.put_var_int(0xaa003201);              EXPECT_EQ(bw.getSize(), 24);
   bw.put_var_int(0x00ff00ff00ff00ffULL);   EXPECT_EQ(bw.getSize(), 33);

   EXPECT_EQ(bw.getData(), out);
   EXPECT_EQ(bw.getDataRef(), out.getRef());
}

////////////////////////////////////////////////////////////////////////////////
TEST(BinaryReadWriteTest, WriterEndian)
{
   BinaryData out = READHEX("01""0100""013200aa""ff00ff00ff00ff00"
                            "ab""fdffff""fe013200aa""ffff00ff00ff00ff00");

   BinaryWriter bw;
   bw.put_uint8_t(1);                          EXPECT_EQ(bw.getSize(), 1);
   bw.put_uint16_t(0x0100, BE);                EXPECT_EQ(bw.getSize(), 3);
   bw.put_uint32_t(0x013200aa, BE);            EXPECT_EQ(bw.getSize(), 7);
   bw.put_uint64_t(0xff00ff00ff00ff00ULL, BE); EXPECT_EQ(bw.getSize(), 15);
   bw.put_var_int(0xab);                       EXPECT_EQ(bw.getSize(), 16);
   bw.put_var_int(0xffff);                     EXPECT_EQ(bw.getSize(), 19);
   bw.put_var_int(0xaa003201);                 EXPECT_EQ(bw.getSize(), 24);
   bw.put_var_int(0x00ff00ff00ff00ffULL);      EXPECT_EQ(bw.getSize(), 33);
   EXPECT_EQ(bw.getData(), out);
   EXPECT_EQ(bw.getDataRef(), out.getRef());

   BinaryWriter bw2;
   bw2.put_uint8_t(1);                          EXPECT_EQ(bw2.getSize(), 1);
   bw2.put_uint16_t(0x0001, LE);                EXPECT_EQ(bw2.getSize(), 3);
   bw2.put_uint32_t(0xaa003201, LE);            EXPECT_EQ(bw2.getSize(), 7);
   bw2.put_uint64_t(0x00ff00ff00ff00ffULL, LE); EXPECT_EQ(bw2.getSize(), 15);
   bw2.put_var_int(0xab);                       EXPECT_EQ(bw2.getSize(), 16);
   bw2.put_var_int(0xffff);                     EXPECT_EQ(bw2.getSize(), 19);
   bw2.put_var_int(0xaa003201);                 EXPECT_EQ(bw2.getSize(), 24);
   bw2.put_var_int(0x00ff00ff00ff00ffULL);      EXPECT_EQ(bw2.getSize(), 33);
   EXPECT_EQ(bw2.getData(), out);
   EXPECT_EQ(bw2.getDataRef(), out.getRef());
}

////////////////////////////////////////////////////////////////////////////////
TEST(BinaryReadWriteTest, Reader)
{
   BinaryData in = READHEX("01""0100""013200aa""ff00ff00ff00ff00"
                           "ab""fdffff""fe013200aa""ffff00ff00ff00ff00");

   BinaryReader br(in);
   EXPECT_EQ(br.get_uint8_t(), 1);                       
   EXPECT_EQ(br.get_uint16_t(), 1);                      
   EXPECT_EQ(br.get_uint32_t(), 0xaa003201);             
   EXPECT_EQ(br.get_uint64_t(), 0x00ff00ff00ff00ffULL);  
   EXPECT_EQ(br.get_var_int(), 0xab);                   
   EXPECT_EQ(br.get_var_int(), 0xffff);                
   EXPECT_EQ(br.get_var_int(), 0xaa003201);           
   EXPECT_EQ(br.get_var_int(), 0x00ff00ff00ff00ffULL);

   BinaryRefReader brr(in);
   EXPECT_EQ(brr.get_uint8_t(), 1);                       
   EXPECT_EQ(brr.get_uint16_t(), 1);                      
   EXPECT_EQ(brr.get_uint32_t(), 0xaa003201);             
   EXPECT_EQ(brr.get_uint64_t(), 0x00ff00ff00ff00ffULL);  
   EXPECT_EQ(brr.get_var_int(), 0xab);                   
   EXPECT_EQ(brr.get_var_int(), 0xffff);                
   EXPECT_EQ(brr.get_var_int(), 0xaa003201);           
   EXPECT_EQ(brr.get_var_int(), 0x00ff00ff00ff00ffULL);
}

////////////////////////////////////////////////////////////////////////////////
TEST(BinaryReadWriteTest, ReaderEndian)
{
   BinaryData in = READHEX("01""0100""013200aa""ff00ff00ff00ff00"
                           "ab""fdffff""fe013200aa""ffff00ff00ff00ff00");

   BinaryReader br(in);
   EXPECT_EQ(br.get_uint8_t(LE), 1);                       
   EXPECT_EQ(br.get_uint16_t(LE), 1);                      
   EXPECT_EQ(br.get_uint32_t(LE), 0xaa003201);             
   EXPECT_EQ(br.get_uint64_t(LE), 0x00ff00ff00ff00ffULL);  
   EXPECT_EQ(br.get_var_int(), 0xab);                   
   EXPECT_EQ(br.get_var_int(), 0xffff);                
   EXPECT_EQ(br.get_var_int(), 0xaa003201);           
   EXPECT_EQ(br.get_var_int(), 0x00ff00ff00ff00ffULL);

   BinaryRefReader brr(in);
   EXPECT_EQ(brr.get_uint8_t(LE), 1);                       
   EXPECT_EQ(brr.get_uint16_t(LE), 1);                      
   EXPECT_EQ(brr.get_uint32_t(LE), 0xaa003201);             
   EXPECT_EQ(brr.get_uint64_t(LE), 0x00ff00ff00ff00ffULL);  
   EXPECT_EQ(brr.get_var_int(), 0xab);                   
   EXPECT_EQ(brr.get_var_int(), 0xffff);                
   EXPECT_EQ(brr.get_var_int(), 0xaa003201);           
   EXPECT_EQ(brr.get_var_int(), 0x00ff00ff00ff00ffULL);

   BinaryReader br2(in);
   EXPECT_EQ(br2.get_uint8_t(LITTLEENDIAN), 1);                       
   EXPECT_EQ(br2.get_uint16_t(LITTLEENDIAN), 1);                      
   EXPECT_EQ(br2.get_uint32_t(LITTLEENDIAN), 0xaa003201);             
   EXPECT_EQ(br2.get_uint64_t(LITTLEENDIAN), 0x00ff00ff00ff00ffULL);  
   EXPECT_EQ(br2.get_var_int(), 0xab);                   
   EXPECT_EQ(br2.get_var_int(), 0xffff);                
   EXPECT_EQ(br2.get_var_int(), 0xaa003201);           
   EXPECT_EQ(br2.get_var_int(), 0x00ff00ff00ff00ffULL);

   BinaryRefReader brr2(in);
   EXPECT_EQ(brr2.get_uint8_t(LITTLEENDIAN), 1);                       
   EXPECT_EQ(brr2.get_uint16_t(LITTLEENDIAN), 1);                      
   EXPECT_EQ(brr2.get_uint32_t(LITTLEENDIAN), 0xaa003201);             
   EXPECT_EQ(brr2.get_uint64_t(LITTLEENDIAN), 0x00ff00ff00ff00ffULL);  
   EXPECT_EQ(brr2.get_var_int(), 0xab);                   
   EXPECT_EQ(brr2.get_var_int(), 0xffff);                
   EXPECT_EQ(brr2.get_var_int(), 0xaa003201);           
   EXPECT_EQ(brr2.get_var_int(), 0x00ff00ff00ff00ffULL);

   BinaryReader brBE(in);
   EXPECT_EQ(brBE.get_uint8_t(BE), 1);                       
   EXPECT_EQ(brBE.get_uint16_t(BE), 0x0100);                      
   EXPECT_EQ(brBE.get_uint32_t(BE), 0x013200aa);
   EXPECT_EQ(brBE.get_uint64_t(BE), 0xff00ff00ff00ff00ULL);  
   EXPECT_EQ(brBE.get_var_int(), 0xab);                   
   EXPECT_EQ(brBE.get_var_int(), 0xffff);                
   EXPECT_EQ(brBE.get_var_int(), 0xaa003201);           
   EXPECT_EQ(brBE.get_var_int(), 0x00ff00ff00ff00ffULL);

   BinaryRefReader brrBE(in);
   EXPECT_EQ(brrBE.get_uint8_t(BE), 1);                       
   EXPECT_EQ(brrBE.get_uint16_t(BE), 0x0100);                      
   EXPECT_EQ(brrBE.get_uint32_t(BE), 0x013200aa);
   EXPECT_EQ(brrBE.get_uint64_t(BE), 0xff00ff00ff00ff00ULL);  
   EXPECT_EQ(brrBE.get_var_int(), 0xab);                   
   EXPECT_EQ(brrBE.get_var_int(), 0xffff);                
   EXPECT_EQ(brrBE.get_var_int(), 0xaa003201);           
   EXPECT_EQ(brrBE.get_var_int(), 0x00ff00ff00ff00ffULL);

   BinaryReader brBE2(in);
   EXPECT_EQ(brBE2.get_uint8_t(BIGENDIAN), 1);                       
   EXPECT_EQ(brBE2.get_uint16_t(BIGENDIAN), 0x0100);                      
   EXPECT_EQ(brBE2.get_uint32_t(BIGENDIAN), 0x013200aa);
   EXPECT_EQ(brBE2.get_uint64_t(BIGENDIAN), 0xff00ff00ff00ff00ULL);  
   EXPECT_EQ(brBE2.get_var_int(), 0xab);                   
   EXPECT_EQ(brBE2.get_var_int(), 0xffff);                
   EXPECT_EQ(brBE2.get_var_int(), 0xaa003201);           
   EXPECT_EQ(brBE2.get_var_int(), 0x00ff00ff00ff00ffULL);

   BinaryRefReader brrBE2(in);
   EXPECT_EQ(brrBE2.get_uint8_t(BIGENDIAN), 1);                       
   EXPECT_EQ(brrBE2.get_uint16_t(BIGENDIAN), 0x0100);                      
   EXPECT_EQ(brrBE2.get_uint32_t(BIGENDIAN), 0x013200aa);
   EXPECT_EQ(brrBE2.get_uint64_t(BIGENDIAN), 0xff00ff00ff00ff00ULL);  
   EXPECT_EQ(brrBE2.get_var_int(), 0xab);                   
   EXPECT_EQ(brrBE2.get_var_int(), 0xffff);                
   EXPECT_EQ(brrBE2.get_var_int(), 0xaa003201);           
   EXPECT_EQ(brrBE2.get_var_int(), 0x00ff00ff00ff00ffULL);
}

////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
class BtcUtilsTest : public ::testing::Test
{
protected:
   virtual void SetUp(void) 
   {
      rawHead_ = READHEX(
         "010000001d8f4ec0443e1f19f305e488c1085c95de7cc3fd25e0d2c5bb5d0000"
         "000000009762547903d36881a86751f3f5049e23050113f779735ef82734ebf0"
         "b4450081d8c8c84db3936a1a334b035b");
      headHashLE_ = READHEX(
         "1195e67a7a6d0674bbd28ae096d602e1f038c8254b49dfe79d47000000000000");
      headHashBE_ = READHEX(
         "000000000000479de7df494b25c838f0e102d696e08ad2bb74066d7a7ae69511");

      satoshiPubKey_ = READHEX( "04"
         "fc9702847840aaf195de8442ebecedf5b095cdbb9bc716bda9110971b28a49e0"
         "ead8564ff0db22209e0374782c093bb899692d524e9d6a6956e7c5ecbcd68284");
      satoshiHash160_ = READHEX("65a4358f4691660849d9f235eb05f11fabbd69fa");

      prevHashCB_  = READHEX(
         "0000000000000000000000000000000000000000000000000000000000000000");
      prevHashReg_ = READHEX(
         "894862e362905c6075074d9ec4b4e2dc34720089b1e9ef4738ee1b13f3bdcdb7");
   }

   BinaryData rawHead_;
   BinaryData headHashLE_;
   BinaryData headHashBE_;

   BinaryData satoshiPubKey_;
   BinaryData satoshiHash160_;

   BinaryData prevHashCB_;
   BinaryData prevHashReg_;
};




TEST_F(BtcUtilsTest, ReadVarInt)
{
   BinaryData vi0 = READHEX("00");
   BinaryData vi1 = READHEX("21");
   BinaryData vi3 = READHEX("fdff00");
   BinaryData vi5 = READHEX("fe00000100");
   BinaryData vi9 = READHEX("ff0010a5d4e8000000");

   uint64_t v = 0;
   uint64_t w = 33;
   uint64_t x = 255;
   uint64_t y = 65536;
   uint64_t z = 1000000000000ULL;

   BinaryRefReader brr;
   pair<uint64_t, uint8_t> a;

   brr.setNewData(vi0);
   a = BtcUtils::readVarInt(brr);
   EXPECT_EQ(a.first,   v);
   EXPECT_EQ(a.second,  1);

   brr.setNewData(vi1);
   a = BtcUtils::readVarInt(brr);
   EXPECT_EQ(a.first,   w);
   EXPECT_EQ(a.second,  1);

   brr.setNewData(vi3);
   a = BtcUtils::readVarInt(brr);
   EXPECT_EQ(a.first,   x);
   EXPECT_EQ(a.second,  3);

   brr.setNewData(vi5);
   a = BtcUtils::readVarInt(brr);
   EXPECT_EQ(a.first,   y);
   EXPECT_EQ(a.second,  5);

   brr.setNewData(vi9);
   a = BtcUtils::readVarInt(brr);
   EXPECT_EQ(a.first,   z);
   EXPECT_EQ(a.second,  9);

   // Just the length
   EXPECT_EQ(BtcUtils::readVarIntLength(vi0.getPtr()), 1);
   EXPECT_EQ(BtcUtils::readVarIntLength(vi1.getPtr()), 1);
   EXPECT_EQ(BtcUtils::readVarIntLength(vi3.getPtr()), 3);
   EXPECT_EQ(BtcUtils::readVarIntLength(vi5.getPtr()), 5);
   EXPECT_EQ(BtcUtils::readVarIntLength(vi9.getPtr()), 9);

   EXPECT_EQ(BtcUtils::calcVarIntSize(v), 1);
   EXPECT_EQ(BtcUtils::calcVarIntSize(w), 1);
   EXPECT_EQ(BtcUtils::calcVarIntSize(x), 3);
   EXPECT_EQ(BtcUtils::calcVarIntSize(y), 5);
   EXPECT_EQ(BtcUtils::calcVarIntSize(z), 9);
}


TEST_F(BtcUtilsTest, Num2Str)
{
   EXPECT_EQ(BtcUtils::numToStrWCommas(0),         string("0"));
   EXPECT_EQ(BtcUtils::numToStrWCommas(100),       string("100"));
   EXPECT_EQ(BtcUtils::numToStrWCommas(-100),      string("-100"));
   EXPECT_EQ(BtcUtils::numToStrWCommas(999),       string("999"));
   EXPECT_EQ(BtcUtils::numToStrWCommas(1234),      string("1,234"));
   EXPECT_EQ(BtcUtils::numToStrWCommas(-1234),     string("-1,234"));
   EXPECT_EQ(BtcUtils::numToStrWCommas(12345678),  string("12,345,678"));
   EXPECT_EQ(BtcUtils::numToStrWCommas(-12345678), string("-12,345,678"));
}



TEST_F(BtcUtilsTest, PackBits)
{
   list<bool>::iterator iter, iter2;
   list<bool> bitList;

   bitList = BtcUtils::UnpackBits( READHEX("00"), 0);
   EXPECT_EQ(bitList.size(), 0);

   bitList = BtcUtils::UnpackBits( READHEX("00"), 3);
   EXPECT_EQ(bitList.size(), 3);
   iter = bitList.begin(); 
   EXPECT_FALSE(*iter);  iter++;
   EXPECT_FALSE(*iter);  iter++;
   EXPECT_FALSE(*iter);  iter++;
   
   
   bitList = BtcUtils::UnpackBits( READHEX("00"), 8);
   EXPECT_EQ(bitList.size(), 8);
   iter = bitList.begin(); 
   EXPECT_FALSE(*iter);  iter++;
   EXPECT_FALSE(*iter);  iter++;
   EXPECT_FALSE(*iter);  iter++;
   EXPECT_FALSE(*iter);  iter++;
   EXPECT_FALSE(*iter);  iter++;
   EXPECT_FALSE(*iter);  iter++;
   EXPECT_FALSE(*iter);  iter++;
   EXPECT_FALSE(*iter);  iter++;

   bitList = BtcUtils::UnpackBits( READHEX("017f"), 8);
   EXPECT_EQ(bitList.size(), 8);
   iter = bitList.begin(); 
   EXPECT_FALSE(*iter);  iter++;
   EXPECT_FALSE(*iter);  iter++;
   EXPECT_FALSE(*iter);  iter++;
   EXPECT_FALSE(*iter);  iter++;
   EXPECT_FALSE(*iter);  iter++;
   EXPECT_FALSE(*iter);  iter++;
   EXPECT_FALSE(*iter);  iter++;
   EXPECT_TRUE( *iter);  iter++;


   bitList = BtcUtils::UnpackBits( READHEX("017f"), 12);
   EXPECT_EQ(bitList.size(), 12);
   iter = bitList.begin(); 
   EXPECT_FALSE(*iter);  iter++;
   EXPECT_FALSE(*iter);  iter++;
   EXPECT_FALSE(*iter);  iter++;
   EXPECT_FALSE(*iter);  iter++;
   EXPECT_FALSE(*iter);  iter++;
   EXPECT_FALSE(*iter);  iter++;
   EXPECT_FALSE(*iter);  iter++;
   EXPECT_TRUE( *iter);  iter++;
   EXPECT_FALSE(*iter);  iter++;
   EXPECT_TRUE( *iter);  iter++;
   EXPECT_TRUE( *iter);  iter++;
   EXPECT_TRUE( *iter);  iter++;

   bitList = BtcUtils::UnpackBits( READHEX("017f"), 16);
   EXPECT_EQ(bitList.size(), 16);
   iter = bitList.begin(); 
   EXPECT_FALSE(*iter);  iter++;
   EXPECT_FALSE(*iter);  iter++;
   EXPECT_FALSE(*iter);  iter++;
   EXPECT_FALSE(*iter);  iter++;
   EXPECT_FALSE(*iter);  iter++;
   EXPECT_FALSE(*iter);  iter++;
   EXPECT_FALSE(*iter);  iter++;
   EXPECT_TRUE( *iter);  iter++;
   EXPECT_FALSE(*iter);  iter++;
   EXPECT_TRUE( *iter);  iter++;
   EXPECT_TRUE( *iter);  iter++;
   EXPECT_TRUE( *iter);  iter++;
   EXPECT_TRUE( *iter);  iter++;
   EXPECT_TRUE( *iter);  iter++;
   EXPECT_TRUE( *iter);  iter++;
   EXPECT_TRUE( *iter);  iter++;


   BinaryData packed;
   packed = BtcUtils::PackBits(bitList);
   EXPECT_EQ(packed, READHEX("017f"));

   bitList = BtcUtils::UnpackBits( READHEX("017f"), 12);
   packed = BtcUtils::PackBits(bitList);
   EXPECT_EQ(packed, READHEX("0170"));
}



////////////////////////////////////////////////////////////////////////////////
TEST_F(BtcUtilsTest, SimpleHash)
{
   BinaryData hashOut; 

   // sha256(sha256(X));
   BtcUtils::getHash256(rawHead_.getPtr(), rawHead_.getSize(), hashOut);
   EXPECT_EQ(hashOut, headHashLE_);
   EXPECT_EQ(hashOut, headHashBE_.copySwapEndian());

   BtcUtils::getHash256_NoSafetyCheck(rawHead_.getPtr(), rawHead_.getSize(), hashOut);
   EXPECT_EQ(hashOut, headHashLE_);
   EXPECT_EQ(hashOut, headHashBE_.copySwapEndian());

   hashOut = BtcUtils::getHash256(rawHead_.getPtr(), rawHead_.getSize());
   EXPECT_EQ(hashOut, headHashLE_);

   BtcUtils::getHash256(rawHead_, hashOut);
   EXPECT_EQ(hashOut, headHashLE_);

   BtcUtils::getHash256(rawHead_.getRef(), hashOut);
   EXPECT_EQ(hashOut, headHashLE_);

   hashOut = BtcUtils::getHash256(rawHead_);
   EXPECT_EQ(hashOut, headHashLE_);

   
   // ripemd160(sha256(X));
   BtcUtils::getHash160(satoshiPubKey_.getPtr(), satoshiPubKey_.getSize(), hashOut);
   EXPECT_EQ(hashOut, satoshiHash160_);

   BtcUtils::getHash160(satoshiPubKey_.getPtr(), satoshiPubKey_.getSize(), hashOut);
   EXPECT_EQ(hashOut, satoshiHash160_);

   hashOut = BtcUtils::getHash160(satoshiPubKey_.getPtr(), satoshiPubKey_.getSize());
   EXPECT_EQ(hashOut, satoshiHash160_);

   BtcUtils::getHash160(satoshiPubKey_, hashOut);
   EXPECT_EQ(hashOut, satoshiHash160_);

   BtcUtils::getHash160(satoshiPubKey_.getRef(), hashOut);
   EXPECT_EQ(hashOut, satoshiHash160_);

   hashOut = BtcUtils::getHash160(satoshiPubKey_);
   EXPECT_EQ(hashOut, satoshiHash160_);
}



////////////////////////////////////////////////////////////////////////////////
TEST_F(BtcUtilsTest, TxOutScriptID_Hash160)
{
   //TXOUT_SCRIPT_STDHASH160,
   //TXOUT_SCRIPT_STDPUBKEY65,
   //TXOUT_SCRIPT_STDPUBKEY33,
   //TXOUT_SCRIPT_MULTISIG,
   //TXOUT_SCRIPT_P2SH,
   //TXOUT_SCRIPT_NONSTANDARD,

   BinaryData script = READHEX("76a914a134408afa258a50ed7a1d9817f26b63cc9002cc88ac");
   BinaryData a160   = READHEX(  "a134408afa258a50ed7a1d9817f26b63cc9002cc");
   BinaryData unique = READHEX("00a134408afa258a50ed7a1d9817f26b63cc9002cc");
   TXOUT_SCRIPT_TYPE scrType = BtcUtils::getTxOutScriptType(script);
   EXPECT_EQ(scrType, TXOUT_SCRIPT_STDHASH160 );
   EXPECT_EQ(BtcUtils::getTxOutRecipientAddr(script), a160 );
   EXPECT_EQ(BtcUtils::getTxOutRecipientAddr(script, scrType), a160 );
   EXPECT_EQ(BtcUtils::getTxOutScriptUniqueKey(script), unique );
   EXPECT_EQ(BtcUtils::getTxOutScriptUniqueKey(script, scrType), unique );
}

////////////////////////////////////////////////////////////////////////////////
TEST_F(BtcUtilsTest, TxOutScriptID_PubKey65)
{
   BinaryData script = READHEX(
      "4104b0bd634234abbb1ba1e986e884185c61cf43e001f9137f23c2c409273eb1"
      "6e6537a576782eba668a7ef8bd3b3cfb1edb7117ab65129b8a2e681f3c1e0908ef7bac");
   BinaryData a160   = READHEX(  "e24b86bff5112623ba67c63b6380636cbdf1a66d");
   BinaryData unique = READHEX("00e24b86bff5112623ba67c63b6380636cbdf1a66d");
   TXOUT_SCRIPT_TYPE scrType = BtcUtils::getTxOutScriptType(script);
   EXPECT_EQ(scrType, TXOUT_SCRIPT_STDPUBKEY65 );
   EXPECT_EQ(BtcUtils::getTxOutRecipientAddr(script), a160 );
   EXPECT_EQ(BtcUtils::getTxOutRecipientAddr(script, scrType), a160 );
   EXPECT_EQ(BtcUtils::getTxOutScriptUniqueKey(script), unique );
   EXPECT_EQ(BtcUtils::getTxOutScriptUniqueKey(script, scrType), unique );
}

////////////////////////////////////////////////////////////////////////////////
TEST_F(BtcUtilsTest, TxOutScriptID_PubKey33)
{
   BinaryData script = READHEX(
      "21024005c945d86ac6b01fb04258345abea7a845bd25689edb723d5ad4068ddd3036ac");
   BinaryData a160   = READHEX(  "0c1b83d01d0ffb2bccae606963376cca3863a7ce");
   BinaryData unique = READHEX("000c1b83d01d0ffb2bccae606963376cca3863a7ce");
   TXOUT_SCRIPT_TYPE scrType = BtcUtils::getTxOutScriptType(script);
   EXPECT_EQ(scrType, TXOUT_SCRIPT_STDPUBKEY33 );
   EXPECT_EQ(BtcUtils::getTxOutRecipientAddr(script), a160 );
   EXPECT_EQ(BtcUtils::getTxOutRecipientAddr(script, scrType), a160 );
   EXPECT_EQ(BtcUtils::getTxOutScriptUniqueKey(script), unique );
   EXPECT_EQ(BtcUtils::getTxOutScriptUniqueKey(script, scrType), unique );
}

////////////////////////////////////////////////////////////////////////////////
TEST_F(BtcUtilsTest, TxOutScriptID_NonStd)
{
   // This was from block 150951 which was erroneously produced by MagicalTux
   // This is not only non-standard, it's non-spendable
   BinaryData script = READHEX("76a90088ac");
   BinaryData a160   = BtcUtils::BadAddress_;
   BinaryData unique = READHEX("ff") + BtcUtils::getHash160(READHEX("76a90088ac"));
   TXOUT_SCRIPT_TYPE scrType = BtcUtils::getTxOutScriptType(script);
   EXPECT_EQ(scrType, TXOUT_SCRIPT_NONSTANDARD );
   EXPECT_EQ(BtcUtils::getTxOutRecipientAddr(script), a160 );
   EXPECT_EQ(BtcUtils::getTxOutRecipientAddr(script, scrType), a160 );
   EXPECT_EQ(BtcUtils::getTxOutScriptUniqueKey(script), unique );
   EXPECT_EQ(BtcUtils::getTxOutScriptUniqueKey(script, scrType), unique );
}

////////////////////////////////////////////////////////////////////////////////
TEST_F(BtcUtilsTest, TxOutScriptID_P2SH)
{
   // P2SH script from tx: 4ac04b4830d115eb9a08f320ef30159cc107dfb72b29bbc2f370093f962397b4 (TxOut: 1)
   // Spent in tx:         fd16d6bbf1a3498ca9777b9d31ceae883eb8cb6ede1fafbdd218bae107de66fe (TxIn: 1)
   // P2SH address:        3Lip6sxQymNr9LD2cAVp6wLrw8xdKBdYFG
   // Hash160:             d0c15a7d41500976056b3345f542d8c944077c8a
   BinaryData script = READHEX("a914d0c15a7d41500976056b3345f542d8c944077c8a87"); // send to P2SH
   BinaryData a160 =   READHEX(  "d0c15a7d41500976056b3345f542d8c944077c8a");
   BinaryData unique = READHEX("05d0c15a7d41500976056b3345f542d8c944077c8a");
   TXOUT_SCRIPT_TYPE scrType = BtcUtils::getTxOutScriptType(script);
   EXPECT_EQ(scrType, TXOUT_SCRIPT_P2SH);
   EXPECT_EQ(BtcUtils::getTxOutRecipientAddr(script), a160 );
   EXPECT_EQ(BtcUtils::getTxOutRecipientAddr(script, scrType), a160 );
   EXPECT_EQ(BtcUtils::getTxOutScriptUniqueKey(script), unique );
   EXPECT_EQ(BtcUtils::getTxOutScriptUniqueKey(script, scrType), unique );
}

////////////////////////////////////////////////////////////////////////////////
TEST_F(BtcUtilsTest, TxOutScriptID_Multisig)
{
   BinaryData script = READHEX(
      "5221034758cefcb75e16e4dfafb32383b709fa632086ea5ca982712de6add93"
      "060b17a2103fe96237629128a0ae8c3825af8a4be8fe3109b16f62af19cec0b1"
      "eb93b8717e252ae");
   BinaryData pub1   = READHEX("034758cefcb75e16e4dfafb32383b709fa632086ea5ca982712de6add93060b17a");
   BinaryData pub2   = READHEX("03fe96237629128a0ae8c3825af8a4be8fe3109b16f62af19cec0b1eb93b8717e2");
   BinaryData addr1  = READHEX("785652a6b8e721e80ffa353e5dfd84f0658284a9");
   BinaryData addr2  = READHEX("b3348abf9dd2d1491359f937e2af64b1bb6d525a");
   BinaryData a160   = BtcUtils::BadAddress_;
   BinaryData unique = READHEX(
      "fe0202785652a6b8e721e80ffa353e5dfd84f0658284a9b3348abf9dd2d14913"
      "59f937e2af64b1bb6d525a");

   TXOUT_SCRIPT_TYPE scrType = BtcUtils::getTxOutScriptType(script);
   EXPECT_EQ(scrType, TXOUT_SCRIPT_MULTISIG);
   EXPECT_EQ(BtcUtils::getTxOutRecipientAddr(script), a160 );
   EXPECT_EQ(BtcUtils::getTxOutRecipientAddr(script, scrType), a160 );
   EXPECT_EQ(BtcUtils::getTxOutScriptUniqueKey(script), unique );
   EXPECT_EQ(BtcUtils::getTxOutScriptUniqueKey(script, scrType), unique );
}


////////////////////////////////////////////////////////////////////////////////
TEST_F(BtcUtilsTest, TxOutScriptID_MultiList)
{
   BinaryData script = READHEX(
      "5221034758cefcb75e16e4dfafb32383b709fa632086ea5ca982712de6add930"
      "60b17a2103fe96237629128a0ae8c3825af8a4be8fe3109b16f62af19cec0b1e"
      "b93b8717e252ae");
   BinaryData addr0  = READHEX("785652a6b8e721e80ffa353e5dfd84f0658284a9");
   BinaryData addr1  = READHEX("b3348abf9dd2d1491359f937e2af64b1bb6d525a");
   BinaryData a160   = BtcUtils::BadAddress_;
   BinaryData unique = READHEX(
      "fe0202785652a6b8e721e80ffa353e5dfd84f0658284a9b3348abf9dd2d14913"
      "59f937e2af64b1bb6d525a");

   vector<BinaryData> a160List;
   uint32_t M;

   M = BtcUtils::getMultisigAddrList(script, a160List);
   EXPECT_EQ(M, 2);              
   EXPECT_EQ(a160List.size(), 2); // N
   
   EXPECT_EQ(a160List[0], addr0);
   EXPECT_EQ(a160List[1], addr1);
}


//TEST_F(BtcUtilsTest, TxInScriptID)
//{
   //TXIN_SCRIPT_STDUNCOMPR,
   //TXIN_SCRIPT_STDCOMPR,
   //TXIN_SCRIPT_COINBASE,
   //TXIN_SCRIPT_SPENDPUBKEY,
   //TXIN_SCRIPT_SPENDMULTI,
   //TXIN_SCRIPT_SPENDP2SH,
   //TXIN_SCRIPT_NONSTANDARD
//}
 
////////////////////////////////////////////////////////////////////////////////
TEST_F(BtcUtilsTest, TxInScriptID_StdUncompr)
{
   BinaryData script = READHEX(
      "493046022100b9daf2733055be73ae00ee0c5d78ca639d554fe779f163396c1a"
      "39b7913e7eac02210091f0deeb2e510c74354afb30cc7d8fbac81b1ca8b39406"
      "13379adc41a6ffd226014104b1537fa5bc2242d25ebf54f31e76ebabe0b3de4a"
      "4dccd9004f058d6c2caa5d31164252e1e04e5df627fae7adec27fa9d40c271fc"
      "4d30ff375ef6b26eba192bac");
   BinaryData a160 = READHEX("c42a8290196b2c5bcb35471b45aa0dc096baed5e");
   BinaryData prevHash = prevHashReg_;

   TXIN_SCRIPT_TYPE scrType = BtcUtils::getTxInScriptType( script, prevHash);
   EXPECT_EQ(scrType,  TXIN_SCRIPT_STDUNCOMPR);
   EXPECT_EQ(BtcUtils::getTxInAddr(script, prevHash), a160);
   EXPECT_EQ(BtcUtils::getTxInAddr(script, prevHash, scrType), a160);
   EXPECT_EQ(BtcUtils::getTxInAddrFromType(script,  scrType), a160);
}

////////////////////////////////////////////////////////////////////////////////
TEST_F(BtcUtilsTest, TxInScriptID_StdCompr)
{
   BinaryData script = READHEX(
      "47304402205299224886e5e3402b0e9fa3527bcfe1d73c4e2040f18de8dd17f1"
      "16e3365a1102202590dcc16c4b711daae6c37977ba579ca65bcaa8fba2bd7168"
      "a984be727ccf7a01210315122ff4d41d9fe3538a0a8c6c7f813cf12a901069a4"
      "3d6478917246dc92a782");
   BinaryData a160 = READHEX("03214fc1433a287e964d6c4242093c34e4ed0001");
   BinaryData prevHash = prevHashReg_;

   TXIN_SCRIPT_TYPE scrType = BtcUtils::getTxInScriptType(script, prevHash);
   EXPECT_EQ(scrType,  TXIN_SCRIPT_STDCOMPR);
   EXPECT_EQ(BtcUtils::getTxInAddr(script, prevHash), a160);
   EXPECT_EQ(BtcUtils::getTxInAddr(script, prevHash, scrType), a160);
   EXPECT_EQ(BtcUtils::getTxInAddrFromType(script,  scrType), a160);
}


////////////////////////////////////////////////////////////////////////////////
TEST_F(BtcUtilsTest, TxInScriptID_Coinbase)
{
   BinaryData script = READHEX(
      "0310920304000071c3124d696e656420627920425443204775696c640800b75f950e000000");
   BinaryData a160 =  BtcUtils::BadAddress_;
   BinaryData prevHash = prevHashCB_;

   TXIN_SCRIPT_TYPE scrType = BtcUtils::getTxInScriptType(script, prevHash);
   EXPECT_EQ(scrType, TXIN_SCRIPT_COINBASE);
   EXPECT_EQ(BtcUtils::getTxInAddr(script, prevHash), a160);
   EXPECT_EQ(BtcUtils::getTxInAddr(script, prevHash, scrType), a160);
   EXPECT_EQ(BtcUtils::getTxInAddrFromType(script,  scrType), a160);
}

////////////////////////////////////////////////////////////////////////////////
TEST_F(BtcUtilsTest, TxInScriptID_SpendPubKey)
{
   BinaryData script = READHEX(
      "47304402201ffc44394e5a3dd9c8b55bdc12147e18574ac945d15dac026793bf"
      "3b8ff732af022035fd832549b5176126f735d87089c8c1c1319447a458a09818"
      "e173eaf0c2eef101");
   BinaryData a160 =  BtcUtils::BadAddress_;
   BinaryData prevHash = prevHashReg_;

   TXIN_SCRIPT_TYPE scrType = BtcUtils::getTxInScriptType(script, prevHash);
   EXPECT_EQ(scrType, TXIN_SCRIPT_SPENDPUBKEY);
   EXPECT_EQ(BtcUtils::getTxInAddr(script, prevHash), a160);
   EXPECT_EQ(BtcUtils::getTxInAddr(script, prevHash, scrType), a160);
   EXPECT_EQ(BtcUtils::getTxInAddrFromType(script,  scrType), a160);
   //txInHash160s.push_back( READHEX("957efec6af757ccbbcf9a436f0083c5ddaa3bf1d")); // this one can't be determined
}



////////////////////////////////////////////////////////////////////////////////
TEST_F(BtcUtilsTest, TxInScriptID_SpendMultisig)
{

   BinaryData script = READHEX(
      "004830450221009254113fa46918f299b1d18ec918613e56cffbeba0960db05f"
      "66b51496e5bf3802201e229de334bd753a2b08b36cc3f38f5263a23e9714a737"
      "520db45494ec095ce80148304502206ee62f539d5cd94f990b7abfda77750f58"
      "ff91043c3f002501e5448ef6dba2520221009d29229cdfedda1dd02a1a90bb71"
      "b30b77e9c3fc28d1353f054c86371f6c2a8101");
   BinaryData a160 =  BtcUtils::BadAddress_;
   BinaryData prevHash = prevHashReg_;
   TXIN_SCRIPT_TYPE scrType = BtcUtils::getTxInScriptType(script, prevHash);
   EXPECT_EQ(scrType, TXIN_SCRIPT_SPENDMULTI);
   EXPECT_EQ(BtcUtils::getTxInAddr(script, prevHash), a160);
   EXPECT_EQ(BtcUtils::getTxInAddr(script, prevHash, scrType), a160);
   EXPECT_EQ(BtcUtils::getTxInAddrFromType(script,  scrType), a160);


   vector<BinaryDataRef> scrParts = BtcUtils::splitPushOnlyScriptRefs(script);
   BinaryData zero = READHEX("00");
   BinaryData sig1 = READHEX(
      "30450221009254113fa46918f299b1d18ec918613e56cffbeba0960db05f66b5"
      "1496e5bf3802201e229de334bd753a2b08b36cc3f38f5263a23e9714a737520d"
      "b45494ec095ce801");
   BinaryData sig2 = READHEX(
      "304502206ee62f539d5cd94f990b7abfda77750f58ff91043c3f002501e5448e"
      "f6dba2520221009d29229cdfedda1dd02a1a90bb71b30b77e9c3fc28d1353f05"
      "4c86371f6c2a8101");

   EXPECT_EQ(scrParts.size(), 3);
   EXPECT_EQ(scrParts[0], zero);
   EXPECT_EQ(scrParts[1], sig1);
   EXPECT_EQ(scrParts[2], sig2);

   //BinaryData p2sh = READHEX("5221034758cefcb75e16e4dfafb32383b709fa632086ea5ca982712de6add93060b17a2103fe96237629128a0ae8c3825af8a4be8fe3109b16f62af19cec0b1eb93b8717e252ae");
   //BinaryData pub1 = READHEX("034758cefcb75e16e4dfafb32383b709fa632086ea5ca982712de6add93060b17a");
   //BinaryData pub1 = READHEX("03fe96237629128a0ae8c3825af8a4be8fe3109b16f62af19cec0b1eb93b8717e2");

   
}

////////////////////////////////////////////////////////////////////////////////
TEST_F(BtcUtilsTest, TxInScriptID_SpendP2SH)
{

   // Spending P2SH output as above:  fd16d6bbf1a3498ca9777b9d31ceae883eb8cb6ede1fafbdd218bae107de66fe (TxIn: 1, 219 B)
   // Leading 0x00 byte is required due to a bug in OP_CHECKMULTISIG
   BinaryData script = READHEX(
      "004830450221009254113fa46918f299b1d18ec918613e56cffbeba0960db05f"
      "66b51496e5bf3802201e229de334bd753a2b08b36cc3f38f5263a23e9714a737"
      "520db45494ec095ce80148304502206ee62f539d5cd94f990b7abfda77750f58"
      "ff91043c3f002501e5448ef6dba2520221009d29229cdfedda1dd02a1a90bb71"
      "b30b77e9c3fc28d1353f054c86371f6c2a8101475221034758cefcb75e16e4df"
      "afb32383b709fa632086ea5ca982712de6add93060b17a2103fe96237629128a"
      "0ae8c3825af8a4be8fe3109b16f62af19cec0b1eb93b8717e252ae");
   BinaryData a160 =  READHEX("d0c15a7d41500976056b3345f542d8c944077c8a");
   BinaryData prevHash = prevHashReg_;
   TXIN_SCRIPT_TYPE scrType = BtcUtils::getTxInScriptType(script, prevHash);
   EXPECT_EQ(scrType, TXIN_SCRIPT_SPENDP2SH);
   EXPECT_EQ(BtcUtils::getTxInAddr(script, prevHash), a160);
   EXPECT_EQ(BtcUtils::getTxInAddr(script, prevHash, scrType), a160);
   EXPECT_EQ(BtcUtils::getTxInAddrFromType(script,  scrType), a160);
}



////////////////////////////////////////////////////////////////////////////////
TEST_F(BtcUtilsTest, BitsToDifficulty)
{

   double a = BtcUtils::convertDiffBitsToDouble(READHEX("ffff001d"));
   double b = BtcUtils::convertDiffBitsToDouble(READHEX("be2f021a"));
   double c = BtcUtils::convertDiffBitsToDouble(READHEX("3daa011a"));
   
   EXPECT_DOUBLE_EQ(a, 1.0);
   EXPECT_DOUBLE_EQ(b, 7672999.920164138);
   EXPECT_DOUBLE_EQ(c, 10076292.883418716);
}


////////////////////////////////////////////////////////////////////////////////
TEST_F(BtcUtilsTest, ScriptToOpCodes)
{
   BinaryData complexScript = READHEX(
      "526b006b7dac7ca9143cd1def404e12a85ead2b4d3f5f9f817fb0d46ef879a6c"
      "936b7dac7ca9146a4e7d5f798e90e84db9244d4805459f87275943879a6c936b"
      "7dac7ca914486efdd300987a054510b4ce1148d4ad290d911e879a6c936b6c6ca2");

   vector<string> opstr;
   opstr.reserve(40);
   opstr.push_back(string("OP_2"));
   opstr.push_back(string("OP_TOALTSTACK"));
   opstr.push_back(string("OP_0"));
   opstr.push_back(string("OP_TOALTSTACK"));
   opstr.push_back(string("OP_TUCK"));
   opstr.push_back(string("OP_CHECKSIG"));
   opstr.push_back(string("OP_SWAP"));
   opstr.push_back(string("OP_HASH160"));
   opstr.push_back(string("[PUSHDATA -- 20 BYTES:]"));
   opstr.push_back(string("3cd1def404e12a85ead2b4d3f5f9f817fb0d46ef"));
   opstr.push_back(string("OP_EQUAL"));
   opstr.push_back(string("OP_BOOLAND"));
   opstr.push_back(string("OP_FROMALTSTACK"));
   opstr.push_back(string("OP_ADD"));
   opstr.push_back(string("OP_TOALTSTACK"));
   opstr.push_back(string("OP_TUCK"));
   opstr.push_back(string("OP_CHECKSIG"));
   opstr.push_back(string("OP_SWAP"));
   opstr.push_back(string("OP_HASH160"));
   opstr.push_back(string("[PUSHDATA -- 20 BYTES:]"));
   opstr.push_back(string("6a4e7d5f798e90e84db9244d4805459f87275943"));
   opstr.push_back(string("OP_EQUAL"));
   opstr.push_back(string("OP_BOOLAND"));
   opstr.push_back(string("OP_FROMALTSTACK"));
   opstr.push_back(string("OP_ADD"));
   opstr.push_back(string("OP_TOALTSTACK"));
   opstr.push_back(string("OP_TUCK"));
   opstr.push_back(string("OP_CHECKSIG"));
   opstr.push_back(string("OP_SWAP"));
   opstr.push_back(string("OP_HASH160"));
   opstr.push_back(string("[PUSHDATA -- 20 BYTES:]"));
   opstr.push_back(string("486efdd300987a054510b4ce1148d4ad290d911e"));
   opstr.push_back(string("OP_EQUAL"));
   opstr.push_back(string("OP_BOOLAND"));
   opstr.push_back(string("OP_FROMALTSTACK"));
   opstr.push_back(string("OP_ADD"));
   opstr.push_back(string("OP_TOALTSTACK"));
   opstr.push_back(string("OP_FROMALTSTACK"));
   opstr.push_back(string("OP_FROMALTSTACK"));
   opstr.push_back(string("OP_GREATERTHANOREQUAL"));

   vector<string> output = BtcUtils::convertScriptToOpStrings(complexScript);
   ASSERT_EQ(output.size(), opstr.size());
   for(uint32_t i=0; i<opstr.size(); i++)
      EXPECT_EQ(output[i], opstr[i]);
}



////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
class BlockObjTest : public ::testing::Test
{
protected:
   virtual void SetUp(void) 
   {
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
         // Header (80 bytes in 6 fields)
         "01000000"
         "eb10c9a996a2340a4d74eaab41421ed8664aa49d18538bab5901000000000000"
         "5a2f06efa9f2bd804f17877537f2080030cadbfa1eb50e02338117cc604d91b9"
         "b7541a4e"
         "cfbb0a1a"
         "64f1ade7"
         // NumTx (3)
         "03"
         // Tx0 (Coinbase)
         "0100000001000000000000000000000000000000000000000000000000000000"
         "0000000000ffffffff0804cfbb0a1a02360affffffff0100f2052a0100000043"
         "4104c2239c4eedb3beb26785753463be3ec62b82f6acd62efb65f452f8806f2e"
         "de0b338e31d1f69b1ce449558d7061aa1648ddc2bf680834d3986624006a272d"
         "c21cac00000000"
         // Tx1 (Regular)
         "0100000003e8caa12bcb2e7e86499c9de49c45c5a1c6167ea4"
         "b894c8c83aebba1b6100f343010000008c493046022100e2f5af5329d1244807"
         "f8347a2c8d9acc55a21a5db769e9274e7e7ba0bb605b26022100c34ca3350df5"
         "089f3415d8af82364d7f567a6a297fcc2c1d2034865633238b8c014104129e42"
         "2ac490ddfcb7b1c405ab9fb42441246c4bca578de4f27b230de08408c64cad03"
         "af71ee8a3140b40408a7058a1984a9f246492386113764c1ac132990d1ffffff"
         "ff5b55c18864e16c08ef9989d31c7a343e34c27c30cd7caa759651b0e08cae01"
         "06000000008c4930460221009ec9aa3e0caf7caa321723dea561e232603e0068"
         "6d4bfadf46c5c7352b07eb00022100a4f18d937d1e2354b2e69e02b18d11620a"
         "6a9332d563e9e2bbcb01cee559680a014104411b35dd963028300e36e82ee8cf"
         "1b0c8d5bf1fc4273e970469f5cb931ee07759a2de5fef638961726d04bd5eb4e"
         "5072330b9b371e479733c942964bb86e2b22ffffffff3de0c1e913e6271769d8"
         "c0172cea2f00d6d3240afc3a20f9fa247ce58af30d2a010000008c4930460221"
         "00b610e169fd15ac9f60fe2b507529281cf2267673f4690ba428cbb2ba3c3811"
         "fd022100ffbe9e3d71b21977a8e97fde4c3ba47b896d08bc09ecb9d086bb5917"
         "5b5b9f03014104ff07a1833fd8098b25f48c66dcf8fde34cbdbcc0f5f21a8c20"
         "05b160406cbf34cc432842c6b37b2590d16b165b36a3efc9908d65fb0e605314"
         "c9b278f40f3e1affffffff0240420f00000000001976a914adfa66f57ded1b65"
         "5eb4ccd96ee07ca62bc1ddfd88ac007d6a7d040000001976a914981a0c9ae61f"
         "a8f8c96ae6f8e383d6e07e77133e88ac00000000"
         // Tx2 (Regular)
         "010000000138e7586e078428"
         "0df58bd3dc5e3d350c9036b1ec4107951378f45881799c92a4000000008a4730"
         "4402207c945ae0bbdaf9dadba07bdf23faa676485a53817af975ddf85a104f76"
         "4fb93b02201ac6af32ddf597e610b4002e41f2de46664587a379a0161323a853"
         "89b4f82dda014104ec8883d3e4f7a39d75c9f5bb9fd581dc9fb1b7cdf7d6b5a6"
         "65e4db1fdb09281a74ab138a2dba25248b5be38bf80249601ae688c90c6e0ac8"
         "811cdb740fcec31dffffffff022f66ac61050000001976a914964642290c194e"
         "3bfab661c1085e47d67786d2d388ac2f77e200000000001976a9141486a7046a"
         "ffd935919a3cb4b50a8a0c233c286c"
         "88ac00000000");

      rawTxIn_ = READHEX(
         // OutPoint
         "0044fbc929d78e4203eed6f1d3d39c0157d8e5c100bbe0886779c0ebf6a69324"
         "01000000"
         // Script Size
         "8a"
         // SigScript
         "47304402206568144ed5e7064d6176c74738b04c08ca19ca54ddeb480084b77f"
         "45eebfe57802207927d6975a5ac0e1bb36f5c05356dcda1f521770511ee5e032"
         "39c8e1eecf3aed0141045d74feae58c4c36d7c35beac05eddddc78b3ce4b0249"
         "1a2eea72043978056a8bc439b99ddaad327207b09ef16a8910828e805b0cc8c1"
         "1fba5caea2ee939346d7"
         // Sequence
         "ffffffff");

      rawTxOut_ = READHEX(
         // Value
         "ac4c8bd500000000"
         // Script size (var_int)
         "19"
         // Script
         "76""a9""14""8dce8946f1c7763bb60ea5cf16ef514cbed0633b""88""ac");
         bh_.unserialize(rawHead_);
         tx1_.unserialize(rawTx0_);
         tx2_.unserialize(rawTx1_);
   }

   BinaryData rawHead_;
   BinaryData headHashLE_;
   BinaryData headHashBE_;

   BinaryData rawBlock_;

   BinaryData rawTx0_;
   BinaryData rawTx1_;
   BinaryData rawTxIn_;
   BinaryData rawTxOut_;

   BlockHeader bh_;
   Tx tx1_;
   Tx tx2_;
};



////////////////////////////////////////////////////////////////////////////////
TEST_F(BlockObjTest, HeaderNoInit)
{
   BlockHeader bh;
   EXPECT_FALSE(bh.isInitialized());
   EXPECT_EQ(bh.getNumTx(), UINT32_MAX);
   EXPECT_EQ(bh.getBlockSize(), UINT32_MAX);
}


////////////////////////////////////////////////////////////////////////////////
TEST_F(BlockObjTest, HeaderUnserialize)
{
   EXPECT_TRUE(bh_.isInitialized());
   EXPECT_EQ(bh_.getNumTx(), UINT32_MAX);
   EXPECT_EQ(bh_.getBlockSize(), UINT32_MAX);
   EXPECT_EQ(bh_.getVersion(), 1);
   EXPECT_EQ(bh_.getThisHash(), headHashLE_);
}

////////////////////////////////////////////////////////////////////////////////
TEST_F(BlockObjTest, HeaderProperties)
{
   BinaryData prevHash = READHEX(
      "1d8f4ec0443e1f19f305e488c1085c95de7cc3fd25e0d2c5bb5d000000000000");
   BinaryData merkleRoot = READHEX(
      "9762547903d36881a86751f3f5049e23050113f779735ef82734ebf0b4450081");

   // The values are actually little-endian in the serialization, but 
   // 0x____ notation requires big-endian
   uint32_t   timestamp =        0x4dc8c8d8;
   uint32_t   nonce     =        0x5b034b33;
   BinaryData diffBits  = READHEX("b3936a1a");

   EXPECT_EQ(bh_.getPrevHash(), prevHash);
   EXPECT_EQ(bh_.getTimestamp(), timestamp);
   EXPECT_EQ(bh_.getDiffBits(), diffBits);
   EXPECT_EQ(bh_.getNonce(), nonce);
   EXPECT_DOUBLE_EQ(bh_.getDifficulty(), 157416.40184364893);

   BinaryDataRef bdrThis(headHashLE_);
   BinaryDataRef bdrPrev(rawHead_.getPtr()+4, 32);
   EXPECT_EQ(bh_.getThisHashRef(), bdrThis);
   EXPECT_EQ(bh_.getPrevHashRef(), bdrPrev);

   EXPECT_EQ(BlockHeader(rawHead_).serialize(), rawHead_);
}



////////////////////////////////////////////////////////////////////////////////
TEST_F(BlockObjTest, OutPointProperties)
{
   BinaryData rawOP = READHEX(
      "0044fbc929d78e4203eed6f1d3d39c0157d8e5c100bbe0886779c0ebf6a69324"
      "01000000");
   BinaryData prevHash = READHEX(
      "0044fbc929d78e4203eed6f1d3d39c0157d8e5c100bbe0886779c0ebf6a69324");
   BinaryData prevIdx = READHEX(
      "01000000");

   OutPoint op;
   EXPECT_EQ(op.getTxHash().getSize(), 32);
   EXPECT_EQ(op.getTxOutIndex(), UINT32_MAX);

   op.setTxHash(prevHash);
   EXPECT_EQ(op.getTxHash().getSize(), 32);
   EXPECT_EQ(op.getTxOutIndex(), UINT32_MAX);
   EXPECT_EQ(op.getTxHash(), prevHash);
   EXPECT_EQ(op.getTxHashRef(), prevHash.getRef());

   op.setTxOutIndex(12);
   EXPECT_EQ(op.getTxHash().getSize(), 32);
   EXPECT_EQ(op.getTxOutIndex(), 12);
   EXPECT_EQ(op.getTxHash(), prevHash);
   EXPECT_EQ(op.getTxHashRef(), prevHash.getRef());
}


////////////////////////////////////////////////////////////////////////////////
TEST_F(BlockObjTest, OutPointSerialize)
{
   BinaryData rawOP = READHEX(
      "0044fbc929d78e4203eed6f1d3d39c0157d8e5c100bbe0886779c0ebf6a69324"
      "01000000");
   BinaryData prevHash = READHEX(
      "0044fbc929d78e4203eed6f1d3d39c0157d8e5c100bbe0886779c0ebf6a69324");
   BinaryData prevIdx = READHEX(
      "01000000");

   OutPoint op(rawOP.getPtr());
   EXPECT_EQ(op.getTxHash().getSize(), 32);
   EXPECT_EQ(op.getTxOutIndex(), 1);
   EXPECT_EQ(op.getTxHash(), prevHash);
   EXPECT_EQ(op.getTxHashRef(), prevHash.getRef());

   EXPECT_EQ(op.serialize(), rawOP);
}


////////////////////////////////////////////////////////////////////////////////
TEST_F(BlockObjTest, TxInNoInit)
{
   TxIn txin;

   EXPECT_FALSE(txin.isInitialized());
   EXPECT_EQ(   txin.serialize().getSize(), 0);
   EXPECT_EQ(   txin.getScriptType(), TXIN_SCRIPT_NONSTANDARD);
   EXPECT_FALSE(txin.isStandard());
   EXPECT_FALSE(txin.isCoinbase());
   EXPECT_EQ(   txin.getParentHeight(), 0xffffffff);

   BinaryData newhash = READHEX("abcd1234");
   txin.setParentHash(newhash);
   txin.setParentHeight(1234);
   
   EXPECT_EQ(txin.getParentHash(),   newhash);
   EXPECT_EQ(txin.getParentHeight(), 1234);
}


////////////////////////////////////////////////////////////////////////////////
TEST_F(BlockObjTest, TxInUnserialize)
{
   BinaryRefReader brr(rawTxIn_);
   uint32_t len = rawTxIn_.getSize();
   BinaryData srcAddr = BtcUtils::getHash160( READHEX("04"
      "5d74feae58c4c36d7c35beac05eddddc78b3ce4b02491a2eea72043978056a8b"
      "c439b99ddaad327207b09ef16a8910828e805b0cc8c11fba5caea2ee939346d7"));
   BinaryData rawOP = READHEX(
      "0044fbc929d78e4203eed6f1d3d39c0157d8e5c100bbe0886779c0ebf6a69324"
      "01000000");

   vector<TxIn> txins(7);
   txins[0] = TxIn(rawTxIn_.getPtr()); 
   txins[1] = TxIn(rawTxIn_.getPtr(), len); 
   txins[2] = TxIn(rawTxIn_.getPtr(), len, TxRef(), 12); 
   txins[3].unserialize(rawTxIn_.getPtr());
   txins[4].unserialize(rawTxIn_.getRef());
   txins[5].unserialize(brr);
   txins[6].unserialize_swigsafe_(rawTxIn_);

   for(uint32_t i=0; i<7; i++)
   {
      EXPECT_TRUE( txins[i].isInitialized());
      EXPECT_EQ(   txins[i].serialize().getSize(), len);
      EXPECT_EQ(   txins[i].getScriptType(), TXIN_SCRIPT_STDUNCOMPR);
      EXPECT_EQ(   txins[i].getScriptSize(), len-(36+1+4));
      EXPECT_TRUE( txins[i].isStandard());
      EXPECT_FALSE(txins[i].isCoinbase());
      EXPECT_EQ(   txins[i].getSequence(), UINT32_MAX);
      EXPECT_EQ(   txins[i].getSenderAddrIfAvailable(), srcAddr);
      EXPECT_EQ(   txins[i].getOutPoint().serialize(), rawOP);

      EXPECT_FALSE(txins[i].getParentTxRef().isInitialized());
      EXPECT_EQ(   txins[i].getParentHeight(), UINT32_MAX);
      EXPECT_EQ(   txins[i].getParentHash(),   BinaryData(0));
      EXPECT_EQ(   txins[i].serialize(),       rawTxIn_);
      if(i==2)
         EXPECT_EQ(txins[i].getIndex(), 12);
      else
         EXPECT_EQ(txins[i].getIndex(), UINT32_MAX);
   }
}


////////////////////////////////////////////////////////////////////////////////
TEST_F(BlockObjTest, TxOutUnserialize)
{
   BinaryRefReader brr(rawTxOut_);
   uint32_t len = rawTxOut_.getSize();
   BinaryData dstAddr = READHEX("8dce8946f1c7763bb60ea5cf16ef514cbed0633b");

   vector<TxOut> txouts(7);
   txouts[0] = TxOut(rawTxOut_.getPtr()); 
   txouts[1] = TxOut(rawTxOut_.getPtr(), len); 
   txouts[2] = TxOut(rawTxOut_.getPtr(), len, TxRef(), 12); 
   txouts[3].unserialize(rawTxOut_.getPtr());
   txouts[4].unserialize(rawTxOut_.getRef());
   txouts[5].unserialize(brr);
   txouts[6].unserialize_swigsafe_(rawTxOut_);

   for(uint32_t i=0; i<7; i++)
   {
      EXPECT_TRUE( txouts[i].isInitialized());
      EXPECT_EQ(   txouts[i].getSize(), len);
      EXPECT_EQ(   txouts[i].getScriptType(), TXOUT_SCRIPT_STDHASH160);
      EXPECT_EQ(   txouts[i].getScriptSize(), 25);
      EXPECT_TRUE( txouts[i].isStandard());
      EXPECT_EQ(   txouts[i].getValue(), 0x00000000d58b4cac);
      EXPECT_EQ(   txouts[i].getScrAddressStr(), HASH160PREFIX+dstAddr);

      EXPECT_TRUE( txouts[i].isScriptStandard());
      EXPECT_TRUE( txouts[i].isScriptStdHash160());
      EXPECT_FALSE(txouts[i].isScriptStdPubKey65());
      EXPECT_FALSE(txouts[i].isScriptStdPubKey33());
      EXPECT_FALSE(txouts[i].isScriptP2SH());
      EXPECT_FALSE(txouts[i].isScriptNonStd());

      EXPECT_FALSE(txouts[i].getParentTxRef().isInitialized());
      EXPECT_EQ(   txouts[i].getParentHeight(), UINT32_MAX);
      EXPECT_EQ(   txouts[i].getParentHash(),   BinaryData(0));
      EXPECT_EQ(   txouts[i].serialize(),       rawTxOut_);
      if(i==2)
         EXPECT_EQ(txouts[i].getIndex(), 12);
      else
         EXPECT_EQ(txouts[i].getIndex(), UINT32_MAX);
   }
}


////////////////////////////////////////////////////////////////////////////////
TEST_F(BlockObjTest, TxNoInit)
{
   Tx tx;
   
   EXPECT_FALSE(tx.isInitialized());

   // Actually, why even bother with all these no-init tests?  We should always
   // check whether the tx is initialized before using it.  If you don't, you
   // deserve to seg fault :)
   //EXPECT_EQ(   tx.getSize(), UINT32_MAX);
   //EXPECT_TRUE( tx.isStandard());
   //EXPECT_EQ(   tx.getValue(), 0x00000000d58b4cac);
   //EXPECT_EQ(   tx.getRecipientAddr(), dstAddr);

   //EXPECT_TRUE( tx.isScriptStandard());
   //EXPECT_TRUE( tx.isScriptStdHash160());
   //EXPECT_FALSE(tx.isScriptStdPubKey65());
   //EXPECT_FALSE(tx.isScriptStdPubKey33());
   //EXPECT_FALSE(tx.isScriptP2SH());
   //EXPECT_FALSE(tx.isScriptNonStd());

}

////////////////////////////////////////////////////////////////////////////////
TEST_F(BlockObjTest, TxUnserialize)
{
   uint32_t len = rawTx0_.getSize();
   BinaryData tx0hash = READHEX(
      "aa739836a44451be555f74a02f088b50a867b1d3a2c917ee863d708ec2db58f6");

   BinaryData tx0_In0  = READHEX("aff189b24a36a1b93de2ea4d157c13d18251270a");
   BinaryData tx0_Out0 = READHEX("c1b4695d53b6ee57a28647ce63e45665df6762c2");
   BinaryData tx0_Out1 = READHEX("0e0aec36fe2545fb31a41164fb6954adcd96b342");
   BinaryData tx0_Val0 = READHEX("42582c0a00000000");
   BinaryData tx0_Val1 = READHEX("80d1f00800000000");
   BinaryRefReader brr(rawTx0_);

   uint64_t v0 = *(uint64_t*)tx0_Val0.getPtr();
   uint64_t v1 = *(uint64_t*)tx0_Val1.getPtr();

   Tx tx;
   vector<Tx> txs(10);
   txs[0] = Tx(rawTx0_.getPtr()); 
   txs[1] = Tx(brr);  brr.resetPosition();
   txs[2] = Tx(rawTx0_);
   txs[3] = Tx(rawTx0_.getRef());
   txs[4].unserialize(rawTx0_.getPtr());
   txs[5].unserialize(rawTx0_);
   txs[6].unserialize(rawTx0_.getRef());
   txs[7].unserialize(brr);  brr.resetPosition();
   txs[8].unserialize_swigsafe_(rawTx0_);
   txs[9] = Tx::createFromStr(rawTx0_);

   for(uint32_t i=0; i<10; i++)
   {
      EXPECT_TRUE( txs[i].isInitialized());
      EXPECT_EQ(   txs[i].getSize(), len);

      EXPECT_EQ(   txs[i].getVersion(), 1);
      EXPECT_EQ(   txs[i].getNumTxIn(), 1);
      EXPECT_EQ(   txs[i].getNumTxOut(), 2);
      EXPECT_EQ(   txs[i].getThisHash(), tx0hash.copySwapEndian());
      //EXPECT_FALSE(txs[i].isMainBranch());

      EXPECT_EQ(   txs[i].getTxInOffset(0),    5);
      EXPECT_EQ(   txs[i].getTxInOffset(1),  185);
      EXPECT_EQ(   txs[i].getTxOutOffset(0), 186);
      EXPECT_EQ(   txs[i].getTxOutOffset(1), 220);
      EXPECT_EQ(   txs[i].getTxOutOffset(2), 254);

      EXPECT_EQ(   txs[i].getLockTime(), 0);

      EXPECT_EQ(   txs[i].serialize(), rawTx0_);
      EXPECT_EQ(   txs[0].getTxIn(0).getSenderAddrIfAvailable(), tx0_In0);
      EXPECT_EQ(   txs[i].getTxOut(0).getScrAddressStr(), HASH160PREFIX+tx0_Out0);
      EXPECT_EQ(   txs[i].getTxOut(1).getScrAddressStr(), HASH160PREFIX+tx0_Out1);
      EXPECT_EQ(   txs[i].getScrAddrForTxOut(0), HASH160PREFIX+tx0_Out0);
      EXPECT_EQ(   txs[i].getScrAddrForTxOut(1), HASH160PREFIX+tx0_Out1);
      EXPECT_EQ(   txs[i].getTxOut(0).getValue(), v0);
      EXPECT_EQ(   txs[i].getTxOut(1).getValue(), v1);
      EXPECT_EQ(   txs[i].getSumOfOutputs(),  v0+v1);

      EXPECT_EQ(   txs[i].getBlockTxIndex(),  UINT16_MAX);
   }
}

////////////////////////////////////////////////////////////////////////////////
TEST_F(BlockObjTest, DISABLED_FullBlock)
{
   EXPECT_TRUE(false);

   BinaryRefReader brr(rawBlock_);
}


////////////////////////////////////////////////////////////////////////////////
TEST_F(BlockObjTest, DISABLED_TxIOPairStuff)
{
   EXPECT_TRUE(false);
}

////////////////////////////////////////////////////////////////////////////////
TEST_F(BlockObjTest, DISABLED_RegisteredTxStuff)
{
   EXPECT_TRUE(false);
}



////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
class StoredBlockObjTest : public ::testing::Test
{
protected:
   virtual void SetUp(void) 
   {
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
         "01000000eb10c9a996a2340a4d74eaab41421ed8664aa49d18538bab59010000"
         "000000005a2f06efa9f2bd804f17877537f2080030cadbfa1eb50e02338117cc"
         "604d91b9b7541a4ecfbb0a1a64f1ade703010000000100000000000000000000"
         "00000000000000000000000000000000000000000000ffffffff0804cfbb0a1a"
         "02360affffffff0100f2052a01000000434104c2239c4eedb3beb26785753463"
         "be3ec62b82f6acd62efb65f452f8806f2ede0b338e31d1f69b1ce449558d7061"
         "aa1648ddc2bf680834d3986624006a272dc21cac000000000100000003e8caa1"
         "2bcb2e7e86499c9de49c45c5a1c6167ea4b894c8c83aebba1b6100f343010000"
         "008c493046022100e2f5af5329d1244807f8347a2c8d9acc55a21a5db769e927"
         "4e7e7ba0bb605b26022100c34ca3350df5089f3415d8af82364d7f567a6a297f"
         "cc2c1d2034865633238b8c014104129e422ac490ddfcb7b1c405ab9fb4244124"
         "6c4bca578de4f27b230de08408c64cad03af71ee8a3140b40408a7058a1984a9"
         "f246492386113764c1ac132990d1ffffffff5b55c18864e16c08ef9989d31c7a"
         "343e34c27c30cd7caa759651b0e08cae0106000000008c4930460221009ec9aa"
         "3e0caf7caa321723dea561e232603e00686d4bfadf46c5c7352b07eb00022100"
         "a4f18d937d1e2354b2e69e02b18d11620a6a9332d563e9e2bbcb01cee559680a"
         "014104411b35dd963028300e36e82ee8cf1b0c8d5bf1fc4273e970469f5cb931"
         "ee07759a2de5fef638961726d04bd5eb4e5072330b9b371e479733c942964bb8"
         "6e2b22ffffffff3de0c1e913e6271769d8c0172cea2f00d6d3240afc3a20f9fa"
         "247ce58af30d2a010000008c493046022100b610e169fd15ac9f60fe2b507529"
         "281cf2267673f4690ba428cbb2ba3c3811fd022100ffbe9e3d71b21977a8e97f"
         "de4c3ba47b896d08bc09ecb9d086bb59175b5b9f03014104ff07a1833fd8098b"
         "25f48c66dcf8fde34cbdbcc0f5f21a8c2005b160406cbf34cc432842c6b37b25"
         "90d16b165b36a3efc9908d65fb0e605314c9b278f40f3e1affffffff0240420f"
         "00000000001976a914adfa66f57ded1b655eb4ccd96ee07ca62bc1ddfd88ac00"
         "7d6a7d040000001976a914981a0c9ae61fa8f8c96ae6f8e383d6e07e77133e88"
         "ac00000000010000000138e7586e0784280df58bd3dc5e3d350c9036b1ec4107"
         "951378f45881799c92a4000000008a47304402207c945ae0bbdaf9dadba07bdf"
         "23faa676485a53817af975ddf85a104f764fb93b02201ac6af32ddf597e610b4"
         "002e41f2de46664587a379a0161323a85389b4f82dda014104ec8883d3e4f7a3"
         "9d75c9f5bb9fd581dc9fb1b7cdf7d6b5a665e4db1fdb09281a74ab138a2dba25"
         "248b5be38bf80249601ae688c90c6e0ac8811cdb740fcec31dffffffff022f66"
         "ac61050000001976a914964642290c194e3bfab661c1085e47d67786d2d388ac"
         "2f77e200000000001976a9141486a7046affd935919a3cb4b50a8a0c233c286c"
         "88ac00000000");

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
         //"01000000020044fbc929d78e4203eed6f1d3d39c0157d8e5c100bbe0886779c0"
         //"ebf6a69324010000008a47304402206568144ed5e7064d6176c74738b04c08ca"
         //"19ca54ddeb480084b77f45eebfe57802207927d6975a5ac0e1bb36f5c05356dc"
         //"da1f521770511ee5e03239c8e1eecf3aed0141045d74feae58c4c36d7c35beac"
         //"05eddddc78b3ce4b02491a2eea72043978056a8bc439b99ddaad327207b09ef1"
         //"6a8910828e805b0cc8c11fba5caea2ee939346d7ffffffff45c866b219b17695"
         //"2508f8e5aea728f950186554fc4a5807e2186a8e1c4009e5000000008c493046"
         //"022100bd5d41662f98cfddc46e86ea7e4a3bc8fe9f1dfc5c4836eaf7df582596"
         //"cfe0e9022100fc459ae4f59b8279d679003b88935896acd10021b6e2e4619377"
         //"e336b5296c5e014104c00bab76a708ba7064b2315420a1c533ca9945eeff9754"
         //"cdc574224589e9113469b4e71752146a10028079e04948ecdf70609bf1b9801f"
         //"6b73ab75947ac339e5ffffffff0200000000");
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


      sbh_.unserialize(rawHead_);

      // Make sure the global DB type and prune type are reset for each test
      DBUtils.setArmoryDbType(ARMORY_DB_FULL);
      DBUtils.setDbPruneType(DB_PRUNE_NONE);
   }

   BinaryData PREFBYTE(DB_PREFIX pref) 
   { 
      BinaryWriter bw;
      bw.put_uint8_t((uint8_t)pref);
      return bw.getData();
   }

   BinaryData rawHead_;
   BinaryData headHashLE_;
   BinaryData headHashBE_;

   BinaryData rawBlock_;

   BinaryData rawTx0_;
   BinaryData rawTx1_;

   BlockHeader bh_;
   Tx tx1_;
   Tx tx2_;

   BinaryData rawTxUnfrag_;
   BinaryData rawTxFragged_;
   BinaryData rawTxOut0_;
   BinaryData rawTxOut1_;



   StoredHeader sbh_;
};


////////////////////////////////////////////////////////////////////////////////
TEST_F(StoredBlockObjTest, StoredObjNoInit)
{
   StoredHeader        sbh;
   StoredTx            stx;
   StoredTxOut         stxo;
   StoredScriptHistory ssh;
   StoredUndoData      sud;
   StoredHeadHgtList   hhl;
   StoredTxHints       sths;

   EXPECT_FALSE( sbh.isInitialized() );
   EXPECT_FALSE( stx.isInitialized() );
   EXPECT_FALSE( stxo.isInitialized() );
   EXPECT_FALSE( ssh.isInitialized() );
   EXPECT_FALSE( sud.isInitialized() );
   EXPECT_FALSE( hhl.isInitialized() );
   EXPECT_FALSE( sths.isInitialized() );
}

////////////////////////////////////////////////////////////////////////////////
TEST_F(StoredBlockObjTest, GetDBKeys)
{
   StoredHeader        sbh;
   StoredTx            stx;
   StoredTxOut         stxo;
   StoredScriptHistory ssh1;
   StoredScriptHistory ssh2;
   StoredUndoData      sud;
   StoredHeadHgtList   hhl;
   StoredTxHints       sths;

   BinaryData key    = READHEX("aaaaffff");
   uint32_t   hgt    = 123000;
   uint8_t    dup    = 15;
   uint8_t    txi    = 7;
   uint8_t    txo    = 1;
   BinaryData hgtx   = READHEX("01e0780f");
   BinaryData txidx  = WRITE_UINT16_BE(txi);
   BinaryData txoidx = WRITE_UINT16_BE(txo);

   sbh.blockHeight_  = hgt;
   sbh.duplicateID_  = dup;

   stx.blockHeight_  = hgt;
   stx.duplicateID_  = dup;
   stx.txIndex_      = txi;

   stxo.blockHeight_ = hgt;
   stxo.duplicateID_ = dup;
   stxo.txIndex_     = txi;
   stxo.txOutIndex_  = txo;

   ssh1.uniqueKey_   = key;
   ssh2.uniqueKey_   = key;
   sud.blockHeight_  = hgt;
   sud.duplicateID_  = dup;
   hhl.height_       = hgt;
   sths.txHashPrefix_= key;

   BinaryData TXB = PREFBYTE(DB_PREFIX_TXDATA);
   BinaryData SSB = PREFBYTE(DB_PREFIX_SCRIPT);
   BinaryData UDB = PREFBYTE(DB_PREFIX_UNDODATA);
   BinaryData HHB = PREFBYTE(DB_PREFIX_HEADHGT);
   BinaryData THB = PREFBYTE(DB_PREFIX_TXHINTS);
   EXPECT_EQ(sbh.getDBKey(  true ),   TXB + hgtx);
   EXPECT_EQ(stx.getDBKey(  true ),   TXB + hgtx + txidx);
   EXPECT_EQ(stxo.getDBKey( true ),   TXB + hgtx + txidx + txoidx);
   EXPECT_EQ(ssh1.getDBKey( true ),   SSB + key);
   EXPECT_EQ(ssh2.getDBKey( true ),   SSB + key);
   EXPECT_EQ(sud.getDBKey(  true ),   UDB + hgtx);
   EXPECT_EQ(hhl.getDBKey(  true ),   HHB + WRITE_UINT32_BE(hgt));
   EXPECT_EQ(sths.getDBKey( true ),   THB + key);

   EXPECT_EQ(sbh.getDBKey(  false ),         hgtx);
   EXPECT_EQ(stx.getDBKey(  false ),         hgtx + txidx);
   EXPECT_EQ(stxo.getDBKey( false ),         hgtx + txidx + txoidx);
   EXPECT_EQ(ssh1.getDBKey( false ),         key);
   EXPECT_EQ(ssh2.getDBKey( false ),         key);
   EXPECT_EQ(sud.getDBKey(  false ),         hgtx);
   EXPECT_EQ(hhl.getDBKey(  false ),         WRITE_UINT32_BE(hgt));
   EXPECT_EQ(sths.getDBKey( false ),         key);
}



////////////////////////////////////////////////////////////////////////////////
TEST_F(StoredBlockObjTest, LengthUnfrag)
{
   StoredTx tx;
   vector<uint32_t> offin, offout;

   uint32_t lenUnfrag  = BtcUtils::StoredTxCalcLength( rawTxUnfrag_.getPtr(), 
                                                       false, 
                                                       &offin, 
                                                       &offout);
   ASSERT_EQ(lenUnfrag,  438);

   ASSERT_EQ(offin.size(),    3);
   EXPECT_EQ(offin[0],        5);
   EXPECT_EQ(offin[1],      184);
   EXPECT_EQ(offin[2],      365);

   ASSERT_EQ(offout.size(),   3);
   EXPECT_EQ(offout[0],     366);
   EXPECT_EQ(offout[1],     400);
   EXPECT_EQ(offout[2],     434);
}



////////////////////////////////////////////////////////////////////////////////
TEST_F(StoredBlockObjTest, LengthFragged)
{
   vector<uint32_t> offin, offout;

   uint32_t lenFragged = BtcUtils::StoredTxCalcLength( rawTxFragged_.getPtr(), 
                                                       true, 
                                                       &offin, 
                                                       &offout);
   ASSERT_EQ(lenFragged, 370);

   ASSERT_EQ(offin.size(),    3);
   EXPECT_EQ(offin[0],        5);
   EXPECT_EQ(offin[1],      184);
   EXPECT_EQ(offin[2],      365);
   
   ASSERT_EQ(offout.size(),   3);
   EXPECT_EQ(offout[0],     366);
   EXPECT_EQ(offout[1],     366);
   EXPECT_EQ(offout[2],     366);
}

////////////////////////////////////////////////////////////////////////////////
TEST_F(StoredBlockObjTest, BlkDataKeys)
{
   uint32_t hgt = 0x001a332b;
   uint8_t  dup = 0x01;
   uint16_t tix = 0x0102;
   uint16_t tox = 0x0021;
   
   EXPECT_EQ(DBUtils.getBlkDataKey(hgt, dup),           
                                               READHEX("031a332b01"));
   EXPECT_EQ(DBUtils.getBlkDataKey(hgt, dup, tix),      
                                               READHEX("031a332b010102"));
   EXPECT_EQ(DBUtils.getBlkDataKey(hgt, dup, tix, tox), 
                                               READHEX("031a332b0101020021"));

   EXPECT_EQ(DBUtils.getBlkDataKeyNoPrefix(hgt, dup),           
                                               READHEX("1a332b01"));
   EXPECT_EQ(DBUtils.getBlkDataKeyNoPrefix(hgt, dup, tix),      
                                               READHEX("1a332b010102"));
   EXPECT_EQ(DBUtils.getBlkDataKeyNoPrefix(hgt, dup, tix, tox), 
                                               READHEX("1a332b0101020021"));
}

////////////////////////////////////////////////////////////////////////////////
TEST_F(StoredBlockObjTest, ReadBlkKeyData)
{
   BinaryData TXP  = WRITE_UINT8_BE((uint8_t)DB_PREFIX_TXDATA);
   BinaryData key5p = TXP + READHEX("01e078""0f");
   BinaryData key7p = TXP + READHEX("01e078""0f""0007");
   BinaryData key9p = TXP + READHEX("01e078""0f""0007""0001");
   BinaryData key5 =        READHEX("01e078""0f");
   BinaryData key7 =        READHEX("01e078""0f""0007");
   BinaryData key9 =        READHEX("01e078""0f""0007""0001");
   BinaryRefReader brr;

   uint32_t hgt;
   uint8_t  dup;
   uint16_t txi;
   uint16_t txo;

   BLKDATA_TYPE bdtype;

   /////////////////////////////////////////////////////////////////////////////
   // 5 bytes, with prefix
   brr.setNewData(key5p);
   bdtype = DBUtils.readBlkDataKey(brr, hgt, dup);
   EXPECT_EQ( hgt,     123000);
   EXPECT_EQ( dup,         15);
   EXPECT_EQ( brr.getSizeRemaining(), 0);
   EXPECT_EQ( bdtype, BLKDATA_HEADER);

   brr.setNewData(key5p);
   bdtype = DBUtils.readBlkDataKey(brr, hgt, dup, txi);
   EXPECT_EQ( hgt,     123000);
   EXPECT_EQ( dup,         15);
   EXPECT_EQ( txi, UINT16_MAX);
   EXPECT_EQ( brr.getSizeRemaining(), 0);
   EXPECT_EQ( bdtype, BLKDATA_HEADER);
   
   brr.setNewData(key5p);
   bdtype = DBUtils.readBlkDataKey(brr, hgt, dup, txi, txo);
   EXPECT_EQ( hgt,     123000);
   EXPECT_EQ( dup,         15);
   EXPECT_EQ( txi, UINT16_MAX);
   EXPECT_EQ( txo, UINT16_MAX);
   EXPECT_EQ( brr.getSizeRemaining(), 0);
   EXPECT_EQ( bdtype, BLKDATA_HEADER);


   /////////////////////////////////////////////////////////////////////////////
   // 7 bytes, with prefix
   brr.setNewData(key7p);
   bdtype = DBUtils.readBlkDataKey(brr, hgt, dup);
   EXPECT_EQ( hgt,     123000);
   EXPECT_EQ( dup,         15);
   EXPECT_EQ( brr.getSizeRemaining(), 0);
   EXPECT_EQ( bdtype, BLKDATA_TX);

   brr.setNewData(key7p);
   bdtype = DBUtils.readBlkDataKey(brr, hgt, dup, txi);
   EXPECT_EQ( hgt,     123000);
   EXPECT_EQ( dup,         15);
   EXPECT_EQ( txi,          7);
   EXPECT_EQ( brr.getSizeRemaining(), 0);
   EXPECT_EQ( bdtype, BLKDATA_TX);
   
   brr.setNewData(key7p);
   bdtype = DBUtils.readBlkDataKey(brr, hgt, dup, txi, txo);
   EXPECT_EQ( hgt,     123000);
   EXPECT_EQ( dup,         15);
   EXPECT_EQ( txi,          7);
   EXPECT_EQ( txo, UINT16_MAX);
   EXPECT_EQ( brr.getSizeRemaining(), 0);
   EXPECT_EQ( bdtype, BLKDATA_TX);


   /////////////////////////////////////////////////////////////////////////////
   // 9 bytes, with prefix
   brr.setNewData(key9p);
   bdtype = DBUtils.readBlkDataKey(brr, hgt, dup);
   EXPECT_EQ( hgt,     123000);
   EXPECT_EQ( dup,         15);
   EXPECT_EQ( brr.getSizeRemaining(), 0);
   EXPECT_EQ( bdtype, BLKDATA_TXOUT);

   brr.setNewData(key9p);
   bdtype = DBUtils.readBlkDataKey(brr, hgt, dup, txi);
   EXPECT_EQ( hgt,     123000);
   EXPECT_EQ( dup,         15);
   EXPECT_EQ( txi,          7);
   EXPECT_EQ( brr.getSizeRemaining(), 0);
   EXPECT_EQ( bdtype, BLKDATA_TXOUT);
   
   brr.setNewData(key9p);
   bdtype = DBUtils.readBlkDataKey(brr, hgt, dup, txi, txo);
   EXPECT_EQ( hgt,     123000);
   EXPECT_EQ( dup,         15);
   EXPECT_EQ( txi,          7);
   EXPECT_EQ( txo,          1);
   EXPECT_EQ( brr.getSizeRemaining(), 0);
   EXPECT_EQ( bdtype, BLKDATA_TXOUT);


   /////////////////////////////////////////////////////////////////////////////
   // 5 bytes, no prefix
   brr.setNewData(key5);
   bdtype = DBUtils.readBlkDataKeyNoPrefix(brr, hgt, dup);
   EXPECT_EQ( hgt,     123000);
   EXPECT_EQ( dup,         15);
   EXPECT_EQ( brr.getSizeRemaining(), 0);
   EXPECT_EQ( bdtype, BLKDATA_HEADER);

   brr.setNewData(key5);
   bdtype = DBUtils.readBlkDataKeyNoPrefix(brr, hgt, dup, txi);
   EXPECT_EQ( hgt,     123000);
   EXPECT_EQ( dup,         15);
   EXPECT_EQ( txi, UINT16_MAX);
   EXPECT_EQ( brr.getSizeRemaining(), 0);
   EXPECT_EQ( bdtype, BLKDATA_HEADER);
   
   brr.setNewData(key5);
   bdtype = DBUtils.readBlkDataKeyNoPrefix(brr, hgt, dup, txi, txo);
   EXPECT_EQ( hgt,     123000);
   EXPECT_EQ( dup,         15);
   EXPECT_EQ( txi, UINT16_MAX);
   EXPECT_EQ( txo, UINT16_MAX);
   EXPECT_EQ( brr.getSizeRemaining(), 0);
   EXPECT_EQ( bdtype, BLKDATA_HEADER);


   /////////////////////////////////////////////////////////////////////////////
   // 7 bytes, no prefix
   brr.setNewData(key7);
   bdtype = DBUtils.readBlkDataKeyNoPrefix(brr, hgt, dup);
   EXPECT_EQ( hgt,     123000);
   EXPECT_EQ( dup,         15);
   EXPECT_EQ( brr.getSizeRemaining(), 0);
   EXPECT_EQ( bdtype, BLKDATA_TX);

   brr.setNewData(key7);
   bdtype = DBUtils.readBlkDataKeyNoPrefix(brr, hgt, dup, txi);
   EXPECT_EQ( hgt,     123000);
   EXPECT_EQ( dup,         15);
   EXPECT_EQ( txi,          7);
   EXPECT_EQ( brr.getSizeRemaining(), 0);
   EXPECT_EQ( bdtype, BLKDATA_TX);
   
   brr.setNewData(key7);
   bdtype = DBUtils.readBlkDataKeyNoPrefix(brr, hgt, dup, txi, txo);
   EXPECT_EQ( hgt,     123000);
   EXPECT_EQ( dup,         15);
   EXPECT_EQ( txi,          7);
   EXPECT_EQ( txo, UINT16_MAX);
   EXPECT_EQ( brr.getSizeRemaining(), 0);
   EXPECT_EQ( bdtype, BLKDATA_TX);


   /////////////////////////////////////////////////////////////////////////////
   // 9 bytes, no prefix
   brr.setNewData(key9);
   bdtype = DBUtils.readBlkDataKeyNoPrefix(brr, hgt, dup);
   EXPECT_EQ( hgt,     123000);
   EXPECT_EQ( dup,         15);
   EXPECT_EQ( brr.getSizeRemaining(), 0);
   EXPECT_EQ( bdtype, BLKDATA_TXOUT);

   brr.setNewData(key9);
   bdtype = DBUtils.readBlkDataKeyNoPrefix(brr, hgt, dup, txi);
   EXPECT_EQ( hgt,     123000);
   EXPECT_EQ( dup,         15);
   EXPECT_EQ( txi,          7);
   EXPECT_EQ( brr.getSizeRemaining(), 0);
   EXPECT_EQ( bdtype, BLKDATA_TXOUT);
   
   brr.setNewData(key9);
   bdtype = DBUtils.readBlkDataKeyNoPrefix(brr, hgt, dup, txi, txo);
   EXPECT_EQ( hgt,     123000);
   EXPECT_EQ( dup,         15);
   EXPECT_EQ( txi,          7);
   EXPECT_EQ( txo,          1);
   EXPECT_EQ( brr.getSizeRemaining(), 0);
   EXPECT_EQ( bdtype, BLKDATA_TXOUT);
}

////////////////////////////////////////////////////////////////////////////////
TEST_F(StoredBlockObjTest, SHeaderUnserialize)
{
   // SetUp already contains sbh_.unserialize(rawHead_);
   EXPECT_TRUE( sbh_.isInitialized());
   EXPECT_FALSE(sbh_.isMainBranch_);
   EXPECT_FALSE(sbh_.haveFullBlock());
   EXPECT_FALSE(sbh_.isMerkleCreated());
   EXPECT_EQ(   sbh_.numTx_,       UINT32_MAX);
   EXPECT_EQ(   sbh_.numBytes_,    UINT32_MAX);
   EXPECT_EQ(   sbh_.blockHeight_, UINT32_MAX);
   EXPECT_EQ(   sbh_.duplicateID_, UINT8_MAX);
   EXPECT_EQ(   sbh_.merkle_.getSize(), 0);
   EXPECT_EQ(   sbh_.stxMap_.size(), 0);
}


////////////////////////////////////////////////////////////////////////////////
TEST_F(StoredBlockObjTest, SHeaderDBSerFull_H)
{
   DBUtils.setArmoryDbType(ARMORY_DB_FULL);
   DBUtils.setDbPruneType(DB_PRUNE_NONE);

   sbh_.blockHeight_      = 65535;
   sbh_.duplicateID_      = 1;
   sbh_.merkle_           = READHEX("deadbeef");
   sbh_.merkleIsPartial_  = false;
   sbh_.isMainBranch_     = true;
   sbh_.numTx_            = 15;
   sbh_.numBytes_         = 65535;

   // SetUp already contains sbh_.unserialize(rawHead_);
   BinaryData last4 = READHEX("00ffff01");
   EXPECT_EQ(sbh_.serializeDBValue(HEADERS), rawHead_ + last4);
}


////////////////////////////////////////////////////////////////////////////////
TEST_F(StoredBlockObjTest, SHeaderDBSerFull_B1)
{
   // ARMORY_DB_FULL means no merkle string (cause all Tx are in the DB
   // so the merkle tree would be redundant.
   DBUtils.setArmoryDbType(ARMORY_DB_FULL);
   DBUtils.setDbPruneType(DB_PRUNE_NONE);

   sbh_.blockHeight_      = 65535;
   sbh_.duplicateID_      = 1;
   sbh_.merkle_           = READHEX("deadbeef");
   sbh_.merkleIsPartial_  = false;
   sbh_.isMainBranch_     = true;
   sbh_.numTx_            = 15;
   sbh_.numBytes_         = 65535;

   // SetUp already contains sbh_.unserialize(rawHead_);
   BinaryData flags = READHEX("01240000");
   BinaryData ntx   = READHEX("0f000000");
   BinaryData nbyte = READHEX("ffff0000");

   BinaryData headBlkData = flags + rawHead_ + ntx + nbyte;
   EXPECT_EQ(sbh_.serializeDBValue(BLKDATA), headBlkData);
}


////////////////////////////////////////////////////////////////////////////////
TEST_F(StoredBlockObjTest, SHeaderDBSerFull_B2)
{
   // With merkle string
   DBUtils.setArmoryDbType(ARMORY_DB_PARTIAL);
   DBUtils.setDbPruneType(DB_PRUNE_NONE);

   BinaryWriter bw;

   sbh_.blockHeight_      = 65535;
   sbh_.duplicateID_      = 1;
   sbh_.merkle_           = READHEX("deadbeef");
   sbh_.merkleIsPartial_  = false;
   sbh_.isMainBranch_     = true;
   sbh_.numTx_            = 15;
   sbh_.numBytes_         = 65535;

   // SetUp already contains sbh_.unserialize(rawHead_);
   BinaryData flags = READHEX("01160000");
   BinaryData ntx   = READHEX("0f000000");
   BinaryData nbyte = READHEX("ffff0000");

   BinaryData headBlkData = flags + rawHead_ + ntx + nbyte + sbh_.merkle_;
   EXPECT_EQ(sbh_.serializeDBValue(BLKDATA), headBlkData);
}

////////////////////////////////////////////////////////////////////////////////
TEST_F(StoredBlockObjTest, SHeaderDBSerFull_B3)
{
   DBUtils.setArmoryDbType(ARMORY_DB_LITE);
   DBUtils.setDbPruneType(DB_PRUNE_ALL);

   BinaryWriter bw;

   sbh_.blockHeight_      = 65535;
   sbh_.duplicateID_      = 1;
   sbh_.merkle_           = BinaryData(0);
   sbh_.merkleIsPartial_  = false;
   sbh_.isMainBranch_     = true;
   sbh_.numTx_            = 15;
   sbh_.numBytes_         = 65535;

   // SetUp already contains sbh_.unserialize(rawHead_);
   BinaryData flags = READHEX("01000000");
   BinaryData ntx   = READHEX("0f000000");
   BinaryData nbyte = READHEX("ffff0000");

   BinaryData headBlkData = flags + rawHead_ + ntx + nbyte;
   EXPECT_EQ(sbh_.serializeDBValue(BLKDATA), headBlkData);
}


////////////////////////////////////////////////////////////////////////////////
TEST_F(StoredBlockObjTest, SHeaderDBUnserFull_H)
{
   BinaryData dbval = READHEX(
      "010000001d8f4ec0443e1f19f305e488c1085c95de7cc3fd25e0d2c5bb5d0000"
      "000000009762547903d36881a86751f3f5049e23050113f779735ef82734ebf0"
      "b4450081d8c8c84db3936a1a334b035b00ffff01");

   BinaryRefReader brr(dbval);
   sbh_.unserializeDBValue(HEADERS, brr);

   EXPECT_EQ(sbh_.blockHeight_, 65535);
   EXPECT_EQ(sbh_.duplicateID_, 1);
}


////////////////////////////////////////////////////////////////////////////////
TEST_F(StoredBlockObjTest, SHeaderDBUnserFull_B1)
{
   BinaryData dbval = READHEX(
      "01240000010000001d8f4ec0443e1f19f305e488c1085c95de7cc3fd25e0d2c5"
      "bb5d0000000000009762547903d36881a86751f3f5049e23050113f779735ef8"
      "2734ebf0b4450081d8c8c84db3936a1a334b035b0f000000ffff0000");

   BinaryRefReader brr(dbval);
   sbh_.unserializeDBValue(BLKDATA, brr);
   sbh_.setHeightAndDup(65535, 1);

   EXPECT_EQ(sbh_.blockHeight_,  65535);
   EXPECT_EQ(sbh_.duplicateID_,  1);
   EXPECT_EQ(sbh_.merkle_     ,  READHEX(""));
   EXPECT_EQ(sbh_.numTx_      ,  15);
   EXPECT_EQ(sbh_.numBytes_   ,  65535);
   EXPECT_EQ(sbh_.unserArmVer_,  0x00);
   EXPECT_EQ(sbh_.unserBlkVer_,  1);
   EXPECT_EQ(sbh_.unserDbType_,  ARMORY_DB_FULL);
   EXPECT_EQ(sbh_.unserPrType_,  DB_PRUNE_NONE);
   EXPECT_EQ(sbh_.unserMkType_,  MERKLE_SER_NONE);
}


////////////////////////////////////////////////////////////////////////////////
TEST_F(StoredBlockObjTest, SHeaderDBUnserFull_B2)
{
   BinaryData dbval = READHEX(
      "01160000010000001d8f4ec0443e1f19f305e488c1085c95de7cc3fd25e0d2c5"
      "bb5d0000000000009762547903d36881a86751f3f5049e23050113f779735ef8"
      "2734ebf0b4450081d8c8c84db3936a1a334b035b0f000000ffff0000deadbeef");

   BinaryRefReader brr(dbval);
   sbh_.unserializeDBValue(BLKDATA, brr);
   sbh_.setHeightAndDup(65535, 1);

   EXPECT_EQ(sbh_.blockHeight_ , 65535);
   EXPECT_EQ(sbh_.duplicateID_ , 1);
   EXPECT_EQ(sbh_.merkle_      , READHEX("deadbeef"));
   EXPECT_EQ(sbh_.numTx_       , 15);
   EXPECT_EQ(sbh_.numBytes_    , 65535);
   EXPECT_EQ(sbh_.unserArmVer_,  0x00);
   EXPECT_EQ(sbh_.unserBlkVer_,  1);
   EXPECT_EQ(sbh_.unserDbType_,  ARMORY_DB_PARTIAL);
   EXPECT_EQ(sbh_.unserPrType_,  DB_PRUNE_NONE);
   EXPECT_EQ(sbh_.unserMkType_,  MERKLE_SER_FULL);
}

////////////////////////////////////////////////////////////////////////////////
TEST_F(StoredBlockObjTest, SHeaderDBUnserFull_B3)
{
   BinaryData dbval = READHEX(
      "01000000010000001d8f4ec0443e1f19f305e488c1085c95de7cc3fd25e0d2c5"
      "bb5d0000000000009762547903d36881a86751f3f5049e23050113f779735ef8"
      "2734ebf0b4450081d8c8c84db3936a1a334b035b0f000000ffff0000");

   BinaryRefReader brr(dbval);
   sbh_.unserializeDBValue(BLKDATA, brr);
   sbh_.setHeightAndDup(65535, 1);

   EXPECT_EQ(sbh_.blockHeight_,  65535);
   EXPECT_EQ(sbh_.duplicateID_,  1);
   EXPECT_EQ(sbh_.merkle_     ,  READHEX(""));
   EXPECT_EQ(sbh_.numTx_      ,  15);
   EXPECT_EQ(sbh_.numBytes_   ,  65535);
   EXPECT_EQ(sbh_.unserArmVer_,  0x00);
   EXPECT_EQ(sbh_.unserBlkVer_,  1);
   EXPECT_EQ(sbh_.unserDbType_,  ARMORY_DB_LITE);
   EXPECT_EQ(sbh_.unserPrType_,  DB_PRUNE_ALL);
   EXPECT_EQ(sbh_.unserMkType_,  MERKLE_SER_NONE);
}




////////////////////////////////////////////////////////////////////////////////
TEST_F(StoredBlockObjTest, STxUnserUnfrag)
{
   Tx regTx(rawTx0_);

   StoredTx stx;
   stx.createFromTx(regTx, false);

   EXPECT_TRUE( stx.isInitialized());
   EXPECT_TRUE( stx.haveAllTxOut());
   EXPECT_FALSE(stx.isFragged_);
   EXPECT_EQ(   stx.version_, 1);
   EXPECT_EQ(   stx.blockHeight_, UINT32_MAX);
   EXPECT_EQ(   stx.duplicateID_,  UINT8_MAX);
   EXPECT_EQ(   stx.txIndex_,     UINT16_MAX);
   EXPECT_EQ(   stx.dataCopy_.getSize(), 258);
   EXPECT_EQ(   stx.numBytes_,    258);
   EXPECT_EQ(   stx.fragBytes_,   190);

   ASSERT_EQ(   stx.stxoMap_.size(), 2);
   EXPECT_TRUE( stx.stxoMap_[0].isInitialized());
   EXPECT_TRUE( stx.stxoMap_[1].isInitialized());
   EXPECT_EQ(   stx.stxoMap_[0].txIndex_, UINT16_MAX);
   EXPECT_EQ(   stx.stxoMap_[1].txIndex_, UINT16_MAX);
   EXPECT_EQ(   stx.stxoMap_[0].txOutIndex_, 0);
   EXPECT_EQ(   stx.stxoMap_[1].txOutIndex_, 1);
}


////////////////////////////////////////////////////////////////////////////////
TEST_F(StoredBlockObjTest, STxUnserFragged)
{
   Tx regTx(rawTx0_);

   StoredTx stx;
   stx.createFromTx(regTx, true);

   EXPECT_TRUE( stx.isInitialized());
   EXPECT_TRUE( stx.haveAllTxOut());
   EXPECT_TRUE( stx.isFragged_);
   EXPECT_EQ(   stx.version_, 1);
   EXPECT_EQ(   stx.blockHeight_, UINT32_MAX);
   EXPECT_EQ(   stx.duplicateID_,  UINT8_MAX);
   EXPECT_EQ(   stx.txIndex_,     UINT16_MAX);
   EXPECT_EQ(   stx.dataCopy_.getSize(), 190);

   ASSERT_EQ(   stx.stxoMap_.size(), 2);
   EXPECT_TRUE( stx.stxoMap_[0].isInitialized());
   EXPECT_TRUE( stx.stxoMap_[1].isInitialized());
   EXPECT_EQ(   stx.stxoMap_[0].txIndex_, UINT16_MAX);
   EXPECT_EQ(   stx.stxoMap_[1].txIndex_, UINT16_MAX);
   EXPECT_EQ(   stx.stxoMap_[0].txOutIndex_, 0);
   EXPECT_EQ(   stx.stxoMap_[1].txOutIndex_, 1);
}



////////////////////////////////////////////////////////////////////////////////
TEST_F(StoredBlockObjTest, STxReconstruct)
{
   Tx regTx, reconTx;
   StoredTx stx;

   // Reconstruct an unfragged tx
   regTx.unserialize(rawTx0_);
   stx.createFromTx(regTx, false);

   reconTx = stx.getTxCopy();
   EXPECT_EQ(reconTx.serialize(),   rawTx0_);
   EXPECT_EQ(stx.getSerializedTx(), rawTx0_);

   // Reconstruct an fragged tx
   regTx.unserialize(rawTx0_);
   stx.createFromTx(regTx, true);

   reconTx = stx.getTxCopy();
   EXPECT_EQ(reconTx.serialize(),   rawTx0_);
   EXPECT_EQ(stx.getSerializedTx(), rawTx0_);
}

////////////////////////////////////////////////////////////////////////////////
TEST_F(StoredBlockObjTest, STxSerUnfragToFrag)
{
   StoredTx stx;
   stx.unserialize(rawTxUnfrag_);

   EXPECT_EQ(stx.getSerializedTx(),        rawTxUnfrag_);
   EXPECT_EQ(stx.getSerializedTxFragged(), rawTxFragged_);
}

////////////////////////////////////////////////////////////////////////////////
TEST_F(StoredBlockObjTest, STxSerDBValue_1)
{
   DBUtils.setArmoryDbType(ARMORY_DB_FULL);
   DBUtils.setDbPruneType(DB_PRUNE_NONE);
   
   Tx origTx(rawTxUnfrag_);

   StoredTx stx;
   stx.unserialize(rawTxUnfrag_);

   //   0123   45   67 01  23 4567 
   //  |----| |--| |-- --|
   //   DBVer TxVer TxSer
   //
   // For this example:  DBVer=0, TxVer=1, TxSer=FRAGGED[1]
   //   0000   01   00 01  -- ----
   BinaryData  first2  = READHEX("0440"); // little-endian, of course
   BinaryData  txHash  = origTx.getThisHash();
   BinaryData  fragged = stx.getSerializedTxFragged();
   BinaryData  output  = first2 + txHash + fragged;
   EXPECT_EQ(stx.serializeDBValue(), output);
}

////////////////////////////////////////////////////////////////////////////////
TEST_F(StoredBlockObjTest, DISABLED_STxSerDBValue_2)
{
   // I modified the ARMORY_DB_SUPER code to frag, as well.  There's no
   // mode that doesn't frag, now.
   DBUtils.setArmoryDbType(ARMORY_DB_SUPER);
   DBUtils.setDbPruneType(DB_PRUNE_NONE);
   
   Tx origTx(rawTxUnfrag_);

   StoredTx stx;
   stx.unserialize(rawTxUnfrag_);

   //   0123   45   67 01  23 4567 
   //  |----| |--| |-- --|
   //   DBVer TxVer TxSer
   //
   // For this example:  DBVer=0, TxVer=1, TxSer=FRAGGED[1]
   //   0000   01   00 00  -- ----
   BinaryData  first2  = READHEX("0400"); // little-endian, of course
   BinaryData  txHash  = origTx.getThisHash();
   BinaryData  fragged = stx.getSerializedTx();  // Full Tx this time
   BinaryData  output  = first2 + txHash + fragged;
   EXPECT_EQ(stx.serializeDBValue(), output);
}

////////////////////////////////////////////////////////////////////////////////
TEST_F(StoredBlockObjTest, STxUnserDBValue_1)
{
   Tx origTx(rawTxUnfrag_);

   BinaryData toUnser = READHEX(
      "0440e471262336aa67391e57c8c6fe03bae29734079e06ff75c7fa4d0a873c83"
      "f03c01000000020044fbc929d78e4203eed6f1d3d39c0157d8e5c100bbe08867"
      "79c0ebf6a69324010000008a47304402206568144ed5e7064d6176c74738b04c"
      "08ca19ca54ddeb480084b77f45eebfe57802207927d6975a5ac0e1bb36f5c053"
      "56dcda1f521770511ee5e03239c8e1eecf3aed0141045d74feae58c4c36d7c35"
      "beac05eddddc78b3ce4b02491a2eea72043978056a8bc439b99ddaad327207b0"
      "9ef16a8910828e805b0cc8c11fba5caea2ee939346d7ffffffff45c866b219b1"
      "76952508f8e5aea728f950186554fc4a5807e2186a8e1c4009e5000000008c49"
      "3046022100bd5d41662f98cfddc46e86ea7e4a3bc8fe9f1dfc5c4836eaf7df58"
      "2596cfe0e9022100fc459ae4f59b8279d679003b88935896acd10021b6e2e461"
      "9377e336b5296c5e014104c00bab76a708ba7064b2315420a1c533ca9945eeff"
      "9754cdc574224589e9113469b4e71752146a10028079e04948ecdf70609bf1b9"
      "801f6b73ab75947ac339e5ffffffff0200000000");

   BinaryRefReader brr(toUnser);

   StoredTx stx;
   stx.unserializeDBValue(brr);

   EXPECT_TRUE( stx.isInitialized());
   EXPECT_EQ(   stx.thisHash_,    origTx.getThisHash());
   EXPECT_EQ(   stx.lockTime_,    origTx.getLockTime());
   EXPECT_EQ(   stx.dataCopy_,    rawTxFragged_);
   EXPECT_TRUE( stx.isFragged_);
   EXPECT_EQ(   stx.version_,     1);
   EXPECT_EQ(   stx.blockHeight_, UINT32_MAX);
   EXPECT_EQ(   stx.duplicateID_, UINT8_MAX);
   EXPECT_EQ(   stx.txIndex_,     UINT16_MAX);
   EXPECT_EQ(   stx.numTxOut_,    origTx.getNumTxOut());
   EXPECT_EQ(   stx.numBytes_,    UINT32_MAX);
   EXPECT_EQ(   stx.fragBytes_,   370);
}

////////////////////////////////////////////////////////////////////////////////
TEST_F(StoredBlockObjTest, STxUnserDBValue_2)
{
   Tx origTx(rawTxUnfrag_);

   BinaryData toUnser = READHEX(
      "0004e471262336aa67391e57c8c6fe03bae29734079e06ff75c7fa4d0a873c83"
      "f03c01000000020044fbc929d78e4203eed6f1d3d39c0157d8e5c100bbe08867"
      "79c0ebf6a69324010000008a47304402206568144ed5e7064d6176c74738b04c"
      "08ca19ca54ddeb480084b77f45eebfe57802207927d6975a5ac0e1bb36f5c053"
      "56dcda1f521770511ee5e03239c8e1eecf3aed0141045d74feae58c4c36d7c35"
      "beac05eddddc78b3ce4b02491a2eea72043978056a8bc439b99ddaad327207b0"
      "9ef16a8910828e805b0cc8c11fba5caea2ee939346d7ffffffff45c866b219b1"
      "76952508f8e5aea728f950186554fc4a5807e2186a8e1c4009e5000000008c49"
      "3046022100bd5d41662f98cfddc46e86ea7e4a3bc8fe9f1dfc5c4836eaf7df58"
      "2596cfe0e9022100fc459ae4f59b8279d679003b88935896acd10021b6e2e461"
      "9377e336b5296c5e014104c00bab76a708ba7064b2315420a1c533ca9945eeff"
      "9754cdc574224589e9113469b4e71752146a10028079e04948ecdf70609bf1b9"
      "801f6b73ab75947ac339e5ffffffff02ac4c8bd5000000001976a9148dce8946"
      "f1c7763bb60ea5cf16ef514cbed0633b88ac002f6859000000001976a9146a59"
      "ac0e8f553f292dfe5e9f3aaa1da93499c15e88ac00000000");

   BinaryRefReader brr(toUnser);

   StoredTx stx;
   stx.unserializeDBValue(brr);

   EXPECT_TRUE( stx.isInitialized());
   EXPECT_EQ(   stx.thisHash_,    origTx.getThisHash());
   EXPECT_EQ(   stx.lockTime_,    origTx.getLockTime());
   EXPECT_EQ(   stx.dataCopy_,    rawTxUnfrag_);
   EXPECT_FALSE(stx.isFragged_);
   EXPECT_EQ(   stx.version_,     1);
   EXPECT_EQ(   stx.blockHeight_, UINT32_MAX);
   EXPECT_EQ(   stx.duplicateID_,  UINT8_MAX);
   EXPECT_EQ(   stx.txIndex_,     UINT16_MAX);
   EXPECT_EQ(   stx.numTxOut_,    origTx.getNumTxOut());
   EXPECT_EQ(   stx.numBytes_,    origTx.getSize());
   EXPECT_EQ(   stx.fragBytes_,   370);
}



////////////////////////////////////////////////////////////////////////////////
TEST_F(StoredBlockObjTest, STxOutUnserialize)
{
   TxOut        txo0,  txo1;
   StoredTxOut stxo0, stxo1;

   stxo0.unserialize(rawTxOut0_);
   stxo1.unserialize(rawTxOut1_);
    txo0.unserialize(rawTxOut0_);
    txo1.unserialize(rawTxOut1_);

   uint64_t val0 = READ_UINT64_HEX_LE("ac4c8bd500000000");
   uint64_t val1 = READ_UINT64_HEX_LE("002f685900000000");

   EXPECT_EQ(stxo0.getSerializedTxOut(), rawTxOut0_);
   EXPECT_EQ(stxo0.getSerializedTxOut(), txo0.serialize());
   EXPECT_EQ(stxo1.getSerializedTxOut(), rawTxOut1_);
   EXPECT_EQ(stxo1.getSerializedTxOut(), txo1.serialize());

   EXPECT_EQ(stxo0.getValue(), val0);
   EXPECT_EQ(stxo1.getValue(), val1);
   
   TxOut txoRecon = stxo0.getTxOutCopy();
   EXPECT_EQ(txoRecon.serialize(), rawTxOut0_);
}

////////////////////////////////////////////////////////////////////////////////
TEST_F(StoredBlockObjTest, STxOutSerDBValue_1)
{
   DBUtils.setArmoryDbType(ARMORY_DB_FULL);
   DBUtils.setDbPruneType(DB_PRUNE_NONE);

   StoredTxOut stxo0;

   stxo0.unserialize(rawTxOut0_);

   stxo0.txVersion_ = 1;
   stxo0.spentness_ = TXOUT_UNSPENT;

   //   0123   45    67   0  123 4567 
   //  |----| |--|  |--| |-|
   //   DBVer TxVer Spnt  CB
   //
   // For this example:  DBVer=0, TxVer=1, TxSer=FRAGGED[1]
   //   0000   01    00   0  --- ----
   EXPECT_EQ(stxo0.serializeDBValue(),  READHEX("0400") + rawTxOut0_);
}
   

////////////////////////////////////////////////////////////////////////////////
TEST_F(StoredBlockObjTest, STxOutSerDBValue_2)
{
   DBUtils.setArmoryDbType(ARMORY_DB_FULL);
   DBUtils.setDbPruneType(DB_PRUNE_NONE);

   StoredTxOut stxo0;
   stxo0.unserialize(rawTxOut0_);
   stxo0.txVersion_ = 1;
   stxo0.spentness_ = TXOUT_UNSPENT;

   // Test a spent TxOut
   //   0000   01    01   0  --- ----
   BinaryData spentStr = DBUtils.getBlkDataKeyNoPrefix( 100000, 1, 127, 15);
   stxo0.spentness_ = TXOUT_SPENT;
   stxo0.spentByTxInKey_ = spentStr;
   EXPECT_EQ(stxo0.serializeDBValue(), READHEX("0500")+rawTxOut0_+spentStr);
}



////////////////////////////////////////////////////////////////////////////////
TEST_F(StoredBlockObjTest, STxOutSerDBValue_3)
{
   DBUtils.setArmoryDbType(ARMORY_DB_FULL);
   DBUtils.setDbPruneType(DB_PRUNE_NONE);

   StoredTxOut stxo0;
   stxo0.unserialize(rawTxOut0_);
   stxo0.txVersion_ = 1;
   stxo0.isCoinbase_ = true;

   // Test a spent TxOut but in lite mode where we don't record spentness
   //   0000   01    01   1  --- ----
   DBUtils.setArmoryDbType(ARMORY_DB_LITE);
   DBUtils.setDbPruneType(DB_PRUNE_NONE);
   BinaryData spentStr = DBUtils.getBlkDataKeyNoPrefix( 100000, 1, 127, 15);
   stxo0.spentness_ = TXOUT_SPENT;
   stxo0.spentByTxInKey_ = spentStr;
   EXPECT_EQ(stxo0.serializeDBValue(), READHEX("0680")+rawTxOut0_);
}


////////////////////////////////////////////////////////////////////////////////
TEST_F(StoredBlockObjTest, STxOutUnserDBValue_1)
{
   BinaryData input = READHEX( "0400ac4c8bd5000000001976a9148dce8946f1c7763b"
                               "b60ea5cf16ef514cbed0633b88ac");
   StoredTxOut stxo;
   stxo.unserializeDBValue(input);

   EXPECT_TRUE( stxo.isInitialized());
   EXPECT_EQ(   stxo.txVersion_,    1);
   EXPECT_EQ(   stxo.dataCopy_,     rawTxOut0_);
   EXPECT_EQ(   stxo.blockHeight_,  UINT32_MAX);
   EXPECT_EQ(   stxo.duplicateID_,   UINT8_MAX);
   EXPECT_EQ(   stxo.txIndex_,      UINT16_MAX);
   EXPECT_EQ(   stxo.txOutIndex_,   UINT16_MAX);
   EXPECT_EQ(   stxo.spentness_,    TXOUT_UNSPENT);
   EXPECT_EQ(   stxo.spentByTxInKey_.getSize(), 0);
   EXPECT_FALSE(stxo.isCoinbase_);
   EXPECT_EQ(   stxo.unserArmVer_,  0);
}
////////////////////////////////////////////////////////////////////////////////
TEST_F(StoredBlockObjTest, STxOutUnserDBValue_2)
{
   BinaryData input = READHEX( "0500ac4c8bd5000000001976a9148dce8946f1c7763b"
                               "b60ea5cf16ef514cbed0633b88ac01a086017f000f00");
   StoredTxOut stxo;
   stxo.unserializeDBValue(input);

   EXPECT_TRUE( stxo.isInitialized());
   EXPECT_EQ(   stxo.txVersion_,    1);
   EXPECT_EQ(   stxo.dataCopy_,     rawTxOut0_);
   EXPECT_EQ(   stxo.blockHeight_,  UINT32_MAX);
   EXPECT_EQ(   stxo.duplicateID_,   UINT8_MAX);
   EXPECT_EQ(   stxo.txIndex_,      UINT16_MAX);
   EXPECT_EQ(   stxo.txOutIndex_,   UINT16_MAX);
   EXPECT_EQ(   stxo.spentness_,    TXOUT_SPENT);
   EXPECT_FALSE(stxo.isCoinbase_);
   EXPECT_EQ(   stxo.spentByTxInKey_, READHEX("01a086017f000f00"));
   EXPECT_EQ(   stxo.unserArmVer_,  0);
}


////////////////////////////////////////////////////////////////////////////////
TEST_F(StoredBlockObjTest, STxOutUnserDBValue_3)
{
   BinaryData input = READHEX( "0680ac4c8bd5000000001976a9148dce8946f1c7763b"
                               "b60ea5cf16ef514cbed0633b88ac");
   StoredTxOut stxo;
   stxo.unserializeDBValue(input);

   EXPECT_TRUE( stxo.isInitialized());
   EXPECT_EQ(   stxo.txVersion_,    1);
   EXPECT_EQ(   stxo.dataCopy_,     rawTxOut0_);
   EXPECT_EQ(   stxo.blockHeight_,  UINT32_MAX);
   EXPECT_EQ(   stxo.duplicateID_,   UINT8_MAX);
   EXPECT_EQ(   stxo.txIndex_,      UINT16_MAX);
   EXPECT_EQ(   stxo.txOutIndex_,   UINT16_MAX);
   EXPECT_EQ(   stxo.spentness_,    TXOUT_SPENTUNK);
   EXPECT_TRUE( stxo.isCoinbase_);
   EXPECT_EQ(   stxo.spentByTxInKey_.getSize(), 0);
   EXPECT_EQ(   stxo.unserArmVer_,  0);
}


////////////////////////////////////////////////////////////////////////////////
TEST_F(StoredBlockObjTest, SHeaderFullBlock)
{
   // I'll make this more robust later... kind of tired of writing tests...
   StoredHeader sbh;
   sbh.unserializeFullBlock(rawBlock_.getRef());

   BinaryWriter bw;
   sbh.serializeFullBlock(bw);

   EXPECT_EQ(bw.getDataRef(), rawBlock_.getRef());
}


////////////////////////////////////////////////////////////////////////////////
TEST_F(StoredBlockObjTest, SUndoDataSer)
{
   DBUtils.setArmoryDbType(ARMORY_DB_FULL);
   DBUtils.setDbPruneType(DB_PRUNE_NONE);

   BinaryData arbHash  = READHEX("11112221111222111122222211112222"
                                 "11112221111222111122211112221111");
   BinaryData op0_str  = READHEX("aaaabbbbaaaabbbbaaaabbbbaaaabbbb"
                                 "aaaabbbbaaaabbbbaaaabbbbaaaabbbb");
   BinaryData op1_str  = READHEX("ffffbbbbffffbbbbffffbbbbffffbbbb"
                                 "ffffbbbbffffbbbbffffbbbbffffbbbb");

   
   StoredUndoData sud;
   OutPoint op0(op0_str, 1);
   OutPoint op1(op1_str, 2);

   StoredTxOut stxo0, stxo1;
   stxo0.unserialize(rawTxOut0_);
   stxo1.unserialize(rawTxOut1_);

   stxo0.txVersion_  = 1;
   stxo1.txVersion_  = 1;
   stxo0.blockHeight_ = 100000;
   stxo1.blockHeight_ = 100000;
   stxo0.duplicateID_ = 2;
   stxo1.duplicateID_ = 2;
   stxo0.txIndex_ = 17;
   stxo1.txIndex_ = 17;
   stxo0.parentHash_ = arbHash;
   stxo1.parentHash_ = arbHash;
   stxo0.txOutIndex_ = 5;
   stxo1.txOutIndex_ = 5;

   sud.stxOutsRemovedByBlock_.clear();
   sud.stxOutsRemovedByBlock_.push_back(stxo0);
   sud.stxOutsRemovedByBlock_.push_back(stxo1);
   sud.outPointsAddedByBlock_.clear();
   sud.outPointsAddedByBlock_.push_back(op0);
   sud.outPointsAddedByBlock_.push_back(op1);

   sud.blockHash_ = arbHash;
   sud.blockHeight_ = 123000; // unused for this test
   sud.duplicateID_ = 15;     // unused for this test

   BinaryData flags = READHEX("24");
   BinaryData str2  = WRITE_UINT32_LE(2);
   BinaryData str5  = WRITE_UINT32_LE(5);
   BinaryData answer = 
         arbHash + 
            str2 + 
               flags + stxo0.getDBKey(false) + arbHash + str5 + rawTxOut0_ +
               flags + stxo1.getDBKey(false) + arbHash + str5 + rawTxOut1_ +
            str2 +
               op0.serialize() +
               op1.serialize();

   EXPECT_EQ(sud.serializeDBValue(), answer);
}



////////////////////////////////////////////////////////////////////////////////
TEST_F(StoredBlockObjTest, SUndoDataUnser)
{
   DBUtils.setArmoryDbType(ARMORY_DB_FULL);
   DBUtils.setDbPruneType(DB_PRUNE_NONE);

   BinaryData arbHash  = READHEX("11112221111222111122222211112222"
                                 "11112221111222111122211112221111");
   BinaryData op0_str  = READHEX("aaaabbbbaaaabbbbaaaabbbbaaaabbbb"
                                 "aaaabbbbaaaabbbbaaaabbbbaaaabbbb");
   BinaryData op1_str  = READHEX("ffffbbbbffffbbbbffffbbbbffffbbbb"
                                 "ffffbbbbffffbbbbffffbbbbffffbbbb");
   OutPoint op0(op0_str, 1);
   OutPoint op1(op1_str, 2);

   //BinaryData sudToUnser = READHEX( 
      //"1111222111122211112222221111222211112221111222111122211112221111"
      //"0200000024111122211112221111222222111122221111222111122211112221"
      //"111222111105000000ac4c8bd5000000001976a9148dce8946f1c7763bb60ea5"
      //"cf16ef514cbed0633b88ac241111222111122211112222221111222211112221"
      //"11122211112221111222111105000000002f6859000000001976a9146a59ac0e"
      //"8f553f292dfe5e9f3aaa1da93499c15e88ac02000000aaaabbbbaaaabbbbaaaa"
      //"bbbbaaaabbbbaaaabbbbaaaabbbbaaaabbbbaaaabbbb01000000ffffbbbbffff"
      //"bbbbffffbbbbffffbbbbffffbbbbffffbbbbffffbbbbffffbbbb02000000");

   BinaryData sudToUnser = READHEX( 
      "1111222111122211112222221111222211112221111222111122211112221111"
      "02000000240186a0020011000511112221111222111122222211112222111122"
      "2111122211112221111222111105000000ac4c8bd5000000001976a9148dce89"
      "46f1c7763bb60ea5cf16ef514cbed0633b88ac240186a0020011000511112221"
      "1112221111222222111122221111222111122211112221111222111105000000"
      "002f6859000000001976a9146a59ac0e8f553f292dfe5e9f3aaa1da93499c15e"
      "88ac02000000aaaabbbbaaaabbbbaaaabbbbaaaabbbbaaaabbbbaaaabbbbaaaa"
      "bbbbaaaabbbb01000000ffffbbbbffffbbbbffffbbbbffffbbbbffffbbbbffff"
      "bbbbffffbbbbffffbbbb02000000");

   StoredUndoData sud;
   sud.unserializeDBValue(sudToUnser);

   ASSERT_EQ(sud.outPointsAddedByBlock_.size(), 2);
   ASSERT_EQ(sud.stxOutsRemovedByBlock_.size(), 2);

   EXPECT_EQ(sud.outPointsAddedByBlock_[0].serialize(), op0.serialize());
   EXPECT_EQ(sud.outPointsAddedByBlock_[1].serialize(), op1.serialize());
   EXPECT_EQ(sud.stxOutsRemovedByBlock_[0].getSerializedTxOut(), rawTxOut0_);
   EXPECT_EQ(sud.stxOutsRemovedByBlock_[1].getSerializedTxOut(), rawTxOut1_);

   EXPECT_EQ(sud.stxOutsRemovedByBlock_[0].parentHash_, arbHash);
   EXPECT_EQ(sud.stxOutsRemovedByBlock_[1].parentHash_, arbHash);

   EXPECT_EQ(sud.stxOutsRemovedByBlock_[0].blockHeight_, 100000);
   EXPECT_EQ(sud.stxOutsRemovedByBlock_[1].blockHeight_, 100000);
   EXPECT_EQ(sud.stxOutsRemovedByBlock_[0].duplicateID_, 2);
   EXPECT_EQ(sud.stxOutsRemovedByBlock_[1].duplicateID_, 2);
   EXPECT_EQ(sud.stxOutsRemovedByBlock_[0].txIndex_, 17);
   EXPECT_EQ(sud.stxOutsRemovedByBlock_[1].txIndex_, 17);
}


////////////////////////////////////////////////////////////////////////////////
TEST_F(StoredBlockObjTest, STxHintsSer)
{
   BinaryData hint0 = DBUtils.getBlkDataKeyNoPrefix(123000,  7, 255);
   BinaryData hint1 = DBUtils.getBlkDataKeyNoPrefix(123000, 15, 127);
   BinaryData hint2 = DBUtils.getBlkDataKeyNoPrefix(183922, 15,   3);

   StoredTxHints sths;
   sths.txHashPrefix_ = READHEX("aaaaffff");
   sths.dbKeyList_.clear();

   /////
   BinaryWriter ans0;
   ans0.put_var_int(0);
   EXPECT_EQ(sths.serializeDBValue(), ans0.getData());

   /////
   sths.dbKeyList_.push_back(hint0);
   sths.preferredDBKey_ = hint0;
   BinaryWriter ans1;
   ans1.put_var_int(1);
   ans1.put_BinaryData(hint0);
   EXPECT_EQ(sths.dbKeyList_.size(), 1);
   EXPECT_EQ(sths.preferredDBKey_, hint0);
   EXPECT_EQ(sths.serializeDBValue(), ans1.getData());

   /////
   sths.dbKeyList_.push_back(hint1);
   sths.dbKeyList_.push_back(hint2);
   BinaryWriter ans3;
   ans3.put_var_int(3);
   ans3.put_BinaryData(hint0);
   ans3.put_BinaryData(hint1);
   ans3.put_BinaryData(hint2);
   EXPECT_EQ(sths.dbKeyList_.size(), 3);
   EXPECT_EQ(sths.preferredDBKey_, hint0);
   EXPECT_EQ(sths.serializeDBValue(), ans3.getData());
}

////////////////////////////////////////////////////////////////////////////////
TEST_F(StoredBlockObjTest, STxHintsReorder)
{
   BinaryData hint0 = DBUtils.getBlkDataKeyNoPrefix(123000,  7, 255);
   BinaryData hint1 = DBUtils.getBlkDataKeyNoPrefix(123000, 15, 127);
   BinaryData hint2 = DBUtils.getBlkDataKeyNoPrefix(183922, 15,   3);

   StoredTxHints sths;
   sths.txHashPrefix_ = READHEX("aaaaffff");
   sths.dbKeyList_.clear();
   sths.dbKeyList_.push_back(hint0);
   sths.dbKeyList_.push_back(hint1);
   sths.dbKeyList_.push_back(hint2);
   sths.preferredDBKey_ = hint1;

   BinaryWriter expectedOut;
   expectedOut.put_var_int(3);
   expectedOut.put_BinaryData(hint1);
   expectedOut.put_BinaryData(hint0);
   expectedOut.put_BinaryData(hint2);

   EXPECT_EQ(sths.serializeDBValue(), expectedOut.getData());
}

////////////////////////////////////////////////////////////////////////////////
TEST_F(StoredBlockObjTest, STxHintsUnser)
{
   BinaryData hint0 = DBUtils.getBlkDataKeyNoPrefix(123000,  7, 255);
   BinaryData hint1 = DBUtils.getBlkDataKeyNoPrefix(123000, 15, 127);
   BinaryData hint2 = DBUtils.getBlkDataKeyNoPrefix(183922, 15,   3);

   BinaryData in0 = READHEX("00");
   BinaryData in1 = READHEX("01""01e0780700ff");
   BinaryData in3 = READHEX("03""01e0780700ff""01e0780f007f""02ce720f0003");

   StoredTxHints sths0, sths1, sths3;

   sths0.unserializeDBValue(in0);

   EXPECT_EQ(sths0.dbKeyList_.size(), 0);
   EXPECT_EQ(sths0.preferredDBKey_.getSize(), 0);

   sths1.unserializeDBValue(in1);

   EXPECT_EQ(sths1.dbKeyList_.size(),  1);
   EXPECT_EQ(sths1.dbKeyList_[0],      hint0);
   EXPECT_EQ(sths1.preferredDBKey_,    hint0);

   sths3.unserializeDBValue(in3);
   EXPECT_EQ(sths3.dbKeyList_.size(),  3);
   EXPECT_EQ(sths3.dbKeyList_[0],      hint0);
   EXPECT_EQ(sths3.dbKeyList_[1],      hint1);
   EXPECT_EQ(sths3.dbKeyList_[2],      hint2);
   EXPECT_EQ(sths3.preferredDBKey_,    hint0);
}

////////////////////////////////////////////////////////////////////////////////
TEST_F(StoredBlockObjTest, SHeadHgtListSer)
{
   StoredHeadHgtList baseHHL, testHHL;
   baseHHL.height_ = 123000;
   baseHHL.dupAndHashList_.resize(0);
   BinaryData hash0 = READHEX("aaaabbbbaaaabbbbaaaabbbbaaaabbbb"
                              "aaaabbbbaaaabbbbaaaabbbbaaaabbbb");
   BinaryData hash1 = READHEX("2222bbbb2222bbbb2222bbbb2222bbbb"
                              "2222bbbb2222bbbb2222bbbb2222bbbb");
   BinaryData hash2 = READHEX("2222ffff2222ffff2222ffff2222ffff"
                              "2222ffff2222ffff2222ffff2222ffff");

   uint8_t dup0 = 0;
   uint8_t dup1 = 1;
   uint8_t dup2 = 7;

   BinaryWriter expectOut;

   // Test writing empty list
   expectOut.reset();
   expectOut.put_uint8_t(0);
   EXPECT_EQ(testHHL.serializeDBValue(), expectOut.getData());

   
   // Test writing list with one entry but no preferred dupID
   expectOut.reset();
   testHHL = baseHHL;
   testHHL.dupAndHashList_.push_back(pair<uint8_t, BinaryData>(dup0, hash0)); 
   expectOut.put_uint8_t(1);
   expectOut.put_uint8_t(dup0);
   expectOut.put_BinaryData(hash0);
   EXPECT_EQ(testHHL.serializeDBValue(), expectOut.getData());
   
   // Test writing list with one entry which is a preferred dupID
   expectOut.reset();
   testHHL = baseHHL;
   testHHL.preferredDup_ = 0;
   testHHL.dupAndHashList_.push_back(pair<uint8_t, BinaryData>(dup0, hash0)); 
   expectOut.put_uint8_t(1);
   expectOut.put_uint8_t(dup0 | 0x80);
   expectOut.put_BinaryData(hash0);
   EXPECT_EQ(testHHL.serializeDBValue(), expectOut.getData());

   // Test writing list with one entry preferred dupID but that dup isn't avail
   expectOut.reset();
   testHHL = baseHHL;
   testHHL.preferredDup_ = 1;
   testHHL.dupAndHashList_.push_back(pair<uint8_t, BinaryData>(dup0, hash0)); 
   expectOut.put_uint8_t(1);
   expectOut.put_uint8_t(dup0);
   expectOut.put_BinaryData(hash0);
   EXPECT_EQ(testHHL.serializeDBValue(), expectOut.getData());

   // Test writing with three entries, no preferred
   expectOut.reset();
   testHHL = baseHHL;
   testHHL.dupAndHashList_.push_back(pair<uint8_t, BinaryData>(dup0, hash0)); 
   testHHL.dupAndHashList_.push_back(pair<uint8_t, BinaryData>(dup1, hash1)); 
   testHHL.dupAndHashList_.push_back(pair<uint8_t, BinaryData>(dup2, hash2)); 
   expectOut.put_uint8_t(3);
   expectOut.put_uint8_t(dup0); expectOut.put_BinaryData(hash0);
   expectOut.put_uint8_t(dup1); expectOut.put_BinaryData(hash1);
   expectOut.put_uint8_t(dup2); expectOut.put_BinaryData(hash2);
   EXPECT_EQ(testHHL.serializeDBValue(), expectOut.getData());


   // Test writing with three entries, with preferred
   expectOut.reset();
   testHHL = baseHHL;
   testHHL.dupAndHashList_.push_back(pair<uint8_t, BinaryData>(dup0, hash0)); 
   testHHL.dupAndHashList_.push_back(pair<uint8_t, BinaryData>(dup1, hash1)); 
   testHHL.dupAndHashList_.push_back(pair<uint8_t, BinaryData>(dup2, hash2)); 
   testHHL.preferredDup_ = 1;
   expectOut.put_uint8_t(3);
   expectOut.put_uint8_t(dup1 | 0x80); expectOut.put_BinaryData(hash1);
   expectOut.put_uint8_t(dup0);        expectOut.put_BinaryData(hash0);
   expectOut.put_uint8_t(dup2);        expectOut.put_BinaryData(hash2);
   EXPECT_EQ(testHHL.serializeDBValue(), expectOut.getData());
}


////////////////////////////////////////////////////////////////////////////////
TEST_F(StoredBlockObjTest, SHeadHgtListUnser)
{
   BinaryData hash0 = READHEX("aaaabbbbaaaabbbbaaaabbbbaaaabbbb"
                              "aaaabbbbaaaabbbbaaaabbbbaaaabbbb");
   BinaryData hash1 = READHEX("2222bbbb2222bbbb2222bbbb2222bbbb"
                              "2222bbbb2222bbbb2222bbbb2222bbbb");
   BinaryData hash2 = READHEX("2222ffff2222ffff2222ffff2222ffff"
                              "2222ffff2222ffff2222ffff2222ffff");

   vector<BinaryData> tests;
   tests.push_back( READHEX(
      "0100aaaabbbbaaaabbbbaaaabbbbaaaabbbbaaaabbbbaaaabbbbaaaabbbbaaaabbbb"));
   tests.push_back( READHEX(
      "0180aaaabbbbaaaabbbbaaaabbbbaaaabbbbaaaabbbbaaaabbbbaaaabbbbaaaabbbb"));
   tests.push_back( READHEX(
      "0300aaaabbbbaaaabbbbaaaabbbbaaaabbbbaaaabbbbaaaabbbbaaaabbbbaaaa"
      "bbbb012222bbbb2222bbbb2222bbbb2222bbbb2222bbbb2222bbbb2222bbbb22"
      "22bbbb072222ffff2222ffff2222ffff2222ffff2222ffff2222ffff2222ffff"
      "2222ffff"));
   tests.push_back( READHEX(
      "03812222bbbb2222bbbb2222bbbb2222bbbb2222bbbb2222bbbb2222bbbb2222"
      "bbbb00aaaabbbbaaaabbbbaaaabbbbaaaabbbbaaaabbbbaaaabbbbaaaabbbbaa"
      "aabbbb072222ffff2222ffff2222ffff2222ffff2222ffff2222ffff2222ffff"
      "2222ffff"));

   uint8_t dup0 = 0;
   uint8_t dup1 = 1;
   uint8_t dup2 = 7;

   for(uint32_t i=0; i<tests.size(); i++)
   {
      BinaryRefReader brr(tests[i]);
      StoredHeadHgtList hhl;
      hhl.unserializeDBValue(brr);

      if(i==0)
      {
         ASSERT_EQ(hhl.dupAndHashList_.size(), 1);
         EXPECT_EQ(hhl.dupAndHashList_[0].first,  dup0);
         EXPECT_EQ(hhl.dupAndHashList_[0].second, hash0);
         EXPECT_EQ(hhl.preferredDup_,  UINT8_MAX);
      }
      else if(i==1)
      {
         ASSERT_EQ(hhl.dupAndHashList_.size(), 1);
         EXPECT_EQ(hhl.dupAndHashList_[0].first,  dup0);
         EXPECT_EQ(hhl.dupAndHashList_[0].second, hash0);
         EXPECT_EQ(hhl.preferredDup_,  0);
      }
      else if(i==2)
      {
         ASSERT_EQ(hhl.dupAndHashList_.size(), 3);
         EXPECT_EQ(hhl.dupAndHashList_[0].first,  dup0);
         EXPECT_EQ(hhl.dupAndHashList_[0].second, hash0);
         EXPECT_EQ(hhl.dupAndHashList_[1].first,  dup1);
         EXPECT_EQ(hhl.dupAndHashList_[1].second, hash1);
         EXPECT_EQ(hhl.dupAndHashList_[2].first,  dup2);
         EXPECT_EQ(hhl.dupAndHashList_[2].second, hash2);
         EXPECT_EQ(hhl.preferredDup_,  UINT8_MAX);
      }
      else if(i==3)
      {
         ASSERT_EQ(hhl.dupAndHashList_.size(), 3);
         EXPECT_EQ(hhl.dupAndHashList_[0].first,  dup1);
         EXPECT_EQ(hhl.dupAndHashList_[0].second, hash1);
         EXPECT_EQ(hhl.dupAndHashList_[1].first,  dup0);
         EXPECT_EQ(hhl.dupAndHashList_[1].second, hash0);
         EXPECT_EQ(hhl.dupAndHashList_[2].first,  dup2);
         EXPECT_EQ(hhl.dupAndHashList_[2].second, hash2);
         EXPECT_EQ(hhl.preferredDup_,  1);
      }
   }
}

////////////////////////////////////////////////////////////////////////////////
TEST_F(StoredBlockObjTest, SScriptHistorySer)
{
   StoredScriptHistory ssh;
   ssh.uniqueKey_ = READHEX("00""1234abcde1234abcde1234abcdefff1234abcdef");
   ssh.version_ = 1;
   ssh.alreadyScannedUpToBlk_ = 65535;

   /////////////////////////////////////////////////////////////////////////////
   // Empty SSH (probably shouldn't even be serialized/written, in the future)
   BinaryData expect, expSub1, expSub2;
   expect = READHEX("0400""ffff0000""00");
   EXPECT_EQ(ssh.serializeDBValue(), expect);

   /////////////////////////////////////////////////////////////////////////////
   // With a single TxIO
   TxIOPair txio0(READHEX("0000ff00""0001""0001"), READ_UINT64_HEX_LE("0100000000000000"));
   txio0.setFromCoinbase(false);
   txio0.setTxOutFromSelf(false);
   txio0.setMultisig(false);
   ssh.insertTxio(txio0);

   expect = READHEX("0400""ffff0000""01""00""0100000000000000""0000ff00""0001""0001");
   EXPECT_EQ(ssh.serializeDBValue(), expect);

   /////////////////////////////////////////////////////////////////////////////
   // Added a second one, different subSSH
   TxIOPair txio1(READHEX("00010000""0002""0002"), READ_UINT64_HEX_LE("0002000000000000"));
   ssh.insertTxio(txio1);
   expect  = READHEX("0480""ffff0000""02""0102000000000000");
   expSub1 = READHEX("01""00""0100000000000000""0001""0001");
   expSub2 = READHEX("01""00""0002000000000000""0002""0002");
   EXPECT_EQ(ssh.serializeDBValue(), expect);
   EXPECT_EQ(ssh.subHistMap_[READHEX("0000ff00")].serializeDBValue(), expSub1);
   EXPECT_EQ(ssh.subHistMap_[READHEX("00010000")].serializeDBValue(), expSub2);

   /////////////////////////////////////////////////////////////////////////////
   // Added another TxIO to the second subSSH
   TxIOPair txio2(READHEX("00010000""0004""0004"), READ_UINT64_HEX_LE("0000030000000000"));
   ssh.insertTxio(txio2);
   expect  = READHEX("0480""ffff0000""03""0102030000000000");
   expSub1 = READHEX("01"
                       "00""0100000000000000""0001""0001");
   expSub2 = READHEX("02"
                       "00""0002000000000000""0002""0002"
                       "00""0000030000000000""0004""0004");
   EXPECT_EQ(ssh.serializeDBValue(), expect);
   EXPECT_EQ(ssh.subHistMap_[READHEX("0000ff00")].serializeDBValue(), expSub1);
   EXPECT_EQ(ssh.subHistMap_[READHEX("00010000")].serializeDBValue(), expSub2);

   /////////////////////////////////////////////////////////////////////////////
   // Now we explicitly delete a TxIO (with pruning, this should be basically
   // equivalent to marking it spent, but we are DB-mode-agnostic here, testing
   // just the base insert/erase operations)
   ssh.eraseTxio(txio1);
   expect  = READHEX("0480""ffff0000""02""0100030000000000");
   expSub1 = READHEX("01"
                       "00""0100000000000000""0001""0001");
   expSub2 = READHEX("01"
                       "00""0000030000000000""0004""0004");
   EXPECT_EQ(ssh.serializeDBValue(), expect);
   EXPECT_EQ(ssh.subHistMap_[READHEX("0000ff00")].serializeDBValue(), expSub1);
   EXPECT_EQ(ssh.subHistMap_[READHEX("00010000")].serializeDBValue(), expSub2);
   
   /////////////////////////////////////////////////////////////////////////////
   // Insert a multisig TxIO -- this should increment totalTxioCount_, but not 
   // the value 
   TxIOPair txio3(READHEX("00010000""0006""0006"), READ_UINT64_HEX_LE("0000000400000000"));
   txio3.setMultisig(true);
   ssh.insertTxio(txio3);
   expect  = READHEX("0480""ffff0000""03""0100030000000000");
   expSub1 = READHEX("01"
                       "00""0100000000000000""0001""0001");
   expSub2 = READHEX("02"
                       "00""0000030000000000""0004""0004"
                       "10""0000000400000000""0006""0006");
   EXPECT_EQ(ssh.serializeDBValue(), expect);
   EXPECT_EQ(ssh.subHistMap_[READHEX("0000ff00")].serializeDBValue(), expSub1);
   EXPECT_EQ(ssh.subHistMap_[READHEX("00010000")].serializeDBValue(), expSub2);
   
   /////////////////////////////////////////////////////////////////////////////
   // Remove the multisig
   ssh.eraseTxio(txio3);
   expect  = READHEX("0480""ffff0000""02""0100030000000000");
   expSub1 = READHEX("01"
                       "00""0100000000000000""0001""0001");
   expSub2 = READHEX("01"
                       "00""0000030000000000""0004""0004");
   EXPECT_EQ(ssh.serializeDBValue(), expect);
   EXPECT_EQ(ssh.subHistMap_[READHEX("0000ff00")].serializeDBValue(), expSub1);
   EXPECT_EQ(ssh.subHistMap_[READHEX("00010000")].serializeDBValue(), expSub2);

   /////////////////////////////////////////////////////////////////////////////
   // Remove a full subSSH (it shouldn't be deleted, though, that will be done
   // by BlockUtils in a post-processing step
   ssh.eraseTxio(txio0);
   expect  = READHEX("0480""ffff0000""01""0000030000000000");
   expSub1 = READHEX("00");
   expSub2 = READHEX("01"
                       "00""0000030000000000""0004""0004");
   EXPECT_EQ(ssh.serializeDBValue(), expect);
   EXPECT_EQ(ssh.subHistMap_[READHEX("0000ff00")].serializeDBValue(), expSub1);
   EXPECT_EQ(ssh.subHistMap_[READHEX("00010000")].serializeDBValue(), expSub2);
   
}

////////////////////////////////////////////////////////////////////////////////
TEST_F(StoredBlockObjTest, SScriptHistoryUnser)
{
   StoredScriptHistory ssh, sshorig;
   BinaryData toUnser;
   BinaryData hgtX0 = READHEX("0000ff00");
   BinaryData hgtX1 = READHEX("00010000");
   BinaryData uniq  = READHEX("00""01ab01ab01ab01ab01ab01ab01ab01ab01ab01ab");

   sshorig.uniqueKey_ = uniq;
   sshorig.version_  = 1;

   /////////////////////////////////////////////////////////////////////////////
   ssh = sshorig;
   toUnser = READHEX("0400""ffff0000""00");
   ssh.unserializeDBValue(toUnser);

   EXPECT_EQ(   ssh.subHistMap_.size(), 0);
   EXPECT_FALSE(ssh.useMultipleEntries_);
   EXPECT_EQ(   ssh.alreadyScannedUpToBlk_, 65535);
   EXPECT_EQ(   ssh.totalTxioCount_, 0);
   EXPECT_EQ(   ssh.totalUnspent_, 0);

   /////////////////////////////////////////////////////////////////////////////
   ssh = sshorig;
   toUnser = READHEX("0400""ffff0000""01""00""0100000000000000""0000ff00""0001""0001");
   ssh.unserializeDBValue(toUnser);
   BinaryData txioKey = hgtX0 + READHEX("00010001");

   EXPECT_EQ(   ssh.subHistMap_.size(), 1);
   EXPECT_FALSE(ssh.useMultipleEntries_);
   EXPECT_EQ(   ssh.alreadyScannedUpToBlk_, 65535);
   EXPECT_EQ(   ssh.totalTxioCount_, 1);
   EXPECT_EQ(   ssh.totalUnspent_, READ_UINT64_HEX_LE("0100000000000000"));
   ASSERT_NE(   ssh.subHistMap_.find(hgtX0), ssh.subHistMap_.end());
   StoredSubHistory & subssh = ssh.subHistMap_[hgtX0];
   EXPECT_EQ(   subssh.uniqueKey_, uniq);
   EXPECT_EQ(   subssh.hgtX_, hgtX0);
   EXPECT_EQ(   subssh.txioSet_.size(), 1);
   ASSERT_NE(   subssh.txioSet_.find(txioKey), subssh.txioSet_.end());
   TxIOPair & txio = subssh.txioSet_[txioKey];
   EXPECT_EQ(   txio.getValue(), READ_UINT64_HEX_LE("0100000000000000"));
   EXPECT_EQ(   txio.getDBKeyOfOutput(), READHEX("0000ff0000010001"));

}

////////////////////////////////////////////////////////////////////////////////
/*
TEST_F(StoredBlockObjTest, SScriptHistoryMarkSpent)
{
   DBUtils.setArmoryDbType(ARMORY_DB_SUPER);
   DBUtils.setDbPruneType(DB_PRUNE_NONE);

   StoredScriptHistory ssh;

   BinaryData a160 = READHEX("aabbccdd11223344aabbccdd11223344aabbccdd"); 

   BinaryData dbKey0 = READHEX("01e078""0f""0007""0001");
   BinaryData dbKey1 = READHEX("01e078""0f""0009""0005");
   BinaryData dbKey2 = READHEX("01e078""0f""000f""0000");
   BinaryData dbKey3 = READHEX("02e078""0f""0030""0003");
   BinaryData dbKey4 = READHEX("02e078""0f""0030""0009");
   BinaryData dbKey5 = READHEX("02e078""0f""00a0""0008");

   uint32_t hgt = READ_UINT32_HEX_BE("0001e078");
   uint32_t dup = READ_UINT8_HEX_BE("0f");

   TxIOPair txio0(dbKey0, 10*COIN);
   TxIOPair txio1(dbKey1, 11*COIN);
   TxIOPair txio2(dbKey2, 12*COIN);
   TxIOPair txio3(dbKey3, 13*COIN);

   txio0.setFromCoinbase(true);
   txio0.setTxOutFromSelf(false);
   txio0.setMultisig(false);

   txio1.setFromCoinbase(false);
   txio1.setTxOutFromSelf(true);
   txio1.setMultisig(false);

   txio2.setFromCoinbase(false);
   txio2.setTxOutFromSelf(false);
   txio2.setMultisig(true);

   txio3.setFromCoinbase(false);
   txio3.setTxOutFromSelf(false);
   txio3.setMultisig(true);

   //BinaryData dbKey0 = READHEX("01e078""0f""0007""0001");
   //BinaryData dbKey1 = READHEX("01e078""0f""0009""0005");
   //BinaryData dbKey2 = READHEX("01e078""0f""000f""0000");
   //BinaryData dbKey3 = READHEX("02e078""0f""0030""0003");
   //BinaryData dbKey4 = READHEX("02e078""0f""0030""0009");
   //BinaryData dbKey5 = READHEX("02e078""0f""00a0""0008");

   // First test, only one TxIO, stored in base SSH object
   BinaryData expect_ssh1 = READHEX(
      "0400""ffffffff"
      "01"
         "40""00ca9a3b00000000""01e0780f0007""0001")


   // First test, only one TxIO, stored in base SSH object
   BinaryData expectSSH_ssh2 = READHEX(
      "0480""ffffffff""02""00752b7d00000000")
   BinaryData expectSSH_ssh2sub1 = READHEX(
      "02"
         "00""00ca9a3b00000000""0007""0001"
         "00""00ab904100000000""0009""0005");


   BinaryData expectSSH_bothspent = READHEX(
      "0400""ffffffff"
      "02"
         "60""00ca9a3b00000000""01e0780f0007""0001""01e0780f00a00008"
         "a0""0065cd1d00000000""01e0780f0009""0005""01e0780f000f0000"
      "02"
         "01e0780f00300003"
         "01e0780f00300009");

   BinaryData expectSSH_bothunspent = READHEX(
      "0400""ffffffff"
      "02"
         "40""00ca9a3b00000000""01e0780f0007""0001"
         "80""0065cd1d00000000""01e0780f0009""0005"
      "02"
         "01e0780f00300003"
         "01e0780f00300009");

   BinaryData expectSSH_afterrm = READHEX(
      "0400""ffffffff"
      "01"
         "40""00ca9a3b00000000""01e0780f0007""0001"
      "02"
         "01e0780f00300003"
         "01e0780f00300009");
  
   // Mark the second one spent (from same block as it was created)
   txio1.setTxIn(dbKey4);

   // In order for for these tests to work properly, the TxIns and TxOuts need
   // to look like they're in the main branch.  Se we set the valid dupID vals
   // so that txio.hasTxInInMain() and txio.hasTxOutInMain() both pass
   LevelDBWrapper::GetInterfacePtr()->setValidDupIDForHeight(hgt,dup);

   ssh.uniqueKey_ = HASH160PREFIX + a160;
   ssh.version_ = 1;
   ssh.alreadyScannedUpToBlk_ = UINT32_MAX;

   ssh.markTxOutUnspent(txio0);

   // Check the initial state matches expectations
   EXPECT_EQ(ssh.serializeDBValue(), expectSSH_orig);

   ssh.insertTxio(txio1);
   // Mark the first output spent (second one was already marked spent)
   ssh.markTxOutSpent( dbKey0, dbKey5);
   EXPECT_EQ(ssh.serializeDBValue(), expectSSH_bothspent);

   // Undo the last operation
   ssh.markTxOutUnspent(dbKey0);
   EXPECT_EQ(ssh.serializeDBValue(), expectSSH_orig);


   ssh.markTxOutUnspent(dbKey1);
   EXPECT_EQ(ssh.serializeDBValue(), expectSSH_bothunspent);

   ssh.markTxOutSpent( dbKey1, dbKey2);
   EXPECT_EQ(ssh.serializeDBValue(), expectSSH_orig);


   ssh.eraseTxio(dbKey1);
   EXPECT_EQ(ssh.serializeDBValue(), expectSSH_afterrm);

}
*/

////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
class TxRefTest : public ::testing::Test
{
protected:
};


////////////////////////////////////////////////////////////////////////////////
TEST_F(TxRefTest, TxRefNoInit)
{
   TxRef txr;
   EXPECT_FALSE(txr.isInitialized());
   //EXPECT_FALSE(txr.isBound());

   EXPECT_EQ(txr.getDBKey(),     BinaryData(0));
   EXPECT_EQ(txr.getDBKeyRef(),  BinaryDataRef());
   //EXPECT_EQ(txr.getBlockTimestamp(), UINT32_MAX);
   EXPECT_EQ(txr.getBlockHeight(),    UINT32_MAX);
   EXPECT_EQ(txr.getDuplicateID(),    UINT8_MAX );
   EXPECT_EQ(txr.getBlockTxIndex(),   UINT16_MAX);
}

////////////////////////////////////////////////////////////////////////////////
TEST_F(TxRefTest, TxRefKeyParts)
{
   TxRef txr;
   BinaryData    newKey = READHEX("e3c4027f000f");
   BinaryDataRef newRef(newKey);


   txr.setDBKey(newKey);
   EXPECT_EQ(txr.getDBKey(),    newKey);
   EXPECT_EQ(txr.getDBKeyRef(), newRef);

   EXPECT_EQ(txr.getBlockHeight(),  0xe3c402);
   EXPECT_EQ(txr.getDuplicateID(),  127);
   EXPECT_EQ(txr.getBlockTxIndex(), 15);
}


////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
// TODO:  These tests were taken directly from the BlockUtilsTest.cpp where 
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
   for(uint32_t i=0; i<7; i++)
   {
      for(uint32_t j=0; j<7; j++)
         isOurs[j] = i==j;

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
   for(uint32_t i=0; i<512; i++)
   {
      if(i<256)
      { 
         // 2/3 of leaves will be selected
         for(uint32_t j=0; j<7; j++)
            isOurs[j] = (rand() % 3 < 2);  
      }
      else
      {
         // 1/3 of leaves will be selected
         for(uint32_t j=0; j<7; j++)
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
      cout << "Equal? " << (pmtSer==pmtSer2 ? "True" : "False") << endl;

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
class BlockUtilsTest : public ::testing::Test
{
protected:

   /////////////////////////////////////////////////////////////////////////////
   virtual void SetUp(void) 
   {
      iface_ = LevelDBWrapper::GetInterfacePtr();
      magic_ = READHEX(MAINNET_MAGIC_BYTES);
      ghash_ = READHEX(MAINNET_GENESIS_HASH_HEX);
      gentx_ = READHEX(MAINNET_GENESIS_TX_HASH_HEX);
      zeros_ = READHEX("00000000");
      DBUtils.setArmoryDbType(ARMORY_DB_FULL);
      DBUtils.setDbPruneType(DB_PRUNE_NONE);

      blkdir_  = string("./blkfiletest");
      homedir_ = string("./fakehomedir");
      ldbdir_  = string("./ldbtestdir");

      iface_->openDatabases( ldbdir_, ghash_, gentx_, magic_, 
                             ARMORY_DB_SUPER, DB_PRUNE_NONE);
      if(!iface_->databasesAreOpen())
         LOGERR << "ERROR OPENING DATABASES FOR TESTING!";

      mkdir(blkdir_);
      mkdir(homedir_);

      // Put the first 5 blocks into the blkdir
      blk0dat_ = BtcUtils::getBlkFilename(blkdir_, 0);
      copyFile("../reorgTest/blk_0_to_4.dat", blk0dat_);

      TheBDM.SelectNetwork("Main");
      TheBDM.SetBlkFileLocation(blkdir_);
      TheBDM.SetHomeDirLocation(homedir_);

      blkHash0 = READHEX("6fe28c0ab6f1b372c1a6a246ae63f74f931e8365e15a089c68d6190000000000");
      blkHash1 = READHEX("1b5514b83257d924be7f10c65b95b1f3c0e50081e1dfd8943eece5eb00000000");
      blkHash2 = READHEX("979fc39616bf1dc6b1f88167f76383d44d65ccd0fc99b7f91bcb2c9500000000");
      blkHash3 = READHEX("50f8231e5fd476f470e1ba4937bc97cb304136c96c765339308935bc00000000");
      blkHash4 = READHEX("8e121ba0d275f49a21bbc171d7d49890de13c9b9733e0104654d262f00000000");
      blkHash3A= READHEX("dd63f62ef59d5b6a6da2a36407f76e4e28026a3fd3a46700d284424700000000");
      blkHash4A= READHEX("bfa204022816102169b4e1d4f78cdf77258048f6d14282144cc01d5500000000");
      blkHash5A= READHEX("4e049fd71ef7381a73e4f550d97812d1eb0fbd1489c1774e18855f1900000000");

      addrA_ = READHEX("62e907b15cbf27d5425399ebf6f0fb50ebb88f18");
      addrB_ = READHEX("ee26c56fc1d942be8d7a24b2a1001dd894693980");
      addrC_ = READHEX("cb2abde8bccacc32e893df3a054b9ef7f227a4ce");
      addrD_ = READHEX("c522664fb0e55cdc5c0cea73b4aad97ec8343232");
   }


   /////////////////////////////////////////////////////////////////////////////
   virtual void TearDown(void)
   {
      rmdir(blkdir_);
      rmdir(homedir_);

      char* delstr = new char[4096];
      sprintf(delstr, "%s/level*", ldbdir_.c_str());
      rmdir(delstr);
      delete[] delstr;

      BlockDataManager_LevelDB::DestroyInstance();
   }


   /////////////////////////////////////////////////////////////////////////////
   // Simple method for copying files (works in all OS, probably not efficient)
   bool copyFile(string src, string dst, uint32_t nbytes=UINT32_MAX)
   {
      uint32_t srcsz = BtcUtils::GetFileSize(src);
      if(srcsz == FILE_DOES_NOT_EXIST)
         return false;

      srcsz = min(srcsz, nbytes);
   
      BinaryData temp(srcsz);
      ifstream is(src.c_str(), ios::in  | ios::binary);
      is.read((char*)temp.getPtr(), srcsz);
      is.close();
   
      ofstream os(dst.c_str(), ios::out | ios::binary);
      os.write((char*)temp.getPtr(), srcsz);
      os.close();
      return true;
   }

   /////////////////////////////////////////////////////////////////////////////
   // Simple method for copying files (works in all OS, probably not efficient)
   bool appendFile(string src, string dst)
   {
      uint32_t srcsz = BtcUtils::GetFileSize(src);
      if(srcsz == FILE_DOES_NOT_EXIST)
         return false;
   
      BinaryData temp(srcsz);
      ifstream is(src.c_str(), ios::in  | ios::binary);
      is.read((char*)temp.getPtr(), srcsz);
      is.close();
   
      ofstream os(dst.c_str(), ios::app | ios::binary);
      os.write((char*)temp.getPtr(), srcsz);
      os.close();
      return true;
   }

#if defined(_MSC_VER) || defined(__MINGW32__)
   compile_error_fixme_what_to_do_in_windows;
#else

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

   InterfaceToLDB* iface_;
   BinaryData magic_;
   BinaryData ghash_;
   BinaryData gentx_;
   BinaryData zeros_;

   string blkdir_;
   string homedir_;
   string ldbdir_;
   string blk0dat_;;

   BinaryData blkHash0;
   BinaryData blkHash1;
   BinaryData blkHash2;
   BinaryData blkHash3;
   BinaryData blkHash4;
   BinaryData blkHash3A;
   BinaryData blkHash4A;
   BinaryData blkHash5A;

   BinaryData addrA_;
   BinaryData addrB_;
   BinaryData addrC_;
   BinaryData addrD_;
};


////////////////////////////////////////////////////////////////////////////////
TEST_F(BlockUtilsTest, HeadersOnly)
{
   EXPECT_EQ(TheBDM.getNumBlocks(), 0);
   TheBDM.processAllHeadersInBlkFiles(0,1);
   
   EXPECT_EQ(TheBDM.getNumBlocks(), 5);
   EXPECT_EQ(TheBDM.getTopBlockHeight(), 4);
   EXPECT_EQ(TheBDM.getTopBlockHash(), blkHash4);
   EXPECT_EQ(iface_->getTopBlockHeight(HEADERS), 4);
   //iface_->printAllDatabaseEntries(HEADERS);
}

////////////////////////////////////////////////////////////////////////////////
TEST_F(BlockUtilsTest, HeadersOnly_Reorg)
{
   SETLOGLEVEL(LogLvlError);
   EXPECT_EQ(TheBDM.getNumBlocks(), 0);
   TheBDM.processAllHeadersInBlkFiles(0,1);
   
   EXPECT_EQ(TheBDM.getNumBlocks(), 5);
   EXPECT_EQ(TheBDM.getTopBlockHeight(), 4);

   EXPECT_EQ(iface_->getTopBlockHeight(HEADERS), 4);
   EXPECT_EQ(iface_->getTopBlockHash(HEADERS), blkHash4);

   copyFile("../reorgTest/blk_3A.dat", BtcUtils::getBlkFilename(blkdir_, 1));
   TheBDM.processAllHeadersInBlkFiles(1,2);
   EXPECT_EQ(iface_->getTopBlockHeight(HEADERS), 4);
   EXPECT_EQ(iface_->getTopBlockHash(HEADERS), blkHash4);
   EXPECT_FALSE(TheBDM.getHeaderByHash(blkHash3A)->isMainBranch());
   EXPECT_TRUE( TheBDM.getHeaderByHash(blkHash3 )->isMainBranch());

   copyFile("../reorgTest/blk_4A.dat", BtcUtils::getBlkFilename(blkdir_, 2));
   TheBDM.processAllHeadersInBlkFiles(2,3);
   EXPECT_EQ(iface_->getTopBlockHeight(HEADERS), 4);
   EXPECT_EQ(iface_->getTopBlockHash(HEADERS), blkHash4);
   EXPECT_FALSE(TheBDM.getHeaderByHash(blkHash3A)->isMainBranch());
   EXPECT_TRUE( TheBDM.getHeaderByHash(blkHash3 )->isMainBranch());
   EXPECT_FALSE(TheBDM.getHeaderByHash(blkHash4A)->isMainBranch());
   EXPECT_TRUE( TheBDM.getHeaderByHash(blkHash4 )->isMainBranch());

   copyFile("../reorgTest/blk_5A.dat", BtcUtils::getBlkFilename(blkdir_, 3));
   TheBDM.processAllHeadersInBlkFiles(3,4);
   EXPECT_EQ(iface_->getTopBlockHeight(HEADERS), 5);
   EXPECT_EQ(iface_->getTopBlockHeight(HEADERS), 5);
   EXPECT_EQ(iface_->getTopBlockHash(HEADERS), blkHash5A);
   EXPECT_FALSE(TheBDM.getHeaderByHash(blkHash3 )->isMainBranch());
   EXPECT_TRUE( TheBDM.getHeaderByHash(blkHash3A)->isMainBranch());
   EXPECT_FALSE(TheBDM.getHeaderByHash(blkHash4 )->isMainBranch());
   EXPECT_TRUE( TheBDM.getHeaderByHash(blkHash4A)->isMainBranch());

   SETLOGLEVEL(LogLvlDebug2);
}

////////////////////////////////////////////////////////////////////////////////
TEST_F(BlockUtilsTest, Load5Blocks)
{
   DBUtils.setArmoryDbType(ARMORY_DB_SUPER);
   DBUtils.setDbPruneType(DB_PRUNE_NONE);
   TheBDM.rebuildDatabasesFromBlkFiles(); 

   StoredScriptHistory ssh;

   iface_->getStoredScriptHistory(ssh, HASH160PREFIX + addrA_);
   EXPECT_EQ(ssh.getScriptBalance(),  100*COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 100*COIN);
   EXPECT_EQ(ssh.totalTxioCount_,       2);

   iface_->getStoredScriptHistory(ssh, HASH160PREFIX + addrB_);
   EXPECT_EQ(ssh.getScriptBalance(),    0*COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 140*COIN);
   EXPECT_EQ(ssh.totalTxioCount_,       3);

   iface_->getStoredScriptHistory(ssh, HASH160PREFIX + addrC_);
   EXPECT_EQ(ssh.getScriptBalance(),   50*COIN);
   EXPECT_EQ(ssh.getScriptReceived(),  60*COIN);
   EXPECT_EQ(ssh.totalTxioCount_,       2);

   iface_->getStoredScriptHistory(ssh, HASH160PREFIX + addrD_);
   EXPECT_EQ(ssh.getScriptBalance(),  100*COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 100*COIN);
   EXPECT_EQ(ssh.totalTxioCount_,       3);
}

////////////////////////////////////////////////////////////////////////////////
TEST_F(BlockUtilsTest, Load4BlocksPlus1)
{
   // Copy only the first four blocks.  Will copy the full file next to test
   // readBlkFileUpdate method on non-reorg blocks.
   copyFile("../reorgTest/blk_0_to_4.dat", blk0dat_, 1596);
   TheBDM.rebuildDatabasesFromBlkFiles(); 
   EXPECT_EQ(iface_->getTopBlockHeight(HEADERS), 3);
   EXPECT_EQ(iface_->getTopBlockHash(HEADERS), blkHash3);
   EXPECT_TRUE(TheBDM.getHeaderByHash(blkHash3)->isMainBranch());
   
   copyFile("../reorgTest/blk_0_to_4.dat", blk0dat_);
   TheBDM.readBlkFileUpdate(); 
   EXPECT_EQ(iface_->getTopBlockHeight(HEADERS), 4);
   EXPECT_EQ(iface_->getTopBlockHash(HEADERS), blkHash4);
   EXPECT_TRUE(TheBDM.getHeaderByHash(blkHash4)->isMainBranch());
}

////////////////////////////////////////////////////////////////////////////////
TEST_F(BlockUtilsTest, Load5Blocks_Plus2NoReorg)
{
   DBUtils.setArmoryDbType(ARMORY_DB_SUPER);
   DBUtils.setDbPruneType(DB_PRUNE_NONE);
   TheBDM.rebuildDatabasesFromBlkFiles(); 


   copyFile("../reorgTest/blk_3A.dat", blk0dat_);
   TheBDM.readBlkFileUpdate();
   EXPECT_EQ(TheBDM.getTopBlockHash(),   blkHash4);
   EXPECT_EQ(TheBDM.getTopBlockHeight(), 4);

   copyFile("../reorgTest/blk_4A.dat", blk0dat_);
   TheBDM.readBlkFileUpdate();
   EXPECT_EQ(TheBDM.getTopBlockHash(),   blkHash4);
   EXPECT_EQ(TheBDM.getTopBlockHeight(), 4);

   //copyFile("../reorgTest/blk_5A.dat", blk0dat_);
   //iface_->pprintBlkDataDB(BLKDATA);
}

////////////////////////////////////////////////////////////////////////////////
TEST_F(BlockUtilsTest, Load5Blocks_FullReorg)
{
   DBUtils.setArmoryDbType(ARMORY_DB_SUPER);
   DBUtils.setDbPruneType(DB_PRUNE_NONE);
   TheBDM.rebuildDatabasesFromBlkFiles(); 

   copyFile("../reorgTest/blk_3A.dat", blk0dat_);
   TheBDM.readBlkFileUpdate();
   copyFile("../reorgTest/blk_4A.dat", blk0dat_);
   TheBDM.readBlkFileUpdate();
   copyFile("../reorgTest/blk_5A.dat", blk0dat_);
   TheBDM.readBlkFileUpdate();

   //iface_->pprintBlkDataDB(BLKDATA);

   StoredScriptHistory ssh;

   iface_->getStoredScriptHistory(ssh, HASH160PREFIX + addrA_);
   EXPECT_EQ(ssh.getScriptBalance(),  150*COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 150*COIN);
   EXPECT_EQ(ssh.totalTxioCount_,       3);

   iface_->getStoredScriptHistory(ssh, HASH160PREFIX + addrB_);
   EXPECT_EQ(ssh.getScriptBalance(),   10*COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 150*COIN);
   EXPECT_EQ(ssh.totalTxioCount_,       4);

   iface_->getStoredScriptHistory(ssh, HASH160PREFIX + addrC_);
   EXPECT_EQ(ssh.getScriptBalance(),    0*COIN);
   EXPECT_EQ(ssh.getScriptReceived(),  10*COIN);
   EXPECT_EQ(ssh.totalTxioCount_,       1);

   iface_->getStoredScriptHistory(ssh, HASH160PREFIX + addrD_);
   EXPECT_EQ(ssh.getScriptBalance(),  140*COIN);
   EXPECT_EQ(ssh.getScriptReceived(), 140*COIN);
   EXPECT_EQ(ssh.totalTxioCount_,       3);
}


////////////////////////////////////////////////////////////////////////////////
TEST_F(BlockUtilsTest, TimeAndSpaceTest_usuallydisabled)
{
   DBUtils.setArmoryDbType(ARMORY_DB_SUPER);
   DBUtils.setDbPruneType(DB_PRUNE_NONE);

   string oldblkdir = blkdir_;
   blkdir_  = string("/home/alan/.bitcoin/blocks");
   TheBDM.SelectNetwork("Main");
   //blkdir_  = string("/home/alan/.bitcoin/testnet3/blocks");
   //TheBDM.SelectNetwork("Test");
   TheBDM.SetBlkFileLocation(blkdir_);
   TheBDM.SetHomeDirLocation(homedir_);

   StoredScriptHistory ssh;
   TheBDM.rebuildDatabasesFromBlkFiles(); 
   BinaryData scrAddr  = READHEX("11b366edfc0a8b66feebae5c2e25a7b6a5d1cf31");
   BinaryData scrAddr2 = READHEX("39aa3d569e06a1d7926dc4be1193c99bf2eb9ee0");
   BinaryData scrAddr3 = READHEX("758e51b5e398a32c6abd091b3fde383291267cfa");
   BinaryData scrAddr4 = READHEX("6c22eb00e3f93acac5ae5d81a9db78a645dfc9c7");
   EXPECT_EQ(TheBDM.getDBBalanceForHash160(scrAddr), 18*COIN);
   TheBDM.pprintSSHInfoAboutHash160(scrAddr);
   TheBDM.pprintSSHInfoAboutHash160(scrAddr2);
   TheBDM.pprintSSHInfoAboutHash160(scrAddr3);
   TheBDM.pprintSSHInfoAboutHash160(scrAddr4);
   blkdir_ = oldblkdir;
   LOGINFO << "waiting... (please copy the DB dir...)";
   int pause;
   cin >> pause;
}

/*
////////////////////////////////////////////////////////////////////////////////
TEST_F(BlockUtils, MultiRescanBlkSafe)
{
   bdm_.rescanBlocks(0, 3);
   bdm_.rescanBlocks(0, 3);
}
*/


////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
#if defined(_MSC_VER) || defined(__MINGW32__)
class LevelDBTest : public ::testing::Test
{
protected:
   virtual void SetUp(void) 
   {
      Log::ERR() << "Have not implemented LevelDB tests in Windows!";
      azjc#ksl_Induce_Compile_Error_klnvjkl;
   }
};
#else
class LevelDBTest : public ::testing::Test
{
protected:
   virtual void SetUp(void) 
   {
      iface_ = LevelDBWrapper::GetInterfacePtr();
      magic_ = READHEX(MAINNET_MAGIC_BYTES);
      ghash_ = READHEX(MAINNET_GENESIS_HASH_HEX);
      gentx_ = READHEX(MAINNET_GENESIS_TX_HASH_HEX);
      zeros_ = READHEX("00000000");
      DBUtils.setArmoryDbType(ARMORY_DB_FULL);
      DBUtils.setDbPruneType(DB_PRUNE_NONE);

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
      sbh_.unserialize(rawHead_);

      // Make sure the global DB type and prune type are reset for each test
      DBUtils.setArmoryDbType(ARMORY_DB_FULL);
      DBUtils.setDbPruneType(DB_PRUNE_NONE);
   }

   /////
   virtual void TearDown(void)
   {
      // This seem to be the best way to remove a dir tree in C++ (in Linux)
      system("rm -rf ./ldbtestdir/level*");
   }

   /////
   void addOutPairH(BinaryData key, BinaryData val)
   { 
      expectOutH_.push_back( pair<BinaryData,BinaryData>(key,val));
   }

   /////
   void addOutPairB(BinaryData key, BinaryData val)
   { 
      expectOutB_.push_back( pair<BinaryData,BinaryData>(key,val));
   }

   /////
   void replaceTopOutPairB(BinaryData key, BinaryData val)
   { 
      uint32_t last = expectOutB_.size() -1;
      expectOutB_[last] = pair<BinaryData,BinaryData>(key,val);
   }

   /////
   void printOutPairs(void)
   {
      cout << "Num Houts: " << expectOutH_.size() << endl;
      for(uint32_t i=0; i<expectOutH_.size(); i++)
      {
         cout << "   \"" << expectOutH_[i].first.toHexStr() << "\"  ";
         cout << "   \"" << expectOutH_[i].second.toHexStr() << "\"    " << endl;
      }
      cout << "Num Bouts: " << expectOutB_.size() << endl;
      for(uint32_t i=0; i<expectOutB_.size(); i++)
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

      if(fromDB.size() < endplus1H || expectOutH_.size() < endplus1H)
      {
         LOGERR << "Headers DB not the correct size";
         LOGERR << "DB  size:  " << (int)fromDB.size();
         LOGERR << "Expected:  " << (int)expectOutH_.size();
         return false;
      }

      for(uint32_t i=startH; i<endplus1H; i++)
         if(fromDB[i].first  != expectOutH_[i].first || 
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
      if(fromDB.size() < endplus1B || expectOutB_.size() < endplus1B)
      {
         LOGERR << "BLKDATA DB not the correct size";
         LOGERR << "DB  size:  " << (int)fromDB.size();
         LOGERR << "Expected:  " << (int)expectOutB_.size();
         return false;
      }

      for(uint32_t i=startB; i<endplus1B; i++)
         if(fromDB[i].first  != expectOutB_[i].first || 
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
      
      iface_->openDatabases( string("ldbtestdir"), 
                             ghash_, gentx_, magic_, 
                             ARMORY_DB_FULL, DB_PRUNE_NONE);

      BinaryData DBINFO = StoredDBInfo().getDBKey();
      BinaryData flags = READHEX("02100000");
      BinaryData val0 = magic_+flags+zeros_+ghash_;
      addOutPairH(DBINFO, val0);
      addOutPairB(DBINFO, val0);

      return iface_->databasesAreOpen();
   }


   InterfaceToLDB* iface_;
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
#endif


////////////////////////////////////////////////////////////////////////////////
TEST_F(LevelDBTest, OpenClose)
{
   iface_->openDatabases( string("ldbtestdir"),
                          ghash_,
                          gentx_,
                          magic_,
                          ARMORY_DB_FULL,
                          DB_PRUNE_NONE);
   
   ASSERT_TRUE(iface_->databasesAreOpen());

   EXPECT_EQ(iface_->getTopBlockHeight(HEADERS), 0);
   EXPECT_EQ(iface_->getTopBlockHash(HEADERS), READHEX(MAINNET_GENESIS_HASH_HEX));
                          
   KVLIST HList = iface_->getAllDatabaseEntries(HEADERS);
   KVLIST BList = iface_->getAllDatabaseEntries(BLKDATA);

   // 0123 4567 0123 4567
   // 0000 0010 0001 ---- ---- ---- ---- ----
   BinaryData flags = READHEX("02100000");

   for(uint32_t i=0; i<HList.size(); i++)
   {
      EXPECT_EQ(HList[i].first,  READHEX("00"));
      EXPECT_EQ(BList[i].second, magic_ + flags + zeros_ + ghash_);
   }

   for(uint32_t i=0; i<BList.size(); i++)
   {
      EXPECT_EQ(HList[i].first,  READHEX("00"));
      EXPECT_EQ(BList[i].second, magic_ + flags + zeros_ + ghash_);
   }
                         
   iface_->closeDatabases();
}


////////////////////////////////////////////////////////////////////////////////
TEST_F(LevelDBTest, OpenCloseOpenNominal)
{
   // 0123 4567 0123 4567
   // 0000 0010 0001 ---- ---- ---- ---- ----
   BinaryData flags = READHEX("02100000");

   iface_->openDatabases( string("ldbtestdir"),
                          ghash_,
                          gentx_,
                          magic_,
                          ARMORY_DB_FULL,
                          DB_PRUNE_NONE);


   iface_->closeDatabases();

   iface_->openDatabases( string("ldbtestdir"),
                          ghash_,
                          gentx_,
                          magic_,
                          ARMORY_DB_FULL,
                          DB_PRUNE_NONE);
   ASSERT_TRUE(iface_->databasesAreOpen());

   KVLIST HList = iface_->getAllDatabaseEntries(HEADERS);
   KVLIST BList = iface_->getAllDatabaseEntries(BLKDATA);

   for(uint32_t i=0; i<HList.size(); i++)
   {
      EXPECT_EQ(HList[i].first,  READHEX("00"));
      EXPECT_EQ(BList[i].second, magic_ + flags + zeros_ + ghash_);
   }

   for(uint32_t i=0; i<BList.size(); i++)
   {
      EXPECT_EQ(HList[i].first,  READHEX("00"));
      EXPECT_EQ(BList[i].second, magic_ + flags + zeros_ + ghash_);
   }
                         
   iface_->closeDatabases();
}


////////////////////////////////////////////////////////////////////////////////
TEST_F(LevelDBTest, DISABLED_OpenCloseOpenMismatch)
{
   LOGERR << "Expecting four error messages here:  this is normal";
   iface_->openDatabases( string("ldbtestdir"),
                          ghash_,
                          gentx_,
                          magic_,
                          ARMORY_DB_FULL,
                          DB_PRUNE_NONE);
   EXPECT_TRUE(iface_->databasesAreOpen());
   iface_->closeDatabases();

   iface_->openDatabases( string("ldbtestdir"),
                          ghash_.getSliceCopy(0, 31) + READHEX("00"),
                          gentx_,
                          magic_,
                          ARMORY_DB_FULL,
                          DB_PRUNE_NONE);
   EXPECT_TRUE(iface_->databasesAreOpen());
   iface_->closeDatabases();

   iface_->openDatabases( string("ldbtestdir"),
                          ghash_,
                          gentx_,
                          magic_.getSliceCopy(0,3) + READHEX("00"),
                          ARMORY_DB_FULL,
                          DB_PRUNE_NONE);
   EXPECT_FALSE(iface_->databasesAreOpen());

   iface_->openDatabases( string("ldbtestdir"),
                          ghash_,
                          gentx_,
                          magic_,
                          ARMORY_DB_SUPER,
                          DB_PRUNE_WHATEVER);
   EXPECT_FALSE(iface_->databasesAreOpen());

   iface_->openDatabases( string("ldbtestdir"),
                          ghash_,
                          gentx_,
                          magic_);
   ASSERT_TRUE( iface_->databasesAreOpen());

   EXPECT_EQ(   DBUtils.getArmoryDbType(), ARMORY_DB_FULL);
   EXPECT_EQ(   DBUtils.getDbPruneType(),  DB_PRUNE_NONE);

   KVLIST HList = iface_->getAllDatabaseEntries(HEADERS);
   KVLIST BList = iface_->getAllDatabaseEntries(BLKDATA);

   EXPECT_EQ(HList.begin()->first,  READHEX("00"));
   EXPECT_EQ(BList.begin()->first,  READHEX("00"));
                         
   iface_->closeDatabases();
   
   
}


////////////////////////////////////////////////////////////////////////////////
TEST_F(LevelDBTest, PutGetDelete)
{
   BinaryData flags = READHEX("02100000");

   iface_->openDatabases( string("ldbtestdir"),
                          ghash_,
                          gentx_,
                          magic_,
                          ARMORY_DB_FULL,
                          DB_PRUNE_NONE);
   ASSERT_TRUE(iface_->databasesAreOpen());
   
   DB_PREFIX TXDATA = DB_PREFIX_TXDATA;
   BinaryData DBINFO = StoredDBInfo().getDBKey();
   BinaryData PREFIX = WRITE_UINT8_BE((uint8_t)TXDATA);
   BinaryData val0 = magic_+flags+zeros_+ghash_;
   BinaryData commonValue = READHEX("abcd1234");
   BinaryData keyAB = READHEX("0000");
   BinaryData nothing = BinaryData(0);

   addOutPairH(DBINFO,         val0);

   addOutPairB(DBINFO,         val0);
   addOutPairB(         keyAB, commonValue);
   addOutPairB(PREFIX + keyAB, commonValue);

   ASSERT_TRUE( compareKVListRange(0,1, 0,1));

   iface_->putValue(BLKDATA, keyAB, commonValue);
   ASSERT_TRUE( compareKVListRange(0,1, 0,2));

   iface_->putValue(BLKDATA, DB_PREFIX_TXDATA, keyAB, commonValue);
   ASSERT_TRUE( compareKVListRange(0,1, 0,3));

   // Now test a bunch of get* methods
   ASSERT_EQ( iface_->getValue(      BLKDATA, PREFIX+keyAB),             commonValue);
   ASSERT_EQ( iface_->getValue(      BLKDATA, DB_PREFIX_DBINFO, nothing),val0);
   ASSERT_EQ( iface_->getValue(      BLKDATA, DBINFO),                   val0);
   ASSERT_EQ( iface_->getValueRef(   BLKDATA, PREFIX+keyAB),             commonValue);
   ASSERT_EQ( iface_->getValueRef(   BLKDATA, TXDATA, keyAB),            commonValue);
   ASSERT_EQ( iface_->getValueReader(BLKDATA, PREFIX+keyAB).getRawRef(), commonValue);
   ASSERT_EQ( iface_->getValueReader(BLKDATA, TXDATA, keyAB).getRawRef(),commonValue);

   iface_->deleteValue(BLKDATA, DB_PREFIX_TXDATA, keyAB);
   ASSERT_TRUE( compareKVListRange(0,1, 0,2));

   iface_->deleteValue(BLKDATA, PREFIX+ keyAB);
   ASSERT_TRUE( compareKVListRange(0,1, 0,1));

   iface_->deleteValue(BLKDATA, PREFIX+ keyAB);
}

////////////////////////////////////////////////////////////////////////////////
TEST_F(LevelDBTest, STxOutPutGet)
{
   BinaryData TXP     = WRITE_UINT8_BE((uint8_t)DB_PREFIX_TXDATA);
   BinaryData stxoVal = READHEX("0400") + rawTxOut0_;
   BinaryData stxoKey = TXP + READHEX("01e078""0f""0007""0001");
   
   ASSERT_TRUE(standardOpenDBs());

   StoredTxOut stxo0;
   stxo0.txVersion_   = 1;
   stxo0.spentness_   = TXOUT_UNSPENT;
   stxo0.blockHeight_ = 123000;
   stxo0.duplicateID_ = 15;
   stxo0.txIndex_     = 7;
   stxo0.txOutIndex_  = 1;
   stxo0.unserialize(rawTxOut0_);
   iface_->putStoredTxOut(stxo0);

   // Construct expected output
   addOutPairB(stxoKey, stxoVal);
   ASSERT_TRUE(compareKVListRange(0,1, 0,2));

   StoredTxOut stxoGet;
   iface_->getStoredTxOut(stxoGet, 123000, 15, 7, 1);
   EXPECT_EQ(stxoGet.serializeDBValue(), stxo0.serializeDBValue());

   //iface_->validDupByHeight_[123000] = 15;
   //iface_->getStoredTxOut(stxoGet, 123000, 7, 1);
   //EXPECT_EQ(stxoGet.serializeDBValue(), stxo0.serializeDBValue());
   
   StoredTxOut stxo1;
   stxo1.txVersion_   = 1;
   stxo1.spentness_   = TXOUT_UNSPENT;
   stxo1.blockHeight_ = 200333;
   stxo1.duplicateID_ = 3;
   stxo1.txIndex_     = 7;
   stxo1.txOutIndex_  = 1;
   stxo1.unserialize(rawTxOut1_);
   stxoVal = READHEX("0400") + rawTxOut1_;
   stxoKey = TXP + READHEX("030e8d""03""00070001");
   iface_->putStoredTxOut(stxo1);

   iface_->getStoredTxOut(stxoGet, 123000, 15, 7, 1);
   EXPECT_EQ(stxoGet.serializeDBValue(), stxo0.serializeDBValue());
   iface_->getStoredTxOut(stxoGet, 200333,  3, 7, 1);
   EXPECT_EQ(stxoGet.serializeDBValue(), stxo1.serializeDBValue());

   addOutPairB(stxoKey, stxoVal);
   ASSERT_TRUE(compareKVListRange(0,1, 0,3));

}

////////////////////////////////////////////////////////////////////////////////
TEST_F(LevelDBTest, PutFullTxNoOuts)
{
   DBUtils.setArmoryDbType(ARMORY_DB_FULL);
   DBUtils.setDbPruneType(DB_PRUNE_NONE);

   ASSERT_TRUE(standardOpenDBs());

   StoredTx stx;
   stx.createFromTx(rawTxUnfrag_);
   stx.setKeyData(123000, 15, 7);

   BinaryData TXP     = WRITE_UINT8_BE((uint8_t)DB_PREFIX_TXDATA);
   BinaryData stxKey  = TXP + READHEX("01e078""0f""0007");
   BinaryData stxVal  = READHEX("0440") + stx.thisHash_ + rawTxFragged_;

   iface_->putStoredTx(stx, false);
   addOutPairB(stxKey,  stxVal);
   EXPECT_TRUE(compareKVListRange(0,1, 0,2));
}

////////////////////////////////////////////////////////////////////////////////
TEST_F(LevelDBTest, PutFullTx)
{
   DBUtils.setArmoryDbType(ARMORY_DB_FULL);
   DBUtils.setDbPruneType(DB_PRUNE_NONE);

   BinaryData TXP     = WRITE_UINT8_BE((uint8_t)DB_PREFIX_TXDATA);
   BinaryData stxoVal = READHEX("0400") + rawTxOut0_;
   BinaryData stxKey   = TXP + READHEX("01e078""0f""0007");
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
   for(uint32_t i=0; i<2; i++)
   {
      stx.stxoMap_[i].spentness_  = TXOUT_UNSPENT;
      stx.stxoMap_[i].isCoinbase_ = false;

      ASSERT_EQ(stx.stxoMap_[i].blockHeight_, 123000);
      ASSERT_EQ(stx.stxoMap_[i].duplicateID_,     15);
      ASSERT_EQ(stx.stxoMap_[i].txIndex_,          7);
      ASSERT_EQ(stx.stxoMap_[i].txOutIndex_,       i);
      ASSERT_EQ(stx.stxoMap_[i].isCoinbase_,   false);
   }

   BinaryData stxVal = READHEX("0440") + stx.thisHash_ + rawTxFragged_;
   BinaryData stxo0Val = READHEX("0400") + stxo0raw;
   BinaryData stxo1Val = READHEX("0400") + stxo1raw;

   iface_->putStoredTx(stx);
   addOutPairB(stxKey,  stxVal);
   addOutPairB(stxo0Key, stxo0Val);
   addOutPairB(stxo1Key, stxo1Val);
   EXPECT_TRUE(compareKVListRange(0,1, 0,4));
}


////////////////////////////////////////////////////////////////////////////////
TEST_F(LevelDBTest, PutFullBlockNoTx)
{
   DBUtils.setArmoryDbType(ARMORY_DB_FULL);
   DBUtils.setDbPruneType(DB_PRUNE_NONE);

   StoredHeader sbh;
   BinaryRefReader brr(rawBlock_);
   sbh.unserializeFullBlock(brr);
   sbh.setKeyData(123000, UINT8_MAX);

   StoredHeadHgtList hhl;
   hhl.height_ = 123000;
   hhl.dupAndHashList_.push_back( pair<uint8_t, BinaryData>(0, sbh.thisHash_));
   hhl.preferredDup_ = UINT8_MAX;

   BinaryData TXP   = WRITE_UINT8_BE((uint8_t)DB_PREFIX_TXDATA);
   BinaryData HHP   = WRITE_UINT8_BE((uint8_t)DB_PREFIX_HEADHASH);
   BinaryData HGP   = WRITE_UINT8_BE((uint8_t)DB_PREFIX_HEADHGT);
   BinaryData hgtx  = READHEX("01e078""00");
   BinaryData sbh_HH_key = HHP + sbh.thisHash_;
   BinaryData sbh_HH_val = sbh.dataCopy_ + hgtx;
   BinaryData sbh_HG_key = hhl.getDBKey();
   BinaryData sbh_HG_val = hhl.serializeDBValue();
   
   ASSERT_TRUE(standardOpenDBs());

   addOutPairH( sbh_HH_key, sbh_HH_val);
   addOutPairH( sbh_HG_key, sbh_HG_val);

   uint8_t sdup = iface_->putStoredHeader(sbh, false);
   EXPECT_TRUE(compareKVListRange(0,3, 0,1));
   EXPECT_EQ(sdup, 0);

   // Try adding it again and see if get the correct dup again, and no touch DB
   sdup = iface_->putStoredHeader(sbh, false);
   EXPECT_TRUE(compareKVListRange(0,3, 0,1));
   EXPECT_EQ(sdup, 0);
}

////////////////////////////////////////////////////////////////////////////////
TEST_F(LevelDBTest, PutGetBareHeader)
{
   DBUtils.setArmoryDbType(ARMORY_DB_FULL);
   DBUtils.setDbPruneType(DB_PRUNE_NONE);

   StoredHeader sbh;
   BinaryRefReader brr(rawBlock_);
   sbh.unserializeFullBlock(brr);
   sbh.setKeyData(123000, UINT8_MAX);
   BinaryData header0 = sbh.thisHash_;

   ASSERT_TRUE(standardOpenDBs());

   uint8_t sdup = iface_->putBareHeader(sbh);
   EXPECT_EQ(sdup, 0);
   EXPECT_EQ(sbh.duplicateID_, 0);

   // Try adding it again and see if get the correct dup again, and no touch DB
   sdup = iface_->putStoredHeader(sbh, false);
   EXPECT_EQ(sdup, 0);
   EXPECT_EQ(sbh.duplicateID_, 0);

   // Add a new header and make sure duplicate ID is done correctly
   BinaryData newHeader = READHEX( 
      "0000000105d3571220ef5f87c6ac0bc8bf5b33c02a9e6edf83c84d840109592c"
      "0000000027523728e15f5fe1ac507bff92499eada4af8a0c485d5178e3f96568"
      "c18f84994e0e4efc1c0175d646a91ad4");
   BinaryData header1 = BtcUtils::getHash256(newHeader);

   StoredHeader sbh2;
   sbh2.unserialize(newHeader);
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

   sbh3.unserialize(anotherHead);
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
TEST_F(LevelDBTest, PutFullBlock)
{
   DBUtils.setArmoryDbType(ARMORY_DB_FULL);
   DBUtils.setDbPruneType(DB_PRUNE_NONE);
   ASSERT_TRUE(standardOpenDBs());

   StoredHeader sbh;
   BinaryRefReader brr(rawBlock_);
   sbh.unserializeFullBlock(brr);
   sbh.setKeyData(123000);

   BinaryData rawHeader = READHEX(
      "01000000eb10c9a996a2340a4d74eaab41421ed8664aa49d18538bab59010000"
      "000000005a2f06efa9f2bd804f17877537f2080030cadbfa1eb50e02338117cc"
      "604d91b9b7541a4ecfbb0a1a64f1ade7");

   // Compute and write the headers to the expected-output
   StoredHeadHgtList hhl;
   hhl.height_ = 123000;
   hhl.dupAndHashList_.push_back( pair<uint8_t, BinaryData>(0, sbh.thisHash_));
   hhl.preferredDup_ = UINT8_MAX;
   BinaryData HHP   = WRITE_UINT8_BE((uint8_t)DB_PREFIX_HEADHASH);
   BinaryData HGP   = WRITE_UINT8_BE((uint8_t)DB_PREFIX_HEADHGT);
   BinaryData sbh_HH_key = HHP + sbh.thisHash_;
   BinaryData sbh_HH_val = rawHeader + READHEX("01e078""00");
   BinaryData sbh_HG_key = hhl.getDBKey();
   BinaryData sbh_HG_val = hhl.serializeDBValue();
   // Only HEADHASH and HEADHGT entries get written
   addOutPairH( sbh_HH_key, sbh_HH_val);
   addOutPairH( sbh_HG_key, sbh_HG_val);

   // Now compute and write the BLKDATA
   BinaryData TXP       = WRITE_UINT8_BE((uint8_t)DB_PREFIX_TXDATA);
   BinaryData sbhKey    = TXP + READHEX("01e078""00");
   BinaryData stx0Key   = sbhKey  + READHEX("0000");
   BinaryData stx1Key   = sbhKey  + READHEX("0001");
   BinaryData stx2Key   = sbhKey  + READHEX("0002");
   BinaryData stxo00Key = stx0Key + READHEX("0000");
   BinaryData stxo10Key = stx1Key + READHEX("0000");
   BinaryData stxo11Key = stx1Key + READHEX("0001");
   BinaryData stxo20Key = stx2Key + READHEX("0000");
   BinaryData stxo21Key = stx2Key + READHEX("0001");
   BinaryData stxo00Raw = READHEX( "00f2052a01000000""434104"
      "c2239c4eedb3beb26785753463be3ec62b82f6acd62efb65f452f8806f2ede0b"
      "338e31d1f69b1ce449558d7061aa1648ddc2bf680834d3986624006a272dc21cac");
   BinaryData stxo10Raw = READHEX( "40420f0000000000"
      "19""76a914adfa66f57ded1b655eb4ccd96ee07ca62bc1ddfd88ac");
   BinaryData stxo11Raw = READHEX( "007d6a7d04000000"
      "19""76a914981a0c9ae61fa8f8c96ae6f8e383d6e07e77133e88ac");
   BinaryData stxo20Raw = READHEX( "2f66ac6105000000"
      "19""76a914964642290c194e3bfab661c1085e47d67786d2d388ac");
   BinaryData stxo21Raw = READHEX( "2f77e20000000000"
      "19""76a9141486a7046affd935919a3cb4b50a8a0c233c286c88ac");

   StoredTx & stx0 = sbh.stxMap_[0];
   StoredTx & stx1 = sbh.stxMap_[1];
   StoredTx & stx2 = sbh.stxMap_[2];
   BinaryData hflags = READHEX("01240000");
   BinaryData ntx    = READHEX("03000000");
   BinaryData nbyte  = READHEX("46040000");

   // Add header to BLKDATA
   addOutPairB(sbhKey, hflags + rawHeader + ntx + nbyte);

   // Add Tx0 to BLKDATA
   addOutPairB(stx0Key,   READHEX("0440") + stx0.thisHash_ + stx0.getSerializedTxFragged());
   addOutPairB(stxo00Key, READHEX("0480") + stxo00Raw); // is coinbase

   // Add Tx1 to BLKDATA
   addOutPairB(stx1Key,   READHEX("0440") + stx1.thisHash_ + stx1.getSerializedTxFragged());
   addOutPairB(stxo10Key, READHEX("0400") + stxo10Raw);
   addOutPairB(stxo11Key, READHEX("0400") + stxo11Raw);

   // Add Tx2 to BLKDATA
   addOutPairB(stx2Key,   READHEX("0440") + stx2.thisHash_ + stx2.getSerializedTxFragged());
   addOutPairB(stxo20Key, READHEX("0400") + stxo20Raw);
   addOutPairB(stxo21Key, READHEX("0400") + stxo21Raw);

   // DuplicateID values get set when we putStoredHeader since we don't know
   // what dupIDs have been taken until we try to put it in the database.
   ASSERT_EQ(sbh.stxMap_.size(), 3);
   for(uint32_t i=0; i<3; i++)
   {
      ASSERT_EQ(sbh.stxMap_[i].blockHeight_,    123000);
      ASSERT_EQ(sbh.stxMap_[i].duplicateID_, UINT8_MAX);
      ASSERT_EQ(sbh.stxMap_[i].txIndex_,             i);
      for(uint32_t j=0; j<sbh.stxMap_[i].stxoMap_.size(); j++)
      {
         sbh.stxMap_[i].stxoMap_[j].spentness_ = TXOUT_UNSPENT;
         //sbh.stxoMap_[i].isCoinbase_ = (j==0);

         ASSERT_EQ(sbh.stxMap_[i].stxoMap_[j].blockHeight_,    123000);
         ASSERT_EQ(sbh.stxMap_[i].stxoMap_[j].duplicateID_, UINT8_MAX);
         ASSERT_EQ(sbh.stxMap_[i].stxoMap_[j].txIndex_,             i);
         ASSERT_EQ(sbh.stxMap_[i].stxoMap_[j].txOutIndex_,          j);
      }
   }

   iface_->putStoredHeader(sbh);

   ASSERT_TRUE(compareKVListRange(0,3, 0,9));
}



////////////////////////////////////////////////////////////////////////////////
// Of course, this test only works if the previous test passes (but doesn't 
// require a saved state, it just re-puts the full block into the DB).  I
// did it this way, because I wasn't comfortable committing the pre-filled
// DB to the repo.
TEST_F(LevelDBTest, GetFullBlock)
{
   DBUtils.setArmoryDbType(ARMORY_DB_FULL);
   DBUtils.setDbPruneType(DB_PRUNE_NONE);
   ASSERT_TRUE(standardOpenDBs());

   StoredHeader sbh;
   BinaryRefReader brr(rawBlock_);
   sbh.unserializeFullBlock(brr);
   sbh.setKeyData(123000);
   sbh.isMainBranch_ = true;

   // Check the DBInfo before and after putting the valid header
   StoredDBInfo sdbi;
   iface_->getStoredDBInfo(HEADERS, sdbi);
   EXPECT_EQ(sdbi.topBlkHgt_,  0);
   EXPECT_EQ(sdbi.topBlkHash_, iface_->getGenesisBlockHash());

   iface_->putStoredHeader(sbh);

   // Since we marked this block main-branch, it should have non-MAX validDup
   EXPECT_EQ(iface_->getValidDupIDForHeight(123000), 0);
   BinaryData headerHash = READHEX(
      "7d97d862654e03d6c43b77820a40df894e3d6890784528e9cd05000000000000");
   iface_->getStoredDBInfo(HEADERS, sdbi);
   EXPECT_EQ(sdbi.topBlkHgt_,  123000);
   EXPECT_EQ(sdbi.topBlkHash_, headerHash);

   BinaryData rawHeader = READHEX(
      "01000000eb10c9a996a2340a4d74eaab41421ed8664aa49d18538bab59010000"
      "000000005a2f06efa9f2bd804f17877537f2080030cadbfa1eb50e02338117cc"
      "604d91b9b7541a4ecfbb0a1a64f1ade7");

   ////////////////////
   // Now test the get methods
  
   for(uint32_t i=0; i<4; i++)
   {
      StoredHeader sbhGet;

      if(i==0)
         EXPECT_TRUE(iface_->getStoredHeader(sbhGet, 123000, 0, false));
      else if(i==1)
         EXPECT_TRUE(iface_->getStoredHeader(sbhGet, headerHash, false));
      else if(i==2)
         EXPECT_TRUE(iface_->getStoredHeader(sbhGet, 123000, 0, true));
      else if(i==3)
         EXPECT_TRUE(iface_->getStoredHeader(sbhGet, headerHash, true));

      EXPECT_TRUE( sbhGet.isInitialized());
      EXPECT_EQ(   sbhGet.dataCopy_,    rawHeader);
      EXPECT_EQ(   sbhGet.thisHash_,    headerHash);
      EXPECT_EQ(   sbhGet.numTx_,       3);
      EXPECT_EQ(   sbhGet.numBytes_,    1094);
      EXPECT_EQ(   sbhGet.blockHeight_, 123000);
      EXPECT_EQ(   sbhGet.duplicateID_, 0);
      EXPECT_EQ(   sbhGet.merkle_.getSize(), 0);
      EXPECT_FALSE(sbhGet.merkleIsPartial_);
      EXPECT_EQ(   sbhGet.unserArmVer_, 0);
      EXPECT_EQ(   sbhGet.unserBlkVer_, 1);
      EXPECT_EQ(   sbhGet.unserDbType_, ARMORY_DB_FULL);
      EXPECT_EQ(   sbhGet.unserPrType_, DB_PRUNE_NONE);

      if(i<2)
         EXPECT_EQ( sbhGet.stxMap_.size(), 0);
      else
      {
         EXPECT_EQ( sbhGet.stxMap_.size(), 3);
         EXPECT_EQ( sbhGet.stxMap_[1].blockHeight_, 123000);
         EXPECT_EQ( sbhGet.stxMap_[1].duplicateID_,      0);
         EXPECT_EQ( sbhGet.stxMap_[1].txIndex_,          1);
         EXPECT_EQ( sbhGet.stxMap_[1].numTxOut_,         2);
         EXPECT_EQ( sbhGet.stxMap_[1].numBytes_,       621);
         EXPECT_EQ( sbhGet.stxMap_[0].stxoMap_[0].isCoinbase_, true);
         EXPECT_EQ( sbhGet.stxMap_[0].stxoMap_[0].spentness_, TXOUT_SPENTUNK);
         EXPECT_EQ( sbhGet.stxMap_[1].stxoMap_[0].isCoinbase_, false);
         EXPECT_EQ( sbhGet.stxMap_[1].stxoMap_[0].blockHeight_, 123000);
         EXPECT_EQ( sbhGet.stxMap_[1].stxoMap_[0].duplicateID_,      0);
         EXPECT_EQ( sbhGet.stxMap_[1].stxoMap_[0].txIndex_,          1);
         EXPECT_EQ( sbhGet.stxMap_[1].stxoMap_[0].txOutIndex_,       0);
      }
   }

}


////////////////////////////////////////////////////////////////////////////////
TEST_F(LevelDBTest, PutGetStoredTxHints)
{
   ASSERT_TRUE(standardOpenDBs());

   BinaryData prefix = READHEX("aabbccdd");

   StoredTxHints sths;
   EXPECT_FALSE(iface_->getStoredTxHints(sths, prefix));

   sths.txHashPrefix_ = prefix;
   
   ASSERT_TRUE(iface_->putStoredTxHints(sths));

   BinaryData THP = WRITE_UINT8_BE((uint8_t)DB_PREFIX_TXHINTS);
   addOutPairB(THP + prefix, READHEX("00"));

   compareKVListRange(0,1, 0,2);
   
   /////
   sths.dbKeyList_.push_back(READHEX("abcd1234ffff"));
   replaceTopOutPairB(THP + prefix,  READHEX("01""abcd1234ffff"));
   EXPECT_TRUE(iface_->putStoredTxHints(sths));
   compareKVListRange(0,1, 0,2);

   /////
   sths.dbKeyList_.push_back(READHEX("00002222aaaa"));
   replaceTopOutPairB(THP + prefix,  READHEX("02""abcd1234ffff""00002222aaaa"));
   EXPECT_TRUE(iface_->putStoredTxHints(sths));
   compareKVListRange(0,1, 0,2);

   /////
   sths.preferredDBKey_ = READHEX("00002222aaaa");
   replaceTopOutPairB(THP + prefix,  READHEX("02""00002222aaaa""abcd1234ffff"));
   EXPECT_TRUE(iface_->putStoredTxHints(sths));
   compareKVListRange(0,1, 0,2);

   // Now test the get methods
   EXPECT_TRUE( iface_->getStoredTxHints(sths, prefix));
   EXPECT_EQ(   sths.txHashPrefix_,  prefix);
   EXPECT_EQ(   sths.dbKeyList_.size(),  2);
   EXPECT_EQ(   sths.preferredDBKey_, READHEX("00002222aaaa"));

   //
   sths.dbKeyList_.resize(0);
   sths.preferredDBKey_.resize(0);
   EXPECT_TRUE( iface_->putStoredTxHints(sths));
   EXPECT_TRUE( iface_->getStoredTxHints(sths, prefix));
   EXPECT_EQ(   sths.txHashPrefix_,  prefix);
   EXPECT_EQ(   sths.dbKeyList_.size(),  0);
   EXPECT_EQ(   sths.preferredDBKey_.getSize(), 0);
}


////////////////////////////////////////////////////////////////////////////////
TEST_F(LevelDBTest, DISABLED_PutGetStoredUndoData)
{
   // We don't actually use undo data at all yet, so I'll skip the tests for now
}


TEST_F(LevelDBTest, HeaderDump)
{
   // We don't actually use undo data at all yet, so I'll skip the tests for now
}

// This was really just to time the logging to determine how much impact it 
// has.  It looks like writing to file is about 1,000,000 logs/sec, while 
// writing to the null stream (below the threshold log level) is about 
// 2,200,000/sec.    As long as we use log messages sparingly (and timer
// calls which call the logger), there will be no problem leaving them
// on even in production code.
/*
TEST(TimeDebugging, WriteToLogNoStdOut)
{
   LOGDISABLESTDOUT();
   for(uint32_t i=0; i<1000000; i++)
      LOGERR << "Testing writing out " << 3 << " diff things";
   LOGENABLESTDOUT();
}

TEST(TimeDebugging, WriteNull)
{
   for(uint32_t i=0; i<1000000; i++)
      LOGDEBUG4 << "Testing writing out " << 3 << " diff things";
}
*/


////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
// Now actually execute all the tests
////////////////////////////////////////////////////////////////////////////////
GTEST_API_ int main(int argc, char **argv) 
{
   std::cout << "Running main() from gtest_main.cc\n";

   // Setup the log file 
   STARTLOGGING("cppTestsLog.txt", LogLvlDebug2);
   //LOGDISABLESTDOUT();

   testing::InitGoogleTest(&argc, argv);
   int exitCode = RUN_ALL_TESTS();
   
   FLUSHLOG();


   return exitCode;
}






