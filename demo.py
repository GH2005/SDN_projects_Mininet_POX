"""
Static router demo: pox hello world
"""

from pox.core import core
import pox.openflow.libopenflow_01 as of
import pox.lib.packet as Packet
import string
import pox.lib.addresses as Addr

log = core.getLogger()

def launch ():
    "starts the component\n"
    def start_switch (event):
        log.info("Controlling %s" % (event.connection))
        StaticRouterNoFlowmod(event.connection)
    core.openflow.addListenerByName("ConnectionUp", start_switch)

class StaticRouterNoFlowmod (object):
    "arp reply, ping reply and static routing\n"

    def __init__ (self, connection):
        self.connection = connection
        connection.addListeners(self)
        
    def resend_packet (self, packet_in, out_port):
        msg = of.ofp_packet_out()
        msg.data = packet_in
        action = of.ofp_action_output(port = out_port)
        msg.actions.append(action)
        self.connection.send(msg)

    def _handle_PacketIn (self, event):
        packet = event.parsed
        if not packet.parsed:
            log.info("Ignoring incomplete packet")
            return
        packet_in = event.ofp
        self.packet_handler(packet, packet_in)
        
    def packet_handler (self, frame, packet_in):
        "process every packet\n"

        # disposal of different kinds of packet, including a default drop
        # generates prompt text for non-data packets and all invalid packets
        isHandled = False
        if frame.type == Packet.ethernet.ARP_TYPE:
            arpPkt = frame.payload
            if arpPkt.opcode == Packet.arp.REQUEST:
                # check if the arp request has a valid target
                arp_req = arpPkt
                srcIPStr = str(arp_req.protosrc)
                prefix = srcIPStr[0:srcIPStr.rfind(".")]
                expectedIPdest = prefix + ".1"
                if expectedIPdest == str(arp_req.protodst): # a valid arp req
                    log.info("a valid arp request is got")
                    arpReply = Packet.arp()
                    macInterface = Addr.EthAddr("00:00:00:00:00:" + prefix[-1]*2)
                    arpReply.hwsrc = macInterface
                    arpReply.hwdst = arp_req.hwsrc
                    arpReply.opcode = Packet.arp.REPLY
                    arpReply.protosrc = Addr.IPAddr(expectedIPdest)
                    arpReply.protodst = arp_req.protosrc
                    
                    ether = Packet.ethernet()
                    ether.type = Packet.ethernet.ARP_TYPE
                    ether.dst = frame.src
                    ether.src = macInterface
                    ether.payload = arpReply
                    
                    msg = of.ofp_packet_out()
                    msg.data = ether
                    action = of.ofp_action_output(port = packet_in.in_port)
                    msg.actions.append(action)
                    self.connection.send(msg)

                    isHandled = True
        elif frame.type == frame.IP_TYPE:
            datagram = frame.payload
            # if it's a valid icmp echo request, reply to it
            if datagram.protocol == datagram.ICMP_PROTOCOL:
                segment = datagram.payload
                if segment.type == Packet.TYPE_ECHO_REQUEST:
                    # check if the destination IP is correct
                    dstIPStr = str(datagram.dstip)
                    if dstIPStr in self.interface_IPs:
                        log.info("an icmp request to router interfaces is got")
                        # generate a reply and send it
                        icmpReply = Packet.icmp()
                        icmpReply.type = Packet.TYPE_ECHO_REPLY
                        icmpReply.payload = segment.payload

                        ipp = Packet.ipv4()
                        ipp.protocol = ipp.ICMP_PROTOCOL
                        ipp.srcip = datagram.dstip
                        ipp.dstip = datagram.srcip

                        e = Packet.ethernet()
                        e.src = frame.dst
                        e.dst = frame.src
                        e.type = e.IP_TYPE

                        ipp.payload = icmpReply
                        e.payload = ipp

                        msg = of.ofp_packet_out()
                        msg.data = e
                        msg.actions.append(
                            of.ofp_action_output(port = packet_in.in_port))
                        self.connection.send(msg)

                        isHandled = True

            # if it's a packet sent to one of the other two hosts
            dstIPStr = str(datagram.dstip)
            if dstIPStr in self.routing_table:
                log.info("a packet between hosts is got")

                tableEntry = self.routing_table[dstIPStr]
                # # flow mod
                # msg = of.ofp_flow_mod(match = of.ofp_match.from_packet(frame))
                # msg.actions.append(
                #     of.ofp_action_dl_addr.set_src(Addr.EthAddr(tableEntry["intMAC"])))
                # msg.actions.append(
                #     of.ofp_action_dl_addr.set_dst(Addr.EthAddr(tableEntry["hostMAC"])))
                # msg.actions.append(of.ofp_action_output(port = tableEntry["port"]))
                # self.connection.send(msg)

                # log.info("a flow entry is installed")

                # modify data link src and dst
                frame.src = Addr.EthAddr(tableEntry["intMAC"])
                frame.dst = Addr.EthAddr(tableEntry["hostMAC"])

                # resend it out
                self.resend_packet(frame, tableEntry["port"])

                isHandled = True

        if not isHandled: # drop it
            log.info("an invalid frame is got")

    interface_IPs = ["10.0.1.1", "10.0.2.1", "10.0.3.1"]
    routing_table = {
        "10.0.1.100":
            { "port": 1, "intMAC": "00:00:00:00:00:11", "hostMAC": "00:00:00:00:01:01" },
        "10.0.2.100":
            { "port": 2, "intMAC": "00:00:00:00:00:22", "hostMAC": "00:00:00:00:02:02" },
        "10.0.3.100":
            { "port": 3, "intMAC": "00:00:00:00:00:33", "hostMAC": "00:00:00:00:03:03" }
    }
