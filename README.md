# SDN_projects_Mininet_POX
containing code I wrote in learning and working on Software-defined Networking

mytopo.py and demo.py: done in a task of the Openflow Tutorial https://github.com/mininet/openflow-tutorial/wiki/Create-a-Learning-Switch. mytopo.py is a Mininet topology definition file and demo.py is a POX controller component module.

l2learningEvaluation.py: a POX controller component that implements layer 2 learning switch logic; Python multiprocessing is used to improve the performance; when used with the POX component, "py", a user can interact with the CLI and make it switch between non-multiprocessing mode and multiprocessing mode; a user can also change the number of worker processes using the CLI; of course, you can designate these parameters when you launch the controller as well.

complexTopo.py: a Mininet topology definition file; the topology contains 23 OpenFlow switches and 2 hosts, and they are connected by 52 links; this topology works together with three POX controller components named complexEvaluation_*.py.

complexEvalution_*.py: 
