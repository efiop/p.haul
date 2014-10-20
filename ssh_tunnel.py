import os

def_ssh_port = 22
def_loc_port = 54321

class Tunnel:
	def __init__(self, dst_opts):
		ssh_user = dst_opts["ssh_username"]
		ssh_address = dst_opts["host"][0]
		remote_port = dst_opts["host"][1]
		local_port = dst_opts["ssh_local_port"]
		ssh_port = dst_opts["ssh_port"]
		use_compression = dst_opts["ssh_compression"]

		self._opts = {}
		self._opts["ssh_remote"] = ssh_user+"@"+ssh_address if ssh_user else ssh_address
		self._opts["ssh_port"] = ssh_port
		self._opts["local_port"] = local_port
		self._opts["remote_port"] = remote_port
		self._opts["compress"] = "C" if use_compression else ""

		self._cmd = "ssh -fN{compress} -L {local_port}:localhost:{remote_port} -p {ssh_port} {ssh_remote}".format(**self._opts)

		self.local_dst = ("127.0.0.1", local_port)

	def start(self):
		os.system(self._cmd)
		while os.system("pkill -0 -f \"" + self._cmd + "\""):
			print("waiting")

		print("SSH tunnel(cmd: %s) started" %self._cmd)

	def stop(self):
		os.system("pkill -9 -f \"" + self._cmd + "\"")
		print ("SSH tunnel stopped")
