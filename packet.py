#!/usr/bin/python

import msgpack

class Packet:
    UNKNOWN = 0
    INFO = 1
    VM_INFO = 2
    MIGRATE = 3

    def __init__(self, header, data):
        self.header = header
        self.data = data

    def getPacketType(self):
        return self.header.packetType

    def toString(self):
        return self.header.toString() + ' ; ' + self.data.toString()

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
            data = PacketInfo()
            data.cpu = dbuf[0]
            data.mem = dbuf[1]
            data.network = dbuf[2]
            packet = Packet(header,data)
        elif header.packetType == Packet.VM_INFO:
            packet = Packet(header,data)
        elif header.packetType == Packet.MIGRATE:
            data = PacketMigrate()
            data.vmName = dbuf[0]
            data.destination = dbuf[1]
            packet = Packet(header,data)

        return packet



class PacketHeader:
    # por enquanto so tem uma informacao, mas podemos querer
    # adicionar outras no futuro
    def __init__(self, packetType=Packet.UNKNOWN):
        self.packetType = packetType

    def serialize(self):
        buf = msgpack.packb([self.packetType])
        return buf

    def toString(self):
        return 'PacketType={0}'.format(self.typeName())

    def typeName(self):
        if self.packetType == Packet.INFO: return 'Info'
        if self.packetType == Packet.VM_INFO: return 'VM_Info'
        if self.packetType == Packet.MIGRATE: return 'Migrate'
        return 'Unknown'


class PacketInfo:
    def __init__(self,cpu=0,mem=0,network=0):
        self.cpu = cpu
        self.mem = mem
        self.network = network

    def serialize(self):
        buf = msgpack.packb([self.cpu,self.mem,self.network])
        return buf

    def toString(self):
        return 'cpu={0},mem={1},network={2}'.format(self.cpu,self.mem,self.network)


class PacketMigrate:
    def __init__(self, vmName='', destination=''):
        self.vmName = vmName
        self.destination = destination

    def serialize(self):
        buf = msgpack.packb([self.vmName,self.destination])
        return buf

    def toString(self):
        return 'vmName={0},destination={1}'.format(self.vmName,self.destination)



