from io import BytesIO
import os
import socket

from datatypes import messages, structures
from exceptions import NodeDisconnectException, UnknownCommand, InvalidChecksum

class BitcoinBasicClient(object):
    """The base class for a Bitcoin network client, this class
    implements utility functions to create your own class.

    :param seed_address: The initial node address from which we will get further node addresses
    :param seed_port: Optional port number
    :param coin: E.g. 'bitcoin', 'bitcoin_testnet3', etc. See datatypes.values.MAGIC_VALUES.
    """

    coin = "bitcoin"

    DEFAULT_PORTS = {
        'bitcoin': 8333,
        'bitcoin_testnet3': 18333,
    }

    def __init__(self, seed_address, seed_port=None, coin=None):
        if coin is not None:
            BitcoinBasicClient.coin = coin

        if seed_port is None:
            seed_port = BitcoinClient.DEFAULT_PORTS[BitcoinBasicClient.coin]

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((seed_address, seed_port))

        self._socket = sock
        self._buffer = BytesIO()

    def close_stream(self):
        """This method will close the socket stream."""
        self._socket.close()

    def handle_message_header(self, header, payload):
        """This method will be called for every message before the
        message payload deserialization.

        :param header: The message header
        :param payload: The payload of the message
        """
        pass

    def handle_send_message(self, header, message):
        """This method will be called for every sent message.

        :param header: The header of the message
        :param message: The message to be sent
        """
        pass

    def read_message(self):
        """This method is called inside the loop() method to
        receive a message from the stream (socket) and then
        deserialize it."""

        # Calculate the size of the buffer
        self._buffer.seek(0, os.SEEK_END)
        buffer_size = self._buffer.tell()

        # If a complete header isn't present, keep buffer and return to wait for more data
        if buffer_size < structures.MessageHeader.calcsize():
            return

        # Go to the beginning of the buffer
        self._buffer.seek(0, os.SEEK_SET)

        # Deserialize the header
        header = structures.MessageHeader()
        header.deserialize(self._buffer)
        total_length = structures.MessageHeader.calcsize() + header.length

        # If incomplete message, keep buffer and return to wait for more data
        if buffer_size < total_length:
            self._buffer.seek(0, os.SEEK_END)
            return

        # Read the payload and reset buffer
        payload = self._buffer.read(header.length)
        remaining_data = self._buffer.read()
        self._buffer = BytesIO(remaining_data)

        self.handle_message_header(header, payload)

        # Verify the payload checksum
        payload_checksum = structures.MessageHeader.calc_checksum(payload)
        if payload_checksum != header.checksum:
            raise InvalidChecksum("The provided checksum '%s' doesn't match the calculated checksum '%s'" %
                (header.checksum, payload_checksum))

        # Deserialize the message
        message = messages.deserialize(header.command, BytesIO(payload))
        return (header, message, len(remaining_data) > 0)

    def send_message(self, message):
        """This method will serialize the message using the
        appropriate serializer based on the message command
        and then it will send it to the socket stream.

        :param message: The message object to send
        """
        header = structures.MessageHeader()
        header.set_coin(self.coin)

        # Serialize the payload
        payload_stream = BytesIO()
        message.serialize(payload_stream)
        payload = payload_stream.getvalue()
        payload_checksum = structures.MessageHeader.calc_checksum(payload)

        # Feed payload meta into the header
        header.command = message.command
        header.length = len(payload)
        header.checksum = payload_checksum

        # Now serialize the header
        transmission = BytesIO()
        header.serialize(transmission)
        transmission.write(payload)

        # Cool, fire it away
        self._socket.sendall(transmission.getvalue())
        self.handle_send_message(header, message)

    def loop(self):
        """The main receive/send loop."""

        while True:
            try:
                data = self._socket.recv(1024*8)
                self._buffer.write(data)

                if len(data) <= 0:
                    raise NodeDisconnectException("Node disconnected.")

                # Loop while there's more data after the parsed message. The next message may be complete, in which
                # case we should read it right away instead of waiting for more data.
                while True:
                    data = self.read_message()
                    if data is None:
                        # Incomplete buffer, wait for more data
                        break

                    header, message, more_data = data
                    if hasattr(self, "handle_%s" % header.command):
                        getattr(self, "handle_%s" % header.command)(header, message)
                    if not more_data:
                        break
            except (InvalidChecksum, UnknownCommand) as e:
                pass


class BitcoinClient(BitcoinBasicClient):
    """This class implements all the protocol rules needed
    for a client to stay up in the network. It will handle
    the handshake rules as well answer the ping messages."""

    def handshake(self, callback=None):
        """Initiate the connection with a Version exchange """
        self.send_message(messages.Version())

    def handle_version(self, header, message):
        """Handle the Version message and reply with VerAck"""
        self.send_message(messages.VerAck())

    def handle_verack(self, header, message):
        self.on_handshake()

    def on_handshake(self):
        pass

    def handle_ping(self, header, message):
        """Handle the Ping message and reploy with Pong"""
        self.send_message(messages.Pong(nonce=message.nonce))
