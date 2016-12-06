"""Custom topology example

Two directly connected switches plus a host for each switch:

   host --- switch --- switch --- host

Adding the 'topos' dict with a key/value pair to generate our newly defined
topology enables one to pass in '--topo=mytopo' from the command line.
"""

from mininet.topo import Topo

class MyTopo( Topo ):
    "Simple topology example."

    def __init__( self ):
        "Create custom topo."

        # Initialize topology
        Topo.__init__( self )

        h1 = self.addHost('h1', ip="10.0.1.100/24", defaultRoute="via 10.0.1.1", mac="00:00:00:00:01:01")
        h2 = self.addHost('h2', ip="10.0.2.100/24", defaultRoute="via 10.0.2.1", mac="00:00:00:00:02:02")
        h3 = self.addHost('h3', ip="10.0.3.100/24", defaultRoute="via 10.0.3.1", mac="00:00:00:00:03:03")
        s1 = self.addSwitch('s1')

        self.addLink(h1, s1)
        self.addLink(h2, s1)
        self.addLink(h3, s1)

topos = { 'mytopo': ( lambda: MyTopo() ) }
