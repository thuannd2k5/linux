#!/bin/bash

SERVER_IP=$1
PORT=$2
USER=$3
PASSWORD=$4
FILE_PATH=$5

sshpass -p "$PASSWORD" ssh -p $PORT -o StrictHostKeyChecking=no \
$USER@$SERVER_IP "rm -f $FILE_PATH"
