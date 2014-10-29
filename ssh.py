import atexit
import select
import signal
import sys
import paramiko
import SocketServer
import threading
import getpass

def_ssh_port = 22

class ForwardServer(SocketServer.ThreadingTCPServer):
	daemon_threads = True
	allow_reuse_address = True

NAT = 2000

class Handler(SocketServer.BaseRequestHandler):
	def handle(self):
		for n in xrange(NAT):
			try:
				chan = self.ssh_transport.open_channel("direct-tcpip",
							(self.chain_host, self.chain_port),
							self.request.getpeername())
			except Exception as e:
				if n < NAT - 1:
					continue
				else:
					raise e
			print(str(n))
			break
		if chan is None:
			raise Exception("Incoming request to %s:%d was rejected by the SSH server." % (self.chain_host, self.chain_port))

		print("Connected! Tunnel open %r -> %r -> %r" % (self.request.getpeername(),
								chan.getpeername(),
								(self.chain_host, self.chain_port)))

		while True:
			r, w, x = select.select([self.request, chan], [], [])
			if self.request in r:
				data = self.request.recv(1024)
				if len(data) == 0:
					break
				chan.send(data)
			if chan in r:
				data = chan.recv(1024)
				if len(data) == 0:
					break
				self.request.send(data)

		peername = self.request.getpeername()
		chan.close()
		self.request.close()
		print("Tunnel closed from %r" % (peername,))

def forward_tunnel(local_port, remote_host, remote_port, transport):
	class SubHander(Handler):
		chain_host = remote_host
		chain_port = remote_port
		ssh_transport = transport
	return ForwardServer(("", local_port), SubHander)

class SSH:
	def __init__(self, opts):
		self._no_ssh	= opts["no_ssh"]
		if self._no_ssh:
			return

		self._host	= opts["to"]
		self._user	= opts["ssh_user"]
		self._password	= getpass.getpass("SSH password:") if opts["ssh_ask_password"] else None
		self._rem_port	= opts["ssh_rem_port"]
		self._ssh_port	= opts["ssh_port"]
		self._ssh_comp	= opts["ssh_comp"]

		paramiko.util.log_to_file("filename.log")

		self._ssh = paramiko.SSHClient()
		self._ssh.load_system_host_keys()
		self._ssh.set_missing_host_key_policy(paramiko.WarningPolicy())

		self._cmd_chan = None
		self._server = None
		self._server_thread = None

	def get_local_dst(self):
		if self._no_ssh:
			return (self._host, self._rem_port)
		else:
			return ("127.0.0.1", self._server.socket.getsockname()[1])

	def start(self):
		if self._no_ssh:
			print("WARNING: SSH is disabled")
		else:

			self._ssh.connect(
					self._host, self._ssh_port,
					username = self._user,
					password = self._password,
					compress = self._ssh_comp)

			self._cmd_chan = self._ssh.get_transport().open_session()
			self._cmd_chan.get_pty()
			self._cmd_chan.exec_command("/root/git/p.haul/p.haul-service --port " + str(self._rem_port)+" &>/root/git/p.haul/test/zdtm/ph.log")

			self._server = forward_tunnel(0,
					"127.0.0.1",
					self._rem_port,
					self._ssh.get_transport())
			self._server_thread = threading.Thread(target = self._server.serve_forever)
			self._server_thread.start()
			print("SSH started")

	def stop(self):
		if self._no_ssh:
			return
		if self._cmd_chan:
			self._cmd_chan.close()
		if self._server:
			self._server.shutdown()
		self._ssh.close()
		if self._server_thread:
			self._server_thread.join()
		print("SSH stopped")
