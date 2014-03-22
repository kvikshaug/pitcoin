class NodeDisconnected(Exception):
    """This exception is thrown when Protocoin detects a
    disconnection from the node it is connected."""
    pass

class UnknownCommand(Exception):
    """Thrown when a message contains an unrecognized command"""
    pass

class InvalidChecksum(Exception):
    """Thrown when a parsed message has an invalid checksum"""
