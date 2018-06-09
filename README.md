# SDN_projects_Mininet_POX
containing code I Wrote in Learning and Working on Software-Defined Networking


Mytopo.py and demo.py: Done in a task of the OpenFlow Tutorial https://github.com/mininet/openflow-tutorial/wiki/Create-a-Learning-Switch. mytopo.py is a Mininet topology definition file and demo.py is a POX controller component module.

L2learningEvaluation.py: a pOX controller component that implements layer 2 learning switch logic; Python multiprocessing is used to improve the performance; when used with the POX component, "py", a user can interact with the CLI and make it switch between non-multiprocessing mode and multiprocessing mode; a user can also change the number of worker processes using the CLI; of course, you can designate these parameters when you launch the controller as well.

complexTopo.py: a Mininet topology definition file; the topology contains 23 OpenFlow switches and 2 hosts, and they are connected by 52 links; this topology works together with three POX controller components named complexEvaluation_*.py.

complexEvalution_*.py: The three files do the same thing but are implemented with different inter-process communication methods - duplex pipes, simplex pipes, or a shared queue - from Python multiprocessing library. The same thing they do is to work together with the topology mentioned above and handle any PacketIn event from any switch. I wrote this to evaluate how well multiprocessing can work in a Python-based SDN controller. A packet sent from one host to another will trigger any switch it passes to send a PacketIn message to the controller; when the controller gets the PacketIn message, it will use the Dijkstra's algorithm to compute the shortest path to the destination and instruct the switch send the packet out through the appropriate port. This component supports the same CLI interactions as l2learningEvaluation.py has, with an addition - randomly regenerating costs of the 52 links.


