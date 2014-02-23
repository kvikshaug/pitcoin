# The Base58 digits
base58_digits = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'

def base58_encode(address_bignum):
    """This function converts an address in bignum formatting
    to a string in base58, it doesn't prepend the '1' prefix
    for the Bitcoin address.

    :param address_bignum: The address in numeric format
    :returns: The string in base58
    """
    basedigits = []
    while address_bignum > 0:
        address_bignum, rem = divmod(address_bignum, 58)
        basedigits.insert(0, base58_digits[rem])
    return ''.join(basedigits)

def base58_decode(address):
    """This function converts an base58 string to a numeric
    format.

    :param address: The base58 string
    :returns: The numeric value decoded
    """
    address_bignum = 0
    for char in address:
        address_bignum *= 58
        digit = base58_digits.index(char)
        address_bignum += digit
    return address_bignum

def compact_to_target(compact):
    """Takes an 8-char hexadecimal compact and returns the decimal representation of the target hash"""
    c1, c2 = int(compact[:2], 16), int(compact[2:], 16)
    return c2 * 2 ** (8 * (c1 - 3))

def target_to_compact(target):
    """Takes a target decimal and returns the 8-char hexadecimal compact representation"""
    def hex_lead(val):
        h = '%x' % val
        if len(h) % 2 == 1:
            h = '0%s' % h
        return h

    base256 = "%s%s" % (hex_lead(target / 256), hex_lead(target % 256))

    if int(base256[:2], 16) > 0x7f:
        base256 = "00%s" % base256

    length = hex_lead(len(base256) / 2)
    compact = "%s%s" % (length, base256[:6])

    missing = 8 - len(compact)
    return '%s%s' % (compact, ('0' * missing))
