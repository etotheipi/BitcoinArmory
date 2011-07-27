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

#include "sha2.h"

#include <iostream>

using namespace std;

// Hash constant words K for SHA-1:
const sha_word32 K1_0_TO_19  = 0x5a827999UL;
const sha_word32 K1_20_TO_39 = 0x6ed9eba1UL;
const sha_word32 K1_40_TO_59 = 0x8f1bbcdcUL;
const sha_word32 K1_60_TO_79 = 0xca62c1d6UL;



//** SHA2 INITIAL HASH VALUES AND CONSTANTS **************************

// Initial hash value H for SHA-1: 
const static sha_word32 sha1_initial_hash_value[5] = {
    0x67452301UL, 0xefcdab89UL, 0x98badcfeUL, 0x10325476UL,
    0xc3d2e1f0UL
};

// Hash constant words K for SHA-224 and SHA-256: 
const static sha_word32 K256[64] = {
    0x428a2f98UL, 0x71374491UL, 0xb5c0fbcfUL, 0xe9b5dba5UL,
    0x3956c25bUL, 0x59f111f1UL, 0x923f82a4UL, 0xab1c5ed5UL,
    0xd807aa98UL, 0x12835b01UL, 0x243185beUL, 0x550c7dc3UL,
    0x72be5d74UL, 0x80deb1feUL, 0x9bdc06a7UL, 0xc19bf174UL,
    0xe49b69c1UL, 0xefbe4786UL, 0x0fc19dc6UL, 0x240ca1ccUL,
    0x2de92c6fUL, 0x4a7484aaUL, 0x5cb0a9dcUL, 0x76f988daUL,
    0x983e5152UL, 0xa831c66dUL, 0xb00327c8UL, 0xbf597fc7UL,
    0xc6e00bf3UL, 0xd5a79147UL, 0x06ca6351UL, 0x14292967UL,
    0x27b70a85UL, 0x2e1b2138UL, 0x4d2c6dfcUL, 0x53380d13UL,
    0x650a7354UL, 0x766a0abbUL, 0x81c2c92eUL, 0x92722c85UL,
    0xa2bfe8a1UL, 0xa81a664bUL, 0xc24b8b70UL, 0xc76c51a3UL,
    0xd192e819UL, 0xd6990624UL, 0xf40e3585UL, 0x106aa070UL,
    0x19a4c116UL, 0x1e376c08UL, 0x2748774cUL, 0x34b0bcb5UL,
    0x391c0cb3UL, 0x4ed8aa4aUL, 0x5b9cca4fUL, 0x682e6ff3UL,
    0x748f82eeUL, 0x78a5636fUL, 0x84c87814UL, 0x8cc70208UL,
    0x90befffaUL, 0xa4506cebUL, 0xbef9a3f7UL, 0xc67178f2UL
};

// Initial hash value H for SHA-224: 
const static sha_word32 sha224_initial_hash_value[8] = {
    0xc1059ed8UL, 0x367cd507UL, 0x3070dd17UL, 0xf70e5939UL,
    0xffc00b31UL, 0x68581511UL, 0x64f98fa7UL, 0xbefa4fa4UL
};

// Initial hash value H for SHA-256: 
const static sha_word32 sha256_initial_hash_value[8] = {
    0x6a09e667UL, 0xbb67ae85UL, 0x3c6ef372UL, 0xa54ff53aUL,
    0x510e527fUL, 0x9b05688cUL, 0x1f83d9abUL, 0x5be0cd19UL
};

