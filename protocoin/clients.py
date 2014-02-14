from cStringIO import StringIO
import os

from datatypes import messages, structures
from exceptions import NodeDisconnectException, UnknownCommand

class BitcoinBasicClient(object):
    """The base class for a Bitcoin network client, this class
    implements utility functions to create your own class.

    :param socket: a socket that supports the makefile()
                   method.
    """

    coin = "bitcoin"

    def __init__(self, socket):
        self.socket = socket
        self.buffer = StringIO()

    def close_stream(self):
        """This method will close the socket stream."""
        self.socket.close()

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

    def receive_message(self):
        """This method is called inside the loop() method to
        receive a message from the stream (socket) and then
        deserialize it."""

        # Calculate the size of the buffer
        self.buffer.seek(0, os.SEEK_END)
        buffer_size = self.buffer.tell()

        # Check if a complete header is present
        if buffer_size < structures.MessageHeader.calcsize():
            return

        # Go to the beginning of the buffer
        self.buffer.reset()

        message_header = structures.MessageHeader()
        message_header.deserialize(self.buffer)
        total_length = structures.MessageHeader.calcsize() + message_header.length

        # Incomplete message
        if buffer_size < total_length:
            self.buffer.seek(0, os.SEEK_END)
            return

        payload = self.buffer.read(message_header.length)
        self.buffer = StringIO()
        self.handle_message_header(message_header, payload)

        payload_checksum = structures.MessageHeader.calc_checksum(payload)

        # Check if the checksum is valid
        if payload_checksum != message_header.checksum:
            return (message_header, None)

        try:
            return (message_header, messages.deserialize(message_header.command, StringIO(payload)))
        except UnknownCommand:
            return (message_header, None)

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
        self.socket.sendall(transmission.getvalue())
        self.handle_send_message(message_header, message)

    def loop(self):
        """This is the main method of the client, it will enter
        in a receive/send loop."""

        while True:
            data = self.socket.recv(1024*8)

            if len(data) <= 0:
                raise NodeDisconnectException("Node disconnected.")

            self.buffer.write(data)
            data = self.receive_message()

            # Check if the message is still incomplete to parse
            if data is None:
                continue

            # Check for the header and message
            message_header, message = data
            if message is None:
                continue

            handle_func_name = "handle_" + message_header.command
            handle_func = getattr(self, handle_func_name, None)
            if handle_func:
                handle_func(message_header, message)

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
