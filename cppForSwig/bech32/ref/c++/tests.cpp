/* Copyright (c) 2017 Pieter Wuille
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 */

#include <stdio.h>
#include <string.h>

#include <algorithm>

#include "segwit_addr.h"
#include "bech32.h"

static const std::string valid_checksum[] = {
    "A12UEL5L",
    "an83characterlonghumanreadablepartthatcontainsthenumber1andtheexcludedcharactersbio1tt5tgs",
    "abcdef1qpzry9x8gf2tvdw0s3jn54khce6mua7lmqqqxw",
    "11qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqc8247j",
    "split1checkupstagehandshakeupstreamerranterredcaperred2y9e3w",
};

static const std::string invalid_checksum[] = {
    " 1nwldj5",
    "\x7f""1axkwrx",
    "an84characterslonghumanreadablepartthatcontainsthenumber1andtheexcludedcharactersbio1569pvx",
    "pzry9x0s0muk",
    "1pzry9x0s0muk",
    "x1b4n0q5v",
    "li1dgmt3",
    "de1lg7wt\xff",
};

struct valid_address_data {
    std::string address;
    size_t scriptPubKeyLen;
    uint8_t scriptPubKey[42];
};

struct invalid_address_data {
    std::string hrp;
    int version;
    size_t program_length;
};

static const struct valid_address_data valid_address[] = {
    {
        "BC1QW508D6QEJXTDG4Y5R3ZARVARY0C5XW7KV8F3T4",
        22, {
            0x00, 0x14, 0x75, 0x1e, 0x76, 0xe8, 0x19, 0x91, 0x96, 0xd4, 0x54,
            0x94, 0x1c, 0x45, 0xd1, 0xb3, 0xa3, 0x23, 0xf1, 0x43, 0x3b, 0xd6
        }
    },
    {
        "tb1qrp33g0q5c5txsp9arysrx4k6zdkfs4nce4xj0gdcccefvpysxf3q0sl5k7",
        34, {
            0x00, 0x20, 0x18, 0x63, 0x14, 0x3c, 0x14, 0xc5, 0x16, 0x68, 0x04,
            0xbd, 0x19, 0x20, 0x33, 0x56, 0xda, 0x13, 0x6c, 0x98, 0x56, 0x78,
            0xcd, 0x4d, 0x27, 0xa1, 0xb8, 0xc6, 0x32, 0x96, 0x04, 0x90, 0x32,
            0x62
        }
    },
    {
        "bc1pw508d6qejxtdg4y5r3zarvary0c5xw7kw508d6qejxtdg4y5r3zarvary0c5xw7k7grplx",
        42, {
            0x81, 0x28, 0x75, 0x1e, 0x76, 0xe8, 0x19, 0x91, 0x96, 0xd4, 0x54,
            0x94, 0x1c, 0x45, 0xd1, 0xb3, 0xa3, 0x23, 0xf1, 0x43, 0x3b, 0xd6,
            0x75, 0x1e, 0x76, 0xe8, 0x19, 0x91, 0x96, 0xd4, 0x54, 0x94, 0x1c,
            0x45, 0xd1, 0xb3, 0xa3, 0x23, 0xf1, 0x43, 0x3b, 0xd6
        }
    },
    {
        "BC1SW50QA3JX3S",
        4, {
           0x90, 0x02, 0x75, 0x1e
        }
    },
    {
        "bc1zw508d6qejxtdg4y5r3zarvaryvg6kdaj",
        18, {
            0x82, 0x10, 0x75, 0x1e, 0x76, 0xe8, 0x19, 0x91, 0x96, 0xd4, 0x54,
            0x94, 0x1c, 0x45, 0xd1, 0xb3, 0xa3, 0x23
        }
    },
    {
        "tb1qqqqqp399et2xygdj5xreqhjjvcmzhxw4aywxecjdzew6hylgvsesrxh6hy",
        34, {
            0x00, 0x20, 0x00, 0x00, 0x00, 0xc4, 0xa5, 0xca, 0xd4, 0x62, 0x21,
            0xb2, 0xa1, 0x87, 0x90, 0x5e, 0x52, 0x66, 0x36, 0x2b, 0x99, 0xd5,
            0xe9, 0x1c, 0x6c, 0xe2, 0x4d, 0x16, 0x5d, 0xab, 0x93, 0xe8, 0x64,
            0x33
        }
    }
};

static const std::string invalid_address[] = {
    "tc1qw508d6qejxtdg4y5r3zarvary0c5xw7kg3g4ty",
    "bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t5",
    "BC13W508D6QEJXTDG4Y5R3ZARVARY0C5XW7KN40WF2",
    "bc1rw5uspcuh",
    "bc10w508d6qejxtdg4y5r3zarvary0c5xw7kw508d6qejxtdg4y5r3zarvary0c5xw7kw5rljs90",
    "BC1QR508D6QEJXTDG4Y5R3ZARVARYV98GJ9P",
    "tb1qrp33g0q5c5txsp9arysrx4k6zdkfs4nce4xj0gdcccefvpysxf3q0sL5k7",
    "bc1zw508d6qejxtdg4y5r3zarvaryvqyzf3du",
    "tb1qrp33g0q5c5txsp9arysrx4k6zdkfs4nce4xj0gdcccefvpysxf3pjxtptv",
    "bc1gmk9yu",
};

