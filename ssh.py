import atexit
import xem_rpc
import getpass
import os

opts = {
	'TUNNEL_FLAGS'	: "-o ExitOnForwardFailure=yes -fN ",
	'SERVER_FLAGS'	: "-ttfM",
	'LOC_PORT'	: 54321,
	'REM_PORT'	: xem_rpc.rpc_port,
	'PORT'		: 22,
	'USER'		: getpass.getuser(),
	'REMOTE'	: "",
	'LOG'		: "/tmp/phs.log",
	'PHS_EXEC'	: "p.haul-service",
	'PHS_OPTS'	: "",
	'SSH_BASE'	: "ssh -p {PORT} {USER}@{REMOTE} -S ~/ph_ssh_{USER}_{REMOTE}_{PORT}"
}

_no_ssh = False

def parse_args(args):
	no_ssh = args.pop('no_ssh')

	if not args.pop('no_ssh_comp'):
		opts['SERVER_FLAGS'] += " -C"
		opts['TUNNEL_FLAGS'] += " -C"

	opts['USER']		= args.pop('ssh_user')
	opts['LOC_PORT']	= args.pop('ssh_loc_port')

	if not _no_ssh:
		# Extract --port option and replace it with LOC_PORT
		opts['REM_PORT']	= args.pop('port')
		args['port']		= opts['LOC_PORT']

	opts['PHS_EXEC']	= args.pop('ssh_phs_exec')
	opts['PORT']		= args.pop('ssh_port')
	opts['LOG']		= args.pop('ssh_log')

	if not _no_ssh:
		# Extract "to" option and replace it with 127.0.0.1
		opts['REMOTE']	= args.pop('to')
		args['to']	= "127.0.0.1"

	# Tell p.haul-service to bind on localhost, so it is not
	# directly accessible from the outer web.
	opts['PHS_OPTS']	= "--bind-port "+str(opts['REM_PORT'])
	opts['PHS_OPTS']	+= " --bind-addr 127.0.0.1"

	# Use ssh multiplexing to speedup establishing additional
	# ssh sessions and to get control over all of them.
	opts['SSH_BASE']	= opts['SSH_BASE'].format(**opts)

	return args

def start():
	if _no_ssh:
		return

	print("Start p.haul-service")
	cmd = "{SSH_BASE} {SERVER_FLAGS} {PHS_EXEC} {PHS_OPTS} &> {LOG} < /dev/null".format(**opts)
	if os.system(cmd):
		raise Exception("Can't start p.haul-service")
	print("Done")

	print("Checking that p.haul-service is started")
	cmd = '{SSH_BASE} "while netstat -lnt | awk \'\$4 ~ /:{REM_PORT}$/ {{exit 1}}\'; do echo \'Waiting...\'; sleep 1; done"'.format(**opts)
	if os.system(cmd):
		raise Exception("Can't check that p.haul-service is started")

	print("Start ssh tunnel")
	cmd = "{SSH_BASE} {TUNNEL_FLAGS} -L 127.0.0.1:{LOC_PORT}:127.0.0.1:{REM_PORT}".format(**opts)
	if os.system(cmd):
		raise Exception("Can't start ssh tunnel")
	print("Done")

	print("Launch p.haul")

def stop():
	if _no_ssh:
		return

	print("Stop SSH")
	cmd = "{SSH_BASE} -O exit &> /dev/null".format(**opts)
	os.system(cmd)

atexit.register(stop)
