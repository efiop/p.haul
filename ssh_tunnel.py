import subprocess
import atexit
import select
import signal
import sys

def_ssh_port = 22
def_loc_port = 54321

ssh_tunnel_cmd = "ssh -N{ssh_comp} -o BatchMode=yes -L {ssh_loc_port}:localhost:{ssh_rem_port} -p {ssh_port} {ssh_user}@{to}"

class Tunnel:
	def __init__(self, dst_opts):
		self._ssh = None
		self._no_ssh = dst_opts.pop("no_ssh")
		self._opts = dst_opts
		atexit.register(self.stop)

	def get_local_dst(self):
		if self._no_ssh:
			return (self._opts["to"], self._opts["ssh_rem_port"])
		else:
			return ("127.0.0.1", self._opts["ssh_loc_port"])

	def start(self):
		if self._no_ssh:
			print("WARNING: SSH tunnel is disabled")
		else:
			cmd = ssh_tunnel_cmd.format(**self._opts)
			self._ssh = subprocess.Popen(cmd.split(), stdout = sys.stdout, stderr = sys.stderr)
			print("SSH tunnel started")

	def stop(self):
		if self._ssh:
			self._ssh.terminate()
			print ("SSH tunnel stopped")
