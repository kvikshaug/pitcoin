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
    MAX_SCRIPTNUM_SIZE = 4

    def __init__(self, script):
        self.datastack = []
        self.altstack = [] # Alternative data stack
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

            # Handles the current flow control (execute or not)
            execute = False not in self.ifstack

            if chunk['type'] == 'data':
                # Verify chunk length
                if len(chunk['value']) > Script.MAX_SCRIPT_DATA_SIZE:
                    raise ScriptException("Script pushed %s bytes of data, max is %s" % (len(chunk['value']), Script.MAX_SCRIPT_DATA_SIZE))

                if not execute:
                    continue

                self.datastack.append(chunk['value'])
            else:
                if chunk['value'] in [OP_CAT, OP_SUBSTR, OP_LEFT, OP_RIGHT, OP_INVERT, OP_AND, OP_OR, OP_XOR, OP_2MUL,
                    OP_2DIV, OP_MUL, OP_DIV, OP_MOD, OP_LSHIFT, OP_RSHIFT]:
                    raise ScriptException("Script contains disabled operation '%s'" % chunk['value'])

                #
                # FLOW CONTROL
                #

                if chunk['value'] == OP_IF:
                    if not execute:
                        # Append an irrelevant value to the flow control stack to keep track of nesting
                        self.ifstack.append(False)
                        continue
                    if len(self.stack) == 0:
                        raise ScriptException("Script attempted OP_IF on empty stack")
                    self.ifstack.append(cast_to_bool(self.stack.pop()))
                    continue

                elif chunk['value'] == OP_NOTIF:
                    if not execute:
                        # Append an irrelevant value to the flow control stack to keep track of nesting
                        self.ifstack.append(False)
                        continue
                    if len(self.stack) == 0:
                        raise ScriptException("Script attempted OP_NOTIF on empty stack")
                    self.ifstack.append(not cast_to_bool(self.stack.pop()))
                    continue

                elif chunk['value'] == OP_ELSE:
                    if len(self.ifstack) == 0:
                        raise ScriptException("Script attempted OP_ELSE on empty if-stack")
                    self.ifstack.append(not ifstack.pop())
                    continue

                elif chunk['value'] == OP_ENDIF:
                    if len(self.ifstack) == 0:
                        raise ScriptException("Script attempted OP_ENDIF on empty if-stack")
                    self.ifstack.pop()
                    continue

                if not execute:
                    # Done with control operations and not executing. Skip ahead to next operation
                    continue

                #
                # PUSH VALUE
                #

                if chunk['value'] == OP_1NEGATE:
                    self.datastack.add(int_to_scriptnum(-1))
                    continue

                if chunk['value'] >= OP_1 and chunk['value'] <= OP_16:
                    push_value = chunk['value'] + 1 - OP_1 # 1 for OP_1, 2 for OP_2, ..., 16 for OP_16
                    self.datastack.add(int_to_scriptnum(push_value))
                    continue

                #
                # NOPES
                #

                if chunk['value'] in [OP_NOP, OP_NOP1, OP_NOP2, OP_NOP3, OP_NOP4, OP_NOP5, OP_NOP6, OP_NOP7, OP_NOP8,
                    OP_NOP9, OP_NOP10]:
                    continue

                #
                # VERIFICATION
                #

                if chunk['value'] == OP_VERIFY:
                    if len(self.datastack) < 1:
                        raise ScriptException("Script attempted OP_VERIFY on empty stack")
                    if not cast_to_bool(self.datastack.pop()):
                        raise ScriptFailure("OP_VERIFY failed")

                if chunk['value'] == OP_RETURN:
                    raise ScriptFailure("Script used OP_RETURN")

                #
                # STACK OPERATIONS
                #

                if chunk['value'] == OP_TOALTSTACK:
                    if len(self.datastack) < 1:
                        raise ScriptException("Script attempted OP_TOALTSTACK on empty stack")
                    self.altstack.append(self.datastack.pop())
                    continue

                if chunk['value'] == OP_FROMALTSTACK:
                    if len(self.altstack) < 1:
                        raise ScriptException("Script attempted OP_FROMALTSTACK on empty stack")
                    self.datastack.append(self.altstack.pop())
                    continue

                if chunk['value'] == OP_2DROP:
                    if len(self.datastack) < 2:
                        raise ScriptException("Script attempted OP_2DROP on too small stack")
                    self.datastack.pop()
                    self.datastack.pop()
                    continue

                if chunk['value'] == OP_2DUP:
                    if len(self.datastack) < 2:
                        raise ScriptException("Script attempted OP_2DUP on too small stack")
                    self.datastack.append(self.datastack[-2])
                    self.datastack.append(self.datastack[-2])
                    continue

                if chunk['value'] == OP_3DUP:
                    if len(self.datastack) < 3:
                        raise ScriptException("Script attempted OP_3DUP on too small stack")
                    self.datastack.append(self.datastack[-3])
                    self.datastack.append(self.datastack[-3])
                    self.datastack.append(self.datastack[-3])
                    continue

                if chunk['value'] == OP_2OVER:
                    if len(self.datastack) < 4:
                        raise ScriptException("Script attempted OP_2OVER on too small stack")
                    self.datastack.append(self.datastack[-4])
                    self.datastack.append(self.datastack[-4])
                    continue

                if chunk['value'] == OP_2ROT:
                    if len(self.datastack) < 6:
                        raise ScriptException("Script attempted OP_2ROT on too small stack")
                    self.datastack.append(self.datastack.pop(-6))
                    self.datastack.append(self.datastack.pop(-6))
                    continue

                if chunk['value'] == OP_2SWAP:
                    if len(self.datastack) < 4:
                        raise ScriptException("Script attempted OP_2SWAP on too small stack")
                    self.datastack.insert(len(self.datastack) - 4, self.datastack.pop())
                    self.datastack.insert(len(self.datastack) - 4, self.datastack.pop())
                    continue

                if chunk['value'] == OP_IFDUP:
                    if len(self.datastack) < 1:
                        raise ScriptException("Script attempted OP_2ROT on empty stack")
                    if cast_to_bool(self.datastack[-1]):
                        self.datastack.append(self.datastack[-1])
                    continue

                if chunk['value'] == OP_DEPTH:
                    self.datastack.append(int_to_scriptnum(len(self.datastack)))
                    continue

                if chunk['value'] == OP_DROP:
                    if len(self.datastack) < 1:
                        raise ScriptException("Script attempted OP_DROP on empty stack")
                    self.datastack.pop()
                    continue

                if chunk['value'] == OP_DUP:
                    if len(self.datastack) < 1:
                        raise ScriptException("Script attempted OP_DUP on empty stack")
                    self.datastack.append(self.datastack[-1])
                    continue

                if chunk['value'] == OP_NIP:
                    if len(self.datastack) < 2:
                        raise ScriptException("Script attempted OP_NIP on too small stack")
                    self.datastack.pop(-2)
                    continue

                if chunk['value'] == OP_OVER:
                    if len(self.datastack) < 2:
                        raise ScriptException("Script attempted OP_OVER on too small stack")
                    self.datastack.append(self.datastack[-2])
                    continue

                if chunk['value'] == OP_PICK:
                    if len(self.datastack) < 2:
                        raise ScriptException("Script attempted OP_PICK on too small stack")
                    n = scriptnum_to_int(self.datastack.pop())
                    if n < 0 or n > len(self.datastack):
                        raise ScriptException("OP_PICK at index %s on too small stack" % n)
                    self.datastack.append(self.datastack[(n + 1) * -1])
                    continue

                if chunk['value'] == OP_ROLL:
                    if len(self.datastack) < 2:
                        raise ScriptException("Script attempted OP_ROLL on too small stack")
                    n = scriptnum_to_int(self.datastack.pop())
                    if n < 0 or n > len(self.datastack):
                        raise ScriptException("OP_ROLL at index %s on too small stack" % n)
                    self.datastack.append(self.datastack.pop((n + 1) * -1))
                    continue

                if chunk['value'] == OP_ROT:
                    if len(self.datastack) < 3:
                        raise ScriptException("Script attempted OP_ROT on too small stack")
                    self.datastack.append(self.datastack.pop(-3))
                    continue

                if chunk['value'] == OP_SWAP:
                    if len(self.datastack) < 2:
                        raise ScriptException("Script attempted OP_SWAP on too small stack")
                    self.datastack.append(self.datastack.pop(-2))
                    continue

                if chunk['value'] == OP_TUCK:
                    if len(self.datastack) < 2:
                        raise ScriptException("Script attempted OP_TUCK on too small stack")
                    self.datastack.insert(len(self.datastack) - 2, self.datastack[-1])
                    continue

                if chunk['value'] == OP_SIZE:
                    if len(self.datastack) < 1:
                        raise ScriptException("Script attempted OP_SIZE on empty stack")
                    self.datastack.push(int_to_scriptnum(len(self.datastack[-1])))
                    continue

    def cast_to_bool(data):
        """Evaluate data to boolean. Exclude 0x80 from last byte because "Can be negative zero" -reference client.
        https://github.com/bitcoin/bitcoin/blob/0.9.0/src/script.cpp#L44"""
        return any([b != 0 for b in data[:-1]]) or (data[-1] != 0 and data[-1] != 0x80)

    def int_to_scriptnum(num):
        """Convert an integer to the interesting number format used in Script. See https://en.bitcoin.it/wiki/Script"""
        return num2mpi(num, include_length=False)[::-1]

    def scriptnum_to_int(snum):
        """Convert the interesting number format used in Script to an integer. See https://en.bitcoin.it/wiki/Script"""
        if len(snum) > MAX_SCRIPTNUM_SIZE:
            # See https://github.com/bitcoin/bitcoin/blob/0.9.0/src/script.cpp#L38
            raise ScriptException("Script tried to use an integer larger than %s bytes" % MAX_SCRIPTNUM_SIZE)
        return mpi2num(snum[::-1], has_length=False)

class ScriptFailure(Exception):
    """Thrown if a valid operation caused the script to fail verification."""

class ScriptException(ScriptFailure):
    """Thrown if the provided script has a syntax error or is otherwise invalid according to the Bitcoin Script rules."""
