#!/usr/bin/python

import socket
import threading

from packet import *
from collections import OrderedDict

UDP_PORT = 11998
addresses = []
# Usado no run da thread de migração para comparar se já chegaram todos os pacotes
addresses_set = set(addresses)
pmInfo = {}

MEM_TOT = 4096

# Fórmula do custo de VM (Cobb-Douglas)
# Constantes
alfa = 0.4
beta = 0.6


def main():
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', UDP_PORT))

    while True:
        data, (addr, port) = sock.recvfrom(32768)
        packet = Packet.deserialize(data)
        if packet.header.packetType == Packet.VM_INFO:
            migration = Migration(addr, packet.data.vmDict)
            migration.start()


class Migration(threading.Thread):
    """ Analyze a physical machine that needs migration
    """

    def __init__(self, addr, vmInfo):
        threading.Thread.__init__(self, name='Migration')
        address = addr
        vmInfo = vmInfo
        migrated = False
        costDict = {}
        addr_received = set()


    def run(self):
        pktHeader = PacketHeader(Packet.SEND_INFO)
        pkt = Packet(pktHeader, None)
        # Send packet to physical machines requesting their usage informations
        for a in addresses:
            sock.sendto(pkt.serialize(), (a, UDP_PORT))
        # Receive information packets and check if have already received all
        while addr_received != addresses_set:
            data, (addr, port) = sock.recvfrom(32768)
            packet = Packet.deserialize(data)
            if packet.header.packetType == Packet.INFO:
                addr_received.add(addr)
                pmInfo[addr] = {}
                pmInfo[addr]['cpu'] = packet.data.cpu
                pmInfo[addr]['mem'] = packet.data.mem
                pmInfo[addr]['network'] = packet.data.network
        migration.analyzeMigration()


    def analyzeMigration(self):
        for k, v in vmInfo.items():
            costDict[k] = costVM(v['cpu'], v['mem'], v['network'], v['img'])

        costDict = OrderedDict(sorted(costDict.items(), key=lambda x: x[1]))
        for k, v in costDict.items():
            if self.aliviaMF(vmInfo[k]['cpu'], vmInfo[k]['mem'], vmInfo[k]['network']):
                dest = findDestination(vmInfo[k]['cpu'], vmInfo[k]['mem'], vmInfo[k]['network'])
                self.migrate([(dest, k)])
                migrated = True
        if not migrated:
            # Buscar duas a duas, depois tres a tres, até encontrar uma situação que resolva
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
        # Tá errado, tem que buscar a menor possivel que possua uma margem
        for k, v in pmInfo.items():
            if v['cpu'] + cpu < 85 and v['mem'] + mem < 85 and v['network'] + network < 85:
                return k
        return None


    def migrate(self, data_migration):
        # data_migration is an array of tuples like (addrDest, vmName)
        pktHeader = PacketHeader(Packet.MIGRATE)
        for d in data_migration:
            migrateDict = {
                d[0]: d[1],
            }
            pktData = PacketMigrate(migrateDict)
            packet = Packet(pktHeader, pktData)
            sock.sendto(packet.serialize(), (self.addr, UDP_PORT))


if __name__ == "main":
    main()
