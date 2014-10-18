# virt_balancer

A simple load balancer for virtual machines.

## Dependencies
- libvirt
- [MessagePack](http://msgpack.org/)

## Basic explanation

We aply black-box monitoring, so all information is obtained from the host machine. There's a central node that receives information from all hosts and decides if a migration is needed and where to migrate. 

We monitor the hosts' CPU, memory and network use. If the utilization of any of these 3 metrics is more than 90%, one of host's virtual machines is migrated to a different host. To prevent that a temporary use spike triggers a migration, exponential moving average is used to keep track of resource utilization.

The balancer doesn't aim to make all hosts have the same utilization. It just makes sure no host is over utilized (> 90% resource use). A VM being migrated can end up in a host which is not the least used among all possible destinations. This is by design, since we try to save low used hosts to receive VMs that can be very large in future migrations.

The heuristics that chooses which virtual machine to migrate and the destination host is explained in this paper: [virt_balancer](https://dl.dropboxusercontent.com/u/5539823/virt_balancer.pdf) (in portuguese).

## How to use

In every node that hosts virtual machines, run alderaan.py. In a central node (preferably not a host node), run tatooine.py.

In both these files the IP addresses of the hosts are hardcoded, so you have to change them.

## Other considerations

- For live migration to work, the VMs' disks must be available through the network to all host nodes. We used NFS for testing.

- Migration happens through SSH, so public keys need to be distributed among hosts.