static const invalid_address_data invalid_address_enc[] = {
    {"BC", 0, 20},
    {"bc", 0, 21},
    {"bc", 17, 32},
    {"bc", 1, 1},
    {"bc", 16, 41},
};

static std::vector<uint8_t> segwit_scriptpubkey(int witver, const std::vector<uint8_t>& witprog) {
    std::vector<uint8_t> ret;
    ret.push_back(witver ? (0x80 | witver) : 0);
    ret.push_back(witprog.size());
    ret.insert(ret.end(), witprog.begin(), witprog.end());
    return ret;
}

bool case_insensitive_equal(const std::string& s1, const std::string& s2) {
    size_t i = 0;
    if (s1.size() != s2.size()) return false;
    while (i < s1.size() && i < s2.size()) {
        char c1 = s1[i];
        char c2 = s2[i];
        if (c1 >= 'A' && c1 <= 'Z') c1 = (c1 - 'A') + 'a';
        if (c2 >= 'A' && c2 <= 'Z') c2 = (c2 - 'A') + 'a';
        if (c1 != c2) return false;
        ++i;
    }
    return true;
}

int main(void) {
    size_t i;
    int fail = 0;
    for (i = 0; i < sizeof(valid_checksum) / sizeof(valid_checksum[0]); ++i) {
        bool ok = true;
        std::pair<std::string, std::vector<uint8_t> > dec = bech32::decode(valid_checksum[i]);
        if (dec.first.empty()) {
            fprintf(stderr, "Failed to parse '%s'\n", valid_checksum[i].c_str());
            ok = false;
        }
        if (ok) {
            std::string recode = bech32::encode(dec.first, dec.second);
            if (recode.empty()) {
                fprintf(stderr, "Failed to encode '%s'\n", valid_checksum[i].c_str());
            } else {
               ok = case_insensitive_equal(recode, valid_checksum[i]);
               if (!ok) fprintf(stderr, "Failed to roundtrip '%s' -> '%s'\n", valid_checksum[i].c_str(), recode.c_str());
            }
        }
        fail += !ok;
    }
    for (i = 0; i < sizeof(invalid_checksum) / sizeof(invalid_checksum[0]); ++i) {
        std::pair<std::string, std::vector<uint8_t> > dec = bech32::decode(invalid_checksum[i]);
        if (!dec.first.empty() || !dec.second.empty()) {
            fprintf(stderr, "Parsed an invalid code: '%s'\n", invalid_checksum[i].c_str());
            ++fail;
        }
    }
    for (i = 0; i < sizeof(valid_address) / sizeof(valid_address[0]); ++i) {
        std::string hrp = "bc";
        std::pair<int, std::vector<uint8_t> > dec = segwit_addr::decode(hrp, valid_address[i].address);
        if (dec.first == -1) {
            hrp = "tb";
            dec = segwit_addr::decode(hrp, valid_address[i].address);
        }
        bool ok = true;
        if (dec.first == -1) {
            ok = false;
            fprintf(stderr, "Failed to segwit_addr::decode '%s'\n", valid_address[i].address.c_str());
        }
        if (ok) {
            std::vector<uint8_t> spk = segwit_scriptpubkey(dec.first, dec.second);
            ok = spk.size() == valid_address[i].scriptPubKeyLen && memcmp(&spk[0], valid_address[i].scriptPubKey, spk.size()) == 0;
            if (!ok) {
                fprintf(stderr, "segwit_addr::decodes produces wrong result: '%s'\n", valid_address[i].address.c_str());
            }
        }
        if (ok) {
            std::string recode = segwit_addr::encode(hrp, dec.first, dec.second);
            if (recode.empty()) {
                fprintf(stderr, "segwit_addr::encode fails on '%s'\n", valid_address[i].address.c_str());
                ok = false;
            }
            if (ok) {
                ok = case_insensitive_equal(valid_address[i].address, recode);
                if (!ok) fprintf(stderr, "segwit_addr::encode roundtrip fails: '%s' -> '%s'\n", valid_address[i].address.c_str(), recode.c_str());
            }
        }
        fail += !ok;
    }
    for (i = 0; i < sizeof(invalid_address) / sizeof(invalid_address[0]); ++i) {
        std::pair<int, std::vector<uint8_t> > dec = segwit_addr::decode("bc", invalid_address[i]);
        bool ok = true;
        if (dec.first != -1) {
            printf("segwit_addr::decode succeeds on invalid '%s'\n", invalid_address[i].c_str());
            ok = false;
        }
        dec = segwit_addr::decode("tb", invalid_address[i]);
        if (dec.first != -1) {
            printf("segwit_addr::decode succeeds on invalid '%s'\n", invalid_address[i].c_str());
            ok = false;
        }
        fail += !ok;
    }
    for (i = 0; i < sizeof(invalid_address_enc) / sizeof(invalid_address_enc[0]); ++i) {
        std::string code = segwit_addr::encode(invalid_address_enc[i].hrp, invalid_address_enc[i].version, std::vector<uint8_t>(invalid_address_enc[i].program_length, 0));
        if (!code.empty()) {
            printf("segwit_addr::encode succeeds on invalid '%s'\n", code.c_str());
            ++fail;
        }
    }
    printf("%i failures\n", fail);
    return fail != 0;
}
