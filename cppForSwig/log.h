////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2014, Armory Technologies, Inc.                        //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE or http://www.gnu.org/licenses/agpl.html                      //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////
//
// This is a convenient little C++ logging class that was based on a Dr. Dobbs
// article on the subject.  The logger was rewritten to include a DualStream
// that pushes the log data to both std output AND file.  This could easily 
// be extended to use an arbitrary number of streams, with a different log lvl
// set on each one.   At the moment, it only supports stdout and one file 
// simultaneously at the same loglvl, though you can use LOGDISABLESTDOUT()
// to turn off the cout portion but still write to the log file.
//
// Usage:
//
// If you do not initialize the logger, the default behavior is to log nothing. 
// All LOGERR, LOGWARN, etc, calls wll execute without error, but they will be
// diverted to a NullStream object (which throws them away).  
//
// To use the logger, all you need to do is make one call to STARTLOGGING with
// the file name and log level, and then all subsequent calls to LOGERR, etc, 
// will work as expected.
//
//    STARTLOGGING("logfile.txt", LogLvlWarn); // ignore anything below LOGWARN
//
//    LOGERR   << "This is an error message, pretty much always logged";
//    LOGWARN  << "This is a warning";
//    LOGINFO  << "Given the LogLvlWarn above, this message will be ignored";
//    LOGDEBUG << "This one will also be ignored"
//
//    FLUSHLOG();          // force-flush all write buffers
//    LOGDISABLESTDOUT();  // Stop writing log msgs to cout, only write to file
//    LOGENABLESTDOUT();   // Okay nevermind, use cout again
//
// All logged lines begin with the msg type (ERROR, WARNING, etc), the current
// time down to one second, and the file:line.  Then the message is printed.
// Newlines are added automatically to the end of each line, so there is no 
// need to use "<< endl" at the end of any log messages (in fact, it will
// croak if you try to).  Here's what the messages look like:
//
//  -ERROR - 22:16:26: (code.cpp:129) I am recording an error!
//  -WARN  - 22:16:26: (code.cpp:130) This is just a warning, don't be alarmed!
//  -DEBUG4- 22:16:26: (code.cpp:131) A seriously low-level debug message.
//
// If you'd like to change the format of the messages, you can modify the 
// #define'd FILEANDLINE just below the #include's, and/or modify the 
// getLogStream() method in the LoggerObj class (just note, you cannot 
// move the __FILE__ and/or __LINE__ commands into the getLogStream() method
// because then it will always print "log.h:282" for the file and line).
//
////////////////////////////////////////////////////////////////////////////////
#ifndef __LOG_H__
#define __LOG_H__

#include <sstream>
#include <ctime>
#include <string>
#include <fstream>
#include <iostream>
#include <stdio.h>
#include "OS_TranslatePath.h"

#define FILEANDLINE "(" << __FILE__ << ":" << __LINE__ << ") "
#define LOGERR    (LoggerObj(LogLvlError ).getLogStream() << FILEANDLINE )
#define LOGWARN   (LoggerObj(LogLvlWarn  ).getLogStream() << FILEANDLINE )
#define LOGINFO   (LoggerObj(LogLvlInfo  ).getLogStream() << FILEANDLINE )
#define LOGDEBUG  (LoggerObj(LogLvlDebug ).getLogStream() << FILEANDLINE )
#define LOGDEBUG1 (LoggerObj(LogLvlDebug1).getLogStream() << FILEANDLINE )
#define LOGDEBUG2 (LoggerObj(LogLvlDebug2).getLogStream() << FILEANDLINE )
#define LOGDEBUG3 (LoggerObj(LogLvlDebug3).getLogStream() << FILEANDLINE )
#define LOGDEBUG4 (LoggerObj(LogLvlDebug4).getLogStream() << FILEANDLINE )
#define STARTLOGGING(LOGFILE, LOGLEVEL)         \
                  Log::SetLogFile(LOGFILE);     \
                  Log::SetLogLevel(LOGLEVEL);
#define LOGDISABLESTDOUT()  Log::SuppressStdout(true)
#define LOGENABLESTDOUT()   Log::SuppressStdout(false)
#define SETLOGLEVEL(LOGLVL) Log::SetLogLevel(LOGLVL)
#define FLUSHLOG()          Log::FlushStreams()


#define MAX_LOG_FILE_SIZE (500*1024)

using namespace std;

inline string NowTime();
inline unsigned long long int NowTimeInt();

typedef enum 
{
   LogLvlDisabled, 
   LogLvlError, 
   LogLvlWarn, 
   LogLvlInfo, 
   LogLvlDebug, 
   LogLvlDebug1, 
   LogLvlDebug2, 
   LogLvlDebug3, 
   LogLvlDebug4 
} LogLevel;


