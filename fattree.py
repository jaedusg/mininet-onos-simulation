import sys, time
from mininet.topo import Topo
from mininet.link import TCLink
from mininet.net import Mininet
from mininet.util import waitListening
from mininet.node import Controller, RemoteController
from mininet.node import Node
from mininet.log import setLogLevel, info
from mininet.cli import CLI


class FatTree( Topo ):

    CoreSwitches = []
    AggSwitches = []
    EdgeSwitches = []
    Hosts = []

    """
    Initialize Topology 
    """
    
    def __init__( self, k):
        self.pod = k
        self.iCoreLayerSwitch = pow((k/2),2)
        self.iAggLayerSwitch = ((k/2)*k)
        self.iEdgeLayerSwitch = ((k/2)*k)
        self.iHost = (k*pow((k/2),2))
        self.density = k/2

        # Initialize Topology
        Topo.__init__(self)
        # Create Switches Core, Aggregation, Edges
        self.createVNetwork()
        # Create Network Links with bandwidth 1000 MB
        self.createNetworkLink(1000)

    """
    Create Switch 
    """

    def createSwitch(self, numSW, prefix, switchList):
        print("\n Begin Creating Switches " + prefix)
        for s in range(1, numSW + 1):
            switchList.append(self.addSwitch(prefix + str(s)))
            print('Creating Switch: ' + prefix + str(s))
            
        print("\n End Creating Switches " + prefix) 
    
        
    """
    Create Host
    """
    
    def createHost(self, numHost):
        print("\n Begin Creating Hosts \n")
        for h in range(1, numHost + 1):
            prefix = "h_"
            self.Hosts.append(self.addHost(prefix + str(h)))
            print('Creating Host: ' + prefix + str(h))
            
        print("\n End Creating Hosts \n")    

    """
    Create Virtual Network
    """

    def createVNetwork(self):
        print("\n Begin Creating Virtual Network \n")
        self.createSwitch(self.iCoreLayerSwitch, "cs_", self.CoreSwitches)
        self.createSwitch(self.iAggLayerSwitch, "as_", self.AggSwitches)
        self.createSwitch(self.iEdgeLayerSwitch, "es_", self.EdgeSwitches)
        self.createHost(self.iHost)
        print("\n End Creating Virtual Network \n")
    

    """
    Create Network Link
    """
    def createNetworkLink(self, bandwidth):
        # bandwidth in Megabytes
        linkbw = dict(bw=bandwidth) 
        end = self.pod/2
        for x in range(0, self.iEdgeLayerSwitch):
            for y in range(0,end):
                self.addLink(self.EdgeSwitches[x], self.Hosts[end * x + y], **linkbw)

        for x in range(0, self.iAggLayerSwitch):
            for y in range(0,end):
                self.addLink(self.AggSwitches[x], self.EdgeSwitches[end * (x/end) + y], **linkbw)

        for x in range(0, self.iAggLayerSwitch, end):
            for y in range(0,end):
                for z in range(0,end):
                    self.addLink(self.CoreSwitches[y * end + z], self.AggSwitches[x + y], **linkbw)


    """
    Assign IPs for Hosts
    """
    def assignIp(network, topology):
        hosts = []
        ipSegmentFormat = "10.%d.%d.%d"
        i = 0
        end = topology.pod/2
        
        for x in range(len(topology.Hosts)):
            hosts.append(network.get(topology.Hosts[x]))
        
        for pod in range(1, topology.pod + 1):
            for edgeSwNum in range(1, end+1):
                for hostNumInSw in range(1, end+1):
                    print("pod = " + str(pod) + " / edgeSwitchNumber = " + str(edgeSwNum) + " / hostNumberInSwitch = " + str(hostNumInSw))
                    hosts[i].setIP(ipSegmentFormat % (pod, edgeSwNum, hostNumInSw))
                    print(hosts[i].IP())
                    i += 1
                


    topos = { 'fattree' : ( lambda k : FatTree(k)) }

    def createTraffic(network, topology):
        print("\n Creating Traffic \n")
        srvCommand = "iperf -s -u &"
        clCmd1 = "iperf -c "
        clCmd2 = " -u -b "
        clCmd3 = "m -t 120 &"
        for bw in range(100, 1000, 100):
            print('bandwidth: ' + bw)
            for i in range(topology.iHost//2):
                destination = network.hosts[2 * i + 1]
                # Create the server command and execute it
                destination.cmd(srvCommand)
                source = network.hosts[i]
                print("IP Source: " + str(source.IP()) + " >> " + " IP Destination: " + str(destination.IP()))
                # Create the client command and execute it
                clCmd = clCmd1 + str(destination.IP()) + clCmd2 + str(bw) + clCmd3
                source.cmd(clCmd)
            time.sleep(120)

    def runSimulation(k, traffic):
        "Create Fat Tree network"
        mn_topo = FatTree(k)
        # Create a remote controller object in local host
        RemoteCon = RemoteController("c0", ip="127.0.0.1")
        network = Mininet(topo=mn_topo, link = TCLink, controller=RemoteCon) 
        network.start()
        # Assign IP addresses.
        assignIp(network, mn_topo)
        print("k: " + str(k) + " , " + "traffic: " + traffic)
        if (traffic == "traffic"):
            # Ping all
            network.pingAll()
            time.sleep(15)
            # Traffic generation
            createTraffic(network, mn_topo)
        else:
            # CLI running
            CLI(network)
        network.stop()
        
    

    if __name__ == '__main__':
        setLogLevel('info')
        if (len(sys.argv) != 3):
            print("your command must have following structure : sudo python fattreevnetwork.py k traffic/notraffic")
        else: 
            runSimulation(int(sys.argv[1]), sys.argv[2])
