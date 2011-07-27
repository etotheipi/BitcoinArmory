/*************************************************************

    This program is a C++ implementation of the Secure Hash Algorithm (SHA)
    that handles the variations from the original 160 bit to 224, 256, 384
    and 512 bit.  The program is intended to be platform independant and
    has been tested on little-endian (Intel) and big-endian (Sun) machines.

    This program is based on a C version written by Aaron D. Gifford
    (as of 11/22/2004 his code could be found at http://www.adg.us/computers/sha.html).
    Attempts to contact him were unsuccessful.  I greatly condensed his version
    and shared as much code and data as I could think of.  I also inlined
    a lot of code that were macros in his version.  My version detects
    endian-ness automatically and adjusts itself accordingly.  This program
    has been tested with Visual C++ versions 6/7 and Dev-C++ on Windows, 
    g++ on Linux and CC on Solaris (g++ on Solaris gave a bus error).

    While I did make half-hearted attempts to optimize as I went along
    (testing on Wintel), any serious attempt at fast implementation is
    probably going to need to make use of in-lined assembly which is not
    very portable.

    The goal of this implementation is ease of use.  As much as possible
    I tried to hide implementation details while making it trivial to change
    the size of the hash and get the results.  The string and charactar
    array value of the hash is supplied as human-readable hex; the raw value
    can also be obtained.

    If you use this implementation somewhere I would like to be credited
    with my work (a link to my page below is fine).  I add no license
    restriction beyond any that is made by the original author.  This
    code comes with no warrenty expressed or implied, use at your own
    risk!

    Keith Oxenrider
    koxenrider[at]sol[dash]biotech[dot]com
    The latest version of this code should be available via the page
    sol-biotech.com/code.

*************************************************************/




#ifndef __SHA2C_H__
#define __SHA2C_H__

#define SHA2_USE_INTTYPES_H
#define SHA2_USE_MEMSET_MEMCPY
#define SHA2_UNROLL_TRANSFORM

#include <stdio.h>
#include <string>
#include <stdlib.h>
#include <cstring>
#include <stdexcept>

// NOTE: You may need to define things by hand for your system: 
typedef unsigned char  sha_byte;           // Exactly 1 byte 
typedef unsigned int sha_word32;           // Exactly 4 bytes 
#ifdef WIN32
    #include <windows.h>
    typedef ULONG64 sha_word64;            // 8-bytes (64-bits) 
#else
    typedef unsigned long long sha_word64; // 8-bytes (64-bits) 
#endif

// Digest lengths for SHA-1/224/256/384/512 
const sha_word32 SHA1_DIGESTC_LENGTH = 20;
const sha_word32 SHA1_DIGESTC_STRING_LENGTH   = (SHA1_DIGESTC_LENGTH   * 2 + 1);
const sha_word32 SHA224_DIGESTC_LENGTH = 28;
const sha_word32 SHA224_DIGESTC_STRING_LENGTH = (SHA224_DIGESTC_LENGTH * 2 + 1);
const sha_word32 SHA256_DIGESTC_LENGTH = 32;
const sha_word32 SHA256_DIGESTC_STRING_LENGTH = (SHA256_DIGESTC_LENGTH * 2 + 1);
const sha_word32 SHA384_DIGESTC_LENGTH = 48;
const sha_word32 SHA384_DIGESTC_STRING_LENGTH = (SHA384_DIGESTC_LENGTH * 2 + 1);
const sha_word32 SHA512_DIGESTC_LENGTH = 64;
const sha_word32 SHA512_DIGESTC_STRING_LENGTH = (SHA512_DIGESTC_LENGTH * 2 + 1);

class sha2{
public:
    enum SHA_TYPE{
        enuSHA_NONE,
        enuSHA1,
        enuSHA160 = enuSHA1,
        enuSHA224,
        enuSHA256,
        enuSHA384,
        enuSHA512,
        enuSHA_LAST //for easier looping during testing
    };

