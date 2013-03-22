////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2013, Alan C. Reiner    <alan.reiner@gmail.com>        //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE or http://www.gnu.org/licenses/agpl.html                      //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////
// 
// A very simple program that simply monitors one PID, and kills another one
// when it disappears.  This is needed for when Armory spawns a bitcoind 
// process in the background, but crashes before it can close it.  Armory 
// will launch this "guardian" to kill bitcoind.exe if Armory.exe disappears.
// 
#include <windows.h>
#include <tlhelp32.h>
#include <tchar.h>
#include <iomanip>
#include <stdio.h>

//  Forward declarations:
BOOL GetProcessList( );
BOOL ListProcessModules( DWORD dwPID );
BOOL ListProcessThreads( DWORD dwOwnerPID );
void printError( TCHAR* msg );
bool processIsStillRunning(HANDLE hndl);

int main(int argc, char** argv )
{
   if(argc != 3)
   {
      _tprintf( TEXT("\nInvalid arguments:"));
      _tprintf( TEXT("\nUSAGE:  guardian.exe pidWatch pidKill"));
      // I know I should use argv[0] instead of "guardian.exe", but I 
      // don't feel like messing with strings<->windows.h.  I had a bad
      // experience once...
      return 1;
   }
   int pidWatch = atoi(argv[1]);
   int pidKill  = atoi(argv[2]);

   HANDLE hWatch = OpenProcess(PROCESS_ALL_ACCESS, FALSE, static_cast<DWORD>(pidWatch));
   HANDLE hKill = OpenProcess(PROCESS_ALL_ACCESS, FALSE, static_cast<DWORD>(pidKill));

   while(processIsStillRunning(hWatch))
      Sleep(static_cast<DWORD>(2000));

   _tprintf( TEXT("\nThe watched process died!"));
   TerminateProcess(hKill, 0);
   _tprintf( TEXT("\nAttempted to kill the other process!"));
   return 0;
}

bool processIsStillRunning(HANDLE hndl)
{
   DWORD exitCode = 0;
   GetExitCodeProcess(hndl, &exitCode);
   return (exitCode==STILL_ACTIVE);
}
