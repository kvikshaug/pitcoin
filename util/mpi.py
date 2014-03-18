import struct

# Thanks to ArtForz from the bitcointalk forums for these snippets.
# https://bitcointalk.org/index.php?topic=587.msg7482#msg7482
# Slightly modified for python3.
# See http://www.openssl.org/docs/crypto/BN_bn2bin.html for more on the MPI format

def mpi2num(m):
    """convert MPI string to number"""
    datasize = struct.unpack(">I", m[0:4])[0]
    r = 0
    if datasize != 0:
        neg_flag = bool(m[4] & 0x80)
        r = m[4] & 0x7F
        for i in range(1, datasize):
            r <<= 8
            r += m[4+i]
        if neg_flag:
            r = -r
    return r

def num2mpi(n):
    """convert number to MPI string"""
    if n == 0:
        return struct.pack(">I", 0)
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
    return struct.pack(">I", len(r)) + r
