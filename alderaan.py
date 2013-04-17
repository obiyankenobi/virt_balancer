#!/usr/bin/python

# Alderaan -> http://en.wikipedia.org/wiki/Alderaan

import util
import sys
import threading
import socket
import time

# a MF esta sobrecarregada e deve mandar as informacoes das MVs
# para o servidor central
overloaded = False

UDP_PORT = 11998
SERVER_IP = '127.0.1.1'

# frequencia de captura das informacoes (em segundos)
interval = 5

def main():
    global overloaded

    # alfa (constante do algoritmo)
    alfa = 0.6

    # iniciar packetListener (recebe informacoes do servidor central)
    spaceport = Spaceport()
    spaceport.start()

    # iniciar thread para monitorar MVs

    while 1:
        if not spaceport.getStopUpdate():
            # pegar percentuais atuais de CPU, memoria e rede

            # atualizar percentuais acumulados de uso da MF

            # algum deles acima do limite?
            # caso sim, habilitar envio das informacoes das MVs
            overloaded = True
            print "sending"
            spaceport.send()



        time.sleep(interval)



class Spaceport(threading.Thread):
    """ Responsavel pela comunicacao com o servidor central. """

    def __init__(self):
        threading.Thread.__init__(self)
        # essa MF esta participando de uma migracao e deve parar de capturar
        # seu uso para nao "contaminar" devido a sobrecarga da migracao
        self.stopUpdate = False

        self.sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.sock.bind(('', UDP_PORT))

    def run(self):
        while True:
            # 32KB devem ser suficientes para os nossos dados
            data, addr = self.sock.recvfrom(32768)

            print 'received message: ', data

    def getStopUpdate(self):
        return self.stopUpdate

    def send(self, Packet):
        self.sock.sendto("teste", (SERVER_IP, 11998))


if __name__ == "__main__":
    main()

