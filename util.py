import libvirt
from xml.etree import ElementTree as ET

def get_all_vms():
    """Returns a dict with all VMs in the machine, using
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



def get_vms():
    """Returns a dict with active VMs in the machine, using
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



def list_info(vm_dict):
    for vm in vm_dict.values():
        info = vm.info()
        print "{0}: state:{1} \t maxMemory:{2} \t memory:{3} \t virCPU:{4} \t cpuTime:{5}ns ".format(vm.name(), info[0], info[1]/1024, info[2]/1024, info[3], info[4])



def network_stats(vm):
    """ Returns the accumulated network usage for the domain
    as an array with the following fields:
    [rx_bytes,rx_packets,rx_errs,rx_drop,tx_bytes,tx_packets,tx_errs,tx_drop]
    """
    stats = [0] * 8

    for dev in get_network_devices(vm):
        stats = [(x + y) for x, y in zip(stats, vm.interfaceStats(dev))]

    return stats



def get_network_devices(dom):
    """Returns a list of network devices used by a VM."""
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


# TODO Essa funcao retorna um valor de CPU diferente do vm.info().
def cpu_stats(vm):
    """ Returns the accumulated CPU time used in nanoseconds."""
    info_cpus = vm.vcpus()[0]
    time = 0
    # info_cpus is a list with info for each VCPU in the VM, so we have
    # to iterate through all of them and sum the time.
    for info in info_cpus:
        time += info[2]

    return time


# TODO nao funciona
def memory_stats(vm):
    return vm.memoryStats()



def main():
    """Main for testing purposes"""
    vm_dict = get_vms()
    list_info(vm_dict)

    print network_stats(vm_dict['ubuntu2'])
    print cpu_stats(vm_dict['ubuntu2'])
    print memory_stats(vm_dict['ubuntu2'])


if __name__ == "__main__":
    main()
