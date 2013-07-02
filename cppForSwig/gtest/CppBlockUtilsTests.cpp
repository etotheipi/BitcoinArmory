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

#define READHEX BinaryData::CreateFromHex

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
TEST(BitReadWriteTest, Writer8)
{
   BitWriter<uint8_t> bitw;
   
   EXPECT_EQ( bitw.getValue(), 0);
   EXPECT_EQ( bitw.getBitsUsed(), 0);
   EXPECT_EQ( bitw.getBinaryData(), READHEX("00"));

   bitw.putBit(true);
   EXPECT_EQ( bitw.getValue(), 128);
   EXPECT_EQ( bitw.getBitsUsed(), 1);
   EXPECT_EQ( bitw.getBinaryData(), READHEX("80"));

   bitw.putBit(false);
   EXPECT_EQ( bitw.getValue(), 128);
   EXPECT_EQ( bitw.getBitsUsed(), 2);
   EXPECT_EQ( bitw.getBinaryData(), READHEX("80"));

   bitw.putBit(true);
   EXPECT_EQ( bitw.getValue(), 160);
   EXPECT_EQ( bitw.getBitsUsed(), 3);
   EXPECT_EQ( bitw.getBinaryData(), READHEX("a0"));

   bitw.putBits(0, 2);
   EXPECT_EQ( bitw.getValue(),  160);
   EXPECT_EQ( bitw.getBitsUsed(), 5);
   EXPECT_EQ( bitw.getBinaryData(), READHEX("a0"));

   bitw.putBits(3, 3);
   EXPECT_EQ( bitw.getValue(),  163);
   EXPECT_EQ( bitw.getBitsUsed(), 8);
   EXPECT_EQ( bitw.getBinaryData(), READHEX("a3"));
}

////////////////////////////////////////////////////////////////////////////////
TEST(BitReadWriteTest, Writer16)
{
   BitWriter<uint16_t> bitw;
   
   EXPECT_EQ( bitw.getValue(), 0);
   EXPECT_EQ( bitw.getBitsUsed(), 0);
   EXPECT_EQ( bitw.getBinaryData(), READHEX("0000"));

   bitw.putBit(true);
   EXPECT_EQ( bitw.getValue(), 0x8000);
   EXPECT_EQ( bitw.getBitsUsed(), 1);
   EXPECT_EQ( bitw.getBinaryData(), READHEX("8000"));

   bitw.putBit(false);
   EXPECT_EQ( bitw.getValue(), 0x8000);
   EXPECT_EQ( bitw.getBitsUsed(), 2);
   EXPECT_EQ( bitw.getBinaryData(), READHEX("8000"));

   bitw.putBit(true);
   EXPECT_EQ( bitw.getValue(), 0xa000);
   EXPECT_EQ( bitw.getBitsUsed(), 3);
   EXPECT_EQ( bitw.getBinaryData(), READHEX("a000"));

   bitw.putBits(0, 2);
   EXPECT_EQ( bitw.getValue(),  0xa000);
   EXPECT_EQ( bitw.getBitsUsed(), 5);
   EXPECT_EQ( bitw.getBinaryData(), READHEX("a000"));

   bitw.putBits(3, 3);
   EXPECT_EQ( bitw.getValue(),  0xa300);
   EXPECT_EQ( bitw.getBitsUsed(), 8);
   EXPECT_EQ( bitw.getBinaryData(), READHEX("a300"));

   bitw.putBits(3, 8);
   EXPECT_EQ( bitw.getValue(),  0xa303);
   EXPECT_EQ( bitw.getBitsUsed(), 16);
   EXPECT_EQ( bitw.getBinaryData(), READHEX("a303"));
}


////////////////////////////////////////////////////////////////////////////////
TEST(BitReadWriteTest, Writer32)
{
   BitWriter<uint32_t> bitw;
   
   bitw.putBits(0xffffff00, 32);
   EXPECT_EQ( bitw.getValue(),  0xffffff00);
   EXPECT_EQ( bitw.getBitsUsed(), 32);
   EXPECT_EQ( bitw.getBinaryData(), READHEX("ffffff00"));
}

