#!/bin/sh

# Get the absolute path of current shell script on Linux
uname_out="$(uname -s)"
case "${uname_out}" in
    Linux*)    SHELL_FOLDER=$(dirname $(readlink -f "$0"));;
         *)    SHELL_FOLDER=./;;
esac

# Check the old log file existence
logfile="/var/tftpboot/cmconsole.log"

if [ ! -f "$logfile" ]; then
    touch "$logfile"
fi

m1=$(md5sum "$logfile")

# Trigger the log transfer via tftp (CM -> RG)
latticecli -n "set Cm.ConsoleRedirect.AdminStatus 3" > /dev/null 2>&1

# Wait for file transfer ready. Exit if timeout happens.
counter=0
rxing=0
while true; do
    counter=$((counter+1))
    if [ "$counter" -gt 20 ]; then
        echo "Timeout when receiving logs!"
        exit 1
    fi
    sleep 0.1
    m2=$(md5sum "$logfile")
    # Make sure the tftp rx starts, aka. md5 value begins to change
    if [ "$rxing" -eq 0 ]; then
        if [ "$m1" != "$m2" ]; then
            rxing=1
            m1="$m2"
        fi
    # Make sure the file rx ends, aka. md5 value doesn't change anymore
    else
        if [ "$m1" != "$m2" ]; then
            m1="$m2"
        else
            break
        fi
    fi
done

# Copy console file to data folder of Loganalyzer
cp "$logfile" "$SHELL_FOLDER"/../data/cooked/cm/test.txt

# Run the prediction
analyzer loglab predict --model LR
