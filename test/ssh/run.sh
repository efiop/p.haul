#!/usr/bin/bash

setsid stress -m 1 &> /dev/null < /dev/null &
PID=${!}

PH=$(realpath ../../p.haul)
PHS=$(realpath ../../p.haul-service)

../../p.haul-ssh --ssh-ph-exec ${PH} --ssh-phs-exec ${PHS} pid ${PID} "192.168.1.101" -v4 --keep-images --dst-rpid "/root/wdir/pid.pid" --img-path "/root/wdir" --force
