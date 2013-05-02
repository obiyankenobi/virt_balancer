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
        if packet.header.packetType == Packet.VM_INFO:
            migration = Migration(addr, packet.data.vmDict)
            migration.analyzeMigration()
            # TODO enviar pacote de request_info para todas as outras máquinas
        elif packet.header.packetType == Packet.INFO:
            # TODO receber o request_info
        else:
            raise ValueError(u'Nunca deveria entrar aqui. Erro! Header do tipo {0} na máquina central'.format(packet.header.packetType))


class Migration():
    """ Analyze a physical machine that needs migration
    """

    def __init__(self, addr, vmInfo):
        address = addr
        vmInfo = vmInfo


    def analyzeMigration(self):
    # TODO Definir quem migrar e pra onde migrar

if __name__ == "main":
    main()