////////////////////////////////////////////////////////////////////////////////
TEST(BitReadWriteTest, Writer64)
{
   BitWriter<uint64_t> bitw;
   
   bitw.putBits(0xffffff00ffffffaaULL, 64);
   EXPECT_EQ( bitw.getValue(),  0xffffff00ffffffaaULL);
   EXPECT_EQ( bitw.getBitsUsed(), 64);
   EXPECT_EQ( bitw.getBinaryData(), READHEX("ffffff00ffffffaa"));

   BitWriter<uint64_t> bitw2;
   bitw2.putBits(0xff, 32);
   bitw2.putBits(0xff, 32);
   EXPECT_EQ( bitw2.getValue(),  0x000000ff000000ffULL);
   EXPECT_EQ( bitw2.getBitsUsed(), 64);
   EXPECT_EQ( bitw2.getBinaryData(), READHEX("000000ff000000ff"));
}

////////////////////////////////////////////////////////////////////////////////
TEST(BitReadWriteTest, Reader8)
{
   BitReader<uint8_t> bitr;
   
   bitr.setValue(0xa3);
   EXPECT_TRUE( bitr.getBit());
   EXPECT_FALSE(bitr.getBit());
   EXPECT_TRUE( bitr.getBit());
   EXPECT_EQ(   bitr.getBits(2), 0);
   EXPECT_EQ(   bitr.getBits(3), 3);
}

////////////////////////////////////////////////////////////////////////////////
TEST(BitReadWriteTest, Reader16)
{
   BitReader<uint16_t> bitr;
   
   bitr.setValue(0xa303);
   
   EXPECT_TRUE( bitr.getBit());
   EXPECT_FALSE(bitr.getBit());
   EXPECT_TRUE( bitr.getBit());
   EXPECT_EQ(   bitr.getBits(2), 0);
   EXPECT_EQ(   bitr.getBits(3), 3);
   EXPECT_EQ(   bitr.getBits(8), 3);
}


////////////////////////////////////////////////////////////////////////////////
TEST(BitReadWriteTest, Reader32)
{
   BitReader<uint32_t> bitr(0xffffff00);
   EXPECT_EQ(bitr.getBits(32), 0xffffff00);
}

