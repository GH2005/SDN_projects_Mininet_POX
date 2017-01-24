"""
a POX component for evaluation of the multiprocessing technique in design of
Python-based SDN controllers

this component works together with Mininet and complexTopo.py

there are two working modes which can be switched interactively by the user
during runtime: monoprocessing and multiprocessing

the user can also trigger a change of the costs of all links in the topo

the number of worker processes can be changed in runtime
"""

from pox.core import core
import pox.openflow.libopenflow_01 as of
import multiprocessing
import threading
import random

log = core.getLogger()


def launch(cWorkerProcesses = 1, mode = 1):
  "launch the component: construct an instance of *Evaluation*"
  
  inst = Evaluation(cWorkerProcesses, mode)
  core.openflow.addListeners(inst) # for listening to ConnectionUp and PacketIn
  core.register("evaluation", inst) # for user interaction


class Evaluation(object):
  "carrying all functionalities for this evaluation"

  def __init__(self, cWorkerProcesses, mode):
    log.info(" the *Evaluation* instance is initiating")

    # initialization of objects related to multiprocessing
    self.maxcWorkers = 0
    self.pipeReceivers = [] # at the worker process end
    self.pipeSenders = [] # at the main process end
    self.workerProcesses = []

    # semaphore
    self.sema = threading.Semaphore()

    # set the working mode
    self.change_mode(int(mode))

    # launch the thread to send openflow messages to switches
    self.msgSendingThread = threading.Thread( \
      target = msg_sending_thread_task, args = (self.pipeSenders, self.sema,))
    self.msgSendingThread.start()

    # randomly generate link costs
    self.regenerate_link_costs()

    # launch worker processes
    self.change_num_worker_processes(int(cWorkerProcesses))


  # def _handle_ConnectionUp(self, event):
  #   "add a listener to this connection"
  #   log.info(" controlling %s" % (event.connection,))
  #   event.connection.addListeners(self)
  
  def change_num_worker_processes(self, newNum):
    self.cWorkerProcesses = newNum
    self.iProcess = -1
    if newNum > self.maxcWorkers:
      # spawn new pipes and worker processes
      diff = newNum - self.maxcWorkers
      pipeEndPairs = [ multiprocessing.Pipe(duplex=True) for i in range(diff) ]
      receivers, senders = zip(*pipeEndPairs)
      newWorkers = [ multiprocessing.Process( \
        target = worker_process_task, args = (receivers[i],)) \
        for i in range(diff) ]
      for p in newWorkers:
        p.start()
      # scatter the adjacency table to the new worker processes
      # (1 --- indicating this message contains an adjacency table, the table)
      for sender in senders:
        sender.send((1, self.adjTable,))
      # append the references to self.
      self.pipeReceivers += list(receivers)
      self.pipeSenders += list(senders)
      self.workerProcesses += newWorkers
      self.maxcWorkers = newNum

    log.info(" number of active worker processes: %i" % (self.cWorkerProcesses,))
    log.info(" number of spawned worker processes: %i" % (self.maxcWorkers,))


  def _handle_PacketIn(self, event):
    "multiprocessing: send necessary information of this packet to a worker process"
    "monoprocessing: immediately compute the packet's out-port and send msg out"
    log.debug(" PacketIn event contains dpid == %i" % (event.dpid,))

    if self.mode != 1: # multiprocessing mode
      # information needed for a worker process to compute the shortest path to
      # the destination: tuple (0 --- indication that packet info is contained in 
      # this message, (source of the packet, dpid, buffer id of the packet))
      self.iProcess = (self.iProcess + 1) % self.cWorkerProcesses
      self.pipeSenders[self.iProcess].send( \
        (0, (event.parsed.src, event.dpid, event.ofp.buffer_id)) )
    else: # monoprocessing
      # acquire the info about this packet
      srcMAC, start, bufferID = event.parsed.src, event.dpid, event.ofp.buffer_id

      # Dijkstra's algorithm, computing the output port for the packet
      # preparations
      closed = { x: False for x in self.adjTable.keys() }
      d = { x: 10000 for x in self.adjTable.keys() } # 10000 is the infinite value
      pred = { x: None for x in self.adjTable.keys() } # predecessor of each node
      d[start] = 0
      cOpenNodes = len(closed)
      end = 200 if str(srcMAC) == "10:10:10:00:00:00" else 100 # the target
      # running: the distance to each other node is to be calculated
      while cOpenNodes > 0:
        # take out the node with the smallest *d*
        distance = 10000
        node = -1
        for switch, dist in d.iteritems():
          if not closed[switch] and dist < distance:
            distance = dist
            node = switch
        closed[node] = True
        cOpenNodes -= 1
        if node == end:
          break
        for neighbor, info in self.adjTable[node].iteritems():
          if closed[neighbor]:
            continue
          if distance + info[1] < d[neighbor]:
            d[neighbor] = distance + info[1]
            pred[neighbor] = node

      # extract the desired result
      succ = end
      while pred[succ] != start:
        succ = pred[succ]
      outport = self.adjTable[start][succ][0]

      # construct ofp_packet_out message 
      msg = of.ofp_packet_out()
      msg.actions.append(of.ofp_action_output(port = outport))
      msg.buffer_id = bufferID
      core.openflow.sendToDPID(start, msg)
      

  def change_mode(self, mode):
    "mode 1 - monoprocessing; mode 2 - multiprocessing "
    "works with component py; will be invoked by the user and the class"

    self.mode = mode

    # semaphore
    if mode == 1:
      self.sema.acquire()
    else:
      self.sema.release()

    log.info(" now working in %s mode" \
      % ("monoprocessing" if mode == 1 else "multiprocessing",))

  def regenerate_link_costs(self):
    "randomly assigns costs of links in topology *ComplextTopo* "
    "and distributes this information to worker processes "
    "works with component py; will be invoked by both the user and the class"

    # all dpids
    dpids = [ x + y for x in range(10, 80, 10) for y in range(1, 4) ]
    # 100 and 200 are dummy dpids to identify the two hosts
    dpids.append(100)
    dpids.append(200)
    dpids.append(1)
    dpids.append(2)

    # a collection of all links
    random.seed()
    # (dpid1, dpid2, port1, port2, link cost)
    links = [ \
      (100, 1, 1, 1, random.randint(1, 100)),

      (1, 11, 2, 1, random.randint(1, 100)),
      (1, 12, 3, 2, random.randint(1, 100)),
      (1, 13, 4, 1, random.randint(1, 100)),

      (11, 12, 2, 1, random.randint(1, 100)),
      (12, 13, 3, 2, random.randint(1, 100)),
      
      (11, 21, 4, 1, random.randint(1, 100)),
      (11, 22, 3, 2, random.randint(1, 100)),
      (12, 22, 4, 3, random.randint(1, 100)),
      (13, 22, 3, 4, random.randint(1, 100)),
      (13, 23, 4, 1, random.randint(1, 100)),

      (21, 22, 2, 1, random.randint(1, 100)),
      (22, 23, 5, 2, random.randint(1, 100)),

      (21, 31, 3, 1, random.randint(1, 100)),
      (22, 31, 8, 2, random.randint(1, 100)),
      (22, 32, 7, 2, random.randint(1, 100)),
      (22, 33, 6, 2, random.randint(1, 100)),
      (23, 33, 3, 1, random.randint(1, 100)),

      (31, 32, 3, 1, random.randint(1, 100)),
      (32, 33, 3, 3, random.randint(1, 100)),

      (31, 41, 5, 1, random.randint(1, 100)),
      (31, 42, 4, 2, random.randint(1, 100)),
      (32, 42, 4, 3, random.randint(1, 100)),
      (33, 42, 4, 4, random.randint(1, 100)),
      (33, 43, 5, 1, random.randint(1, 100)),

      (41, 42, 2, 1, random.randint(1, 100)),
      (42, 43, 5, 2, random.randint(1, 100)),

      (41, 51, 3, 1, random.randint(1, 100)),
      (42, 51, 8, 2, random.randint(1, 100)),
      (42, 52, 7, 2, random.randint(1, 100)),
      (42, 53, 6, 2, random.randint(1, 100)),
      (43, 53, 3, 1, random.randint(1, 100)),

      (51, 52, 3, 1, random.randint(1, 100)),
      (52, 53, 3, 3, random.randint(1, 100)),

      (51, 61, 5, 1, random.randint(1, 100)),
      (51, 62, 4, 2, random.randint(1, 100)),
      (52, 62, 4, 3, random.randint(1, 100)),
      (53, 62, 4, 4, random.randint(1, 100)),
      (53, 63, 5, 1, random.randint(1, 100)),

      (61, 62, 2, 1, random.randint(1, 100)),
      (62, 63, 5, 2, random.randint(1, 100)),

      (61, 71, 3, 1, random.randint(1, 100)),
      (62, 71, 8, 2, random.randint(1, 100)),
      (62, 72, 7, 2, random.randint(1, 100)),
      (62, 73, 6, 2, random.randint(1, 100)),
      (63, 73, 3, 1, random.randint(1, 100)),

      (71, 72, 3, 1, random.randint(1, 100)),
      (72, 73, 3, 3, random.randint(1, 100)),

      (71, 2, 4, 2, random.randint(1, 100)),
      (72, 2, 4, 3, random.randint(1, 100)),
      (73, 2, 4, 4, random.randint(1, 100)),

      (2, 200, 1, 1, random.randint(1, 100))
      ]

    # an adjacency table
    self.adjTable = { dpid: {} for dpid in dpids }
    for tp in links:
      # set an entry for each node on a link
      self.adjTable[tp[0]][tp[1]] = (tp[2], tp[4],) # (outport, cost)
      self.adjTable[tp[1]][tp[0]] = (tp[3], tp[4],) # (outport, cost)

    # scatter the adjacency table to worker processes
    # (1 --- indicating this message contains an adjacency table, the table)
    for sender in self.pipeSenders:
      sender.send((1, self.adjTable,))

    log.info(" link costs have been regenerated, stored and sent to workers")
    log.info(" the new adjacency table: %s" % (self.adjTable,))


