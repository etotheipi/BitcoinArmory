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

#![warn(missing_docs)]

//! Encoding and decoding Bech32 Bitcoin Segwit Addresses
//! 
//! Encoding and decoding for Bech32 strings and Bitcoin Segregated Witness 
//! addresses. Bech32 is a 5-bit (base-32) encoding scheme that produces
//! strings that comprise a human-readable part, a separator, a data part,
//! and a checksum. The encoding implements a BCH code that guarantees
//! error detection of up to four characters with less than 1 in 1 billion
//! chance of failing to detect more errors.
//! 
//! The library contains `bech32` utilities for generic encoding of Bech32
//! strings and `wit_prog` for converting witness programs to Bitcoin
//! addresses and back.
//! 
//! # Examples
//! 
//! ```rust
//! use bech32::wit_prog::WitnessProgram;
//! 
//! let witness_program = WitnessProgram {
//!     version: 0,
//!     program: vec![
//!                 0x00, 0x00, 0x00, 0xc4, 0xa5, 0xca, 0xd4, 0x62, 
//!                 0x21, 0xb2, 0xa1, 0x87, 0x90, 0x5e, 0x52, 0x66, 
//!                 0x36, 0x2b, 0x99, 0xd5, 0xe9, 0x1c, 0x6c, 0xe2, 
//!                 0x4d, 0x16, 0x5d, 0xab, 0x93, 0xe8, 0x64, 0x33]
//! };
//! 
//! let enc_result = witness_program.to_address("tb".to_string());
//! assert_eq!(enc_result.unwrap(), 
//!     "tb1qqqqqp399et2xygdj5xreqhjjvcmzhxw4aywxecjdzew6hylgvsesrxh6hy".to_string());
//! ```

pub mod bech32;
pub mod wit_prog;

/// Error types for Bech32 encoding / decoding
#[derive(PartialEq, Debug)]
pub enum CodingError {
    /// String does not contain the separator character
    MissingSeparator,
    /// The checksum does not match the rest of the data
    InvalidChecksum,
    /// The data or human-readable part is too long or too short
    InvalidLength,
    /// Some part of the string contains an invalid character
    InvalidChar,
    /// Some part of the data has an invalid value
    InvalidData,
    /// The whole string must be of one case
    MixedCase,
}

/// Error types for validating scriptpubkeys
#[derive(PartialEq, Debug)]
pub enum ScriptPubKeyError {
    /// scriptpubkeys does not have enough data
    TooShort,
    /// The provided length byte does not match the data
    InvalidLengthByte,
}

/// Error types for witness programs
///
/// BIP141 specifies Segregated Witness and defines valid program lengths
/// for Version 0 scripts. Script version is also limited to values 0-16.
#[derive(PartialEq, Debug)]
pub enum WitnessProgramError {
    /// Denotes that the WitnessProgram is too long or too short
    ///
    /// Programs must be between 2 and 40 bytes
    InvalidLength,
    /// Given the program version, the length is invalid
    ///
    /// Version 0 scripts must be either 20 or 32 bytes
    InvalidVersionLength,
    /// Script version must be 0 to 16 inclusive
    InvalidScriptVersion,
}

/// Error types during bit conversion
#[derive(PartialEq, Debug)]
pub enum BitConversionError {
    /// Input value exceeds "from bits" size
    InvalidInputValue(u8),
    /// Invalid padding values in data
    InvalidPadding,
}

/// Error types while encoding and decoding SegWit addresses
#[derive(PartialEq, Debug)]
pub enum AddressError {
    /// Some Bech32 conversion error
    Bech32(CodingError),
    /// Some witness program error
    WitnessProgram(WitnessProgramError),
    /// Some 5-bit <-> 8-bit conversion error
    Conversion(BitConversionError),
    /// The provided human-readable portion does not match
    HumanReadableMismatch,
    /// The human-readable part is invalid (must be "bc" or "tb")
    InvalidHumanReadablePart,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn valid_checksum() {
        let strings: Vec<&str> = vec!(
            "A12UEL5L",
            "an83characterlonghumanreadablepartthatcontainsthenumber1andtheexcludedcharactersbio1tt5tgs",
            "abcdef1qpzry9x8gf2tvdw0s3jn54khce6mua7lmqqqxw",
            "11qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqc8247j",
            "split1checkupstagehandshakeupstreamerranterredcaperred2y9e3w",
        );
        for s in strings {
            let decode_result = bech32::Bech32::from_string(s.to_string());
            if !decode_result.is_ok() {
                panic!("Did not decode: {:?} Reason: {:?}", s, decode_result.unwrap_err());
            }
            assert!(decode_result.is_ok());
            let encode_result = decode_result.unwrap().to_string();
            assert!(encode_result.is_ok());
            assert_eq!(s.to_lowercase(), encode_result.unwrap().to_lowercase());
        }
    }

