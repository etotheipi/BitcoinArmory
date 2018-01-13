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

%module(directors="1") CppBlockUtils
%feature("director") PythonCallback;
%feature("director") PythonSigner;
%feature("director") PythonSigner_BCH;
%feature("director") UniversalSigner;
%feature("director") ProcessMutex;

%{
#define SWIG_PYTHON_EXTRA_NATIVE_CONTAINERS
#include "BtcUtils.h"
#include "EncryptionUtils.h"
#include "DbHeader.h"
#include "SwigClient.h"
#include "bdmenums.h"
#include "TxClasses.h"
#include "WalletManager.h"
#include "BlockDataManagerConfig.h"
#include "TransactionBatch.h"
#include "TxEvalState.h"
%}

%include "std_string.i"
%include "std_vector.i"
%include "std_set.i"
%include "std_map.i"
%include "std_shared_ptr.i"
%include "exception.i"

%typedef std::string string;
%typedef unsigned char      uint8_t;
%typedef unsigned short     uint16_t;
%typedef unsigned int       uint32_t;

#if defined(_WIN32) || defined(__WIN32__) || defined(__CYGWIN__) || defined(__CLANG__)
%typedef unsigned long long uint64_t;
#else
#if defined(__GNUC__) // Linux
#if defined(__LP64__) // 64bit
%typedef long unsigned int uint64_t;
#else // Linux 32bit
%typedef long long unsigned int uint64_t;
#endif
#else
%typedef unsigned long long uint64_t;
#endif
#endif

%typedef char               int8_t;
%typedef short              int16_t;
%typedef int                int32_t;
%typedef long long          int64_t;
%typedef unsigned int       TXIN_SCRIPT_TYPE;
%typedef unsigned int       TXOUT_SCRIPT_TYPE;
%typedef unsigned long long size_t;

%ignore readVarInt(BinaryRefReader & brr);

%allowexception;

namespace std
{
   %template(vector_int) std::vector<int>;
   %template(vector_uint64_t) std::vector<uint64_t>; 
   %template(vector_float) std::vector<float>;
   %template(vector_string) std::vector<string>;
   %template(vector_LedgerEntryData) std::vector<LedgerEntryData>;
   %template(set_BinaryData) std::set<BinaryData>;
   %template(vector_UTXO) std::vector<UTXO>;
   %template(vector_AddressBookEntry) std::vector<AddressBookEntry>;
   %template(vector_TxBatchRecipient) std::vector<Recipient>;
   %template(vector_TxBatchSpender) std::vector<Spender>;
}

