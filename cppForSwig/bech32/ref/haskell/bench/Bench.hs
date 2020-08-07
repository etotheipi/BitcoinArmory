import Criterion.Main
import Codec.Binary.Bech32 (toBase32, toBase256, word5)

main :: IO ()
main = defaultMain [
  bgroup "bit conversions"
    [ bench "toBase32"  $ whnf toBase32 $ concat $ replicate 100 [0..255]
    , bench "toBase256"  $ whnf toBase256 $ map word5 $ concat $ replicate 1000 [(0::Word)..31]
    ]
  ]
