/* File BlockUtils.i */
/*
////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011, Alan C. Reiner    <alan.reiner@gmail.com>             //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE or http://www.gnu.org/licenses/agpl.html                      //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////
*/

%module CppBlockUtils

%{
#define SWIG_PYTHON_EXTRA_NATIVE_CONTAINERS
#include "BlockObj.h"
#include "BlockObjRef.h"
#include "BlockUtils.h"
#include "BtcUtils.h"
#include "EncryptionUtils.h"
%}

%include "std_string.i"
%include "std_vector.i"

%typedef std::string string;
%typedef unsigned char      uint8_t;
%typedef unsigned short     uint16_t;
%typedef unsigned int       uint32_t;
%typedef unsigned long long uint64_t;
%typedef char               int8_t;
%typedef short              int16_t;
%typedef int                int32_t;
%typedef long long          int64_t;
%typedef unsigned int       size_t;
%typedef long int64_t;
%typedef unsigned int TXIN_SCRIPT_TYPE;
%typedef unsigned int TXOUT_SCRIPT_TYPE;

namespace std
{
   %template(vector_int) std::vector<int>;
   %template(vector_float) std::vector<float>;
   %template(vector_BinaryData) std::vector<BinaryData>;
   %template(vector_LedgerEntry) std::vector<LedgerEntry>;
   %template(vector_TxRefPtr) std::vector<TxRef*>;
   %template(vector_HeaderRefPtr) std::vector<BlockHeaderRef*>;
   %template(vector_UnspentTxOut) std::vector<UnspentTxOut>;
}

/*
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
class BinaryData
{
public:
   BinaryData(string str);
   BinaryData(size_t sz);
   BinaryData(BinaryDataRef const & bdRef);

   void copyFrom(BinaryDataRef const & bdr);

   size_t getSize(void);
   void   createFromHex(string const & str);
   string toString(void);
   string toHex(void);
};
*/

/*
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
class BinaryDataRef
{
public:
   BinaryDataRef(void);
   BinaryDataRef(BinaryData const & bd);

   size_t getSize(void) const;
   string toString(void) const;
   string toHex(void) const;
   BinaryData copy(void) const;
};
*/

/******************************************************************************/
/* Convert Python(str) to C++(BinaryData) */
%typemap(in) BinaryData
{
   if(!PyString_Check($input))
   {
      PyErr_SetString(PyExc_ValueError, "Expected string argument!");
      return NULL;
   }
   
   $1 = BinaryData((uint8_t*)PyString_AsString($input), PyString_Size($input));
}

/******************************************************************************/
/* Convert C++(BinaryData) to Python(str) */
%typemap(out) BinaryData
{
   $result = PyString_FromStringAndSize((char*)($1.getPtr()), $1.getSize());
}

/******************************************************************************/
/*
// Convert Python(str) to C++(BinaryData const &) 
// We add a bdObj which will get created outside the typemap block,
// so that we have a BinaryData obj that isn't destroyed before it 
// is referenced (search CppBlockUtils_wrap.cxx for "bdObj")
*/
%typemap(in) BinaryData const & (BinaryData bdObj)
{
   if(!PyString_Check($input))
   {
      PyErr_SetString(PyExc_ValueError, "Expected string argument!");
      return NULL;
   }
   bdObj.copyFrom((uint8_t*)PyString_AsString($input), PyString_Size($input));
   $1 = &bdObj;
}

/******************************************************************************/
/* Convert C++(BinaryData const &) to Python(str) */
%typemap(out) BinaryData const & 
{
   $result = PyString_FromStringAndSize((char*)($1->getPtr()), $1->getSize());
}



/* With our typemaps, we can finally include our other objects */
%include "BlockObj.h"
%include "BlockObjRef.h"
%include "BlockUtils.h"
%include "BtcUtils.h"
%include "EncryptionUtils.h"



/*
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
struct BtcAddress
{
   BtcAddress(void);
   BtcAddress(BinaryData    addr, 
              BinaryData    pubKey65  = BinaryData(0),
              BinaryData    privKey32 = BinaryData(0),
              uint32_t      createdBlockNum  = 0,
              uint32_t      createdTimestamp = 0);

   BinaryData address20_;
   BinaryData pubkey65_;
   BinaryData privkey32_;
   uint32_t createdBlockNum_;
   uint32_t createdTimestamp_;

};


/*
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
class BtcWallet
{
   void addAddress(BtcAddress const & newAddr);
   void addAddress(BinaryData    addr, 
                   BinaryData    pubKey65  = BinaryData(0),
                   BinaryData    privKey32 = BinaryData(0),
                   uint32_t      createdBlockNum  = 0,
                   uint32_t      createdTimestamp = 0);


   uint64_t getBalance(void);
   uint64_t getBalance(BinaryData const & addr20);
 
   uint32_t getNumAddr(void);
   BtcAddress & getAddrByIndex(uint32_t i);
};


////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
class BlockHeader
{
public:
   BlockHeader(void);
   BlockHeader(BinaryData const & header80B);
   BinaryData serialize(void);

   uint32_t     getVersion(void) const;        
   BinaryData   getPrevHash(void) const;
   BinaryData   getMerkleRoot(void) const;
   uint32_t     getTimestamp(void) const;
   BinaryData   getDiffBits(void) const;
   uint32_t     getNonce(void) const;
   double       getDifficulty(void) const;
   double       getDifficultySum(void) const;
   uint32_t     getBlockHeight(void) const;
   uint32_t     isMainBranch(void) const;
   uint32_t     isOrphan(void) const;
   void         printHeader(ostream & os=cout);
   BinaryData   getThisHash(void) const;

};

////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
class TxIn
{

};

////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
class TxOut
{

};

////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
class Tx
{

};

////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
class BlockHeaderRef
{
public:
   BlockHeader(void);
   BlockHeader(BinaryData const & header80B);
   BinaryDataRef serialize(void);

   uint32_t        getVersion(void) const;        
   BinaryDataRef   getPrevHash(void) const;
   BinaryDataRef   getMerkleRoot(void) const;
   uint32_t        getTimestamp(void) const;
   BinaryDataRef   getDiffBits(void) const;
   uint32_t        getNonce(void) const;
   double          getDifficulty(void) const;
   double          getDifficultySum(void) const;
   uint32_t        getBlockHeight(void) const;
   uint32_t        isMainBranch(void) const;
   uint32_t        isOrphan(void) const;
   void            printHeader(ostream & os=cout);
   BinaryDataRef   getThisHash(void);

};

////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
class TxInRef
{

};

////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
class TxOutRef
{

};

////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
class TxRef
{

};

////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
class BlockDataManager
{
public:
   BlockDataManager(void);

   void loadBlockchain(char* filename);
   void resetBlockchainData(void);

   BlockHeader getHeaderByHeight(unsigned int height);
   BlockHeader getHeaderByHash(BinaryData const & theHash);
   BlockHeader getTopBlockHeader(void);
   unsigned int     getTopBlockHeight(void);

   vector<int>        getTop10BlockHeights(void);
   vector<BinaryData> getTop10BlockHashes(void);

};
*/