// ui64 Hash constant words K for SHA-384 and SHA-512: 
#ifdef _VC6
    const static sha_word64 K512[80] = {
        0x428a2f98d728ae22ui64, 0x7137449123ef65cdui64,
        0xb5c0fbcfec4d3b2fui64, 0xe9b5dba58189dbbcui64,
        0x3956c25bf348b538ui64, 0x59f111f1b605d019ui64,
        0x923f82a4af194f9bui64, 0xab1c5ed5da6d8118ui64,
        0xd807aa98a3030242ui64, 0x12835b0145706fbeui64,
        0x243185be4ee4b28cui64, 0x550c7dc3d5ffb4e2ui64,
        0x72be5d74f27b896fui64, 0x80deb1fe3b1696b1ui64,
        0x9bdc06a725c71235ui64, 0xc19bf174cf692694ui64,
        0xe49b69c19ef14ad2ui64, 0xefbe4786384f25e3ui64,
        0x0fc19dc68b8cd5b5ui64, 0x240ca1cc77ac9c65ui64,
        0x2de92c6f592b0275ui64, 0x4a7484aa6ea6e483ui64,
        0x5cb0a9dcbd41fbd4ui64, 0x76f988da831153b5ui64,
        0x983e5152ee66dfabui64, 0xa831c66d2db43210ui64,
        0xb00327c898fb213fui64, 0xbf597fc7beef0ee4ui64,
        0xc6e00bf33da88fc2ui64, 0xd5a79147930aa725ui64,
        0x06ca6351e003826fui64, 0x142929670a0e6e70ui64,
        0x27b70a8546d22ffcui64, 0x2e1b21385c26c926ui64,
        0x4d2c6dfc5ac42aedui64, 0x53380d139d95b3dfui64,
        0x650a73548baf63deui64, 0x766a0abb3c77b2a8ui64,
        0x81c2c92e47edaee6ui64, 0x92722c851482353bui64,
        0xa2bfe8a14cf10364ui64, 0xa81a664bbc423001ui64,
        0xc24b8b70d0f89791ui64, 0xc76c51a30654be30ui64,
        0xd192e819d6ef5218ui64, 0xd69906245565a910ui64,
        0xf40e35855771202aui64, 0x106aa07032bbd1b8ui64,
        0x19a4c116b8d2d0c8ui64, 0x1e376c085141ab53ui64,
        0x2748774cdf8eeb99ui64, 0x34b0bcb5e19b48a8ui64,
        0x391c0cb3c5c95a63ui64, 0x4ed8aa4ae3418acbui64,
        0x5b9cca4f7763e373ui64, 0x682e6ff3d6b2b8a3ui64,
        0x748f82ee5defb2fcui64, 0x78a5636f43172f60ui64,
        0x84c87814a1f0ab72ui64, 0x8cc702081a6439ecui64,
        0x90befffa23631e28ui64, 0xa4506cebde82bde9ui64,
        0xbef9a3f7b2c67915ui64, 0xc67178f2e372532bui64,
        0xca273eceea26619cui64, 0xd186b8c721c0c207ui64,
        0xeada7dd6cde0eb1eui64, 0xf57d4f7fee6ed178ui64,
        0x06f067aa72176fbaui64, 0x0a637dc5a2c898a6ui64,
        0x113f9804bef90daeui64, 0x1b710b35131c471bui64,
        0x28db77f523047d84ui64, 0x32caab7b40c72493ui64,
        0x3c9ebe0a15c9bebcui64, 0x431d67c49c100d4cui64,
        0x4cc5d4becb3e42b6ui64, 0x597f299cfc657e2aui64,
        0x5fcb6fab3ad6faecui64, 0x6c44198c4a475817ui64
    };
    // Initial hash value H for SHA-384 
    const static sha_word64 sha384_initial_hash_value[8] = {
        0xcbbb9d5dc1059ed8ui64, 0x629a292a367cd507ui64,
        0x9159015a3070dd17ui64, 0x152fecd8f70e5939ui64,
        0x67332667ffc00b31ui64, 0x8eb44a8768581511ui64,
        0xdb0c2e0d64f98fa7ui64, 0x47b5481dbefa4fa4ui64
    };

    // Initial hash value H for SHA-512 
    const static sha_word64 sha512_initial_hash_value[8] = {
        0x6a09e667f3bcc908ui64, 0xbb67ae8584caa73bui64,
        0x3c6ef372fe94f82bui64, 0xa54ff53a5f1d36f1ui64,
        0x510e527fade682d1ui64, 0x9b05688c2b3e6c1fui64,
        0x1f83d9abfb41bd6bui64, 0x5be0cd19137e2179ui64
    };
