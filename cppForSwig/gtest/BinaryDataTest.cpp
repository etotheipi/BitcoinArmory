#include <limits.h>
#include <iostream>
#include "gtest/gtest.h"

#include "../BinaryData.h"


////////////////////////////////////////////////////////////////////////////////
class BinaryDataTest : public ::testing::Test
{
protected:
   virtual void SetUp(void) 
   {
      str0_ = "";
      str4_ = "1234abcd";
      str5_ = "1234abcdef";

      bd0_ = BinaryData::CreateFromHex(str0_);
      bd4_ = BinaryData::CreateFromHex(str4_);
      bd5_ = BinaryData::CreateFromHex(str5_);
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
   BinaryData aAns = BinaryData::CreateFromHex("");
   BinaryData bAns = BinaryData::CreateFromHex("aa");
   BinaryData cAns = BinaryData::CreateFromHex("aaaaaaaa");

   a.fill(0xaa);
   b.fill(0xaa);
   c.fill(0xaa);

   EXPECT_EQ(a, aAns);
   EXPECT_EQ(b, bAns);
   EXPECT_EQ(c, cAns);
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
TEST_F(BinaryDataTest, IndexOp)
{
   //str4_ = "1234abcd";
   //str5_ = "1234abcdef";
   EXPECT_EQ(bd4_[0], 0x12);
   EXPECT_EQ(bd4_[1], 0x34);
   EXPECT_EQ(bd4_[2], 0xab);
   EXPECT_EQ(bd4_[3], 0xcd);

   bd4_[1] = 0xff;
   EXPECT_EQ(bd4_[0], 0x12);
   EXPECT_EQ(bd4_[1], 0xff);
   EXPECT_EQ(bd4_[2], 0xab);
   EXPECT_EQ(bd4_[3], 0xcd);

   EXPECT_EQ(bd4_.toHexStr(), string("12ffabcd"));
}

////////////////////////////////////////////////////////////////////////////////
TEST_F(BinaryDataTest, StartsWith)
{
   EXPECT_TRUE( bd0_.startsWith(bd0_));
   EXPECT_TRUE( bd4_.startsWith(bd0_));
   EXPECT_TRUE( bd5_.startsWith(bd4_));
   EXPECT_TRUE( bd5_.startsWith(bd5_));
   EXPECT_FALSE(bd4_.startsWith(bd5_));
   EXPECT_TRUE( bd0_.startsWith(bd0_));
   EXPECT_FALSE(bd0_.startsWith(bd4_));
}


////////////////////////////////////////////////////////////////////////////////
TEST_F(BinaryDataTest, ToHexStr)
{
   EXPECT_EQ(bd4_.toHexStr(), str4_);
   EXPECT_EQ(bd4_.toHexStr(), str4_);
}


////////////////////////////////////////////////////////////////////////////////
TEST_F(BinaryDataTest, Append)
{
   BinaryData a = BinaryData::CreateFromHex("ef");

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