////////////////////////////////////////////////////////////////////////////////
TEST(BitReadWriteTest, Reader64)
{
   BitReader<uint64_t> bitr(0xffffff00ffffffaaULL);
   EXPECT_EQ( bitr.getBits(64),  0xffffff00ffffffaaULL);
}

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
   BinaryData script = READHEX("4104b0bd634234abbb1ba1e986e884185c61cf43e001f9137f23c2c409273eb16e6537a576782eba668a7ef8bd3b3cfb1edb7117ab65129b8a2e681f3c1e0908ef7bac");
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
   BinaryData script = READHEX("21024005c945d86ac6b01fb04258345abea7a845bd25689edb723d5ad4068ddd3036ac");
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
   BinaryData unique = READHEX("ff76a90088ac");
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
   BinaryData script = READHEX("5221034758cefcb75e16e4dfafb32383b709fa632086ea5ca982712de6add93060b17a2103fe96237629128a0ae8c3825af8a4be8fe3109b16f62af19cec0b1eb93b8717e252ae");
   BinaryData pub1   = READHEX("034758cefcb75e16e4dfafb32383b709fa632086ea5ca982712de6add93060b17a");
   BinaryData pub2   = READHEX("03fe96237629128a0ae8c3825af8a4be8fe3109b16f62af19cec0b1eb93b8717e2");
   BinaryData addr1  = READHEX("785652a6b8e721e80ffa353e5dfd84f0658284a9");
   BinaryData addr2  = READHEX("b3348abf9dd2d1491359f937e2af64b1bb6d525a");
   BinaryData a160   = BtcUtils::BadAddress_;
   BinaryData unique = READHEX("fe0202785652a6b8e721e80ffa353e5dfd84f0658284a9b3348abf9dd2d1491359f937e2af64b1bb6d525a");

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
   BinaryData script = READHEX("5221034758cefcb75e16e4dfafb32383b709fa632086ea5ca982712de6add93060b17a2103fe96237629128a0ae8c3825af8a4be8fe3109b16f62af19cec0b1eb93b8717e252ae");
   BinaryData addr0  = READHEX("785652a6b8e721e80ffa353e5dfd84f0658284a9");
   BinaryData addr1  = READHEX("b3348abf9dd2d1491359f937e2af64b1bb6d525a");
   BinaryData a160   = BtcUtils::BadAddress_;
   BinaryData unique = READHEX("fe0202785652a6b8e721e80ffa353e5dfd84f0658284a9b3348abf9dd2d1491359f937e2af64b1bb6d525a");

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
   BinaryData script = READHEX("493046022100b9daf2733055be73ae00ee0c5d78ca639d554fe779f163396c1a39b7913e7eac02210091f0deeb2e510c74354afb30cc7d8fbac81b1ca8b3940613379adc41a6ffd226014104b1537fa5bc2242d25ebf54f31e76ebabe0b3de4a4dccd9004f058d6c2caa5d31164252e1e04e5df627fae7adec27fa9d40c271fc4d30ff375ef6b26eba192bac");
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
   BinaryData script = READHEX("47304402205299224886e5e3402b0e9fa3527bcfe1d73c4e2040f18de8dd17f116e3365a1102202590dcc16c4b711daae6c37977ba579ca65bcaa8fba2bd7168a984be727ccf7a01210315122ff4d41d9fe3538a0a8c6c7f813cf12a901069a43d6478917246dc92a782");
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
   BinaryData script = READHEX("0310920304000071c3124d696e656420627920425443204775696c640800b75f950e000000");
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
   BinaryData script = READHEX("47304402201ffc44394e5a3dd9c8b55bdc12147e18574ac945d15dac026793bf3b8ff732af022035fd832549b5176126f735d87089c8c1c1319447a458a09818e173eaf0c2eef101");
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

   BinaryData script = READHEX("004830450221009254113fa46918f299b1d18ec918613e56cffbeba0960db05f66b51496e5bf3802201e229de334bd753a2b08b36cc3f38f5263a23e9714a737520db45494ec095ce80148304502206ee62f539d5cd94f990b7abfda77750f58ff91043c3f002501e5448ef6dba2520221009d29229cdfedda1dd02a1a90bb71b30b77e9c3fc28d1353f054c86371f6c2a8101");
   BinaryData a160 =  BtcUtils::BadAddress_;
   BinaryData prevHash = prevHashReg_;
   TXIN_SCRIPT_TYPE scrType = BtcUtils::getTxInScriptType(script, prevHash);
   EXPECT_EQ(scrType, TXIN_SCRIPT_SPENDMULTI);
   EXPECT_EQ(BtcUtils::getTxInAddr(script, prevHash), a160);
   EXPECT_EQ(BtcUtils::getTxInAddr(script, prevHash, scrType), a160);
   EXPECT_EQ(BtcUtils::getTxInAddrFromType(script,  scrType), a160);


   vector<BinaryDataRef> scrParts = BtcUtils::splitPushOnlyScriptRefs(script);
   BinaryData zero = READHEX("00");
   BinaryData sig1 = READHEX("30450221009254113fa46918f299b1d18ec918613e56cffbeba0960db05f66b51496e5bf3802201e229de334bd753a2b08b36cc3f38f5263a23e9714a737520db45494ec095ce801");
   BinaryData sig2 = READHEX("304502206ee62f539d5cd94f990b7abfda77750f58ff91043c3f002501e5448ef6dba2520221009d29229cdfedda1dd02a1a90bb71b30b77e9c3fc28d1353f054c86371f6c2a8101");

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
   BinaryData script = READHEX("004830450221009254113fa46918f299b1d18ec918613e56cffbeba0960db05f66b51496e5bf3802201e229de334bd753a2b08b36cc3f38f5263a23e9714a737520db45494ec095ce80148304502206ee62f539d5cd94f990b7abfda77750f58ff91043c3f002501e5448ef6dba2520221009d29229cdfedda1dd02a1a90bb71b30b77e9c3fc28d1353f054c86371f6c2a8101475221034758cefcb75e16e4dfafb32383b709fa632086ea5ca982712de6add93060b17a2103fe96237629128a0ae8c3825af8a4be8fe3109b16f62af19cec0b1eb93b8717e252ae");
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
      EXPECT_EQ(   txouts[i].getRecipientAddr(), dstAddr);

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
      EXPECT_FALSE(txs[i].isMainBranch());

      EXPECT_EQ(   txs[i].getTxInOffset(0),    5);
      EXPECT_EQ(   txs[i].getTxInOffset(1),  185);
      EXPECT_EQ(   txs[i].getTxOutOffset(0), 186);
      EXPECT_EQ(   txs[i].getTxOutOffset(1), 220);
      EXPECT_EQ(   txs[i].getTxOutOffset(2), 254);

      EXPECT_EQ(   txs[i].getLockTime(), 0);

      EXPECT_EQ(   txs[i].serialize(), rawTx0_);
      EXPECT_EQ(   txs[0].getTxIn(0).getSenderAddrIfAvailable(), tx0_In0);
      EXPECT_EQ(   txs[i].getTxOut(0).getRecipientAddr(), tx0_Out0);
      EXPECT_EQ(   txs[i].getTxOut(1).getRecipientAddr(), tx0_Out1);
      EXPECT_EQ(   txs[i].getRecipientForTxOut(0), tx0_Out0);
      EXPECT_EQ(   txs[i].getRecipientForTxOut(1), tx0_Out1);
      EXPECT_EQ(   txs[i].getTxOut(0).getValue(), v0);
      EXPECT_EQ(   txs[i].getTxOut(1).getValue(), v1);
      EXPECT_EQ(   txs[i].getSumOfOutputs(),  v0+v1);

      EXPECT_EQ(   txs[i].getBlockTxIndex(),  UINT32_MAX);
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
         "76a9146a59ac0e8f553f292dfe5e9f3aaa1da93499c15e88ac");

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

   BlockHeader bh_;
   Tx tx1_;
   Tx tx2_;

   BinaryData rawTxUnfrag_;
   BinaryData rawTxFragged_;
   BinaryData rawTxOut0_;
   BinaryData rawTxOut1_;
};



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
TEST_F(StoredBlockObjTest, StoredHeaderNoInit)
{
   StoredHeader sbh;
   
   EXPECT_FALSE(sbh.isInitialized());
   EXPECT_FALSE(sbh.haveFullBlock());
   EXPECT_FALSE(sbh.isMerkleCreated());
}


