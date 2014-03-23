import sys
import inspect

from .exceptions import UnknownCommand
from datatypes.meta import BitcoinSerializable
import db.models

# All messages are subclasses of BitcoinSerializable. Most are defined in the 'datatypes.messages' module,
# and some that are saveable through the ORM are defined in 'db.models'.
MESSAGES = {}
for module in ['datatypes.messages', 'db.models']:
    MESSAGES.update({
        c.command: c \
        for name, c in inspect.getmembers(sys.modules[module])
        if inspect.isclass(c) and issubclass(c, BitcoinSerializable) and c is not BitcoinSerializable
    })

def deserialize(command, stream):
    try:
        return MESSAGES[command](stream=stream)
    except KeyError:
        raise UnknownCommand("Unknown command: %s" % command)
