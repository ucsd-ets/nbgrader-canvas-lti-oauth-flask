#!/bin/bash


mkdir -p /mnt/nbgrader
cp -r /tmp/nbgrader/* /mnt/nbgrader

nbgrader_dirs=($(ls /mnt/nbgrader))
for dirname in "${nbgrader_dirs[@]}"; do
    username=$(tr -dc a-z </dev/urandom | head -c 13)
    useradd -m $username
    chown -R $username:nbgrader2canvas /mnt/nbgrader/$dirname
    chmod 0640 /mnt/nbgrader/$dirname/grader/gradebook.db
done