////////////////////////////////////////////////////////////////////////////////
TEST_F(StoredBlockObjTest, StoredHeaderUnserialize)
{
   StoredHeader sbh;

   sbh.unserialize(rawHead_);
   
   EXPECT_TRUE( sbh.isInitialized());
   EXPECT_FALSE(sbh.isMainBranch_);
   EXPECT_FALSE(sbh.haveFullBlock());
   EXPECT_FALSE(sbh.isMerkleCreated());
   EXPECT_EQ(   sbh.numTx_,       UINT32_MAX);
   EXPECT_EQ(   sbh.numBytes_,    UINT32_MAX);
   EXPECT_EQ(   sbh.blockHeight_, UINT32_MAX);
   EXPECT_EQ(   sbh.duplicateID_, UINT8_MAX);
   EXPECT_EQ(   sbh.merkle_.getSize(), 0);
   EXPECT_EQ(   sbh.stxMap_.size(), 0);
}


////////////////////////////////////////////////////////////////////////////////
TEST_F(StoredBlockObjTest, StoredTxNoInit)
{
   StoredTx stx;

   EXPECT_FALSE(stx.isInitialized());
   EXPECT_FALSE(stx.haveAllTxOut());
}

////////////////////////////////////////////////////////////////////////////////
TEST_F(StoredBlockObjTest, StoredTxUnserUnfrag)
{
   Tx regTx(rawTx0_);

   StoredTx stx;
   stx.createFromTx(regTx, false);

   EXPECT_TRUE( stx.isInitialized());
   EXPECT_TRUE( stx.haveAllTxOut());
   EXPECT_FALSE(stx.isFragged_);
   EXPECT_EQ(   stx.version_, 1);
   EXPECT_EQ(   stx.blockHeight_, UINT32_MAX);
   EXPECT_EQ(   stx.blockDupID_,  UINT8_MAX);
   EXPECT_EQ(   stx.txIndex_,     UINT16_MAX);
   EXPECT_EQ(   stx.dataCopy_.getSize(), 258);

   ASSERT_EQ(   stx.stxoMap_.size(), 2);
   EXPECT_TRUE( stx.stxoMap_[0].isInitialized());
   EXPECT_TRUE( stx.stxoMap_[1].isInitialized());
   EXPECT_EQ(   stx.stxoMap_[0].txIndex_, UINT16_MAX);
   EXPECT_EQ(   stx.stxoMap_[1].txIndex_, UINT16_MAX);
   EXPECT_EQ(   stx.stxoMap_[0].txOutIndex_, 0);
   EXPECT_EQ(   stx.stxoMap_[1].txOutIndex_, 1);
}


