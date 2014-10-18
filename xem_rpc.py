import socket
import select
import threading
import traceback
import util
import struct

rpc_port = 12345
rpc_sk_buf = 256

RPC_CMD = 1
RPC_CALL = 2

RPC_RESP = 1
RPC_EXC = 2

#
# Client
#

class _rpc_proxy_caller:
	def __init__(self, sk, typ, fname):
		self._rpc_sk = sk
		self._fn_typ = typ
		self._fn_name = fname

	def __call__(self, *args):
		call = (self._fn_typ, self._fn_name, args)
		raw_data = repr(call)
		self._rpc_sk.send(raw_data)
		raw_data = self._rpc_sk.recv(rpc_sk_buf)
		resp = eval(raw_data)

		if resp[0] == RPC_RESP:
			return resp[1]
		elif resp[0] == RPC_EXC:
			print "Remote exception"
			raise Exception(resp[1])
		else:
			raise Exception("Proto resp error")

class rpc_proxy:
	def __init__(self, conn, *args):
		self._srv = conn
		self._rpc_sk = self._make_sk("rpc")
		util.set_cloexec(self._rpc_sk)
		_rpc_proxy_caller(self._rpc_sk, RPC_CMD, "init_rpc")(args)

	def __getattr__(self, attr):
		return _rpc_proxy_caller(self._rpc_sk, RPC_CALL, attr)

	def _make_sk(self, uname):
		sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sk.connect((self._srv, rpc_port))
		sk.send(struct.pack("!i", len(uname)))
		sk.send(uname.encode())
		return sk

	def open_socket(self, uname):
		sk = self._make_sk(uname)
		c = _rpc_proxy_caller(self._rpc_sk, RPC_CMD, "pick_channel")
		c(uname)
		return sk



#
# Server
#

class _rpc_server_sk:
	def __init__(self, sk, uname):
		self._sk = sk
		self._master = None
		self._uname = uname

	def fileno(self):
		return self._sk.fileno()

	def hash_name(self):
		return self._uname

	def work(self, mgr):
		raw_data = self._sk.recv(rpc_sk_buf)
		if not raw_data:
			mgr.remove(self)
			if self._master:
				self._master.on_disconnect()
			self._sk.close()
			return

		data = eval(raw_data)
		try:
			if data[0] == RPC_CALL:
				if not self._master:
					raise Exception("Proto seq error")

				res = getattr(self._master, "rpc_" + data[1])(*data[2])
			elif data[0] == RPC_CMD:
				res = getattr(self, data[1])(mgr, *data[2])
			else:
				raise Exception(("Proto typ error", data[0]))
		except Exception as e:
			traceback.print_exc()
			res = (RPC_EXC, e)
		else:
			res = (RPC_RESP, res)

		raw_data = repr(res)
		self._sk.send(raw_data)

	def init_rpc(self, mgr, args):
		util.set_cloexec(self)
		self._master = mgr.make_master()
		self._master.on_connect(*args)

	def pick_channel(self, mgr, uname):
		sk = mgr.pick_sk(uname)
		if sk:
			self._master.on_socket_open(sk._sk, uname)

class _rpc_server_ask:
	def __init__(self):
		sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sk.bind(("0.0.0.0", rpc_port))
		sk.listen(8)
		self._sk = sk
		util.set_cloexec(self)

	def fileno(self):
		return self._sk.fileno()

	def work(self, mgr):
		sk, addr = self._sk.accept()
		size, = struct.unpack("!i", sk.recv(4))
		uname = sk.recv(size).decode()
		mgr.add(_rpc_server_sk(sk, uname))

class _rpc_stop_fd:
	def __init__(self, fd):
		self._fd = fd

	def fileno(self):
		return self._fd.fileno()

	def work(self, mgr):
		mgr.stop()

class _rpc_server_manager:
	def __init__(self, srv_class):
		self._srv_class = srv_class
		self._sk_by_name = {}
		self._poll_list = [_rpc_server_ask()]
		self._alive = True

	def add(self, sk):
		self._sk_by_name[sk.hash_name()] = sk
		self._poll_list.append(sk)

	def remove(self, sk):
		self._sk_by_name.pop(sk.hash_name())
		self._poll_list.remove(sk)

	def pick_sk(self, hash_name):
		sk = self._sk_by_name.pop(hash_name, None)
		if sk:
			self._poll_list.remove(sk)
		return sk

	def make_master(self):
		return self._srv_class()

	def stop(self):
		self._alive = False

	def loop(self, stop_fd):
		if stop_fd:
			self._poll_list.append(_rpc_stop_fd(stop_fd))

		while self._alive:
			r, w, x = select.select(self._poll_list, [], [])
			for sk in r:
				sk.work(self)

		print "RPC Service stops"

class rpc_threaded_srv(threading.Thread):
	def __init__(self, srv_class):
		threading.Thread.__init__(self)
		self._mgr = _rpc_server_manager(srv_class)
		self._stop_fd = None

	def run(self):
		self._mgr.loop(self._stop_fd)

	def get_stop_fd(self):
		sks = socket.socketpair()
		self._stop_fd = sks[0]
		return sks[1]
