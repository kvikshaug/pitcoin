def bits_to_target(compact):
    """Takes a packed difficulty representation ("bits") and returns the decimal representation of the target hash.
    See https://en.bitcoin.it/wiki/Difficulty"""
    hex_value = "{:x}".format(compact)
    c1, c2 = int(hex_value[:2], 16), int(hex_value[2:], 16)
    return c2 * 2 ** (8 * (c1 - 3))

def target_to_bits(target):
    """Takes a target hash decimal and returns the packed compact representation ("bits").
    See https://en.bitcoin.it/wiki/Difficulty"""
    def hex_lead(val):
        h = "{:x}".format(val)
        if len(h) % 2 == 1:
            h = '0%s' % h
        return h

    base256 = "%s%s" % (hex_lead(target / 256), hex_lead(target % 256))

    if int(base256[:2], 16) > 0x7f:
        base256 = "00%s" % base256

    length = hex_lead(len(base256) / 2)
    compact = "%s%s" % (length, base256[:6])

    missing = 8 - len(compact)
    return int('%s%s' % (compact, ('0' * missing)), 16)
