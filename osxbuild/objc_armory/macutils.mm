// Copyright (c) 2011-2014 The Bitcoin Core developers
// Distributed under the MIT/X11 software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.

////////////////////////////////////////////////////////////////////////////////
//
// Copyright (C) 2011-2014, Armory Technologies, Inc.
// Distributed under the GNU Affero General Public License (AGPL v3)
// See LICENSE or http://www.gnu.org/licenses/agpl.html
//
////////////////////////////////////////////////////////////////////////////////

#include "ArmoryMac.h"

#undef slots
#include <Cocoa/Cocoa.h>
#include <QString>

// For future reference, the following C++string/NSString code _should_ work.
// C++ to Obj-C++
// NSString* result = [[NSString alloc] initWithUTF8String:cppString.c_str()];
// Obj-C++ to C++
// NSString* strToConv = "xyz"; string retStr = [strToConv UTF8String];

// Code that create a file open dialog. For unknown reasons, Qt/PyQt/SWIG/???
// creates non-responsive native file dialogs. Handling things directly seems to
// help. Only returns one filename for now. Needs more polish.
QString MacUtils::openFile()
{
    NSUInteger i; // Loop counter.
    NSString* fileName = nil;

    // Create the File Open Dialog class.
    NSOpenPanel* openDlg = [NSOpenPanel openPanel];

    // Enable the selection of files in the dialog.
    [openDlg setCanChooseFiles:YES];

    // Enable the selection of directories in the dialog.
    [openDlg setCanChooseDirectories:YES];

    // Display the dialog. If the OK button was pressed,
    // process the files.
    if ( [openDlg runModalForDirectory:nil file:nil] == NSOKButton )
    {
        // Get an array containing the full filenames of all
        // files and directories selected.
        NSArray* files = [openDlg filenames];

        // Loop through all the files and process them.
        for( i = 0; i < [files count]; i++ )
        {
            fileName = [files objectAtIndex:i];
        }
    }
    QString retStr = [fileName UTF8String];
    return retStr;
}

MacUtils* MacUtils::instance()
{
    static MacUtils* s_instance = NULL;
    if (!s_instance)
        s_instance = new MacUtils();
    return s_instance;
}
