#ifndef __LOG_H__
#define __LOG_H__

#include <sstream>
#include <string>
#include <fstream>
#include <iostream>
#include <stdio.h>

#define LOGERR    (LogNewLine(LogError).getLogStream()   << "(" << __FILE__ << ":" << __LINE__ << ") ")
#define LOGWARN   (LogNewLine(LogWarn).getLogStream()    << "(" << __FILE__ << ":" << __LINE__ << ") ")
#define LOGINFO   (LogNewLine(LogInfo).getLogStream()    << "(" << __FILE__ << ":" << __LINE__ << ") ")
#define LOGDEBUG  (LogNewLine(LogDebug).getLogStream()   << "(" << __FILE__ << ":" << __LINE__ << ") ")
#define LOGDEBUG1 (LogNewLine(LogDebug1).getLogStream()  << "(" << __FILE__ << ":" << __LINE__ << ") ")
#define LOGDEBUG2 (LogNewLine(LogDebug2).getLogStream()  << "(" << __FILE__ << ":" << __LINE__ << ") ")
#define LOGDEBUG3 (LogNewLine(LogDebug3).getLogStream()  << "(" << __FILE__ << ":" << __LINE__ << ") ")
#define LOGDEBUG4 (LogNewLine(LogDebug4).getLogStream()  << "(" << __FILE__ << ":" << __LINE__ << ") ")

using namespace std;

inline string NowTime();

typedef enum 
{
   LogDisabled, 
   LogError, 
   LogWarn, 
   LogInfo, 
   LogDebug, 
   LogDebug1, 
   LogDebug2, 
   LogDebug3, 
   LogDebug4 
} LogLevel;


////////////////////////////////////////////////////////////////////////////////
class LogStream
{
public:
   virtual LogStream& operator<<(const char * str) = 0;
   virtual LogStream& operator<<(string const & str) = 0;
   virtual LogStream& operator<<(int i) = 0;
   virtual LogStream& operator<<(size_t i) = 0;
   virtual LogStream& operator<<(unsigned int i) = 0;
   virtual LogStream& operator<<(float f) = 0;
   virtual LogStream& operator<<(double d) = 0;
};

////////////////////////////////////////////////////////////////////////////////
class DualStream : public LogStream
{
public:
   DualStream(void) : noStdout_(false) {}

   void enableStdOut(bool newbool) { noStdout_ = !newbool; }

   void setLogFile(string logfile) 
   { 
      fname_ = logfile;
      fout_.open(fname_.c_str(), ios::app); 
      fout_ << "\n\nLog file opened at " << NowTime() << ": " << fname_.c_str() << endl;
   }

   LogStream& operator<<(const char * str)   { if(!noStdout_) cout << str;  if(fout_.is_open()) fout_ << str; return *this; }
   LogStream& operator<<(string const & str) { if(!noStdout_) cout << str.c_str(); if(fout_.is_open()) fout_ << str.c_str(); return *this; }
   LogStream& operator<<(size_t i)           { if(!noStdout_) cout << i;    if(fout_.is_open()) fout_ << i; return *this; }
   LogStream& operator<<(int i)              { if(!noStdout_) cout << i;    if(fout_.is_open()) fout_ << i; return *this; }
   LogStream& operator<<(unsigned int i)     { if(!noStdout_) cout << i;    if(fout_.is_open()) fout_ << i; return *this; }
   LogStream& operator<<(float f)            { if(!noStdout_) cout << f;    if(fout_.is_open()) fout_ << f; return *this; }
   LogStream& operator<<(double d)           { if(!noStdout_) cout << d;    if(fout_.is_open()) fout_ << d; return *this; }

   void flushStreams(void) {cout.flush(); fout_.flush();}

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
   LogStream& operator<<(size_t i)           { return *this; }
   LogStream& operator<<(int i)              { return *this; }
   LogStream& operator<<(unsigned int i)     { return *this; }
   LogStream& operator<<(float f)            { return *this; }
   LogStream& operator<<(double d)           { return *this; }

   void flushStreams(void) {}
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

   LogStream& Get(LogLevel level = LogInfo)
   {
      if((int)level > logLevel_ || !isInitialized_)
         return ns_;
      else 
         return ds_;
   }

   static void SetLogFile(string logfile) { GetInstance(logfile.c_str()); }
   static void CloseLogFile(void)
   { 
      GetInstance().ds_.flushStreams();
      GetInstance().ds_ << "Closing logfile.\n";
      GetInstance().ds_.close();
   }

   static void SetLogLevel(LogLevel level) { GetInstance().logLevel_ = (int)level; }
   static void SuppressStdout(bool b=true) { GetInstance().ds_.enableStdOut(!b);}

   static string ToString(LogLevel level)
   {
	   static const char* const buffer[] = {"DISABLED", "ERROR ", "WARN  ", "INFO  ", "DEBUG ", "DEBUG1", "DEBUG2", "DEBUG3", "DEBUG4"};
      return buffer[level];
   }

    static bool isOpen(void) {GetInstance().ds_.fout_.is_open();}
    static string filename(void) {return GetInstance().ds_.fname_;}
    static void FlushStreams(void) {GetInstance().ds_.flushStreams();}

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
class LogNewLine
{
public:
   LogNewLine(LogLevel lvl) : logLevel_(lvl) {}

   LogStream & getLogStream(void) 
   { 
      LogStream & lg = Log::GetInstance().Get(logLevel_);
      lg << "-" << Log::ToString(logLevel_);
      lg << "- " << NowTime() << ": ";
      return lg;
   }

   ~LogNewLine(void) { Log::GetInstance().Get(logLevel_) << "\n"; }

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
//#define FILELOG_MAX_LEVEL LogDEBUG4
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

#endif //WIN32

#endif //__LOG_H__