#else
    const static sha_word64 K512[80] = {
        0x428a2f98d728ae22ULL, 0x7137449123ef65cdULL,
        0xb5c0fbcfec4d3b2fULL, 0xe9b5dba58189dbbcULL,
        0x3956c25bf348b538ULL, 0x59f111f1b605d019ULL,
        0x923f82a4af194f9bULL, 0xab1c5ed5da6d8118ULL,
        0xd807aa98a3030242ULL, 0x12835b0145706fbeULL,
        0x243185be4ee4b28cULL, 0x550c7dc3d5ffb4e2ULL,
        0x72be5d74f27b896fULL, 0x80deb1fe3b1696b1ULL,
        0x9bdc06a725c71235ULL, 0xc19bf174cf692694ULL,
        0xe49b69c19ef14ad2ULL, 0xefbe4786384f25e3ULL,
        0x0fc19dc68b8cd5b5ULL, 0x240ca1cc77ac9c65ULL,
        0x2de92c6f592b0275ULL, 0x4a7484aa6ea6e483ULL,
        0x5cb0a9dcbd41fbd4ULL, 0x76f988da831153b5ULL,
        0x983e5152ee66dfabULL, 0xa831c66d2db43210ULL,
        0xb00327c898fb213fULL, 0xbf597fc7beef0ee4ULL,
        0xc6e00bf33da88fc2ULL, 0xd5a79147930aa725ULL,
        0x06ca6351e003826fULL, 0x142929670a0e6e70ULL,
        0x27b70a8546d22ffcULL, 0x2e1b21385c26c926ULL,
        0x4d2c6dfc5ac42aedULL, 0x53380d139d95b3dfULL,
        0x650a73548baf63deULL, 0x766a0abb3c77b2a8ULL,
        0x81c2c92e47edaee6ULL, 0x92722c851482353bULL,
        0xa2bfe8a14cf10364ULL, 0xa81a664bbc423001ULL,
        0xc24b8b70d0f89791ULL, 0xc76c51a30654be30ULL,
        0xd192e819d6ef5218ULL, 0xd69906245565a910ULL,
        0xf40e35855771202aULL, 0x106aa07032bbd1b8ULL,
        0x19a4c116b8d2d0c8ULL, 0x1e376c085141ab53ULL,
        0x2748774cdf8eeb99ULL, 0x34b0bcb5e19b48a8ULL,
        0x391c0cb3c5c95a63ULL, 0x4ed8aa4ae3418acbULL,
        0x5b9cca4f7763e373ULL, 0x682e6ff3d6b2b8a3ULL,
        0x748f82ee5defb2fcULL, 0x78a5636f43172f60ULL,
        0x84c87814a1f0ab72ULL, 0x8cc702081a6439ecULL,
        0x90befffa23631e28ULL, 0xa4506cebde82bde9ULL,
        0xbef9a3f7b2c67915ULL, 0xc67178f2e372532bULL,
        0xca273eceea26619cULL, 0xd186b8c721c0c207ULL,
        0xeada7dd6cde0eb1eULL, 0xf57d4f7fee6ed178ULL,
        0x06f067aa72176fbaULL, 0x0a637dc5a2c898a6ULL,
        0x113f9804bef90daeULL, 0x1b710b35131c471bULL,
        0x28db77f523047d84ULL, 0x32caab7b40c72493ULL,
        0x3c9ebe0a15c9bebcULL, 0x431d67c49c100d4cULL,
        0x4cc5d4becb3e42b6ULL, 0x597f299cfc657e2aULL,
        0x5fcb6fab3ad6faecULL, 0x6c44198c4a475817ULL
    };
    // Initial hash value H for SHA-384 
    const static sha_word64 sha384_initial_hash_value[8] = {
        0xcbbb9d5dc1059ed8ULL, 0x629a292a367cd507ULL,
        0x9159015a3070dd17ULL, 0x152fecd8f70e5939ULL,
        0x67332667ffc00b31ULL, 0x8eb44a8768581511ULL,
        0xdb0c2e0d64f98fa7ULL, 0x47b5481dbefa4fa4ULL
    };

    // Initial hash value H for SHA-512 
    const static sha_word64 sha512_initial_hash_value[8] = {
        0x6a09e667f3bcc908ULL, 0xbb67ae8584caa73bULL,
        0x3c6ef372fe94f82bULL, 0xa54ff53a5f1d36f1ULL,
        0x510e527fade682d1ULL, 0x9b05688c2b3e6c1fULL,
        0x1f83d9abfb41bd6bULL, 0x5be0cd19137e2179ULL
    };
