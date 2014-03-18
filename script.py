from protocoin.clients import BitcoinClient
from protocoin.datatypes import messages, structures, values

from db.models import Block
from script_opcodes import *

def run():
    client = TestClient("as")
    client.handshake()
    client.loop()

class TestClient(BitcoinClient):
    def __init__(self, *args, **kwargs):
        super(TestClient, self).__init__(coin='bitcoin_testnet3', *args, **kwargs)

    def on_handshake(self):
        self.send_message(messages.GetData(inventory=[structures.Inventory(
            inv_type=values.INVENTORY_TYPE["MSG_BLOCK"],
            inv_hash=int(Block.objects.get(height=0).calculate_hash(), 16),
        )]))

    def handle_block(self, header, block_message):
        print("Got genesis block: %s" % block_message)
        for tx in block_message.txns:
            for tx_out in tx.tx_out:
                print(tx_out.pk_script)
                script = Script(tx_out.pk_script)
                script.execute()

class Script(object):
    """The stack-based bitcoin script language for transaction redemption. See https://en.bitcoin.it/wiki/Script"""

    MAX_SCRIPT_DATA_SIZE = 520
    MAX_OPCODE_COUNT = 201

    def __init__(self, script):
        self.datastack = []
        self.ifstack = []
        self.chunks = []
        self.parse(script)

    def parse(self, script):
        """Parse pushed data and non-pushdata opcodes into chunks"""

        i = 0
        opcode_count = 0
        while i < len(script):
            opcode = script[i]
            i += 1

            if opcode >= 0 and opcode < OP_PUSHDATA1:
                read_length = opcode
                self.chunks.append({'type': 'data', 'value': script[i:i+read_length]})
                i += read_length
            elif opcode == OP_PUSHDATA1:
                read_length = int.from_bytes(script.read(1), byteorder='little')
                self.chunks.append({'type': 'data', 'value': script[i:i+read_length]})
                i += read_length
            elif opcode == OP_PUSHDATA2:
                read_length = int.from_bytes(script.read(2), byteorder='little')
                self.chunks.append({'type': 'data', 'value': script[i:i+read_length]})
                i += read_length
            elif opcode == OP_PUSHDATA4:
                # OP_PUSHDATA4 should never be used, as pushes over 520 bytes are not allowed, and
                # those below can be done using OP_PUSHDATA2, but we'll implement it nevertheless
                read_length = int.from_bytes(script.read(4), byteorder='little')
                self.chunks.append({'type': 'data', 'value': script[i:i+read_length]})
                i += read_length
            else:
                if opcode >= OP_NOP:
                    # Note how OP_RESERVED does not count towards the opcode limit.
                    # https://github.com/bitcoin/bitcoin/blob/0.9.0/src/script.cpp#L335
                    opcode_count += 1
                    if opcode_count > Script.MAX_OPCODE_COUNT:
                        raise ScriptException("Script contains more than the allowed %s opcodes" % Script.MAX_OPCODE_COUNT)
                self.chunks.append({'type': 'opcode', 'value': opcode})

    def execute(self):
        for chunk in self.chunks:
            if chunk['type'] == 'data':
                # Verify chunk length
                if len(chunk['value']) > Script.MAX_SCRIPT_DATA_SIZE:
                    raise ScriptException("Script pushed %s bytes of data, max is %s" % (len(chunk['value']), Script.MAX_SCRIPT_DATA_SIZE))

                stack.append(chunk['value'])
            else:
                if chunk['value'] in [OP_CAT, OP_SUBSTR, OP_LEFT, OP_RIGHT, OP_INVERT, OP_AND, OP_OR, OP_XOR, OP_2MUL,
                    OP_2DIV, OP_MUL, OP_DIV, OP_MOD, OP_LSHIFT, OP_RSHIFT]:
                    raise ScriptException("Script contains disabled operation '%s'" % chunk['value'])

                if chunk['value'] == OP_IF:
                    if len(self.stack) == 0:
                        raise ScriptException("Attempted OP_IF on empty stack")
                    self.ifstack.append(cast_to_bool(self.stack.pop()))

    def cast_to_bool(data):
        """Evaluate data to boolean. Exclude 0x80 from last byte because "Can be negative zero" -reference client.
        https://github.com/bitcoin/bitcoin/blob/0.9.0/src/script.cpp#L44"""
        return any([b != 0 for b in data[:-1]]) or (data[-1] != 0 and data[-1] != 0x80)

class ScriptException(Exception):
    """Thrown if the provided script has a syntax error or is otherwise invalid according to the Bitcoin Script rules."""
