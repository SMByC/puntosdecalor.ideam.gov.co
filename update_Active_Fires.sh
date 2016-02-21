#!/usr/bin/env bash

# clone
# hg clone https://XavierCLL@bitbucket.org/SMBYC/active-fires Active_Fires

# synchronize changes with repository, update and clean
hg pull
hg update -C
#hg status -un|xargs rm 2> /dev/null

# print status
echo -e "\nThe last commit:\n"
hg tip
echo -e "Update finished\n"