#endif

/*
 * Constant used by SHA224/256/384/512_End() functions for converting the
 * digest to a readable hexadecimal character string:
 */
static const char *sha_hex_digits = "0123456789abcdef";


void sha2::SHA1_Internal_Transform(const sha_word32 *data) {
    sha_word32  a, b, c, d, e;
    sha_word32 *state = (sha_word32*)ctx.state;
    sha_word32  T1, T2, *W1=(sha_word32*)ctx.buffer;
    int j;

// Initialize registers with the prev. intermediate value 
    a = state[0];
    b = state[1];
    c = state[2];
    d = state[3];
    e = state[4];
    j = 0;
    do {
        if (m_boolIsBigEndian) W1[j] = *data++;
        else REVERSE32(*data++, W1[j]);// Copy data while converting to host byte order
        T1 = ROTL32(5, a) + Ch(b, c, d) + e + K1_0_TO_19 + W1[j];
        e = d;
        d = c;
        c = ROTL32(30, b);
        b = a;
        a = T1;
        j++;
    } while (j < 16);

    do {
        T1 = W1[(j+13)&0x0f] ^ W1[(j+8)&0x0f] ^ W1[(j+2)&0x0f] ^ W1[j&0x0f];
        if (j < 20)      T2 = Ch(b,c,d)     + K1_0_TO_19;
        else if (j < 40) T2 = Parity(b,c,d) + K1_20_TO_39;
        else if (j < 60) T2 = Maj(b,c,d)    + K1_40_TO_59;
        else             T2 = Parity(b,c,d) + K1_60_TO_79;
        T1 = ROTL32(5, a) + T2 + e + (W1[j&0x0f] = ROTL32(1, T1));
        e = d;
        d = c;
        c = ROTL32(30, b);
        b = a;
        a = T1;
        j++;
    } while (j < 80);

    state[0] += a;
    state[1] += b;
    state[2] += c;
    state[3] += d;
    state[4] += e;
}



///* SHA-256: ********************************************************

void sha2::SHA256_Internal_Transform(const sha_word32* data) {
    sha_word32  a, b, c, d, e, f, g, h, s0, s1;
    sha_word32 *state = (sha_word32*)ctx.state;
    sha_word32  T1, T2, *W256=(sha_word32*)ctx.buffer;;
    int j;

// Initialize registers with the prev. intermediate value 
    a = state[0];
    b = state[1];
    c = state[2];
    d = state[3];
    e = state[4];
    f = state[5];
    g = state[6];
    h = state[7];

    j = 0;
    do {
        if (m_boolIsBigEndian) W256[j] = *data++;
        else REVERSE32(*data++,W256[j]);// Copy data while converting to host byte order

        T1 = h + Sigma1_256(e) + Ch(e, f, g) + K256[j] + W256[j];
        T2 = Sigma0_256(a) + Maj(a, b, c);
        h = g;
        g = f;
        f = e;
        e = d + T1;
        d = c;
        c = b;
        b = a;
        a = T1 + T2;

        j++;
    } while (j < 16);

    do {
// Part of the message block expansion: 
        s0 = W256[(j+1)&0x0f];
        s0 = sigma0_256(s0);
        s1 = W256[(j+14)&0x0f];
        s1 = sigma1_256(s1);

// Apply the SHA-256 compression function to update a..h 
        T1 = h + Sigma1_256(e) + Ch(e, f, g) + K256[j] +
        (W256[j&0x0f] += s1 + W256[(j+9)&0x0f] + s0);
        T2 = Sigma0_256(a) + Maj(a, b, c);
        h = g;
        g = f;
        f = e;
        e = d + T1;
        d = c;
        c = b;
        b = a;
        a = T1 + T2;

        j++;
    } while (j < 64);

// Compute the current intermediate hash value 
    state[0] += a;
    state[1] += b;
    state[2] += c;
    state[3] += d;
    state[4] += e;
    state[5] += f;
    state[6] += g;
    state[7] += h;
}