////////////////////////////////////////////////////////////////////////////////
TEST_F(StoredBlockObjTest, StoredTxUnserFragged)
{
   Tx regTx(rawTx0_);

   StoredTx stx;
   stx.createFromTx(regTx, true);

   EXPECT_TRUE( stx.isInitialized());
   EXPECT_TRUE( stx.haveAllTxOut());
   EXPECT_TRUE( stx.isFragged_);
   EXPECT_EQ(   stx.version_, 1);
   EXPECT_EQ(   stx.blockHeight_, UINT32_MAX);
   EXPECT_EQ(   stx.blockDupID_,  UINT8_MAX);
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
TEST_F(StoredBlockObjTest, StoredTxReconstruct)
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
////////////////////////////////////////////////////////////////////////////////
class TxRefTest : public ::testing::Test
{
protected:
};



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
TEST_F(TxRefTest, TxRefNoInit)
{
   TxRef txr;
   EXPECT_FALSE(txr.isInitialized());
   EXPECT_FALSE(txr.isBound());

   EXPECT_EQ(txr.getLevelDBKey(),     BinaryData(0));
   EXPECT_EQ(txr.getLevelDBKeyRef(),  BinaryDataRef());
   //EXPECT_EQ(txr.getBlockTimestamp(), UINT32_MAX);
   EXPECT_EQ(txr.getBlockHeight(),    UINT32_MAX);
   EXPECT_EQ(txr.getBlockDupID(),     UINT8_MAX );
   EXPECT_EQ(txr.getBlockTxIndex(),   UINT16_MAX);
}

////////////////////////////////////////////////////////////////////////////////
TEST_F(TxRefTest, TxRefKeyParts)
{
   TxRef txr;
   //BinaryData    newKey = READHEX("02c4e3020100");
   BinaryData    newKey = READHEX("7fe3c4020f00");
   BinaryDataRef newRef(newKey);


   txr.setLevelDBKey(newKey);
   EXPECT_EQ(txr.getLevelDBKey(),    newKey);
   EXPECT_EQ(txr.getLevelDBKeyRef(), newRef);

   EXPECT_EQ(txr.getBlockHeight(),  0x02c4e3);
   EXPECT_EQ(txr.getBlockDupID(),   127);
   EXPECT_EQ(txr.getBlockTxIndex(), 15);
}


////////////////////////////////////////////////////////////////////////////////
// Now actually execute all the tests
////////////////////////////////////////////////////////////////////////////////
GTEST_API_ int main(int argc, char **argv) 
{
   std::cout << "Running main() from gtest_main.cc\n";

   // Setup the log file 
   Log::SetLogFile("cppTestsLog.txt");
   Log::SetLogLevel(LogDebug4);

   testing::InitGoogleTest(&argc, argv);
   return RUN_ALL_TESTS();
}






