# Bech32 Ruby

## Usage

Require code:

```ruby
require './bech32'
require './segwit_addr'
```

### Decode

Decode Bech32-encoded data into hrp part and data part.

```ruby
hrp, data = Bech32.decode('BC1QW508D6QEJXTDG4Y5R3ZARVARY0C5XW7KV8F3T4')

# hrp is human-readable part of Bech32 format
'bc'

# data is data part of Bech32 format
[0, 14, 20, 15, 7, 13, 26, 0, 25, 18, 6, 11, 13, 8, 21, 4, 20, 3, 17, 2, 29, 3, 12, 29, 3, 4, 15, 24, 20, 6, 14, 30, 22]
```

Decode Bech32-encoded Segwit address into `SegwitAddr` instance.

```ruby
addr = 'BC1QW508D6QEJXTDG4Y5R3ZARVARY0C5XW7KV8F3T4'
segwit_addr = SegwitAddr.new(addr)

# generate script pubkey
segwit_addr.to_script_pubkey
=> 0014751e76e8199196d454941c45d1b3a323f1433bd6
```

### Encode

Encode Bech32 human-readable part and data part into Bech32 string.

```ruby
hrp = 'bc'
data = [0, 14, 20, 15, 7, 13, 26, 0, 25, 18, 6, 11, 13, 8, 21, 4, 20, 3, 17, 2, 29, 3, 12, 29, 3, 4, 15, 24, 20, 6, 14, 30, 22]

bech = Bech32.encode(hrp, data)
=> bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4
```

Encode Segwit script into Bech32 Segwit address.

```ruby
segwit_addr = SegwitAddr.new
segwit_addr.hrp = 'bc'
segwit_addr.scriptpubkey = '0014751e76e8199196d454941c45d1b3a323f1433bd6'

# generate addr
segwit_addr.addr
=> bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4
```

## Test

Run test with:

    $ ruby test_bech32.rb
