"this is a complex topology designed for evaluation of the multiprocessing technique "
"in POX, a python-based controller platform"

from mininet.topo import Topo


class ComplexTopo(Topo):
  "two hosts, 23 switches, and 52 links"

  def __init__(self):
    Topo.__init__(self)

    h1 = self.addHost('h1', ip = "10.0.0.1/24", mac = "10:10:10:00:00:00")
    h2 = self.addHost('h2', ip = "10.0.0.2/24", mac = "20:20:20:00:00:00")

    s1 = self.addSwitch('s1', dpid = "1")
    s2 = self.addSwitch('s2', dpid = "2")
    s11 = self.addSwitch('s11', dpid = "b")
    s12 = self.addSwitch('s12', dpid = "c")
    s13 = self.addSwitch('s13', dpid = "d")
    s21 = self.addSwitch('s21', dpid = "15")
    s22 = self.addSwitch('s22', dpid = "16")
    s23 = self.addSwitch('s23', dpid = "17")
    s31 = self.addSwitch('s31', dpid = "1f")
    s32 = self.addSwitch('s32', dpid = "20")
    s33 = self.addSwitch('s33', dpid = "21")
    s41 = self.addSwitch('s41', dpid = "29")
    s42 = self.addSwitch('s42', dpid = "2a")
    s43 = self.addSwitch('s43', dpid = "2b")
    s51 = self.addSwitch('s51', dpid = "33")
    s52 = self.addSwitch('s52', dpid = "34")
    s53 = self.addSwitch('s53', dpid = "35")
    s61 = self.addSwitch('s61', dpid = "3d")
    s62 = self.addSwitch('s62', dpid = "3e")
    s63 = self.addSwitch('s63', dpid = "3f")
    s71 = self.addSwitch('s71', dpid = "47")
    s72 = self.addSwitch('s72', dpid = "48")
    s73 = self.addSwitch('s73', dpid = "49")

    self.addLink(h1, s1, port2 = 1)

    self.addLink(s1, s11, port1 = 2, port2 = 1)
    self.addLink(s1, s12, port1 = 3, port2 = 2)
    self.addLink(s1, s13, port1 = 4, port2 = 1)

    self.addLink(s11, s12, port1 = 2, port2 = 1)
    self.addLink(s12, s13, port1 = 3, port2 = 2)

    self.addLink(s11, s21, port1 = 4, port2 = 1)
    self.addLink(s11, s22, port1 = 3, port2 = 2)
    self.addLink(s12, s22, port1 = 4, port2 = 3)
    self.addLink(s13, s22, port1 = 3, port2 = 4)
    self.addLink(s13, s23, port1 = 4, port2 = 1)

    self.addLink(s21, s22, port1 = 2, port2 = 1)
    self.addLink(s22, s23, port1 = 5, port2 = 2)

    self.addLink(s21, s31, port1 = 3, port2 = 1)
    self.addLink(s22, s31, port1 = 8, port2 = 2)
    self.addLink(s22, s32, port1 = 7, port2 = 2)
    self.addLink(s22, s33, port1 = 6, port2 = 2)
    self.addLink(s23, s33, port1 = 3, port2 = 1)

    self.addLink(s31, s32, port1 = 3, port2 = 1)
    self.addLink(s32, s33, port1 = 3, port2 = 3)

    self.addLink(s31, s41, port1 = 5, port2 = 1)
    self.addLink(s31, s42, port1 = 4, port2 = 2)
    self.addLink(s32, s42, port1 = 4, port2 = 3)
    self.addLink(s33, s42, port1 = 4, port2 = 4)
    self.addLink(s33, s43, port1 = 5, port2 = 1)

    self.addLink(s41, s42, port1 = 2, port2 = 1)
    self.addLink(s42, s43, port1 = 5, port2 = 2)

    self.addLink(s41, s51, port1 = 3, port2 = 1)
    self.addLink(s42, s51, port1 = 8, port2 = 2)
    self.addLink(s42, s52, port1 = 7, port2 = 2)
    self.addLink(s42, s53, port1 = 6, port2 = 2)
    self.addLink(s43, s53, port1 = 3, port2 = 1)

    self.addLink(s51, s52, port1 = 3, port2 = 1)
    self.addLink(s52, s53, port1 = 3, port2 = 3)

    self.addLink(s51, s61, port1 = 5, port2 = 1)
    self.addLink(s51, s62, port1 = 4, port2 = 2)
    self.addLink(s52, s62, port1 = 4, port2 = 3)
    self.addLink(s53, s62, port1 = 4, port2 = 4)
    self.addLink(s53, s63, port1 = 5, port2 = 1)

    self.addLink(s61, s62, port1 = 2, port2 = 1)
    self.addLink(s62, s63, port1 = 5, port2 = 2)

    self.addLink(s61, s71, port1 = 3, port2 = 1)
    self.addLink(s62, s71, port1 = 8, port2 = 2)
    self.addLink(s62, s72, port1 = 7, port2 = 2)
    self.addLink(s62, s73, port1 = 6, port2 = 2)
    self.addLink(s63, s73, port1 = 3, port2 = 1)

    self.addLink(s71, s72, port1 = 3, port2 = 1)
    self.addLink(s72, s73, port1 = 3, port2 = 3)

    self.addLink(s71, s2, port1 = 4, port2 = 2)
    self.addLink(s72, s2, port1 = 4, port2 = 3)
    self.addLink(s73, s2, port1 = 4, port2 = 4)

    self.addLink(s2, h2, port1 = 1)


topos = { 'complexTopo': (lambda: ComplexTopo()) }