def worker_process_task(pipeReceiver):
  "a worker process receives topo (including link costs) "
  "and packet information, and compute the shortest path"
  adjTable = {}
  while 1:
    # receive a message from the main process
    (indicator, content) = pipeReceiver.recv()

    # do different things for different kinds of message
    if indicator == 1: # an adjacency table is received
      adjTable = content
      print "the new adjacency table has been received by one worker"
    else: # a request to handle a packet
      # acquire the info about this packet
      (srcMAC, start, bufferID) = content

      # Dijkstra's algorithm, computing the output port for the packet
      # preparations
      closed = { x: False for x in adjTable.keys() }
      d = { x: 10000 for x in adjTable.keys() } # 10000 is the infinite value
      pred = { x: None for x in adjTable.keys() } # predecessor of each node
      d[start] = 0
      cOpenNodes = len(closed)
      end = 200 if str(srcMAC) == "10:10:10:00:00:00" else 100 # the target
      # running: the distance to each other node is to be calculated
      while cOpenNodes > 0:
        # take out the node with the smallest *d*
        distance = 10000
        node = -1
        for switch, dist in d.iteritems():
          if not closed[switch] and dist < distance:
            distance = dist
            node = switch
        closed[node] = True
        cOpenNodes -= 1
        if node == end:
          break
        for neighbor, info in adjTable[node].iteritems():
          if closed[neighbor]:
            continue
          if distance + info[1] < d[neighbor]:
            d[neighbor] = distance + info[1]
            pred[neighbor] = node

      # extract the desired result
      succ = end
      while pred[succ] != start:
        succ = pred[succ]
      outport = adjTable[start][succ][0]

      # construct ofp_packet_out message and deliver it to main proc
      msg = of.ofp_packet_out()
      msg.actions.append(of.ofp_action_output(port = outport))
      msg.buffer_id = bufferID
      pipeReceiver.send((msg, start))

def msg_sending_thread_task(senders, sema):
  "this thread identifies the switch to whom a msg is to be sent, "
  "then sends the msg"
  
  while 1:
    sema.acquire()
    for i in range(100):
      for sender in senders:
        if sender.poll(1):
          (msg, dpid,) = sender.recv()
          core.openflow.sendToDPID(dpid, msg)
    sema.release()
