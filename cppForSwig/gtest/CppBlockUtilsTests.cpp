#include <limits.h>
#include <iostream>
#include "gtest/gtest.h"

#include "../log.h"
#include "../BinaryData.h"
#include "../BtcUtils.h"

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
   BinaryData pub1   = READHEX("034758cefcb75e16e4dfafb32383b709fa632086ea5ca982712de6add93060b17a");
   BinaryData pub2   = READHEX("03fe96237629128a0ae8c3825af8a4be8fe3109b16f62af19cec0b1eb93b8717e2");
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






