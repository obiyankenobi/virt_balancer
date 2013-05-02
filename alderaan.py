#!/usr/bin/python

# Alderaan -> http://en.wikipedia.org/wiki/Alderaan

import threading
import socket
import time
import logging
import logging.handlers

from packet import *
import util


UDP_PORT = 11998
SERVER_IP = '127.0.1.1'

# define quando uma MF esta sobrecarregada
LIMIT = 90

# arquivo de log
LOG_FILENAME = 'log/alderaan.log'

# frequencia de captura das informacoes (em segundos)
INTERVAL = 5

# mi (constante do algoritmo)
MI = 0.6


def main():
    global overloaded

    # configuracao do log
    hdlr = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=4*1024*1024, backupCount=5)
    fmtr = logging.Formatter('%(asctime)s - %(threadName)s - %(funcName)s - %(levelname)s: %(message)s')
    log = logging.getLogger()
    log.setLevel(logging.DEBUG)
    log.addHandler(hdlr)
    log.info('\n================================ Alderaan started @ %s ================================\n',
            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
    hdlr.setFormatter(fmtr)


    sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    sock.bind(('', UDP_PORT))

    vmSpy = VMspy()
    vmSpy.start()
    parasite = Parasite(sock, vmSpy)
    parasite.start()


    while True:
        # 32KB devem ser suficientes para os nossos dados
        data, (addr,port) = sock.recvfrom(32768)

        pkt = Packet.deserialize(data)
        log.info('received %s from %s', pkt.toString(), addr)

        if pkt.getPacketType() == Packet.SEND_INFO:
            pktHeader = PacketHeader(Packet.INFO)
            cpu, mem, network = parasite.getInfo()
            pktData = PacketInfo(cpu,mem,network)
            pkt = Packet(pktHeader,pktData)
            sock.sendto(pkt.serialize(), (addr, UDP_PORT))
            log.info('Sent {0}'.format(pkt.toString()))




class Parasite(threading.Thread):
    """Monitora os recursos da maquina fisica."""
    def __init__(self, socket, vmSpy):
        threading.Thread.__init__(self, name='Parasite')
        self.stopUpdate = False
        self.socket = socket
        self.vmSpy = vmSpy
        self.cpu = 0
        self.mem = 0

    def setStopUpdate(value):
        self.stopUpdate = value

    def run(self):
        log = logging.getLogger()

        # Inicializacao das variaveis, para que a media nao seja feita
        # com os valores iniciais zerados, o que causaria uma distorcao
        # TODO solucao mais 'elegante'
        _, network_last = util.getNetworkPercentage(1, 0)
        time.sleep(INTERVAL)
        self.cpu = util.getCpuPercentage()
        self.mem = util.getMemoryPercentage()
        self.network, network_last = util.getNetworkPercentage(INTERVAL, network_last)
        time.sleep(INTERVAL)

        while True:
            if not self.stopUpdate:
                # valores instantaneos
                cpu = util.getCpuPercentage()
                mem = util.getMemoryPercentage()
                network, network_last = util.getNetworkPercentage(INTERVAL, network_last)

                # valores acumulados
                self.cpu = MI*cpu + (1-MI)*self.cpu
                self.mem = MI*mem + (1-MI)*self.mem
                self.network = MI*network + (1-MI)*self.network

                log.info('Acumulado - CPU=%.2f,Mem=%.2f,Network=%.2f; Instantaneo - CPU=%.2f,Mem=%.2f,Network=%.2f',
                        self.cpu,self.mem,self.network,cpu,mem,network)

                # algum acima do limite?
                if (self.cpu > LIMIT or self.mem > LIMIT or self.network > LIMIT):
                    pktHeader = PacketHeader(Packet.VM_INFO)
                    pktData = PacketVMInfo(self.vmSpy.getVMInfo(),cpu,mem,network)
                    pkt = Packet(pktHeader,pktData)
                    self.socket.sendto(pkt.serialize(), (SERVER_IP, UDP_PORT))
                    log.info('Sent {0}'.format(pkt.toString()))

            time.sleep(INTERVAL)

    def getInfo(self):
        return self.cpu, self.mem, self.network


class VMspy(threading.Thread):
    """Interface de comunicacao com as MVs."""
    def __init__(self):
        threading.Thread.__init__(self, name='VMspy')
        self.stopUpdate = False
        #self.vmDict = {}
        self.vmDict = {'yan': [32,435,432],'pedro':[89,43,65],'raquel':[98,67,789]}
        self.libvirtConn = None

    def run(self):
        log = logging.getLogger()
        while True:
            if not self.stopUpdate:
                # atualizar valores
                valor = 1

            time.sleep(INTERVAL)

    def setStopUpdate(value):
        self.stopUpdate = value

    def getVMInfo(self):
        return self.vmDict

    def migrate(self, vmName, destination):
        self.stopUpdate = True
        # implementar logica de migracao


if __name__ == "__main__":
    main()