    #[test]
    fn invalid_bech32() {
        let pairs: Vec<(&str, CodingError)> = vec!(
            (" 1nwldj5",
                CodingError::InvalidChar),
            ("\x7f1axkwrx",
                CodingError::InvalidChar),
            ("an84characterslonghumanreadablepartthatcontainsthenumber1andtheexcludedcharactersbio1569pvx",
                CodingError::InvalidLength),
            ("pzry9x0s0muk",
                CodingError::MissingSeparator),
            ("1pzry9x0s0muk",
                CodingError::InvalidLength),
            ("x1b4n0q5v",
                CodingError::InvalidChar),
            ("li1dgmt3",
                CodingError::InvalidLength),
            ("de1lg7wt\u{ff}",
                CodingError::InvalidChar),
        );
        for p in pairs {
            let (s, expected_error) = p;
            let dec_result = bech32::Bech32::from_string(s.to_string());
            println!("{:?}", s.to_string());
            if dec_result.is_ok() {
                println!("{:?}", dec_result.unwrap());
                panic!("Should be invalid: {:?}", s);
            }
            assert_eq!(dec_result.unwrap_err(), expected_error);
        }
    }

    #[test]
    fn valid_address() {
        let pairs: Vec<(&str, Vec<u8>)> = vec![
            (
                "BC1QW508D6QEJXTDG4Y5R3ZARVARY0C5XW7KV8F3T4",
                vec![
                    0x00, 0x14, 0x75, 0x1e, 0x76, 0xe8, 0x19, 0x91, 0x96, 0xd4, 0x54,
                    0x94, 0x1c, 0x45, 0xd1, 0xb3, 0xa3, 0x23, 0xf1, 0x43, 0x3b, 0xd6
                ]
            ),
            (
                "tb1qrp33g0q5c5txsp9arysrx4k6zdkfs4nce4xj0gdcccefvpysxf3q0sl5k7",
                vec![
                    0x00, 0x20, 0x18, 0x63, 0x14, 0x3c, 0x14, 0xc5, 0x16, 0x68, 0x04,
                    0xbd, 0x19, 0x20, 0x33, 0x56, 0xda, 0x13, 0x6c, 0x98, 0x56, 0x78,
                    0xcd, 0x4d, 0x27, 0xa1, 0xb8, 0xc6, 0x32, 0x96, 0x04, 0x90, 0x32,
                    0x62
                ]
            ),
            (
                "bc1pw508d6qejxtdg4y5r3zarvary0c5xw7kw508d6qejxtdg4y5r3zarvary0c5xw7k7grplx",
                vec![
                    0x51, 0x28, 0x75, 0x1e, 0x76, 0xe8, 0x19, 0x91, 0x96, 0xd4, 0x54,
                    0x94, 0x1c, 0x45, 0xd1, 0xb3, 0xa3, 0x23, 0xf1, 0x43, 0x3b, 0xd6,
                    0x75, 0x1e, 0x76, 0xe8, 0x19, 0x91, 0x96, 0xd4, 0x54, 0x94, 0x1c,
                    0x45, 0xd1, 0xb3, 0xa3, 0x23, 0xf1, 0x43, 0x3b, 0xd6
                ]
            ),
            (
                "BC1SW50QA3JX3S",
                vec![
                   0x60, 0x02, 0x75, 0x1e
                ]
            ),
            (
                "bc1zw508d6qejxtdg4y5r3zarvaryvg6kdaj",
                vec![
                    0x52, 0x10, 0x75, 0x1e, 0x76, 0xe8, 0x19, 0x91, 0x96, 0xd4, 0x54,
                    0x94, 0x1c, 0x45, 0xd1, 0xb3, 0xa3, 0x23
                ]
            ),
            (
                "tb1qqqqqp399et2xygdj5xreqhjjvcmzhxw4aywxecjdzew6hylgvsesrxh6hy",
                vec![
                    0x00, 0x20, 0x00, 0x00, 0x00, 0xc4, 0xa5, 0xca, 0xd4, 0x62, 0x21,
                    0xb2, 0xa1, 0x87, 0x90, 0x5e, 0x52, 0x66, 0x36, 0x2b, 0x99, 0xd5,
                    0xe9, 0x1c, 0x6c, 0xe2, 0x4d, 0x16, 0x5d, 0xab, 0x93, 0xe8, 0x64,
                    0x33
                ]
            ),
        ];
        for p in pairs {
            let (address, scriptpubkey) = p;
            let mut hrp = "bc".to_string();
            let mut dec_result = wit_prog::WitnessProgram::from_address(hrp.clone(),
                address.to_string());
            if !dec_result.is_ok() {
                hrp = "tb".to_string();
                dec_result = wit_prog::WitnessProgram::from_address(hrp.clone(),
                    address.to_string());
                if !dec_result.is_ok() {
                    println!("Should be valid: {:?}", address);
                }
            }
            assert!(dec_result.is_ok());

            let prog = dec_result.unwrap();
            let pubkey = prog.clone().to_scriptpubkey();
            assert_eq!(pubkey, scriptpubkey);

            let spk_result = wit_prog::WitnessProgram::from_scriptpubkey(&scriptpubkey);
            assert!(spk_result.is_ok());
            assert_eq!(prog, spk_result.unwrap());

            let enc_result = prog.to_address(hrp);
            assert!(enc_result.is_ok());

            let enc_address = enc_result.unwrap();
            assert_eq!(address.to_lowercase(), enc_address.to_lowercase());
        }
    }

