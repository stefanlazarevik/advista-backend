#!/bin/bash

## get server list
set -e
servers=""
all_servers=(${servers//,/ })
username=""
password=""
git_repo="https://${username}:${password}@github.com/midas19910709/Advista-project-backend.git"

echo "ALL_SERVERS ${servers}"

## iterate servers for deploy and pull last commit
for server in "${all_servers[@]}"
do
  echo "deploying to ${server}"
  ssh ubuntu@${server} "cd projects/Advista-project  && git pull origin develop && pm2 restart advista && pm2 save"
done