////////////////////////////////////////////////////////////////////////////////
class LogStream
{
public:
   virtual LogStream& operator<<(const char * str) = 0;
   virtual LogStream& operator<<(string const & str) = 0;
   virtual LogStream& operator<<(int i) = 0;
   virtual LogStream& operator<<(unsigned int i) = 0;
   virtual LogStream& operator<<(unsigned long long int i) = 0;
   virtual LogStream& operator<<(float f) = 0;
   virtual LogStream& operator<<(double d) = 0;
#if !defined(_MSC_VER) && !defined(__MINGW32__) && defined(__LP64__)
   virtual LogStream& operator<<(size_t i) = 0;
#endif
};

////////////////////////////////////////////////////////////////////////////////
class DualStream : public LogStream
{
public:
   DualStream(void) : noStdout_(false) {}

   void enableStdOut(bool newbool) { noStdout_ = !newbool; }

   void setLogFile(string logfile, unsigned long long maxSz=MAX_LOG_FILE_SIZE)
   { 
      fname_ = logfile;
      truncateFile(fname_, maxSz);
      fout_.open(OS_TranslatePath(fname_.c_str()), ios::app); 
      fout_ << "\n\nLog file opened at " << NowTimeInt() << ": " << fname_.c_str() << endl;
   }

   
   void truncateFile(string logfile, unsigned long long int maxSizeInBytes)
   {
      ifstream is(OS_TranslatePath(logfile.c_str()), ios::in|ios::binary);

      // If file does not exist, nothing to do
      if(!is.is_open())
         return;
   
      // Check the filesize
      is.seekg(0, ios::end);
      unsigned long long int fsize = (size_t)is.tellg();
      is.close();

      if(fsize < maxSizeInBytes)
      {
         // If it's already smaller than max, we're done
         return;
      }
      else
      {
         // Otherwise, seek to <maxSize> before end of log file
         ifstream is(OS_TranslatePath(logfile.c_str()), ios::in|ios::binary);
         is.seekg(fsize - maxSizeInBytes);

         // Allocate buffer to hold the rest of the file (about maxSizeInBytes)
         unsigned long long int bytesToCopy = fsize - is.tellg();
         char* lastBytes = new char[(unsigned int)bytesToCopy];
         is.read(lastBytes, bytesToCopy);
         is.close();
         
         // Create temporary file and dump the bytes there
         string tempfile = logfile + string("temp");
         ofstream os(OS_TranslatePath(tempfile.c_str()), ios::out|ios::binary);
         os.write(lastBytes, bytesToCopy);
         os.close();
         delete[] lastBytes;

         // Remove the original and rename the temp file to original
			#ifndef _MSC_VER
				remove(logfile.c_str());
				rename(tempfile.c_str(), logfile.c_str());
			#else
				_wunlink(OS_TranslatePath(logfile).c_str());
				_wrename(OS_TranslatePath(tempfile).c_str(), OS_TranslatePath(logfile).c_str());
			#endif
      }
   }

   LogStream& operator<<(const char * str)   { if(!noStdout_) cout << str;  if(fout_.is_open()) fout_ << str; return *this; }
   LogStream& operator<<(string const & str) { if(!noStdout_) cout << str.c_str(); if(fout_.is_open()) fout_ << str.c_str(); return *this; }
   LogStream& operator<<(int i)              { if(!noStdout_) cout << i;    if(fout_.is_open()) fout_ << i; return *this; }
   LogStream& operator<<(unsigned int i)     { if(!noStdout_) cout << i;    if(fout_.is_open()) fout_ << i; return *this; }
   LogStream& operator<<(unsigned long long int i) { if(!noStdout_) cout << i;    if(fout_.is_open()) fout_ << i; return *this; }
   LogStream& operator<<(float f)            { if(!noStdout_) cout << f;    if(fout_.is_open()) fout_ << f; return *this; }
   LogStream& operator<<(double d)           { if(!noStdout_) cout << d;    if(fout_.is_open()) fout_ << d; return *this; }
#if !defined(_MSC_VER) && !defined(__MINGW32__) && defined(__LP64__)
   LogStream& operator<<(size_t i)           { if(!noStdout_) cout << i;    if(fout_.is_open()) fout_ << i; return *this; }
#endif

   void FlushStreams(void) {cout.flush(); fout_.flush();}

   void newline(void) { *this << "\n"; }
   void close(void) { fout_.close(); }

   ofstream fout_;
   string   fname_;
   bool     noStdout_;
};


////////////////////////////////////////////////////////////////////////////////
class NullStream : public LogStream
{
public:
   LogStream& operator<<(const char * str)   { return *this; }
   LogStream& operator<<(string const & str) { return *this; }
   LogStream& operator<<(int i)              { return *this; }
   LogStream& operator<<(unsigned int i)     { return *this; }
   LogStream& operator<<(unsigned long long int i)     { return *this; }
   LogStream& operator<<(float f)            { return *this; }
   LogStream& operator<<(double d)           { return *this; }
#if !defined(_MSC_VER) && !defined(__MINGW32__) && defined(__LP64__)
   LogStream& operator<<(size_t i)           { return *this; }
#endif

   void FlushStreams(void) {}
};


