class NodeDisconnectException(Exception):
    """This exception is thrown when Protocoin detects a
    disconnection from the node it is connected."""
    pass

class UnknownCommand(Exception):
    """Thrown when a message contains an unrecognized command"""
    pass
