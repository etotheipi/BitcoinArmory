// Copyright (c) 2017 Clark Moody
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in
// all copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
// THE SOFTWARE.

// Bech32 { hrp: "bech32", data: [0, 1, 2] }->"bech321qpz4nc4pe"

//! Encode and decode the Bech32 format, with checksums
//! 
//! # Examples
//! ```rust
//! use bech32::bech32::Bech32;
//! 
//! let b = Bech32 {
//!     hrp: "bech32".to_string(), 
//!     data: vec![0x00, 0x01, 0x02] 
//! };
//! let encode = b.to_string().unwrap();
//! assert_eq!(encode, "bech321qpz4nc4pe".to_string());
//! ```

use super::CodingError;

/// Grouping structure for the human-readable part and the data part
/// of decoded Bech32 string.
#[derive(PartialEq, Debug, Clone)]
pub struct Bech32 {
    /// Human-readable part
    pub hrp: String,
    /// Data payload
    pub data: Vec<u8>
}

// Human-readable part and data part separator
const SEP: char = '1';

// Encoding character set. Maps data value -> char
const CHARSET: [char; 32] = [
    'q','p','z','r','y','9','x','8',
    'g','f','2','t','v','d','w','0',
    's','3','j','n','5','4','k','h',
    'c','e','6','m','u','a','7','l'
];

// Reverse character set. Maps ASCII byte -> CHARSET index on [0,31]
const CHARSET_REV: [i8; 128] = [
    -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
    -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
    -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
    15, -1, 10, 17, 21, 20, 26, 30,  7,  5, -1, -1, -1, -1, -1, -1,
    -1, 29, -1, 24, 13, 25,  9,  8, 23, -1, 18, 22, 31, 27, 19, -1,
     1,  0,  3, 16, 11, 28, 12, 14,  6,  4,  2, -1, -1, -1, -1, -1,
    -1, 29, -1, 24, 13, 25,  9,  8, 23, -1, 18, 22, 31, 27, 19, -1,
     1,  0,  3, 16, 11, 28, 12, 14,  6,  4,  2, -1, -1, -1, -1, -1
];

type EncodeResult = Result<String, CodingError>;
type DecodeResult = Result<Bech32, CodingError>;

impl Bech32 {
    /// Encode as a string
    pub fn to_string(&self) -> EncodeResult {
        if self.hrp.len() < 1 {
            return Err(CodingError::InvalidLength)
        }
        let hrp_bytes: Vec<u8> = self.hrp.clone().into_bytes();
        let mut combined: Vec<u8> = self.data.clone();
        combined.extend_from_slice(&create_checksum(&hrp_bytes, &self.data));
        let mut encoded: String = format!("{}{}", self.hrp, SEP);
        for p in combined {
            if p >= 32 {
                return Err(CodingError::InvalidData)
            }
            encoded.push(CHARSET[p as usize]);
        }
        Ok(encoded)
    }

    /// Decode from a string
    pub fn from_string(s: String) -> DecodeResult {
        // Ensure overall length is within bounds
        let len: usize = s.len();
        if len < 8 || len > 90 {
            return Err(CodingError::InvalidLength)
        }

        // Check for missing separator
        if s.find(SEP).is_none() {
            return Err(CodingError::MissingSeparator)
        }

        // Split at separator and check for two pieces
        let parts: Vec<&str> = s.rsplitn(2, SEP).collect();
        let raw_hrp = parts[1];
        let raw_data = parts[0];
        if raw_hrp.len() < 1 || raw_data.len() < 6 {
            return Err(CodingError::InvalidLength)
        }

        let mut has_lower: bool = false;
        let mut has_upper: bool = false;
        let mut hrp_bytes: Vec<u8> = Vec::new();
        for b in raw_hrp.bytes() {
            // Valid subset of ASCII
            if b < 33 || b > 126 {
                return Err(CodingError::InvalidChar)
            }
            let mut c = b;
            // Lowercase
            if b >= b'a' && b <= b'z' {
                has_lower = true;
            }
            // Uppercase
            if b >= b'A' && b <= b'Z' {
                has_upper = true;
                // Convert to lowercase
                c = b + (b'a'-b'A');
            }
            hrp_bytes.push(c);
        }

        // Check data payload
        let mut data_bytes: Vec<u8> = Vec::new();
        for b in raw_data.bytes() {
            // Aphanumeric only
            if !((b >= b'0' && b <= b'9') || (b >= b'A' && b <= b'Z') || (b >= b'a' && b <= b'z')) {
                return Err(CodingError::InvalidChar)
            }
            // Excludes these characters: [1,b,i,o]
            if b == b'1' || b == b'b' || b == b'i' || b == b'o' {
                return Err(CodingError::InvalidChar)
            }
            // Lowercase
            if b >= b'a' && b <= b'z' {
                has_lower = true;
            }
            let mut c = b;
            // Uppercase
            if b >= b'A' && b <= b'Z' {
                has_upper = true;
                // Convert to lowercase
                c = b + (b'a'-b'A');
            }
            data_bytes.push(CHARSET_REV[c as usize] as u8);
        }

        // Ensure no mixed case
        if has_lower && has_upper {
            return Err(CodingError::MixedCase)
        }

        // Ensure checksum
        if !verify_checksum(&hrp_bytes, &data_bytes) {
            return Err(CodingError::InvalidChecksum)
        }

        // Remove checksum from data payload
        let dbl: usize = data_bytes.len();
        data_bytes.truncate(dbl - 6);

        Ok(Bech32 {
            hrp: String::from_utf8(hrp_bytes).unwrap(),
            data: data_bytes
        })
    }
}

fn create_checksum(hrp: &Vec<u8>, data: &Vec<u8>) -> Vec<u8> {
    let mut values: Vec<u8> = hrp_expand(hrp);
    values.extend_from_slice(data);
    // Pad with 6 zeros
    values.extend_from_slice(&[0u8; 6]);
    let plm: u32 = polymod(values) ^ 1;
    let mut checksum: Vec<u8> = Vec::new();
    for p in 0..6 {
        checksum.push(((plm >> 5 * (5 - p)) & 0x1f) as u8);
    }
    checksum
}

fn verify_checksum(hrp: &Vec<u8>, data: &Vec<u8>) -> bool {
    let mut exp = hrp_expand(hrp);
    exp.extend_from_slice(data);
    polymod(exp) == 1u32
}

fn hrp_expand(hrp: &Vec<u8>) -> Vec<u8> {
    let mut v: Vec<u8> = Vec::new();
    for b in hrp {
        v.push(*b >> 5);
    }
    v.push(0);
    for b in hrp {
        v.push(*b & 0x1f);
    }
    v
}

// Generator coefficients
const GEN: [u32; 5] = [0x3b6a57b2, 0x26508e6d, 0x1ea119fa, 0x3d4233dd, 0x2a1462b3];

fn polymod(values: Vec<u8>) -> u32 {
    let mut chk: u32 = 1;
    let mut b: u8;
    for v in values {
        b = (chk >> 25) as u8;
        chk = (chk & 0x1ffffff) << 5 ^ (v as u32);
        for i in 0..5 {
            if (b >> i) & 1 == 1 {
                chk ^= GEN[i]
            }
        }
    }
    chk
}
