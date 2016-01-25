////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2014, Armory Technologies, Inc.                        //
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

bool processIsStillRunning(HANDLE hndl)
{
   DWORD exitCode = 0;
   GetExitCodeProcess(hndl, &exitCode);
   return (exitCode==STILL_ACTIVE);
}

DWORD getProcessWithParent(int pid)
{
  HANDLE hProcessSnap;
  PROCESSENTRY32 pe32;

  // Take a snapshot of all processes in the system.
  hProcessSnap = CreateToolhelp32Snapshot( TH32CS_SNAPPROCESS, 0 );
  if( hProcessSnap == INVALID_HANDLE_VALUE )
  {
    return( FALSE );
  }

  // Set the size of the structure before using it.
  pe32.dwSize = sizeof( PROCESSENTRY32 );

  // Retrieve information about the first process,
  // and exit if unsuccessful
  if( !Process32First( hProcessSnap, &pe32 ) )
  {
    CloseHandle( hProcessSnap );          // clean the snapshot object
    return( FALSE );
  }

  // Now walk the snapshot of processes, and
  // display information about each process in turn
  DWORD parent = static_cast<DWORD>(pid);
  DWORD childID = 0xffffffff;
  do
  {
      if(pe32.th32ParentProcessID == parent)
         return static_cast<int>(pe32.th32ProcessID);
  } while( Process32Next( hProcessSnap, &pe32 ) );

  _tprintf( TEXT("Never found process with parent!") );
  return childID;
}

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
   int pidKillA = atoi(argv[2]);
   int pidKillB = getProcessWithParent(pidKillA);

   _tprintf( TEXT("Found two processes to kill: "), pidKillA, TEXT(" "), pidKillB);

   HANDLE hWatch = OpenProcess(PROCESS_ALL_ACCESS, FALSE, static_cast<DWORD>(pidWatch));
   HANDLE hKillA = OpenProcess(PROCESS_ALL_ACCESS, FALSE, static_cast<DWORD>(pidKillA));
   HANDLE hKillB = OpenProcess(PROCESS_ALL_ACCESS, FALSE, static_cast<DWORD>(pidKillB));

   while(processIsStillRunning(hWatch))
      Sleep(static_cast<DWORD>(2000));

   _tprintf( TEXT("\nThe watched process died!"));
   TerminateProcess(hKillA, 0);
   TerminateProcess(hKillB, 0);
   _tprintf( TEXT("\nAttempted to kill the two processes! "), pidKillA, TEXT(" "), pidKillB);
   return 0;
}

