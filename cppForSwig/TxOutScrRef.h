////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2016, goatpig.                                              //
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //                                      
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#ifndef _H_TXOUTSCRIPTREF
#define _H_TXOUTSCRIPTREF

struct TxOutScriptRef
{
   SCRIPT_PREFIX type_ = SCRIPT_PREFIX_NONSTD;
   BinaryDataRef scriptRef_;
   BinaryData scriptCopy_;

   void copyFrom(const TxOutScriptRef& outscr)
   {
      type_ = outscr.type_;
      if(outscr.scriptCopy_.getSize())
      {
         scriptCopy_ = outscr.scriptCopy_;
         scriptRef_.setRef(scriptCopy_);
      }
      else
      {
         scriptRef_ = outscr.scriptRef_;
      }
   }

   TxOutScriptRef()
   {}

   TxOutScriptRef(const TxOutScriptRef& outscr)
   {
      copyFrom(outscr);
   }

   TxOutScriptRef(TxOutScriptRef&& outscr)
   {
      type_ = move(outscr.type_);
      if (outscr.scriptCopy_.getSize() > 0)
      {
         scriptCopy_ = move(outscr.scriptCopy_);
         outscr.scriptRef_.setRef(scriptCopy_);
      }

      scriptRef_ = move(outscr.scriptRef_);
   }

   TxOutScriptRef& operator=(const TxOutScriptRef& rhs)
   {
      if(this !=  &rhs)
         copyFrom(rhs);
      return *this;
   }

   bool operator == (const TxOutScriptRef& rhs) const
   {
      if (this->type_ != rhs.type_)
         return false;

      return this->scriptRef_ == rhs.scriptRef_;
   }

   bool operator < (const TxOutScriptRef& rhs) const
   {
      if (this->type_ == rhs.type_)
         return this->scriptRef_ < rhs.scriptRef_;
      else
         return this->type_ < rhs.type_;
   }

   void setRef(const BinaryData& bd)
   {
      type_ = (SCRIPT_PREFIX)bd.getPtr()[0];
      scriptRef_ = bd.getSliceRef(1, bd.getSize() - 1);
   }

   BinaryData getScrAddr(void) const
   {
      BinaryWriter bw;
      bw.put_uint8_t(type_);
      bw.put_BinaryData(scriptRef_);

      return bw.getData();
   }
};

#endif
