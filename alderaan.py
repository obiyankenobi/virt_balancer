#!/usr/bin/python

# Alderaan -> http://en.wikipedia.org/wiki/Alderaan

import threading
import socket
import time
import logging
import logging.handlers

from packet import *
import util
import vmUtil


UDP_PORT = 11998
SERVER_IP = '127.0.1.1'

# define quando uma MF esta sobrecarregada
LIMIT = 20

# arquivos de log
LOG_FILENAME = 'log/alderaan.log'
LOG_EXCEL = 'log/alderaan_excel.log'

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
        log.info('Received %s from %s', pkt.toString(), addr)

        if pkt.getPacketType() == Packet.SEND_INFO:
            pktHeader = PacketHeader(Packet.INFO)
            cpu, mem, network = parasite.getInfo()
            pktData = PacketInfo(cpu,mem,network)
            pkt = Packet(pktHeader,pktData)
            sock.sendto(pkt.serialize(), (addr, UDP_PORT))
            log.info('Sent {0}'.format(pkt.toString()))
        elif pkt.getPacketType() == Packet.MIGRATE:
            parasite.setStopUpdate = True
            vmSpy.setStopUpdate = True
            migrateDict = pkt.data.migrateDict
            for addrDest in migrateDict.keys():
                vmName = migrateDict[addrDest]
                vmSpy.migrate(vmName,addrDest)
            parasite.setStopUpdate = False
            vmSpy.setStopUpdate = False



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
        log_excel = open(LOG_EXCEL,'a',1)
        log_excel.write('\n================================ Alderaan started @ {0} ================================\n'.format(
                time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))
        log_excel.write('time\t\tcpu_total\tmem_total\tnetwork_total\tcpu_inst\tmem_inst\tnetwork_inst\n')

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

                log.info('Final - CPU=%.2f,Mem=%.2f,Network=%.2f; Instant - CPU=%.2f,Mem=%.2f,Network=%.2f',
                        self.cpu,self.mem,self.network,cpu,mem,network)
                log_excel.write('{0}\t{1:.2f}\t\t{2:.2f}\t\t{3:.2f}\t\t{4:.2f}\t\t{5:.2f}\t\t{6:.2f}\n'.format(
                    time.strftime("%H:%M:%S", time.localtime()),self.cpu,self.mem,self.network,cpu,mem,network))

                # algum acima do limite?
                if (self.cpu > LIMIT or self.mem > LIMIT or self.network > LIMIT):
                    pktHeader = PacketHeader(Packet.VM_INFO)
                    pktData = PacketVMInfo(self.vmSpy.getVMInfo(),cpu,mem,network)
                    pkt = Packet(pktHeader,pktData)
                    self.socket.sendto(pkt.serialize(), (SERVER_IP, UDP_PORT))
                    log.info('Sent {0}'.format(pkt.toString()))

            time.sleep(INTERVAL)
        log_excel.close()

    def getInfo(self):
        return self.cpu, self.mem, self.network


class VMspy(threading.Thread):
    """Interface de comunicacao com as MVs."""
    def __init__(self):
        threading.Thread.__init__(self, name='VMspy')
        self.stopUpdate = False
        self.vmDict = {}
        #self.vmDict = {'yan': [32,435,432],'pedro':[89,43,65],'raquel':[98,67,789]}

    def run(self):
        log = logging.getLogger()

        # guarda os valores instantaneos capturados
        newDict = {}

        # valores passados
        oldDict = {}

        while True:
            if not self.stopUpdate:
                newDict = vmUtil.getInfoAll(vmUtil.getVMs())
                # cpu e rede sao cumulativos
                intervalDict = vmUtil.intervalDiff(newDict,oldDict)
                # guardar para a proxima iteracao
                oldDict = newDict
                # combinar os dois dicts, usando a formula do algoritmo
                self.vmDict = vmUtil.mergeDicts(intervalDict,self.vmDict,MI)
            time.sleep(INTERVAL)

    def setStopUpdate(value):
        self.stopUpdate = value

    def getVMInfo(self):
        # vmDict esta em valores absolutos
        percentDict = vmUtil.getPercents(self.vmDict,INTERVAL)
        return percentDict

    def migrate(self, vmName, destination):
        log = logging.getLogger()
        log_excel = open(LOG_EXCEL,'a',1)

        # implementar logica de migracao
        command_line =  "virsh migrate --live {0} qemu+ssh://{1}/system --persistent --undefinesource".format(vmName,destination)
        args = shlex.split(command_line)
        log.info("Starting migration with command: {0}".format(command_line))
        log_excel.write('{0} to {1} starting\n'.format(vmName,destination))
        rc = subprocess.call(args)
        if rc is 0:
            log.info("Migration successfully finished.")
            log_excel.write('{0} to {1} finished\n'.format(vmName,destination))
        else:
            log.error("Error migrating virtual machine {0} to {1}.".format(vmName,destination))
            log_excel.write('{0}: {1} to {2} error\n'.format(time.strftime("%H:%M:%S", time.localtime()),vmName,destination))
        log_excel.close()
        return rc

if __name__ == "__main__":
    main()