//** SHA-512: ********************************************************

void sha2::SHA512_Internal_Transform(const sha_word64* data) {
    sha_word64  a, b, c, d, e, f, g, h, s0, s1;
    sha_word64 *state = (sha_word64 *)ctx.state;
    sha_word64  T1, T2, *W512 = (sha_word64*)ctx.buffer;
    int j;

// Initialize registers with the prev. intermediate value 
    a = state[0];
    b = state[1];
    c = state[2];
    d = state[3];
    e = state[4];
    f = state[5];
    g = state[6];
    h = state[7];

    j = 0;

    do {

        if (m_boolIsBigEndian){
            W512[j] = *data;
            data++;
        }else{
            REVERSE64(*data++, W512[j]);// copy and convert TO host byte order
        }

        T1 = h + Sigma1_512(e) + Ch(e, f, g) + K512[j] + W512[j];
        T2 = Sigma0_512(a) + Maj(a, b, c);
        h = g;
        g = f;
        f = e;
        e = d + T1;
        d = c;
        c = b;
        b = a;
        a = T1 + T2;

        j++;
    } while (j < 16);

    do {
// Part of the message block expansion: 
        s0 = W512[(j+1)&0x0f];
        s0 = sigma0_512(s0);
        s1 = W512[(j+14)&0x0f];
        s1 =  sigma1_512(s1);

// Apply the SHA-512 compression function to update a..h 
        T1 = h + Sigma1_512(e) + Ch(e, f, g) + K512[j] +
        (W512[j&0x0f] += s1 + W512[(j+9)&0x0f] + s0);
        T2 = Sigma0_512(a) + Maj(a, b, c);
        h = g;
        g = f;
        f = e;
        e = d + T1;
        d = c;
        c = b;
        b = a;
        a = T1 + T2;

        j++;
    } while (j < 80);

// Compute the current intermediate hash value 
    state[0] += a;
    state[1] += b;
    state[2] += c;
    state[3] += d;
    state[4] += e;
    state[5] += f;
    state[6] += g;
    state[7] += h;
}


void sha2::SHA256_Internal_Last(bool isSha1) {
    sha_word32    usedspace;

    usedspace = (sha_word32)(ctx.bitcount[0] >> 3) % 64;
    if (usedspace == 0) {
        MEMSET_BZERO(ctx.buffer, 56);
        ctx.buffer[0] = 0x80;
    }else {
        ctx.buffer[usedspace++] = 0x80;
        if (usedspace <= 56) {
            MEMSET_BZERO(&ctx.buffer[usedspace], 56 - usedspace);
        }else {
            if (usedspace < 64) {
                MEMSET_BZERO(&ctx.buffer[usedspace], 64 - usedspace);
            }
            if (isSha1) SHA1_Internal_Transform((sha_word32*)ctx.buffer);
            else SHA256_Internal_Transform((sha_word32*)ctx.buffer);
            MEMSET_BZERO(ctx.buffer, 56);
        }
    }

    if (!m_boolIsBigEndian) REVERSE64(ctx.bitcount[0],ctx.bitcount[0]);
    *(sha_word64*)&ctx.buffer[56] = ctx.bitcount[0];
    if (isSha1) SHA1_Internal_Transform((sha_word32*)ctx.buffer);
    else SHA256_Internal_Transform((sha_word32*)ctx.buffer);
}


