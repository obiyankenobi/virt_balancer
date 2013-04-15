#!/usr/bin/python

import util
import sys
import thread
import socket
import time
import msgpack

# a MF esta sobrecarregada e deve mandar as informacoes das MVs
# para o servidor central
overloaded = False

# essa MF esta participando de uma migracao e deve parar de capturar
# seu uso para nao "contaminar" devido a sobrecarga da migracao
stopUpdate = False

UDP_PORT = 11998


def main():
    global overloaded

    # frequencia de captura das informacoes (em segundos)
    interval = 5

    # alfa (constante do algoritmo)
    alfa = 0.6

    # iniciar packetListener (recebe informacoes do servidor central)
    thread.start_new_thread(packetListener, ())

    # iniciar thread para monitorar MVs

    while 1:
        if not stopUpdate:
            # pegar percentuais atuais de CPU, memoria e rede

            # atualizar percentuais acumulados de uso da MF

            # algum deles acima do limite?
            # caso sim, habilitar envio das informacoes das MVs
            overloaded = True

        time.sleep(interval)



def packetListener():
    global stopUpdate

    sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    sock.bind(('', UDP_PORT))

    while True:
        print 'waiting'
        # 32768 deve ser suficiente para os nossos dados
        data, addr = sock.recvfrom(32768)

        print 'received message: ', data




if __name__ == "__main__":
    main()

