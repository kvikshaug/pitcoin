#: The protocol version
PROTOCOL_VERSION = 60002

#: The network magic values
MAGIC_VALUES = {
    "bitcoin":          0xD9B4BEF9,
    "bitcoin_testnet":  0xDAB5BFFA,
    "bitcoin_testnet3": 0x0709110B,
    "namecoin":         0xFEB4BEF9,
    "litecoin":         0xDBB6C0FB,
    "litecoin_testnet": 0xDCB7C1FC
}

#: The available services
SERVICES = {
    "NODE_NETWORK": 0x1,
}

#: The type of the inventories
INVENTORY_TYPE = {
    "ERROR": 0,
    "MSG_TX": 1,
    "MSG_BLOCK": 2,
}