    #[test]
    fn invalid_address() {
        let pairs: Vec<(&str, AddressError)> = vec!(
            ("tc1qw508d6qejxtdg4y5r3zarvary0c5xw7kg3g4ty",
                AddressError::InvalidHumanReadablePart),
            ("bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t5",
                AddressError::Bech32(CodingError::InvalidChecksum)),
            ("BC13W508D6QEJXTDG4Y5R3ZARVARY0C5XW7KN40WF2",
                AddressError::WitnessProgram(WitnessProgramError::InvalidScriptVersion)),
            ("bc1rw5uspcuh",
                AddressError::WitnessProgram(WitnessProgramError::InvalidLength)),
            ("bc10w508d6qejxtdg4y5r3zarvary0c5xw7kw508d6qejxtdg4y5r3zarvary0c5xw7kw5rljs90",
                AddressError::Bech32(CodingError::InvalidLength)),
            ("BC1QR508D6QEJXTDG4Y5R3ZARVARYV98GJ9P",
                AddressError::WitnessProgram(WitnessProgramError::InvalidVersionLength)),
            ("tb1qrp33g0q5c5txsp9arysrx4k6zdkfs4nce4xj0gdcccefvpysxf3q0sL5k7",
                AddressError::Bech32(CodingError::MixedCase)),
            ("tb1pw508d6qejxtdg4y5r3zarqfsj6c3",
                AddressError::Conversion(BitConversionError::InvalidPadding)),
            ("tb1qrp33g0q5c5txsp9arysrx4k6zdkfs4nce4xj0gdcccefvpysxf3pjxtptv",
                AddressError::Conversion(BitConversionError::InvalidPadding)),
        );
        for p in pairs {
            let (address, desired_error) = p;
            let hrp = address[0..2].to_string();
            let dec_result = wit_prog::WitnessProgram::from_address(
                hrp.to_lowercase(), address.to_string());
            println!("{:?}", address.to_string());
            if dec_result.is_ok() {
                println!("{:?}", dec_result.unwrap());
                panic!("Should be invalid: {:?}", address);
            }
            assert_eq!(dec_result.unwrap_err(), desired_error);
        }
    }
}
