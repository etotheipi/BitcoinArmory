////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2012, Alan C. Reiner    <alan.reiner@gmail.com>        //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE or http://www.gnu.org/licenses/agpl.html                      //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////
#ifndef _BINARYDATAMMAP_H_
#define _BINARYDATAMMAP_H_

// Memory-Mapped Files.  Unfortunately, completely different between Win & Linux
#if defined(_MSC_VER) || defined(__MINGW32__)
   #include "BinaryDataMMAP_Windows.h"
#else
   #include "BinaryDataMMAP_POSIX.h"
#endif


#endif