    sha2(){
        m_Type = enuSHA_NONE;
        m_boolIsBigEndian = true;
        m_boolEnded = false;

        //run-time check for endian-ness
        unsigned int test = 1;
        unsigned char *ptr = (unsigned char *)&test;
        if (ptr[0]) m_boolIsBigEndian = false;

        //these checks here because I wasn't able to figure out how to 
        //check at compile time
        if (sizeof(sha_byte) != 1) throw std::runtime_error("sha_byte != 1!");
        if (sizeof(sha_word32) != 4) throw std::runtime_error("sha_word32 != 4!");
        if (sizeof(sha_word64) != 8) throw std::runtime_error("sha_word64 != 8!");

        memset(m_chrRawHash, 0, SHA512_DIGESTC_LENGTH);
        memset(m_chrHexHash, 0, SHA512_DIGESTC_STRING_LENGTH);
        memset(m_digest, 0, SHA512_DIGESTC_LENGTH);
    };

    SHA_TYPE GetEnumType(){return m_Type;};
    bool IsBigEndian(){return m_boolIsBigEndian;};
    const char * GetTypeString(){
        switch (m_Type){
            case sha2::enuSHA1   : return "SHA160";
            case sha2::enuSHA224 : return "SHA224";
            case sha2::enuSHA256 : return "SHA256";
            case sha2::enuSHA384 : return "SHA384";
            case sha2::enuSHA512 : return "SHA512";
            default : return "Unknown!";
        }
    };

//call these three in order if you want to load chunk-by-chunk...
    void Init(SHA_TYPE type);
    //these two throw a std::runtime_error if the type is not defined
    void Update(const sha_byte *data, size_t len);//call as many times as needed
    void End();

//or call this one if you only have one chunk of data
    const std::string &GetHash(SHA_TYPE type, const sha_byte* data, size_t len);

//call one of these routines to access the hash
    //these throw a std::runtime_error if End has not been called
    const char *HexHash();//NULL terminated
    const std::string &StringHash();
    const char *RawHash(int &length);//NO NULL termination! size stored in 'length'


private:
    SHA_TYPE m_Type;
    std::string m_strHash;
    bool m_boolEnded, m_boolIsBigEndian;
    char m_chrRawHash[SHA512_DIGESTC_LENGTH], m_chrHexHash[SHA512_DIGESTC_STRING_LENGTH];
    sha_byte m_digest[SHA512_DIGESTC_LENGTH];

//these are common buffers for maintaining the hash
    struct SHA_CTX{
        sha_byte   state[sizeof(sha_word64) * 8];//maximum size
        sha_word64 bitcount[2];//sha1, 224 and 256 only use the first entry
        sha_byte   buffer[128];
    }ctx;

    
//** INTERNAL FUNCTION PROTOTYPES ************************************
    void SHA256_Internal_Last(bool isSha1 = false);
    void SHA512_Internal_Last();

    void SHA1_Internal_Transform(const sha_word32 *data);
    void SHA256_Internal_Transform(const sha_word32* data);
    void SHA512_Internal_Transform(const sha_word64*);

    void SHA32bit_Update(const sha_byte *data, size_t len, bool isSha1=false);
    void SHA64bit_Update(const sha_byte *data, size_t len);

//macro replacements
    inline void MEMSET_BZERO(void *p, size_t l){memset(p, 0, l);};
    inline void MEMCPY_BCOPY(void *d,const void *s, size_t l) {memcpy(d, s, l);};

    //For incrementally adding the unsigned 64-bit integer n to the
    //unsigned 128-bit integer (represented using a two-element array of
    //64-bit words):
    inline void ADDINC128(sha_word64 *w, sha_word32 n)  {
        w[0] += (sha_word64)(n);
        if (w[0] < (n)) w[1]++;
    }