%exception
{
	try
	{
		$function
	}
	catch (std::exception& e)
	{
		SWIG_exception(SWIG_RuntimeError, e.what());
	}
	catch (DbErrorMsg& e)
	{
		SWIG_Python_Raise(SWIG_NewPointerObj(
			(new DbErrorMsg(static_cast<const DbErrorMsg&>(e))),
			SWIGTYPE_p_DbErrorMsg, SWIG_POINTER_OWN),
			"DbErrorMsg", SWIGTYPE_p_DbErrorMsg);
		SWIG_fail;
	}
	catch (RecipientReuseException& e)
	{
		SWIG_Python_Raise(SWIG_NewPointerObj(
			(new RecipientReuseException(static_cast<const RecipientReuseException&>(e))),
			SWIGTYPE_p_RecipientReuseException, SWIG_POINTER_OWN),
			"RecipientReuseException", SWIGTYPE_p_RecipientReuseException);
		SWIG_fail;
	}

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

/* Convert C++(const BinaryDataRef) to Python(str) */
%typemap(out) const BinaryDataRef
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

/******************************************************************************/
// Convert Python(list[string]) to C++(vector<BinaryData>) 
%typemap(in) const std::vector<BinaryData> & (std::vector<BinaryData> bdObjVec)
{
	for(int i=0; i<PyList_Size($input); i++)
	{
		PyObject* strobj = PyList_GetItem($input, i);
		
		BinaryData bdStr((uint8_t*)PyString_AsString(strobj), PyString_Size(strobj));

		bdObjVec.push_back(bdStr);
	}

	$1 = &bdObjVec;
}

/******************************************************************************/
// Convert C++(vector<BinaryData>) to Python(list[string])
%typemap(out) vector<BinaryData>
{
	vector<BinaryData>::iterator bdIter = $1.begin();
	PyObject* thisList = PyList_New($1.size());
	int i=0;

	while(bdIter != $1.end())
	{
		BinaryData & bdobj = (*bdIter);
		
		PyObject* thisPyObj = PyString_FromStringAndSize((char*)(bdobj.getPtr()), bdobj.getSize());

		PyList_SET_ITEM(thisList, i, thisPyObj);

		++i;
		++bdIter;
	}

	$result = thisList;
}

/******************************************************************************/
// Convert C++(set<BinaryData>) to Python(list[string])
%typemap(out) set<BinaryData>
{
	set<BinaryData>::iterator bdIter = $1.begin();
	PyObject* thisList = PyList_New($1.size());
	int i=0;

	while(bdIter != $1.end())
	{
		auto& bdobj = (*bdIter);
		
		PyObject* thisPyObj = PyString_FromStringAndSize(bdobj.getCharPtr(), bdobj.getSize());

		PyList_SET_ITEM(thisList, i, thisPyObj);

		++i;
		++bdIter;
	}

	$result = thisList;
}

/******************************************************************************/
// Convert Python(dict{str:list[str]}) to C++(map<BinaryData, vector<BinaryData>) 
%typemap(in) const std::map<BinaryData, std::vector<BinaryData> >& (std::map<BinaryData, std::vector<BinaryData> > map_bd_vec_bd)
{
	PyObject *key, *value;
	Py_ssize_t pos = 0;

	while(PyDict_Next($input, &pos, &key, &value))
	{
		BinaryData wltIDStr((uint8_t*)PyString_AsString(key), PyString_Size(key));
		std::vector<BinaryData> bdObjVec;

		for(int i=0; i<PyList_Size(value); i++)
		{
			PyObject* strobj = PyList_GetItem(value, i);
		
			BinaryData bdStr((uint8_t*)PyString_AsString(strobj), PyString_Size(strobj));

			bdObjVec.push_back(bdStr);
		}

		map_bd_vec_bd.insert(std::make_pair(wltIDStr, std::move(bdObjVec)));
	}
	$1 = &map_bd_vec_bd;
}

/******************************************************************************/
// Convert C++(StoredHeader) to a Python dict with the following key:val pairs:
// {
// "height":int
// "blockHash":str
// "merkle":str
// "numBytes":int
// "numTx":int
// "txHashList":[TxHash, TxHash, TxHash, ...]
// }
%typemap(out) StoredHeader
{
	PyObject *thisDict = PyDict_New();

	//height
	PyDict_SetItemString(thisDict, "height", PyInt_FromSize_t($1.blockHeight_));

	//block hash
	std::string hashStr = $1.thisHash_.toHexStr(true);
	PyDict_SetItemString(thisDict, "blockHash", 
		PyString_FromStringAndSize(hashStr.c_str(), hashStr.size()));

	//merkle
	std::string merkleStr = $1.merkle_.toHexStr(true);
	PyDict_SetItemString(thisDict, "merkle", 
		PyString_FromStringAndSize(merkleStr.c_str(), merkleStr.size()));

	//size of block in bytes
	PyDict_SetItemString(thisDict, "numBytes", PyInt_FromSize_t($1.numBytes_));

	//tx count
	PyDict_SetItemString(thisDict, "numTx", PyInt_FromSize_t($1.getNumTx()));

	PyObject *thisList = PyList_New($1.getNumTx());
	
	//tx hash list
	for(unsigned i=0; i<$1.getNumTx(); i++)
	{
		DBTx& tx = $1.getTxByIndex(i);
		std::string hashStr = tx.thisHash_.toHexStr(true);
		PyList_SET_ITEM(thisList, i, 
			PyString_FromStringAndSize(hashStr.c_str(), hashStr.size()));
	}

	//add list to dict
	PyDict_SetItemString(thisDict, "txHashList", thisList);

	$result = thisDict;
}

/******************************************************************************/
// Convert C++(map<BinaryData, uint32_t>) to Python(dict{string, int})
%typemap(out) const map<BinaryData, uint32_t> &
{
	PyObject* thisDict = PyDict_New();
	auto bdIter = $1->begin();

	while(bdIter != $1->end())
	{
		auto& bdobj = bdIter->first;
		PyObject* pyStringObj = 
		   PyString_FromStringAndSize(bdobj.getCharPtr(), bdobj.getSize());
		
		PyObject* pyIntObj =
		   PyInt_FromLong(bdIter->second);

		PyDict_SetItem(thisDict, pyStringObj, pyIntObj);

		++bdIter;
	}

	$result = thisDict;
}

/******************************************************************************/
// Convert C++(map<BinaryData, vector<uint64_t>>) to Python(dict{string, list[int]})
%typemap(out) const map<BinaryData, vector<uint64_t> > &
{
	PyObject* thisDict = PyDict_New();
	auto bdIter = $1->begin();

	while(bdIter != $1->end())
	{
		auto& bdobj = bdIter->first;
		PyObject* pyStringObj = 
		   PyString_FromStringAndSize(bdobj.getCharPtr(), bdobj.getSize());
		
		auto& vectorObj = bdIter->second;
		auto vectorIter = vectorObj.begin();

		PyObject* thisList = PyList_New(vectorObj.size());
		int i=0;
		while(vectorIter != vectorObj.end())
		{
			PyObject* pyIntObj =
				PyInt_FromSize_t(*vectorIter);

			PyList_SET_ITEM(thisList, i, pyIntObj);

			++vectorIter;
			++i;
		}

		PyDict_SetItem(thisDict, pyStringObj, thisList);

		++bdIter;
	}

	$result = thisDict;
}

/******************************************************************************/
// Convert Python(dict{str:dict{int:str}}) to 
// C++(map<BinaryData. map<unsigned, BinaryData>>
%typemap(in) const std::map<BinaryData, std::map<unsigned, BinaryData> > & (std::map<BinaryData, std::map<unsigned, BinaryData> > map_bd_map_uint_bd)
{
	PyObject *key, *value;
	Py_ssize_t pos = 0;

	while(PyDict_Next($input, &pos, &key, &value))
	{
		BinaryData key_bd((uint8_t*)PyString_AsString(key), PyString_Size(key));
		std::map<unsigned, BinaryData> bdObjMap;

		PyObject *inner_key, *inner_value;
		Py_ssize_t inner_pos = 0;

		while(PyDict_Next(value, &inner_pos, &inner_key, &inner_value))
		{
			unsigned inner_key_uint = PyInt_AsLong(inner_key);
			 
			BinaryData inner_value_bd(
				(uint8_t*)PyString_AsString(inner_value), PyString_Size(inner_value));

			bdObjMap.insert(std::move(std::make_pair(
				inner_key_uint,
				std::move(inner_value_bd))));
		}

		map_bd_map_uint_bd.insert(std::move(std::make_pair(
			key_bd, 
			std::move(bdObjMap))));
	}
	
	$1 = &map_bd_map_uint_bd;	
}


%include "BtcUtils.h"
%include "EncryptionUtils.h"
%include "DbHeader.h"
%include "SwigClient.h"
%include "bdmenums.h"
%include "LedgerEntryData.h"
%include "TxClasses.h"
%include "WalletManager.h"
%include "BlockDataManagerConfig.h"
%include "TransactionBatch.h"
%include "TxEvalState.h"

