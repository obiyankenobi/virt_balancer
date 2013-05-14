#!/usr/bin/python

import libvirt
import psutil
from xml.etree import ElementTree as ET

def getAllVMs():
    """ Returns a dict with all VMs in the machine, using
    the VM name as key.
    """
    conn = libvirt.open(None)
    result = {}
    vmList = conn.listDomainsID()
    for id in vmList:
        vm = conn.lookupByID(id)
        vmName = vm.name()
        result[vmName] = vm
    vmList = conn.listDefinedDomains()
    for vmName in vmList:
        vm = conn.lookupByName(vmName)
        result[vmName] = vm
    return result


def getVMs():
    """ Returns a dict with active VMs in the machine, using
    the VM name as key.
    """
    conn = libvirt.open(None)
    result = {}
    vmList = conn.listDomainsID()
    for id in vmList:
        vm = conn.lookupByID(id)
        vmName = vm.name()
        result[vmName] = vm
    return result


def networkAllStats(vm):
    """ Returns the accumulated network usage for the domain
    as an array with the following fields:
    [rx_bytes,rx_packets,rx_errs,rx_drop,tx_bytes,tx_packets,tx_errs,tx_drop]
    """
    stats = [0] * 8

    for dev in getNetworkDevices(vm):
        stats = [(x + y) for x, y in zip(stats, vm.interfaceStats(dev))]

    return stats


def networkStats(vm):
    """ Returns only [rx_bytes,tx_bytes] """
    [rx_bytes,_,_,_,tx_bytes,_,_,_] = networkAllStats(vm)
    return [rx_bytes,tx_bytes]

def aggNetworkStats(vm):
    """ Returns aggregated network stats (rx_bytes + tx_bytes) """
    [rx_bytes,tx_bytes] = networkStats(vm)
    return rx_bytes + tx_bytes

def getNetworkDevices(dom):
    """ Returns a list of network devices used by a VM """
    #Create a XML tree from the domain XML description.
    tree=ET.fromstring(dom.XMLDesc(0))
    #The list of network device names.
    devices=[]

    #Iterate through all network interface target elements of the domain.
    for target in tree.findall("devices/interface/target"):
        #Get the device name.
        dev=target.get("dev")

        #Check if we have already found the device name for this domain.
        if not dev in devices:
            devices.append(dev)

    #Completed device name list.
    return devices


def cpuStats(vm):
    """ Returns the accumulated CPU time used in nanoseconds """
    info_cpus = vm.vcpus()[0]
    time = 0
    # info_cpus is a list with info for each VCPU in the VM, so we have
    # to iterate through all of them and sum the time.
    for info in info_cpus:
        time += info[2]
    return time


# TODO is RSS ok?
def memoryStats(vm):
    """ Value in bytes """
    # libvirt returns in kB
    return vm.memoryStats()['rss']*1000


def getInfo(vm):
    """ Returns [cpu,mem,network] for a VM """
    return [cpuStats(vm), memoryStats(vm), aggNetworkStats(vm)]


def getInfoAll(vmDict):
    """ Same as above, but for a list of VMs and using the VM name as key. """
    infoDict = {}
    for vm in vmDict.keys():
        infoDict[vm] = getInfo(vmDict[vm])
    return infoDict


def mergeDicts(newDict, oldDict, coef):
    """ Merges the two dicts using the algorithm's equation """
    auxDict = {}
    for vmName in newDict.keys():
        oldValue = oldDict.get(vmName)
        if oldValue:
            newValue = [coef*new + (1-coef)*old for new,old in zip(newDict[vmName],oldValue)]
        else:
            newValue = newDict[vmName]
        auxDict[vmName] = newValue
    return auxDict


def intervalDiff(newDict, oldDict):
    """ Get the differences between newDict and oldDict """
    finalDict = {}
    for vmName in newDict.keys():
        oldValue = oldDict.get(vmName)
        if oldValue:
            newValue = vmDiff(newDict[vmName],oldValue)
        else:
            newValue = newDict[vmName]
        finalDict[vmName] = newValue
    return finalDict


def vmDiff(newValue, oldValue):
    # Does not need the difference for memory
    return [newValue[0]-oldValue[0], newValue[1], newValue[2]-oldValue[2]]

def getPercents(vmDict, interval):
    """ Transform the dict to percentages """
    nano = 10**9 # e Gbps
    percentDict = {}
    memory = psutil.virtual_memory()[0]
    for vmName in vmDict:
        absoluteValues = vmDict[vmName]
        percentDict[vmName] = [absoluteValues[0]*100/(nano*interval), absoluteValues[1]*100/memory, absoluteValues[2]*100/(nano*interval)]
    return percentDict


def main():
    """Main for testing purposes"""
    #machine_name = 'ubuntu1'
    #vm_dict = get_vms()
    #listInfo(vm_dict)
    #print networkStats(vm_dict[machine_name])
    #print cpuStats(vm_dict[machine_name])
    #getMemStats(vm_dict[machine_name])

if __name__ == "__main__":
    main()