void sha2::SHA512_Internal_Last() {
    sha_word32    usedspace;

    usedspace = (sha_word32)(ctx.bitcount[0] >> 3) % 128;
    if (usedspace == 0) {
        MEMSET_BZERO(ctx.buffer, 112);
        ctx.buffer[0] = 0x80;
    }else{
        ctx.buffer[usedspace++] = 0x80;
        if (usedspace <= 112) {
            MEMSET_BZERO(&ctx.buffer[usedspace], 112 - usedspace);
        }else {
            if (usedspace < 128) {
                MEMSET_BZERO(&ctx.buffer[usedspace], 128 - usedspace);
            }
            SHA512_Internal_Transform((sha_word64*)ctx.buffer);
            MEMSET_BZERO(ctx.buffer, 112);
        }
        usedspace = 0;
    }

    if (!m_boolIsBigEndian){
        REVERSE64(ctx.bitcount[0],ctx.bitcount[0]);
        REVERSE64(ctx.bitcount[1],ctx.bitcount[1]);
    }

    *(sha_word64*)&ctx.buffer[112] = ctx.bitcount[1];
    *(sha_word64*)&ctx.buffer[120] = ctx.bitcount[0];
    SHA512_Internal_Transform((sha_word64*)ctx.buffer);
}



void sha2::SHA32bit_Update(const sha_byte *data, size_t len, bool isSha1) {
    sha_word32 freespace, usedspace;
    
    if (len<1){return;}// Calling with no data is valid - we do nothing 

    usedspace = (sha_word32)(ctx.bitcount[0] >> 3) % 64;
    if (usedspace > 0) {// Calculate how much free space is available in the buffer 
        freespace = 64 - usedspace;
        if (len >= freespace) {// Fill the buffer completely and process it 
            MEMCPY_BCOPY(&ctx.buffer[usedspace], data, freespace);
            ctx.bitcount[0] += freespace << 3;
            len -= freespace;
            data += freespace;
            if (isSha1) SHA1_Internal_Transform((sha_word32 *)ctx.buffer);
            else SHA256_Internal_Transform((sha_word32 *)ctx.buffer);
        }else {// The buffer is not yet full
            MEMCPY_BCOPY(&ctx.buffer[usedspace], data, len);
            ctx.bitcount[0] += len << 3;
            return;
        }
    }
    while (len >= 64) {// Process as many complete blocks as we can
        if (isSha1) SHA1_Internal_Transform((sha_word32*)data);
        else SHA256_Internal_Transform((sha_word32*)data);
        ctx.bitcount[0] += 512;
        len -= 64;
        data += 64;
    }
    if (len > 0) {// There's left-overs, so save 'em
        MEMCPY_BCOPY(&ctx.buffer, data, len);
        ctx.bitcount[0] += len << 3;
    }
}



void sha2::SHA64bit_Update(const sha_byte *data, size_t len) {
    sha_word32 freespace, usedspace;

    if (len < 1){return;}// Calling with no data is valid - we do nothing 

    usedspace = (sha_word32)(ctx.bitcount[0] >> 3) % 128;
    if (usedspace > 0) {// Calculate how much free space is available in the buffer 
        freespace = 128 - usedspace;
        if (len >= freespace) {// Fill the buffer completely and process it 
            MEMCPY_BCOPY(&ctx.buffer[usedspace], data, freespace);
            ADDINC128(ctx.bitcount, freespace << 3);
            len -= freespace;
            data += freespace;
            SHA512_Internal_Transform((sha_word64*)ctx.buffer);
        }else {// The buffer is not yet full 
            MEMCPY_BCOPY(&ctx.buffer[usedspace], data, len);
            ADDINC128(ctx.bitcount, len << 3);
            return;
        }
    }
    while (len >= 128) {// Process as many complete blocks as we can 
        SHA512_Internal_Transform((sha_word64*)data);
        ADDINC128(ctx.bitcount, 1024);
        len -= 128;
        data += 128;
    }
    if (len > 0) {// There's left-overs, so save 'em 
        MEMCPY_BCOPY(ctx.buffer, data, len);
        ADDINC128(ctx.bitcount, len << 3);
    }
}


/*
 *
 *
 *
 *  Public interfaces...
 *
 *
 *
 */

