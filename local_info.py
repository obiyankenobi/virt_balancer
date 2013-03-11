import psutil
import time


def get_memory_percentage():
    return psutil.virtual_memory()[2]


def get_cpu_percentage():
    return psutil.cpu_percent(interval=1)


def get_network_percentage():
    # TODO Get percentage rather than bytes_sent or receive
    # Loopback tem que contar na hora de analisar rede?
    return psutil.network_io_counters()


def main():
    alfa = 0.4
    last_mem = 0
    last_cpu = 0
    last_net = 0
    
    while True:
        mem = alfa*get_memory_percentage() + (1-alfa)*last_mem
        cpu = alfa*get_cpu_percentage() + (1-alfa)*last_cpu
        net = alfa*get_network_percentage() + (1-alfa)*last_net

        last_mem = mem
        last_cpu = cpu
        last_net = net

        # TODO code to send data to centralized server or distributed servers

        time.sleep(300)

if __name__ == "__main__":
    main()
