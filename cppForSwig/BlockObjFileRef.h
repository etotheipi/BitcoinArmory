#ifndef _BLOCKOBJFILEREF_H_
#define _BLOCKOBJFILEREF_H_

#include "BinaryData.h"
#include "BtcUtils.h"
#include "FileDataRef.h"



////////////////////////////////////////////////////////////////////////////////
class BlockHeaderFileRef
{
   BlockHeaderRef getBlockHeaderRef(void)
   {
      tempCopy_.copyFrom(fdr_.getTempDataPtr(), fdr_.getNumBytes());
      return BlockHeaderRef(tempCopy_);
   }

private:
   FileDataRef fdr_;
   BinaryData  tempCopy_;
};


////////////////////////////////////////////////////////////////////////////////
class OutPointFileRef
{

private:
   FileDataRef fdr_;
   BinaryData  tempCopy_;
};


////////////////////////////////////////////////////////////////////////////////
class TxInFileRef
{

private:
   FileDataRef fdr_;
   BinaryData  tempCopy_;
};


////////////////////////////////////////////////////////////////////////////////
class TxOutFileRef
{

private:
   FileDataRef fdr_;
   BinaryData  tempCopy_;
};

////////////////////////////////////////////////////////////////////////////////
class TxFileRef
{

private:
   FileDataRef fdr_;
   BinaryData  tempCopy_;
};
#endif
