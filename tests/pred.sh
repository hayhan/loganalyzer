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

# echo $1 > $SHELL_FOLDER/../data/test/cm/tmp.txt

# Use '=' instead of '==' to be back compatible with sh. It was also
# verified with shell_exec() in php where '==' doesn't seem to  work.
if [ $1 = machine ]
then
    analyzer loglab predict
else
    analyzer oldschool run
fi
