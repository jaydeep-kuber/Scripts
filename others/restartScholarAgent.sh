#!/bin/bash

# var declaration
container_name="nginx-agent"
path="/home/jay/work/scripts/UT/test"
# check is container is running
if [ "$(docker ps -q -f name="^/${container_name}$")" ] ; then
	echo "Container is running..."
	docker ps | grep -i "${container_name}"
else
	echo "container is NOT running..."
	docker rm "${container_name}"
	echo "container removed..."
	echo "starting container from yml"
	cd ${path} ; docker compose -f docker-compose.yml up -d
fi
