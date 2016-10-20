////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2016, goatpig.                                              //
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //                                      
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#ifndef _H_DB_HEADER
#define _H_DB_HEADER

#include <string>

class DbErrorMsg
{
   const std::string err_;

public:
   DbErrorMsg(const std::string& errstr) : 
      err_(errstr)
   {}

   const std::string& what(void) const { return err_; }
};

#endif
