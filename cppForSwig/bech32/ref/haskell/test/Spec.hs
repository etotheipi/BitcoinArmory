import Control.Monad (forM_)
import Data.Bits (xor)
import qualified Data.ByteString as BS
import qualified Data.ByteString.Base16 as B16
import qualified Data.ByteString.Char8 as BSC
import Data.Char (toLower)
import Data.Maybe (isNothing, isJust)
import Data.Word (Word8)
import Codec.Binary.Bech32 (bech32Encode, bech32Decode, segwitEncode, segwitDecode, word5)
import Test.Tasty
import Test.Tasty.HUnit

main :: IO ()
main = defaultMain tests

validChecksums :: [BS.ByteString]
validChecksums = map BSC.pack
    [ "A12UEL5L"
    , "an83characterlonghumanreadablepartthatcontainsthenumber1andtheexcludedcharactersbio1tt5tgs"
    , "abcdef1qpzry9x8gf2tvdw0s3jn54khce6mua7lmqqqxw"
    , "11qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqc8247j"
    , "split1checkupstagehandshakeupstreamerranterredcaperred2y9e3w"
    ]

invalidChecksums :: [BS.ByteString]
invalidChecksums = map BSC.pack
    [ " 1nwldj5"
    , "\DEL1axkwrx"
    , "an84characterslonghumanreadablepartthatcontainsthenumber1andtheexcludedcharactersbio1569pvx"
    , "pzry9x0s0muk"
    , "1pzry9x0s0muk"
    , "x1b4n0q5v"
    , "li1dgmt3"
    , "de1lg7wt\xFF"
    ]

validAddresses :: [(BS.ByteString, BS.ByteString)]
validAddresses = map mapTuple
    [ ("BC1QW508D6QEJXTDG4Y5R3ZARVARY0C5XW7KV8F3T4", "0014751e76e8199196d454941c45d1b3a323f1433bd6")
    , ("tb1qrp33g0q5c5txsp9arysrx4k6zdkfs4nce4xj0gdcccefvpysxf3q0sl5k7"
      ,"00201863143c14c5166804bd19203356da136c985678cd4d27a1b8c6329604903262")
    , ("bc1pw508d6qejxtdg4y5r3zarvary0c5xw7kw508d6qejxtdg4y5r3zarvary0c5xw7k7grplx"
      ,"5128751e76e8199196d454941c45d1b3a323f1433bd6751e76e8199196d454941c45d1b3a323f1433bd6")
    , ("BC1SW50QA3JX3S", "6002751e")
    , ("bc1zw508d6qejxtdg4y5r3zarvaryvg6kdaj", "5210751e76e8199196d454941c45d1b3a323")
    , ("tb1qqqqqp399et2xygdj5xreqhjjvcmzhxw4aywxecjdzew6hylgvsesrxh6hy"
      ,"0020000000c4a5cad46221b2a187905e5266362b99d5e91c6ce24d165dab93e86433")
    ]
  where
    mapTuple (a, b) = (BSC.pack a, BSC.pack b)

invalidAddresses :: [BS.ByteString]
invalidAddresses = map BSC.pack
    [ "tc1qw508d6qejxtdg4y5r3zarvary0c5xw7kg3g4ty"
    , "bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t5"
    , "BC13W508D6QEJXTDG4Y5R3ZARVARY0C5XW7KN40WF2"
    , "bc1rw5uspcuh"
    , "bc10w508d6qejxtdg4y5r3zarvary0c5xw7kw508d6qejxtdg4y5r3zarvary0c5xw7kw5rljs90"
    , "BC1QR508D6QEJXTDG4Y5R3ZARVARYV98GJ9P"
    , "tb1qrp33g0q5c5txsp9arysrx4k6zdkfs4nce4xj0gdcccefvpysxf3q0sL5k7"
    , "bc1zw508d6qejxtdg4y5r3zarvaryvqyzf3du"
    , "tb1qrp33g0q5c5txsp9arysrx4k6zdkfs4nce4xj0gdcccefvpysxf3pjxtptv"
    , "bc1gmk9yu"
    ]

hexDecode :: BS.ByteString -> BS.ByteString
hexDecode s = let (ret, rest) = B16.decode s
              in if BS.null rest then ret else undefined

segwitScriptPubkey :: Word8 -> [Word8] -> BS.ByteString
segwitScriptPubkey witver witprog = BS.pack $ witver' : (fromIntegral $ length witprog) : witprog
  where witver' = if witver == 0 then 0 else witver + 0x50

tests :: TestTree
tests = testGroup "Tests"
    [ testCase "Checksums" $ forM_ validChecksums $ \checksum -> do
          case bech32Decode checksum of
            Nothing -> assertFailure (show checksum)
            Just (resultHRP, resultData) -> do
                -- test that a corrupted checksum fails decoding.
                let (hrp, rest) = BSC.breakEnd (== '1') checksum
                    Just (first, rest') = BS.uncons rest
                    checksumCorrupted = (hrp `BS.snoc` (first `xor` 1)) `BS.append` rest'
                assertBool (show checksum ++ " corrupted") $ isNothing (bech32Decode checksumCorrupted)
                -- test that re-encoding the decoded checksum results in the same checksum.
                let checksumEncoded = bech32Encode resultHRP resultData
                    expectedChecksum = Just $ BSC.map toLower checksum
                assertEqual (show checksum ++ " re-encode") expectedChecksum checksumEncoded
    , testCase "Invalid checksums" $ forM_ invalidChecksums $
          \checksum -> assertBool (show checksum) (isNothing $ bech32Decode checksum)
    , testCase "Addresses" $ forM_ validAddresses $ \(address, hexscript) -> do
          let address' = BSC.map toLower address
              hrp = BSC.take 2 address'
          case segwitDecode hrp address of
            Nothing -> assertFailure "decode failed"
            Just (witver, witprog) -> do
                assertEqual (show address) (hexDecode hexscript) (segwitScriptPubkey witver witprog)
                assertEqual (show address) (Just address') (segwitEncode hrp witver witprog)
    , testCase "Invalid Addresses" $ forM_ invalidAddresses $ \address -> do
          assertBool (show address) (isNothing $ segwitDecode (BSC.pack "bc") address)
          assertBool (show address) (isNothing $ segwitDecode (BSC.pack "tb") address)
    , testCase "More Encoding/Decoding Cases" $ do
          assertBool "length > 90" $ isNothing $
              bech32Encode (BSC.pack "bc") (replicate 82 (word5 (1::Word8)))
          assertBool "segwit version bounds" $ isNothing $
              segwitEncode (BSC.pack "bc") 17 []
          assertBool "segwit prog len version 0" $ isNothing $
              segwitEncode (BSC.pack "bc") 0 (replicate 30 1)
          assertBool "segwit prog len version != 0" $ isJust $
              segwitEncode (BSC.pack "bc") 1 (replicate 30 1)
          assertBool "segwit prog len version != 0" $ isNothing $
              segwitEncode (BSC.pack "bc") 1 (replicate 41 1)
          assertBool "empty HRP encode" $ isNothing $ bech32Encode (BSC.pack "") []
          assertBool "empty HRP decode" $ isNothing $ bech32Decode (BSC.pack "10a06t8")
          assertEqual "hrp lowercased"
              (Just $ BSC.pack "hrp1g9xj8m")
              (bech32Encode (BSC.pack "HRP") [])
    ]
