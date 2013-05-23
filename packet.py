#!/usr/bin/python

import msgpack

class Packet:
    UNKNOWN = 0
    INFO = 1
    VM_INFO = 2
    MIGRATE = 3
    SEND_INFO = 4

    def __init__(self, header, data=None):
        self.header = header
        self.data = data

    def getPacketType(self):
        return self.header.packetType

    def toString(self):
        try:
            string = self.header.toString() + ' ; ' + self.data.toString()
        except Exception:
            # caso Packet.SEND_INFO
            string = self.header.toString()
        return string

    def serialize(self):
        try:
            buf = self.header.serialize() + self.data.serialize()
        except Exception:
            # caso Packet.SEND_INFO
            buf = self.header.serialize()
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
            data = PacketVMInfo()
            data.cpu = dbuf[0]
            data.mem = dbuf[1]
            data.network = dbuf[2]
            data.vmDict = dbuf[3]
            packet = Packet(header,data)
        elif header.packetType == Packet.MIGRATE:
            data = PacketMigrate()
            data.migrateDict = dbuf[0]
            packet = Packet(header,data)
        elif header.packetType == Packet.SEND_INFO:
            packet = Packet(header,None)

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
        if self.packetType == Packet.UNKNOWN: return 'Unknown'
        if self.packetType == Packet.INFO: return 'Info'
        if self.packetType == Packet.VM_INFO: return 'VM_Info'
        if self.packetType == Packet.MIGRATE: return 'Migrate'
        if self.packetType == Packet.SEND_INFO: return 'Send_info'
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


class PacketVMInfo:
    def __init__(self,vmDict=None,cpu=0,mem=0,network=0):
        self.vmDict = vmDict
        self.cpu = cpu
        self.mem = mem
        self.network = network

    def serialize(self):
        buf = msgpack.packb([self.cpu,self.mem,self.network,self.vmDict])
        return buf

    def toString(self):
        return 'cpu={0},mem={1},network={2},vmDict={3}'.format(self.cpu,self.mem,self.network,str(self.vmDict))


class PacketMigrate:
    def __init__(self, migrateDict=None):
        # dict com vmName:destination, podendo descrever mais de uma migracao
        self.migrateDict = migrateDict

    def serialize(self):
        buf = msgpack.packb([self.migrateDict])
        return buf

    def toString(self):
        return '{0}'.format(self.migrationDict)



