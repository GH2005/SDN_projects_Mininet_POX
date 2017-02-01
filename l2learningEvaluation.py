"""
a POX component for evaluation of the multiprocessing technique in design of
Python-based SDN controllers
this component works together with Mininet; you can also use cbench
there are two working modes which can be switched interactively by the user
during runtime: monoprocessing and multiprocessing
the number of worker processes can be changed in runtime
"""

from pox.core import core
import pox.openflow.libopenflow_01 as of
import multiprocessing
import threading

log = core.getLogger()


def launch(cWorkerProcesses = 1, mode = 1, add = 0):
  "launch the component: construct an instance of *Evaluation*"
  
  inst = Evaluation(cWorkerProcesses, mode, add)
  core.openflow.addListeners(inst) # for listening to ConnectionUp and PacketIn
  core.register("evaluation", inst) # for user interaction


class Evaluation(object):
  "carrying all functionalities for this evaluation"

  def __init__(self, cWorkerProcesses, mode, add):
    log.info(" the *Evaluation* instance is initiating")

    # initialization of objects related to multiprocessing
    self.maxcWorkers = 0
    self.g1Receivers = []
    self.g1Senders = []
    self.g2Receivers = []
    self.g2Senders = []
    self.workerProcesses = []

    self.add = int(add)

    # semaphore
    self.sema = threading.Semaphore()

    # set the working mode
    self.change_mode(int(mode))

    # launch the thread to send openflow messages to switches
    self.msgSendingThread = threading.Thread( \
      target = msg_sending_thread_task, args = (self.g2Receivers, self.sema,))
    self.msgSendingThread.start()

    # launch worker processes
    self.change_num_worker_processes(int(cWorkerProcesses))

    # forwading tables
    self.forwardingTables = {}
  
  def change_num_worker_processes(self, newNum):
    self.cWorkerProcesses = newNum
    self.iProcess = -1
    if newNum > self.maxcWorkers:
      # spawn new pipes and worker processes
      diff = newNum - self.maxcWorkers
      newG1PipePairs = [ multiprocessing.Pipe(duplex=False) for i in range(diff) ]
      newG2PipePairs = [ multiprocessing.Pipe(duplex=False) for i in range(diff) ]
      newG1Receivers, newG1Senders = zip(*newG1PipePairs)
      newG2Receivers, newG2Senders = zip(*newG2PipePairs)
      newWorkers = [ multiprocessing.Process( \
        target = worker_process_task, args = (newG1Receivers[i], newG2Senders[i], self.add)) \
        for i in range(diff) ]
      for p in newWorkers:
        p.start()

      # append the references to self.
      self.g1Receivers += list(newG1Receivers)
      self.g1Senders += list(newG1Senders)
      self.g2Receivers += list(newG2Receivers)
      self.g2Senders += list(newG2Senders)
      self.workerProcesses += newWorkers
      self.maxcWorkers = newNum

    log.info(" number of active worker processes: %i" % (self.cWorkerProcesses,))
    log.info(" number of spawned worker processes: %i" % (self.maxcWorkers,))


  def _handle_PacketIn(self, event):
    "multiprocessing: send necessary information of this packet to a worker process"
    "monoprocessing: immediately compute the packet's out-port and send msg out"
    log.debug(" PacketIn event contains dpid == %i" % (event.dpid,))

    if self.mode != 1: # multiprocessing mode
      self.iProcess = (self.iProcess + 1) % self.cWorkerProcesses
      self.g1Senders[self.iProcess].send( \
        (event.dpid, event.parsed.src, event.parsed.dst, event.port, event.ofp.buffer_id,) )
    else: # monoprocessing
      if event.dpid not in self.forwardingTables:
        self.forwardingTables[event.dpid] = {}
      table = self.forwardingTables[event.dpid]
      frame = event.parsed
      table[frame.src] = event.port
      load = 0
      for i in range(self.add):
        load += 1
      if frame.dst in table:
        outPort = table[frame.dst]
      else:
        outPort = of.OFPP_ALL

      # construct ofp_packet_out message 
      msg = of.ofp_packet_out()
      msg.actions.append(of.ofp_action_output(port = outPort))
      msg.in_port = event.port
      msg.buffer_id = event.ofp.buffer_id
      msg.data = None
      core.openflow.sendToDPID(event.dpid, msg)
      

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


def worker_process_task(g1Receiver, g2Sender, add):
  forwardingTables = {}
  while 1:
    (dpid, src, dst, inPort, bufferID,) = g1Receiver.recv()
    if dpid not in forwardingTables:
      forwardingTables[dpid] = {}
    table = forwardingTables[dpid]
    table[src] = inPort
    load = 0
    for i in range(add):
      load += 1
    if dst in table:
      outPort = table[dst]
    else:
      outPort = of.OFPP_ALL
    # construct ofp_packet_out message and deliver it to main proc
    msg = of.ofp_packet_out()
    msg.actions.append(of.ofp_action_output(port = outPort))
    msg.buffer_id = bufferID
    msg.in_port = inPort
    msg.data = None
    g2Sender.send((msg, dpid,))


def msg_sending_thread_task(g2Receivers, sema):
  "this thread identifies the switch to whom a msg is to be sent, "
  "then sends the msg"
  
  while 1:
    sema.acquire()
    sema.release()
    for i in range(5):
      for receiver in g2Receivers:
        if receiver.poll(1):
          (msg, dpid,) = receiver.recv()
          core.openflow.sendToDPID(dpid, msg)
