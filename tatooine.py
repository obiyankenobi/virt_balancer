#!/usr/bin/python

import socket
import threading

from packet import *
from collections import OrderedDict

UDP_PORT = 11998
addresses = []
pmInfo = {}

# Fórmula do custo de VM (Cobb-Douglas)
# Constantes
alfa = 0.4
beta = 0.6


def main():
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', UDP_PORT))

    analyzer = Analyzer()

    while True:
        data, (addr, port) = sock.recvfrom(32768)
        packet = Packet.deserialize(data)
        if packet.header.packetType == Packet.VM_INFO:
            pktHeader = PacketHeader(Packet.SEND_INFO)
            pkt = Packet(pktHeader, None)
            for a in addresses:
                sock.sendto(pkt.serialize(), (a, UDP_PORT))
            migration = Migration(addr, packet.data.vmDict)
            migration.analyzeMigration()
        elif packet.header.packetType == Packet.INFO:
            pmInfo[addr] = {}
            pmInfo[addr]['cpu'] = packet.data.cpu
            pmInfo[addr]['mem'] = packet.data.mem
            pmInfo[addr]['network'] = packet.data.network
        else:
            raise ValueError(u'Nunca deveria entrar aqui. Erro! Header do tipo {0} na máquina central'.format(packet.header.packetType))


class Migration():
    """ Analyze a physical machine that needs migration
    """

    def __init__(self, addr, vmInfo):
        address = addr
        vmInfo = vmInfo
        migrated = False
        costDict = {}


    def analyzeMigration(self):
        for k, v in vmInfo.items():
            costDict[k] = costVM(v['cpu'], v['mem'], v['network'], v['img'])

        costDict = OrderedDict(sorted(costDict.items(), key=lambda x: x[1]))
        for k, v in costDict.items():
            if self.aliviaMF(vmInfo[k]['cpu'], vmInfo[k]['mem'], vmInfo[k]['network']):
                dest = findDestination(vmInfo[k]['cpu'], vmInfo[k]['mem'], vmInfo[k]['network'])
                self.migrate(dest, k)
                migrated = True
        if not migrated:
            raise Exception(u'Ainda não foi implementado o que fazer quando não houver uma VM que alivia a máquina sobrecarregada ou uma outra máquina física para suportar essa VM. Em breve o método migrate vai suportar migrar mais de uma VM e isso será resolvido.')


    def volumeVM(self, cpu, mem, network):
        return (1.0/(1-cpu))*(1.0/(1-mem))*(1.0/(1-network))


    def costVM(self, cpu, mem, network, img):
        return (self.volumeVM(cpu, mem, network)**alfa)*(img**beta)


    def aliviaMF(self, cpu, mem, network):
        if pmInfo[self.address]['cpu'] + cpu < 85 and pmInfo[self.address]['mem'] + mem < 85 and pmInfo[self.address]['network'] + network < 85:
            return True
        return False


    def findDestination(self, cpu, mem, network):
        for k, v in pmInfo.items():
            if v['cpu'] + cpu < 85 and v['mem'] + mem < 85 and v['network'] + network < 85:
                return k
        return None


    def migrate(self, addrDest, vmName):
    # TODO Expandir método para poder realizar mais de uma migração
        pktHeader = PacketHeader(Packet.MIGRATE)
        migrateDict = {
            vmName: addrDest,
        }
        pktData = PacketMigrate(migrateDict)
        packet = Packet(pktHeader, pktData)
        sock.sendto(packet.serialize(), (self.addr, UDP_PORT))


if __name__ == "main":
    main()
