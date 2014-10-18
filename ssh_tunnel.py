import os

def_ssh_port = 22
def_loc_port = 54321

class Tunnel:
	def __init__(self):
		self._cmd = None

	def filter_opts(self, opts):
		# Pop() all "ssh*" opts. If ssh tunnel is requested,
		# set "to" option to (localhost, local_port).

		use_ssh = opts.pop("ssh")
		ssh_user = opts.pop("ssh_username")
		ssh_address = opts["to"][0]
		remote_port = opts["to"][1]
		local_port = opts.pop("ssh_local_port")
		ssh_port = opts.pop("ssh_port")
		use_compression = opts.pop("ssh_compression")

		if not use_ssh:
			self._cmd = None
			return opts

		self._opts = {}
		self._opts["ssh_remote"] = ssh_user+"@"+ssh_address if ssh_user else ssh_address
		self._opts["ssh_port"] = ssh_port
		self._opts["local_port"] = local_port
		self._opts["remote_port"] = remote_port
		self._opts["compress"] = "C" if use_compression else ""

		self._cmd = "ssh -fN{compress} -L {local_port}:localhost:{remote_port} -p {ssh_port} {ssh_remote}".format(**self._opts)

		opts["to"] = ("127.0.0.1", local_port)

		return opts

	def start(self):
		if not self._cmd:
			return

		os.system(self._cmd)
		while os.system("pkill -0 -f \"" + self._cmd + "\""):
			print("waiting")

		print("SSH tunnel(cmd: %s) started" %self._cmd)

	def stop(self):
		if not self._cmd:
			return

		os.system("pkill -9 -f \"" + self._cmd + "\"")
		print ("SSH tunnel stopped")
