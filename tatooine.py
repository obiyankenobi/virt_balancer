#!/usr/bin/python

import socket
import threading

from packet import *

UDP_PORT = 11998


def main():
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', UDP_PORT))

    analyzer = Analyzer()

    while True:
        data, addr = sock.recvfrom(32768)
        packet = Packet.deserialize(data)
        if packet.header.packetType == Packet.INFO:
            analyzer.updateInfo(addr, packet.toString())
        elif packet.header.packetType == Packet.VM_INFO:
            analyzer.VManalyze(addr, packet.toString())
        else:
            raise ValueError(u'Nunca deveria entrar aqui. Erro! Header do tipo {0} na máquina central'.format(packet.header.packetType))


class Analyzer(threading.Thread):
    # XXX Implemetar como um singleton???
    """ Just analyze data arrived from physical machines that are being used
    """

    def __init__(self):
        self.pmInfo = {}


    def updateInfo(self, addr, data):
        if self.pmInfo.has_key(addr):
            if self.pmInfo[addr][update]:
                self.updateDict(addr, data['cpu'], data['mem'], data['net'], True)
        else:
            self.updateDict(addr, data['cpu'], data['mem'], data['net'], True)


    def VManalyze(self, addr, data): 
        self.updateDict(addr, data['cpu'], data['mem'], data['net'], False)
        migration = Migration(addr, data['vmDict'])
        migration.migrate()


    def updateDict(self, addr, cpu, mem, net, update):
        self.pmInfo[addr] = {'cpu': cpu, 'mem': mem, 'net': net, 'update': update}


class Migration(threading.Thread):
    # TODO Caso Analyzer seja um singleton não precisa mudar nada aqui,
    # caso contrário tem que dar um jeito de pegar o analyzer global no init
    """ Analyze a physical machine that needs migration
    """

    def __init__(self, addr, vmInfo):
        pmAnalyzer = Analyzer()
        address = addr
        vmInfo = vmInfo


    def migrate(self):
    # TODO Definir quem migrar e pra onde migrar

if __name__ == "main":
    main()
