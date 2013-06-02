import psutil
import time
import re


def getMemoryPercentage():
    return psutil.virtual_memory()[2]


def getCpuPercentage():
    return psutil.cpu_percent(None)


def getNetworkPercentage(interval, last_used_net):
    max = 10**9 # 1 Gbps
    dict = psutil.network_io_counters(pernic=True)
    used = 0
    for k, v in dict.items():
        if re.search("eth(\d+)", k):
            used += v[0] + v[1]
    return (((used-last_used_net)*8)/(max*interval))*100, used


def main():
    interval = 2
    alfa = 0.4
    last_mem = 0
    last_cpu = 0
    last_net = 0
    last_used_net = 0

    while True:
        new_percentage_net, last_used_net = get_network_percentage(interval, last_used_net)
        mem = alfa*get_memory_percentage() + (1-alfa)*last_mem
        cpu = alfa*get_cpu_percentage() + (1-alfa)*last_cpu
        net = alfa*new_percentage_net + (1-alfa)*last_net

        print "\nMEM: {0} - {1}\nCPU: {2} - {3}\nNET: {4} - {5}".format(mem, last_mem, cpu, last_cpu, net, last_net)

        last_mem = mem
        last_cpu = cpu
        last_net = net


        time.sleep(interval)

if __name__ == "__main__":
    main()