void sha2::Init(SHA_TYPE type){
    m_Type = type;
    m_boolEnded = false;
    MEMSET_BZERO(&ctx, sizeof(SHA_CTX));
    switch (m_Type){
        case enuSHA1   : MEMCPY_BCOPY(ctx.state, sha1_initial_hash_value, sizeof(sha_word32) * 5); break;
        case enuSHA224 : MEMCPY_BCOPY(ctx.state, sha224_initial_hash_value, sizeof(sha_word32) * 8); break;
        case enuSHA256 : MEMCPY_BCOPY(ctx.state, sha256_initial_hash_value, sizeof(sha_word32) * 8); break;
        case enuSHA384 : MEMCPY_BCOPY(ctx.state, sha384_initial_hash_value, sizeof(sha_word64) * 8); break;
        case enuSHA512 : MEMCPY_BCOPY(ctx.state, sha512_initial_hash_value, sizeof(sha_word64) * 8); break;
        default : throw std::runtime_error("Invalid SHA_TYPE type!");
    }
}


void sha2::Update(const sha_byte* data, size_t len){
    switch (m_Type){
        case enuSHA1   : SHA32bit_Update(data, len, true); break;
        case enuSHA224 : SHA32bit_Update(data, len); break;
        case enuSHA256 : SHA32bit_Update(data, len); break;
        case enuSHA384 : SHA64bit_Update(data, len); break;
        case enuSHA512 : SHA64bit_Update(data, len); break;
        default : throw std::runtime_error("Invalid SHA_TYPE type!");
    }
}


void sha2::End(){
    sha_byte *d = m_digest;
    char *buf = m_chrHexHash;
    int i, j, diglen, statecnt=8;
    bool is64bit=false;
    sha_word32 *state32=(sha_word32 *)ctx.state;
    sha_word64 *state64=(sha_word64 *)ctx.state;

    switch (m_Type){
        case enuSHA1   : {
            SHA256_Internal_Last(true);
            statecnt = 5;
            diglen = SHA1_DIGESTC_LENGTH;
            break;
        }
        case enuSHA224 : {
            SHA256_Internal_Last();
            diglen = SHA224_DIGESTC_LENGTH;
            break;
        }
        case enuSHA256 : {
            SHA256_Internal_Last();
            diglen = SHA256_DIGESTC_LENGTH;
            break;
        }
        case enuSHA384 : {
            SHA512_Internal_Last();
            is64bit = true;
            diglen = SHA384_DIGESTC_LENGTH;
            break;
        }
        case enuSHA512 : {
            SHA512_Internal_Last();
            is64bit = true;
            diglen = SHA512_DIGESTC_LENGTH;
            break;
        }
        default : throw std::runtime_error("Invalid SHA_TYPE type!");
    }
    if (m_boolIsBigEndian){
        MEMCPY_BCOPY(&m_digest, &ctx.state, diglen);
    }else{
        sha_byte *dp = m_digest, *ptr;
        for (i=0; i<statecnt; i++){
            if (is64bit) ptr = (sha_byte *)&state64[i];
            else ptr = (sha_byte *)&state32[i];
            for (j = is64bit ? 7 : 3; j>-1; --j) *dp++ = ptr[j];
        }
    }

    for (i=0; i<diglen; i++) {
        *buf++ = sha_hex_digits[(*d & 0xf0) >> 4];
        *buf++ = sha_hex_digits[*d & 0x0f];
        d++;
    }
    *buf = (char)0;
    m_strHash = m_chrHexHash;
    m_boolEnded = true;
}

const string &sha2::GetHash(SHA_TYPE type, const sha_byte* data, size_t len){
    Init(type);
    Update(data, len);
    End();
    return m_strHash;
}



const char *sha2::HexHash(){
    if (!m_boolEnded) throw std::runtime_error("Unfinished execution!");
    return m_strHash.c_str();
}
const string &sha2::StringHash(){
    if (!m_boolEnded) throw std::runtime_error("Unfinished execution!");
    return m_strHash;
}
const char *sha2::RawHash(int &length){
    if (!m_boolEnded) throw std::runtime_error("Unfinished execution!");
    switch (m_Type){
        case enuSHA1   : length = SHA1_DIGESTC_LENGTH;   break;
        case enuSHA224 : length = SHA224_DIGESTC_LENGTH; break;
        case enuSHA256 : length = SHA256_DIGESTC_LENGTH; break;
        case enuSHA384 : length = SHA384_DIGESTC_LENGTH; break;
        case enuSHA512 : length = SHA512_DIGESTC_LENGTH; break;
        default : length = 0;
    }
    return (const char *)m_digest;
}

