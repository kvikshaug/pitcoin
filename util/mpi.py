import struct

# Thanks to ArtForz from the bitcointalk forums for these snippets.
# https://bitcointalk.org/index.php?topic=587.msg7482#msg7482
# Slightly modified for python3, and added has_length/include parameters
# See http://www.openssl.org/docs/crypto/BN_bn2bin.html for more on the MPI format

def mpi2num(m, has_length=True):
    """Convert MPI string to number. Set has_length to False if the values misses initial 4 length-bytes."""
    if has_length:
        datasize = struct.unpack(">I", m[0:4])[0]
        data_start = 4
    else:
        datasize = len(m)
        data_start = 0
    r = 0
    if datasize != 0:
        neg_flag = bool(m[data_start] & 0x80)
        r = m[data_start] & 0x7F
        for i in range(1, datasize):
            r <<= 8
            r += m[(data_start) + i]
        if neg_flag:
            r = -r
    return r

def num2mpi(n, include_length=True):
    """Convert number to MPI string. Set include_length to False to omit the initial 4 length-bytes."""
    if n == 0:
        if include_length:
            return struct.pack(">I", 0)
        else:
            return b''
    r = b""
    neg_flag = n < 0
    n = abs(n)
    while n > 0:
        r = bytes([n & 0xFF]) + r
        n >>= 8
    if r[0] & 0x80:
        r = bytes([0]) + r
    if neg_flag:
        r = bytes([r[0] | 0x80]) + r[1:]
    if include_length:
        r = struct.pack(">I", len(r)) + r
    return r
