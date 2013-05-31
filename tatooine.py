#!/usr/bin/python
# -*- coding: utf-8 -*-

import socket
import threading
import itertools
import time

import logging
import logging.handlers

from packet import *
from collections import OrderedDict

UDP_PORT = 11998

# List of IP's of physical machines
# We could get this list with other methods, but this is easier for tests
addresses = []

# Used at run method of migration thread to compare if all INFO packet have already arrived
addressesSet = set(addresses)

pmInfo = {}

# Assure that a physical machine wont receive more than one VM in one migration
receiveMigration = {}

# Used to calculate VM image (MEM_TOT*mem/100.0)
MEM_TOT = 4096

# VM cost formula (Cobb-Douglas)
# Constants
alfa = 0.4
beta = 0.6

# Log file
LOG_FILENAME = 'log/tatooine.log'


def main():

    hdlr = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=4*1024*1024, backupCount=5)
    fmtr = logging.Formatter('%(asctime)s - %(threadName)s - %(funcName)s - %(levelname)s: %(message)s')
    log = logging.getLogger()
    log.setLevel(logging.DEBUG)
    log.addHandler(hdlr)
    log.info('\n================================ Tatooine started @ %s ================================\n',
            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
    hdlr.setFormatter(fmtr)

    for a in addresses:
        receiveMigration[a] = True
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', UDP_PORT))

    while True:
        data, (addr, port) = sock.recvfrom(32768)
        packet = Packet.deserialize(data)
        if packet.header.packetType == Packet.VM_INFO:
            log.info(u'Received VM_INFO packet from {0}. vmDict = {1}'.format(addr, packet.data.vmDict))
            migration = Migration(addr, packet.data.vmDict, sock)
            migration.start()
        elif packet.header.packetType == Packet.MIGRATION_FINISHED:
            for machine in packet.data.destList:
                receiveMigration[machine] = True


class Migration(threading.Thread):
    """ Analyze a physical machine that needs migration
    """

    def __init__(self, addr, vmInfo, socket):
        threading.Thread.__init__(self, name='Migration')
        self.address = addr
        # vmInfo is a dict like {'vm1': [cpu1, mem1, network1], 'vm2': [cpu2, mem2, network2]}
        self.vmInfo = vmInfo
        self.migrated = False
        self.costDict = {}
        self.addrReceived = set()
        self.sock = socket


    def run(self):
        log = logging.getLogger()
        pktHeader = PacketHeader(Packet.SEND_INFO)
        pkt = Packet(pktHeader, None)
        # Send packet to physical machines requesting their usage informations
        for a in addresses:
            self.sock.sendto(pkt.serialize(), (a, UDP_PORT))
        # Receive information packets and check if have already received all
        while self.addrReceived != addressesSet:
            data, (addr, port) = self.sock.recvfrom(32768)
            packet = Packet.deserialize(data)
            if packet.header.packetType == Packet.INFO:
                log.info(u'Received INFO packet from {0}. pmInfo = {1}'.format(addr, pmInfo))
                self.addrReceived.add(addr)
                pmInfo[addr] = {}
                pmInfo[addr]['cpu'] = packet.data.cpu
                pmInfo[addr]['mem'] = packet.data.mem
                pmInfo[addr]['network'] = packet.data.network
        self.analyzeMigration()


    def analyzeMigration(self):
        for k, v in self.vmInfo.items():
            self.costDict[k] = self.costVM(v[0], v[1], v[2], MEM_TOT*v[1]/100.0)

        arrayMV = []
        self.costDict = OrderedDict(sorted(self.costDict.items(), key=lambda x: x[1]))
        # Using itertools with dict is a problema because I lost the order, thats why the array is created
        for k, v in self.costDict.items():
            arrayMV.append(k)
        dataMigration = self.getDataMigration(arrayMV)
        if dataMigration:
            self.migrate(dataMigration)
        else:
            raise Exception(u'Doesn`t exist a combination of virtual machines that can be migrated so that the physical machine will be relieved.')


    def volumeVM(self, cpu, mem, network):
        return (1.0/(1-(cpu/100.0)))*(1.0/(1-(mem/100.0)))*(1.0/(1-(network/100.0)))


    def costVM(self, cpu, mem, network, img):
        return (self.volumeVM(cpu, mem, network)**alfa)*(img**beta)


    def relievePM(self, resource):
        # Resource is an array of tuples, used when the algorithm have to migrate more than one VM,
        # so we must check if the migration of all VM's will relieve the PM
        cpuTot = 0
        memTot = 0
        networkTot = 0
        for r in resource:
            cpuTot += r[0]
            memTot += r[1]
            networkTot += r[2]

        if pmInfo[self.address]['cpu'] - cpuTot < 85 and pmInfo[self.address]['mem'] - memTot < 85 and pmInfo[self.address]['network'] - networkTot < 85:
            return True
        return False


    def canReceiveVM(self, cpu, mem, network, address):
        # We assume that one physical machine can receive only one migrated virtual machine
        if address != self.address:
            if pmInfo[address]['cpu'] + cpu < 85 and pmInfo[address]['mem'] + mem < 85 and pmInfo[address]['network'] + network < 85:
                return True
        return False


    def findDestination(self, cpu, mem, network):
        # Chosen defines the physical machine that will receive the virtual machine migration
        chosen = {'addr': None, 'usage': 0}
        for k, v in pmInfo.items():
            if self.canReceiveVM(cpu, mem, network, k) and receiveMigration[k]:
                usage = v['cpu'] + v['mem'] + v['network'] + cpu + mem + network
                if usage > chosen['usage']:
                    chosen = {'addr': k, 'usage': usage}
        return chosen['addr']


    def migrate(self, dataMigration):
        log = logging.getLogger()
        # data_migration is an array of tuples like (addrDest, vmName)
        migrateDict = {}
        for d in dataMigration:
            migrateDict[d[0]] = d[1]
        pktHeader = PacketHeader(Packet.MIGRATE)
        pktData = PacketMigrate(migrateDict)
        packet = Packet(pktHeader, pktData)
        self.sock.sendto(packet.serialize(), (self.address, UDP_PORT))
        log.info(u'Migrate packet sent {0}'.format(dataMigration))


    def getDataMigration(self, arrayMV):
        for n in range(1, len(arrayMV)+1):
            combinations = list(itertools.combinations(arrayMV, n))
            for c in combinations:
                # Check if this combination relieves the physical machine, if True find destination for them
                cost = []
                for vm in c:
                    cost.append((self.vmInfo[vm][0], self.vmInfo[vm][1], self.vmInfo[vm][2]))
                if self.relievePM(cost):
                    addrDest = []
                    willMigrate = True
                    for vm in c:
                        addr = self.findDestination(self.vmInfo[vm][0], self.vmInfo[vm][1], self.vmInfo[vm][2])
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


if __name__ == "__main__":
    main()
