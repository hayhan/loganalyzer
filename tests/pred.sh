#! /bin/bash

# Get the absolute path of current shell script on Linux
uname_out="$(uname -s)"
case "${uname_out}" in
    Linux*)    SHELL_FOLDER=$(dirname $(readlink -f "$0"));;
         *)    SHELL_FOLDER=./;;
esac

# Set the python virtual enviroment
source $SHELL_FOLDER/../../pyVirtEnvs/log_env/bin/activate
export ANALYZER_DATA=$SHELL_FOLDER/../data

#analyzer oldschool run
analyzer loglab predict
