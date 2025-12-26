#!/bin/bash

SERVER_IP=$1
PORT=$2
USER=$3
PASSWORD=$4
PATH_SEARCH=$5
KEYWORD=$6

sshpass -p "$PASSWORD" ssh -p $PORT -o StrictHostKeyChecking=no \
$USER@$SERVER_IP "find $PATH_SEARCH -name \"*$KEYWORD*\""