class Log
{
public:
   Log(void) : isInitialized_(false), disableStdout_(false) {}

   static Log & GetInstance(const char * filename=NULL)
   {
      static Log* theOneLog=NULL;
      if(theOneLog==NULL || filename!=NULL)
      {
         // Close and delete any existing Log object
         if(theOneLog != NULL)
         {
            theOneLog->ds_.close();
            delete theOneLog;
         }
   
         // Create a Log object
         theOneLog = new Log;
   
         // Open the filestream if it's open
         if(filename != NULL)
         {
            theOneLog->ds_.setLogFile(string(filename));
            theOneLog->isInitialized_ = true;
         }
      }
      return *theOneLog;
   }

   ~Log(void)
   {
      CloseLogFile();
   }

   LogStream& Get(LogLevel level = LogLvlInfo)
   {
      if((int)level > logLevel_ || !isInitialized_)
         return ns_;
      else 
         return ds_;
   }

   static void SetLogFile(string logfile) { GetInstance(logfile.c_str()); }
   static void CloseLogFile(void)
   { 
      GetInstance().ds_.FlushStreams();
      GetInstance().ds_ << "Closing logfile.\n";
      GetInstance().ds_.close();
      // This doesn't actually seem to stop the StdOut logging... not sure why yet
      GetInstance().isInitialized_ = false;
      GetInstance().logLevel_ = LogLvlDisabled;
   }

   static void SetLogLevel(LogLevel level) { GetInstance().logLevel_ = (int)level; }
   static void SuppressStdout(bool b=true) { GetInstance().ds_.enableStdOut(!b);}

   static string ToString(LogLevel level)
   {
	   static const char* const buffer[] = {"DISABLED", "ERROR ", "WARN  ", "INFO  ", "DEBUG ", "DEBUG1", "DEBUG2", "DEBUG3", "DEBUG4"};
      return buffer[level];
   }

    static bool isOpen(void) {return GetInstance().ds_.fout_.is_open();}
    static string filename(void) {return GetInstance().ds_.fname_;}
    static void FlushStreams(void) {GetInstance().ds_.FlushStreams();}

protected:
    DualStream ds_;
    NullStream ns_;
    int logLevel_;
    bool isInitialized_;
    bool disableStdout_;
private:
    Log(const Log&);
    Log& operator =(const Log&);

};



// I missed the opportunity with the above class, to design it as a constantly
// constructing/destructing object that adds a newline on every destruct.  So 
// instead I create this little wrapper that does it for me.
class LoggerObj
{
public:
   LoggerObj(LogLevel lvl) : logLevel_(lvl) {}

   LogStream & getLogStream(void) 
   { 
      LogStream & lg = Log::GetInstance().Get(logLevel_);
      lg << "-" << Log::ToString(logLevel_);
      lg << "- " << NowTimeInt() << ": ";
      return lg;
   }

   ~LoggerObj(void) 
   { 
      Log::GetInstance().Get(logLevel_) << "\n";
      Log::GetInstance().FlushStreams();
   }

private:
   LogLevel logLevel_;
};





//#if defined(WIN32) || defined(_WIN32) || defined(__WIN32__)
//#   if defined (BUILDING_FILELOG_DLL)
//#       define FILELOG_DECLSPEC   __declspec (dllexport)
//#   elif defined (USING_FILELOG_DLL)
//#       define FILELOG_DECLSPEC   __declspec (dllimport)
//#   else
//#       define FILELOG_DECLSPEC
//#   endif // BUILDING_DBSIMPLE_DLL
//#else
//#   define FILELOG_DECLSPEC
//#endif // _WIN32


//#ifndef FILELOG_MAX_LEVEL
//#define FILELOG_MAX_LEVEL LogLvlDEBUG4
//#endif

#if defined(WIN32) || defined(_WIN32) || defined(__WIN32__)

#include <windows.h>

inline string NowTime()
{
    const int MAX_LEN = 200;
    char buffer[MAX_LEN];
    if (GetTimeFormatA(LOCALE_USER_DEFAULT, 0, 0, 
            "HH':'mm':'ss", buffer, MAX_LEN) == 0)
        return "Error in NowTime()";

    char result[100] = {0};
    static DWORD first = GetTickCount();
    sprintf(result, "%s.%03ld", buffer, (long)(GetTickCount() - first) % 1000); 
    return result;
}

inline unsigned long long int NowTimeInt(void)
{
   time_t t;
   time(&t);
   return (unsigned long long int)t;
}

#else

#include <sys/time.h>

inline string NowTime()
{
    char buffer[11];
    time_t t;
    time(&t);
    tm r = {0};
    strftime(buffer, sizeof(buffer), "%X", localtime_r(&t, &r));
    struct timeval tv;
    gettimeofday(&tv, 0);
    char result[100] = {0};
    sprintf(result, "%s", buffer);
    return result;
}

inline unsigned long long int NowTimeInt(void)
{
   time_t t;
   time(&t);
   return (unsigned long long int)t;
}

#endif //WIN32

#endif //__LOG_H__
