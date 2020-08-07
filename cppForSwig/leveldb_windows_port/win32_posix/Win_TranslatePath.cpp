////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2015, Armory Technologies, Inc.                        //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE-ATI or http://www.gnu.org/licenses/agpl.html                  //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////
#include <Win_TranslatePath.h>

std::wstring Win_TranslatePath(std::string path)
{
	wchar_t rtw[MAX_PATH];
	MultiByteToWideChar(CP_UTF8, 0, path.c_str(), -1, rtw, MAX_PATH);

	std::wstring rtstring; 

	rtstring.assign(rtw);

	return rtstring;
}
