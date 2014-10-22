#
# FS haul driver, that copies the subtree from
# one node to another using rsync. It's used in
# legacy OpenVZ configurations.
#

import subprocess as sp
import os

rsync_log_file = "rsync.log"

class p_haul_fs:
	def __init__(self, subtree_path):
		print "Initialized subtree FS hauler (%s)" % subtree_path
		self.__root = subtree_path
		pass

	def set_target_host(self, thost):
		self.__thost = thost

	def set_work_dir(self, wdir):
		self.__wdir = wdir

	def __run_rsync(self):
		logf = open(os.path.join(self.__wdir, rsync_log_file), "w+")
		dst = "%s:%s" % (self.__thost, os.path.dirname(self.__root))

		# First rsync might be very long. Wait for it not
		# to produce big pause between the 1st pre-dump and
		# .stop_migration

		ret = sp.call(["rsync", "-a", self.__root, dst],
				stdout = logf, stderr = logf)
		if ret != 0:
			raise Exception("Rsync failed")

	def start_migration(self):
		print "Starting FS migration"
		self.__run_rsync()

	def next_iteration(self):
		pass

	def stop_migration(self):
		print "Doing final FS sync"
		self.__run_rsync()

	# When rsync-ing FS inodes number will change
	def persistent_inodes(self):
		return False
