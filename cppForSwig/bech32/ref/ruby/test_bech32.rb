# Copyright (c) 2017 Shigeyuki Azuchi
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

require './bech32'
require './segwit_addr'
require 'test/unit'

class TestBech32 < Test::Unit::TestCase

  VALID_CHECKSUM = [
      "A12UEL5L",
      "an83characterlonghumanreadablepartthatcontainsthenumber1andtheexcludedcharactersbio1tt5tgs",
      "abcdef1qpzry9x8gf2tvdw0s3jn54khce6mua7lmqqqxw",
      "11qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqc8247j",
      "split1checkupstagehandshakeupstreamerranterredcaperred2y9e3w",
  ]

  INVALID_CHECKSUM = [
      " 1nwldj5",
      "\x7F" + "1axkwrx",
      "an84characterslonghumanreadablepartthatcontainsthenumber1andtheexcludedcharactersbio1569pvx",
      "pzry9x0s0muk",
      "1pzry9x0s0muk",
      "x1b4n0q5v",
      "li1dgmt3",
      "de1lg7wt\xff",
  ]

  VALID_ADDRESS = [
      ["BC1QW508D6QEJXTDG4Y5R3ZARVARY0C5XW7KV8F3T4", "0014751e76e8199196d454941c45d1b3a323f1433bd6"],
      ["tb1qrp33g0q5c5txsp9arysrx4k6zdkfs4nce4xj0gdcccefvpysxf3q0sl5k7",
       "00201863143c14c5166804bd19203356da136c985678cd4d27a1b8c6329604903262"],
      ["bc1pw508d6qejxtdg4y5r3zarvary0c5xw7kw508d6qejxtdg4y5r3zarvary0c5xw7k7grplx",
       "5128751e76e8199196d454941c45d1b3a323f1433bd6751e76e8199196d454941c45d1b3a323f1433bd6"],
      ["BC1SW50QA3JX3S", "6002751e"],
      ["bc1zw508d6qejxtdg4y5r3zarvaryvg6kdaj", "5210751e76e8199196d454941c45d1b3a323"],
      ["tb1qqqqqp399et2xygdj5xreqhjjvcmzhxw4aywxecjdzew6hylgvsesrxh6hy",
       "0020000000c4a5cad46221b2a187905e5266362b99d5e91c6ce24d165dab93e86433"],
  ]

  INVALID_ADDRESS = [
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
  ]
  
  def test_valid_checksum
    VALID_CHECKSUM.each do |bech|
      hrp, _ = Bech32.decode(bech)
      assert_not_nil (hrp)
      pos = bech.rindex('1')
      bech = bech[0..pos] + (bech[pos + 1].ord ^ 1).chr + bech[pos+2..-1]
      hrp, _ = Bech32.decode(bech)
      assert_nil (hrp)
    end
  end

  def test_invalid_checksum
    INVALID_CHECKSUM.each do |bech|
      hrp, _ = Bech32.decode(bech)
      assert_nil (hrp)
    end
  end

  def test_valid_address
    VALID_ADDRESS.each do |addr, hex|
      segwit_addr = SegwitAddr.new(addr)
      assert_not_nil(segwit_addr.ver)
      assert_equal(hex, segwit_addr.to_scriptpubkey)
      assert_equal(addr.downcase, segwit_addr.addr)
    end
  end

  def test_invalid_address
    INVALID_ADDRESS.each do |addr|
      assert_raise(RuntimeError){SegwitAddr.new(addr)}
    end
  end

  def test_scriptpubkey=
    segwit_addr = SegwitAddr.new
    segwit_addr.hrp = 'bc'
    segwit_addr.scriptpubkey = '0014751e76e8199196d454941c45d1b3a323f1433bd6'
    assert_equal('bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4', segwit_addr.addr)
  end

end
