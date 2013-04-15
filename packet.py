#!/usr/bin/python

import msgpack

class Packet:
     INFO = 1
     VM_INFO = 2
     MIGRATE = 3

     def __init__(self, header, data):
         self.header = header
         self.data = data

     def getPacketType(self):
         return self.header.packetType

     def serialize(self):
         buf = self.header.serialize() + self.data.serialize()
         return buf

     @staticmethod
     def deserialize(buf):
         unpacker = msgpack.Unpacker()
         unpacker.feed(buf)
         hbuf = unpacker.unpack()
         header = PacketHeader()
         header.packetType = hbuf[0]
         unpacker.feed(buf)
         dbuf = unpacker.unpack()
         if header.packetType == Packet.INFO:
             # unpack info
         elif header.packetType == Packet.VM_INFO:
             # unpack vm_info
         elif header.packetType == Packet.MIGRATE:
             # unpack migrate


class PacketHeader:
    # por enquanto so tem uma informacao, mas podemos querer
    # adicionar outras no futuro
    def __init__(self, packetType):
        self.packetType = packetType

    def serialize(self):
        buf = msgpack.packb([self.packetType])
        return buf

    @staticmethod
    def deserialize(buf):
        return PacketHeader(buf[0])


class Migrate:
    def __init__(self, vmName, destination):
        self.vmName = vmName
        self.destination = destination

    def serialize(self):
        return Migrate(buf[0],buf[1])






