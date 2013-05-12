#!/usr/bin/python

import socket
import threading
import itertools

from packet import *
from collections import OrderedDict

UDP_PORT = 11998
addresses = []
# Used at run method of migration thread to compare if all INFO packet have already arrived
addressesSet = set(addresses)

pmInfo = {}

# Quando temos mais de uma mv para migrar, vamos considerar que escolhida a MF destino da primeira MV, a segunda não pode escolher a mesma MF?
# Essa dict garante essa condição
receiveMigration = {}

# Used to calculate VM image (MEM_TOT*mem/100.0)
MEM_TOT = 4096

# VM cost formula (Cobb-Douglas)
# Constants
alfa = 0.4
beta = 0.6


def main():

    for a in addresses:
        receiveMigration[a] = True
    
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
        addrReceived = set()


    def run(self):
        pktHeader = PacketHeader(Packet.SEND_INFO)
        pkt = Packet(pktHeader, None)
        # Send packet to physical machines requesting their usage informations
        for a in addresses:
            sock.sendto(pkt.serialize(), (a, UDP_PORT))
        # Receive information packets and check if have already received all
        while addrReceived != addressesSet:
            data, (addr, port) = sock.recvfrom(32768)
            packet = Packet.deserialize(data)
            if packet.header.packetType == Packet.INFO:
                addrReceived.add(addr)
                pmInfo[addr] = {}
                pmInfo[addr]['cpu'] = packet.data.cpu
                pmInfo[addr]['mem'] = packet.data.mem
                pmInfo[addr]['network'] = packet.data.network
        migration.analyzeMigration()


    def analyzeMigration(self):
        for k, v in vmInfo.items():
            self.costDict[k] = costVM(v['cpu'], v['mem'], v['network'], MEM_TOT*v['mem']/100.0)

        arrayMV = []
        self.costDict = OrderedDict(sorted(self.costDict.items(), key=lambda x: x[1]))
        for k, v in self.costDict.items():
            arrayMV.append(k)
        dataMigration = self.getDataMigration(arrayMV)
        if dataMigration:
            self.migrate(dataMigration)
            # Se migrate for assincrona essa linha de baixo pode causar problemas, pois a MF vai ser liberada para migração antes de acabar a sua
            for d in dataMigration:
                receiveMigration[d[0]] = True
        else:
            raise Exception(u'Doesn`t exist a combination of virtual machines that can be migrated so that the physical machine will be relieved.')


    def volumeVM(self, cpu, mem, network):
        return (1.0/(1-cpu))*(1.0/(1-mem))*(1.0/(1-network))


    def costVM(self, cpu, mem, network, img):
        return (self.volumeVM(cpu, mem, network)**alfa)*(img**beta)


    def relievePM(self, resource, address):
        # Resource is an array of tuples, used when the algorithm have to migrate more than one VM,
        # so we must check if the migration of all VM's will relieve the PM
        cpuTot = 0
        memTot = 0
        networkTot = 0
        for r in resource:
            cpuTot += r[0]
            memTot += r[1]
            networkTot += r[2]

        if pmInfo[address]['cpu'] + cpuTot < 85 and pmInfo[address]['mem'] + memTot < 85 and pmInfo[address]['network'] + networkTot < 85:
            return True
        return False


    def findDestination(self, cpu, mem, network):
        # Chosen defines the physical machine that will receive the virtual machine migration
        chosen = {'addr': None, 'usage': 0}
        for k, v in pmInfo.items():
            if self.relievePM([(cpu, mem, network)], k) and receiveMigration[k]:
                usage = v['cpu'] + v['mem'] + v['network'] + cpu + mem + network
                if usage > chosen['usage']:
                    chosen = {'addr': k, 'usage': usage}
        return chosen['addr']


    def migrate(self, dataMigration):
        # data_migration is an array of tuples like (addrDest, vmName)
        pktHeader = PacketHeader(Packet.MIGRATE)
        for d in dataMigration:
            migrateDict = {
                d[0]: d[1],
            }
            pktData = PacketMigrate(migrateDict)
            packet = Packet(pktHeader, pktData)
            sock.sendto(packet.serialize(), (self.addr, UDP_PORT))


    def getDataMigration(self, arrayMV):
        # Usar itertools com a dict diretamente é um problema, pois não fica ordenado corretamente, por isso criei um array de MV's e itero em cima dele
        for n in range(1, len(arrayMV)+1):
            combinations = list(itertools.combinations(arrayMV, n))
            for c in combinations:
                # Check if this combination relieves the physical machine, if True find destination for them
                cost = []
                for vm in c:
                    cost.append((self.costDict[vm]['cpu'], self.costDict[vm]['mem'], self.costDict[vm]['network']))
                if self.relievePM(cost, self.address):
                    addrDest = []
                    willMigrate = True
                    for vm in c:
                        addr = self.findDestination(self.costDict[vm]['cpu'], self.costDict[vm]['mem'], self.costDict[vm]['network'])
                        if addr:
                            addrDest.append(addr)
                            receiveMigration[addr] = False
                        else:
                            willMigrate = False
                            for pm in addrDest:
                                receiveMigration[pm] = True
                            break
                    if willMigrate:
                        dataMigration = []
                        for x in range(0, len(c)):
                            dataMigration.append((addrDest[x], c[x]))
                        return dataMigration
        return []


if __name__ == "main":
    main()
