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

# Quando temos mais de uma mv para migrar, vamos considerar que escolhida a MF destino da primeira MV, a segunda não pode escolher a mesma MF?
# Essa dict garante essa condição
receive_migration = {}

MEM_TOT = 4096

# Fórmula do custo de VM (Cobb-Douglas)
# Constantes
alfa = 0.4
beta = 0.6


def main():

    for a in addresses:
        receive_migration[a] = True
    
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
            if self.aliviaMF(vmInfo[k]['cpu'], vmInfo[k]['mem'], vmInfo[k]['network'], self.address):
                dest = findDestination(vmInfo[k]['cpu'], vmInfo[k]['mem'], vmInfo[k]['network'])
                if dest:
                    self.migrate([(dest, k)])
                    migrated = True
                    break
                else:
                    raise Exception(u'Não temos nenhuma máquina física que suporta essa MV. O que fazer? Escolher outra?')
        if not migrated:
            # Buscar duas a duas, depois tres a tres, até encontrar uma situação que resolva
            raise Exception(u'Ainda não foi implementado o que fazer quando não houver uma VM que alivia a máquina sobrecarregada ou uma outra máquina física para suportar essa VM. Em breve o método migrate vai suportar migrar mais de uma VM e isso será resolvido.')


    def volumeVM(self, cpu, mem, network):
        return (1.0/(1-cpu))*(1.0/(1-mem))*(1.0/(1-network))


    def costVM(self, cpu, mem, network, img):
        return (self.volumeVM(cpu, mem, network)**alfa)*(img**beta)


    def aliviaMF(self, cpu, mem, network, address):
        if pmInfo[address]['cpu'] + cpu < 85 and pmInfo[address]['mem'] + mem < 85 and pmInfo[address]['network'] + network < 85:
            return True
        return False


    def findDestination(self, cpu, mem, network):
        # Chosen defines the physical machine that will receive the virtual machine migration
        chosen = {'addr': None, 'usage': 0}
        for k, v in pmInfo.items():
            if self.aliviaMF(cpu, mem, network, k) and receive_migration[k]:
                usage = v['cpu'] + v['mem'] + v['network'] + cpu + mem + network
                if usage > chosen['usage']:
                    chosen = {'addr': k, 'usage': usage}
        return chosen['addr']


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