    // Shift-right (used in SHA-256, SHA-384, and SHA-512): 
    inline sha_word32 SHR(sha_word32 b,sha_word32 x){return (x >> b);};
    inline sha_word64 SHR(sha_word64 b,sha_word64 x){return (x >> b);};
    // 32-bit Rotate-right (used in SHA-256): 
    inline sha_word32 ROTR32(sha_word32 b,sha_word32 x){return ((x >> b) | (x << (32 - b)));};
    // 64-bit Rotate-right (used in SHA-384 and SHA-512): 
    inline sha_word64 ROTR64(sha_word64 b,sha_word64 x){return ((x >> b) | (x << (64 - b)));};
    // 32-bit Rotate-left (used in SHA-1): 
    inline sha_word32 ROTL32(sha_word32 b,sha_word32 x){return ((x << b) | (x >> (32 - b)));};

    // Two logical functions used in SHA-1, SHA-254, SHA-256, SHA-384, and SHA-512: 
    inline sha_word32 Ch(sha_word32 x,sha_word32 y,sha_word32 z){return ((x & y) ^ ((~x) & z));};
    inline sha_word64 Ch(sha_word64 x,sha_word64 y,sha_word64 z){return ((x & y) ^ ((~x) & z));};
    inline sha_word32 Maj(sha_word32 x,sha_word32 y,sha_word32 z){return ((x & y) ^ (x & z) ^ (y & z));};
    inline sha_word64 Maj(sha_word64 x,sha_word64 y,sha_word64 z){return ((x & y) ^ (x & z) ^ (y & z));};

    // Function used in SHA-1: 
    inline sha_word32 Parity(sha_word32 x,sha_word32 y,sha_word32 z){return (x ^ y ^ z);};

// Four logical functions used in SHA-256: 
    inline sha_word32 Sigma0_256(sha_word32 x){return (ROTR32(2, x) ^ ROTR32(13, x) ^ ROTR32(22, x));};
    inline sha_word32 Sigma1_256(sha_word32 x){return (ROTR32(6, x) ^ ROTR32(11, x) ^ ROTR32(25, x));};
    inline sha_word32 sigma0_256(sha_word32 x){return (ROTR32(7, x) ^ ROTR32(18, x) ^ SHR(   3 , x));};
    inline sha_word32 sigma1_256(sha_word32 x){return (ROTR32(17,x) ^ ROTR32(19, x) ^ SHR(   10, x));};

// Four of six logical functions used in SHA-384 and SHA-512: 
    inline sha_word64 Sigma0_512(sha_word64 x){return (ROTR64(28, x) ^ ROTR64(34, x) ^ ROTR64(39, x));};
    inline sha_word64 Sigma1_512(sha_word64 x){return (ROTR64(14, x) ^ ROTR64(18, x) ^ ROTR64(41, x));};
    inline sha_word64 sigma0_512(sha_word64 x){return (ROTR64( 1, x) ^ ROTR64( 8, x) ^ SHR(    7, x));};
    inline sha_word64 sigma1_512(sha_word64 x){return (ROTR64(19, x) ^ ROTR64(61, x) ^ SHR(    6, x));};

    inline void REVERSE32(sha_word32 w, sha_word32 &x)  {
        w = (w >> 16) | (w << 16);
        x = ((w & 0xff00ff00UL) >> 8) | ((w & 0x00ff00ffUL) << 8);
    }
    #ifdef _VC6
        inline void REVERSE64(sha_word64 w, sha_word64 &x)  {
            w = (w >> 32) | (w << 32);
            w =   ((w & 0xff00ff00ff00ff00ui64) >> 8) |
                  ((w & 0x00ff00ff00ff00ffui64) << 8);
            (x) = ((w & 0xffff0000ffff0000ui64) >> 16) |
                  ((w & 0x0000ffff0000ffffui64) << 16);
        }
    #else
        inline void REVERSE64(sha_word64 w, sha_word64 &x)  {
            w = (w >> 32) | (w << 32);
            w =   ((w & 0xff00ff00ff00ff00ULL) >> 8) |
                  ((w & 0x00ff00ff00ff00ffULL) << 8);
            (x) = ((w & 0xffff0000ffff0000ULL) >> 16) |
                  ((w & 0x0000ffff0000ffffULL) << 16);
        }
    #endif

};//end class sha2
#endif // __SHA2C_H__ 
