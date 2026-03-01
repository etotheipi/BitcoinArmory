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

class SegwitAddr

  attr_accessor :hrp # human-readable part
  attr_accessor :ver # witness version
  attr_accessor :prog # witness program

  def initialize(addr = nil)
    @hrp, @ver, @prog = parse_addr(addr) if addr
  end

  def to_scriptpubkey
    v = ver == 0 ? ver : ver + 0x50
    ([v, prog.length].pack("CC") + prog.map{|p|[p].pack("C")}.join).unpack('H*').first
  end

  def scriptpubkey=(script)
    values = [script].pack('H*').unpack("C*")
    @ver = values[0]
    @prog = values[2..-1]
  end

  def addr
    encoded = Bech32.encode(hrp, [ver] + convert_bits(prog, 8, 5))
    chrp, cver, cprog = parse_addr(encoded)
    raise 'Invalid address' if chrp != hrp || cver != ver || cprog != prog
    encoded
  end

  private

  def parse_addr(addr)
    hrp, data = Bech32.decode(addr)
    raise 'Invalid address.' if hrp.nil? || data[0].nil? || (hrp != 'bc' && hrp != 'tb')
    ver = data[0]
    raise 'Invalid witness version' if ver > 16
    prog = convert_bits(data[1..-1], 5, 8, false)
    raise 'Invalid witness program' if prog.nil? || prog.length < 2 || prog.length > 40
    raise 'Invalid witness program with version 0' if ver == 0 && (prog.length != 20 && prog.length != 32)
    [hrp, ver, prog]
  end

  def convert_bits(data, from, to, padding=true)
    acc = 0
    bits = 0
    ret = []
    maxv = (1 << to) - 1
    max_acc = (1 << (from + to - 1)) - 1
    data.each do |v|
      return nil if v < 0 || (v >> from) != 0
      acc = ((acc << from) | v) & max_acc
      bits += from
      while bits >= to
        bits -= to
        ret << ((acc >> bits) & maxv)
      end
    end
    if padding
      ret << ((acc << (to - bits)) & maxv) unless bits == 0
    elsif bits >= from || ((acc << (to - bits)) & maxv) != 0
      return nil
    end
    ret
  end

end
