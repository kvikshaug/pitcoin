from cStringIO import StringIO
import os

from datatypes import messages, structures
from exceptions import NodeDisconnectException, UnknownCommand, InvalidChecksum

class BitcoinBasicClient(object):
    """The base class for a Bitcoin network client, this class
    implements utility functions to create your own class.

    :param socket: a socket that supports the makefile()
                   method.
    """

    coin = "bitcoin"

    def __init__(self, socket):
        self._socket = socket
        self._buffer = StringIO()

    def close_stream(self):
        """This method will close the socket stream."""
        self._socket.close()

    def handle_message_header(self, message_header, payload):
        """This method will be called for every message before the
        message payload deserialization.

        :param message_header: The message header
        :param payload: The payload of the message
        """
        pass

    def handle_send_message(self, message_header, message):
        """This method will be called for every sent message.

        :param message_header: The header of the message
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
        self._buffer.reset()

        # Deserialize the header
        header = structures.MessageHeader()
        header.deserialize(self._buffer)
        total_length = structures.MessageHeader.calcsize() + header.length

        # If incomplete message, keep buffer and return to wait for more data
        if buffer_size < total_length:
            self._buffer.seek(0, os.SEEK_END)
            return

        payload = self._buffer.read(header.length)
        self._buffer = StringIO()
        self.handle_message_header(header, payload)

        # Verify the payload checksum
        payload_checksum = structures.MessageHeader.calc_checksum(payload)
        if payload_checksum != header.checksum:
            raise InvalidChecksum("The provided checksum '%s' doesn't match the calculated checksum '%s'" %
                (header.checksum, payload_checksum))

        # Deserialize the message
        message = messages.deserialize(header.command, StringIO(payload))
        return (header, message)

    def send_message(self, message):
        """This method will serialize the message using the
        appropriate serializer based on the message command
        and then it will send it to the socket stream.

        :param message: The message object to send
        """
        message_header = structures.MessageHeader()
        message_header.set_coin(self.coin)

        # Serialize the payload
        payload_stream = StringIO()
        message.serialize(payload_stream)
        payload = payload_stream.getvalue()
        payload_checksum = structures.MessageHeader.calc_checksum(payload)

        # Feed payload meta into the header
        message_header.command = message.command
        message_header.length = len(payload)
        message_header.checksum = payload_checksum

        # Now serialize the header
        transmission = StringIO()
        message_header.serialize(transmission)
        transmission.write(payload)

        # Cool, fire it away
        self._socket.sendall(transmission.getvalue())
        self.handle_send_message(message_header, message)

    def loop(self):
        """The main receive/send loop."""

        while True:
            try:
                data = self._socket.recv(1024*8)
                self._buffer.write(data)

                if len(data) <= 0:
                    raise NodeDisconnectException("Node disconnected.")

                data = self.read_message()
                if data is None:
                    continue

                header, message = data
                handle_func = getattr(self, "handle_%s" % header.command, None)
                if handle_func:
                    handle_func(header, message)
            except (InvalidChecksum, UnknownCommand) as e:
                pass


class BitcoinClient(BitcoinBasicClient):
    """This class implements all the protocol rules needed
    for a client to stay up in the network. It will handle
    the handshake rules as well answer the ping messages."""

    def handshake(self):
        """This method will implement the handshake of the
        Bitcoin protocol. It will send the Version message."""
        version = messages.Version()
        self.send_message(version)

    def handle_version(self, message_header, message):
        """This method will handle the Version message and
        will send a VerAck message when it receives the
        Version message.

        :param message_header: The Version message header
        :param message: The Version message
        """
        verack = messages.VerAck()
        self.send_message(verack)

    def handle_ping(self, message_header, message):
        """This method will handle the Ping message and then
        will answer every Ping message with a Pong message
        using the nonce received.

        :param message_header: The header of the Ping message
        :param message: The Ping message
        """
        pong = messages.Pong()
        pong.nonce = message.nonce
        self.send_message(pong)
