import subprocess
import atexit

def_ssh_port = 22
def_loc_port = 54321

ssh_tunnel_cmd = "ssh -N{ssh_comp} -L {ssh_loc_port}:localhost:{ssh_rem_port} -p {ssh_port} {ssh_user}@{to}"

class Tunnel:
	def __init__(self, dst_opts):
		self._ssh = None
		self._opts = dst_opts
		atexit.register(self.stop)

	def get_local_dst(self):
		return ("127.0.0.1", self._opts["ssh_loc_port"])

	def start(self):
		cmd = ssh_tunnel_cmd.format(**self._opts)
		self._ssh = subprocess.Popen(cmd.split())
		print("SSH tunnel started")

	def stop(self):
		if self._ssh:
			self._ssh.terminate()
			print ("SSH tunnel stopped")
