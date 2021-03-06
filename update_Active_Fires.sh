#!/usr/bin/env bash

#SOURCE=$(dirname $(dirname "${BASH_SOURCE[0]}"))

#cd $SOURCE

# synchronize changes with repository, update and clean
git fetch
git pull
git checkout -f
git log -m -1 --name-status --pretty="format:"

# print status
echo -e "\nThe last commit:\n"
git log -1
echo -e "Update finished\n"
