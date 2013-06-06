#ifndef __LOG_H__
#define __LOG_H__

#include <sstream>
#include <string>
#include <fstream>
#include <iostream>
#include <stdio.h>

using namespace std;

inline string NowTime();

typedef enum 
{
   logError, 
   logWarn, 
   logInfo, 
   logDebug, 
   logDebug1, 
   logDebug2, 
   logDebug3, 
   logDebug4 
} LogLevel;


////////////////////////////////////////////////////////////////////////////////
class LogStream
{
public:
   virtual LogStream& operator<<(const char * str) = 0;
   virtual LogStream& operator<<(string const & str) = 0;
   virtual LogStream& operator<<(int i) = 0;
   virtual LogStream& operator<<(unsigned int i) = 0;
   virtual LogStream& operator<<(float f) = 0;
   virtual LogStream& operator<<(double d) = 0;
};

////////////////////////////////////////////////////////////////////////////////
class DualStream : public LogStream
{
public:
   void setLogFile(string logfile) 
   { 
      fname_ = logfile;
      fout_.open(fname_.c_str(), ios::app); 
      fout_ << "\n\nLog file opened at " << NowTime() << ": " << fname_.c_str() << endl;
   }

   LogStream& operator<<(const char * str)   { cout << str;  if(fout_.is_open()) fout_ << str; return *this; }
   LogStream& operator<<(string const & str) { cout << str.c_str(); if(fout_.is_open()) fout_ << str.c_str(); return *this; }
   LogStream& operator<<(int i)              { cout << i;    if(fout_.is_open()) fout_ << i; return *this; }
   LogStream& operator<<(unsigned int i)     { cout << i;    if(fout_.is_open()) fout_ << i; return *this; }
   LogStream& operator<<(float f)            { cout << f;    if(fout_.is_open()) fout_ << f; return *this; }
   LogStream& operator<<(double d)           { cout << d;    if(fout_.is_open()) fout_ << d; return *this; }

   void newline(void) { fout_ << endl;  cout << endl;}
   void close(void) { fout_.close(); }

   ofstream fout_;
   string   fname_;
};


////////////////////////////////////////////////////////////////////////////////
class NullStream : public LogStream
{
public:
   LogStream& operator<<(const char * str)   { return *this; }
   LogStream& operator<<(string const & str) { return *this; }
   LogStream& operator<<(int i)              { return *this; }
   LogStream& operator<<(unsigned int i)     { return *this; }
   LogStream& operator<<(float f)            { return *this; }
   LogStream& operator<<(double d)           { return *this; }
};


class Log
{
public:
    Log(void) : isInitialized_(false) {}
    static Log & GetInstance(const char * filename=NULL);
    virtual ~Log();

    LogStream& Get(LogLevel level = logInfo);
    static void SetLogFile(string logfile) { GetInstance(logfile.c_str()); }
    static void SetLogLevel(LogLevel level) { GetInstance().logLevel_ = (int)level; }
    static string ToString(LogLevel level);

    // Had to use "ERR" instead of "ERROR" because Windows didn't like ERROR
    static LogStream & ERR(void)    { return GetInstance().Get(logError);  }
    static LogStream & WARN(void)   { return GetInstance().Get(logWarn);   }
    static LogStream & INFO(void)   { return GetInstance().Get(logInfo);   }
    static LogStream & DEBUG(void)  { return GetInstance().Get(logDebug);  }
    static LogStream & DEBUG1(void) { return GetInstance().Get(logDebug1); }
    static LogStream & DEBUG2(void) { return GetInstance().Get(logDebug2); }
    static LogStream & DEBUG3(void) { return GetInstance().Get(logDebug3); }
    static LogStream & DEBUG4(void) { return GetInstance().Get(logDebug4); }

    static bool isOpen(void) {GetInstance().ds_.fout_.is_open();}
    static string filename(void) {return GetInstance().ds_.fname_;}

protected:
    DualStream ds_;
    NullStream ns_;
    int logLevel_;
    bool isInitialized_;
private:
    Log(const Log&);
    Log& operator =(const Log&);

};


Log& Log::GetInstance(const char * filename)
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


LogStream& Log::Get(LogLevel level)
{
   if((int)level > logLevel_ || !isInitialized_)
      return ns_;
   
   ds_.newline();
   ds_ << "- " << NowTime();
   ds_ << " " << ToString(level) << ": ";
   return ds_;
}

Log::~Log()
{
    ds_ << "Closing logfile.\n";
    ds_ << "...";
}


string Log::ToString(LogLevel level)
{
	static const char* const buffer[] = {"ERROR ", "WARN  ", "INFO  ", "DEBUG ", "DEBUG1", "DEBUG2", "DEBUG3", "DEBUG4"};
   return buffer[level];
}




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
//#define FILELOG_MAX_LEVEL logDEBUG4
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
