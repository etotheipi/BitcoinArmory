// Copyright (c) 2017 Pieter Wuille
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

var bech32_ecc = require('./bech32_ecc');

module.exports = {
  check: check
};

function convertbits (data, frombits, tobits, pad) {
  var acc = 0;
  var bits = 0;
  var ret = [];
  var maxv = (1 << tobits) - 1;
  for (var p = 0; p < data.length; ++p) {
    var value = data[p];
    if (value < 0 || (value >> frombits) !== 0) {
      return null;
    }
    acc = (acc << frombits) | value;
    bits += frombits;
    while (bits >= tobits) {
      bits -= tobits;
      ret.push((acc >> bits) & maxv);
    }
  }
  if (pad) {
    if (bits > 0) {
      ret.push((acc << (tobits - bits)) & maxv);
    }
  } else if (bits >= frombits || ((acc << (tobits - bits)) & maxv)) {
    return null;
  }
  return ret;
}

function check (addr, validHrp) {
  if (addr.length < 14) {
    return {error:"Too short", pos:null};
  }
  if (addr.length > 74) {
    return {error:"Too long", pos:null};
  }
  if ((addr.length % 8) == 0 || (addr.length % 8) == 3 || (addr.length % 8) == 5) {
    return {error:"Invalid length", pos:null};
  }
  var dec = bech32_ecc.check(addr, validHrp);
  if (dec.error !== null) {
    return {error:dec.error, pos:dec.pos};
  }
  var res = convertbits(dec.data.slice(1), 5, 8, false);
  if (res === null) {
    return {error:"Padding error", pos:[addr.length - 6]};
  }
  if (res.length < 2 || res.length > 40) {
    return {error:"Invalid witness program length", pos:null};
  }
  if (dec.data[0] > 16) {
    return {error:"Invalid witness version", pos:[dec.hrp.length + 1]};
  }
  if (dec.data[0] === 0 && res.length !== 20 && res.length !== 32) {
    return {error:"Invalid witness program length for v0", pos:null};
  }
  return {error:null, version:dec.data[0], program:res};
}
