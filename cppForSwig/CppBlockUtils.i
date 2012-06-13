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
%typedef unsigned int       TXIN_SCRIPT_TYPE;
%typedef unsigned int       TXOUT_SCRIPT_TYPE;

namespace std
{
   %template(vector_int) std::vector<int>;
   %template(vector_float) std::vector<float>;
   %template(vector_BinaryData) std::vector<BinaryData>;
   %template(vector_LedgerEntry) std::vector<LedgerEntry>;
   %template(vector_TxRefPtr) std::vector<TxRef*>;
   %template(vector_Tx) std::vector<Tx>;
   %template(vector_BlockHeaderPtr) std::vector<BlockHeader>;
   %template(vector_UnspentTxOut) std::vector<UnspentTxOut>;
   %template(vector_BtcWallet) std::vector<BtcWallet*>;
   %template(vector_AddressBookEntry) std::vector<AddressBookEntry>;
   %template(vector_RegisteredTx) std::vector<RegisteredTx>;
}
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
%include "BlockUtils.h"
%include "BtcUtils.h"
%include "EncryptionUtils.h"


