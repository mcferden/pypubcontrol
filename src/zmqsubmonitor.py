#    zmqsubmonitor.py
#    ~~~~~~~~~
#    This module implements the features that monitor channel
#    subscriptions from ZMQ PUB sockets.
#    :authors: Justin Karneges, Konstantin Bokarius.
#    :copyright: (c) 2015 by Fanout, Inc.
#    :license: MIT, see LICENSE for more details.

import zmq
import time
import threading

# The ZmqSubMonitor class facilitates the monitoring of subscriptions via
# ZMQ PUB sockets.
class ZmqSubMonitor(object):

	# Initialize with a ZMQ PUB socket instance, threading lock, and callback
	# where the callback accepts two parameters: the first parameter a string
	# containing 'sub' or 'unsub' and the second parameter containing the
	# subscription name. The threading lock will be used relative to the
	# ZMQ socket operations.
	def __init__(self, socket, lock, callback):
		self.subscriptions = list()
		self._lock = lock
		self._socket = socket
		self._callback = callback
		self._thread = threading.Thread(target=self._monitor)
		self._thread.daemon = True
		self._thread.start()
	
	# This method is meant to run a separate thread and poll the ZMQ socket
	# for subscribe and unsubscribe events. When an event is encountered then
	# the callback is executed with the event information.
	def _monitor(self):
		# TODO: is socket locking necessary here?
		poller = zmq.Poller()
		poller.register(self._socket, zmq.POLLIN)
		while True:
			if self._socket.closed:
				return
			# TODO: Do we need to try - except for socket closed errors?
			socks = dict(poller.poll())
			if socks.get(self._socket) == zmq.POLLIN:
				self._lock.acquire()
				m = self._socket.recv()
				mtype = m[0]
				item = m[1:]
				if mtype == '\x01':
					if item not in self.subscriptions:
						self._callback('sub', item)
						self.subscriptions.append(item)
				elif mtype == '\x00':
					if item in self.subscriptions:
						self.subscriptions.remove(item)
					self._callback('unsub', item)
				self._lock.release()
