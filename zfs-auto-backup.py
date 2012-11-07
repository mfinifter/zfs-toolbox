#! /usr/bin/env python

#  This program is free software. It comes without any warranty, to
#  the extent permitted by applicable law. You can redistribute it
#  and/or modify it under the terms of the Do What The Fuck You Want
#  To Public License, Version 2, as published by Sam Hocevar. See
#  http://sam.zoy.org/wtfpl/COPYING for more details.

import re
import subprocess
import sys
import time


# Backup each pool (or don't) according to the value of its
# "zfs-auto-backup:backup-pools" property
def main():
    list_of_pools = get_list_of_pools()
    for pool in list_of_pools:
        backup_pools = get_backup_pools(pool)
        for backup_pool in backup_pools:
            # If the pool is ineligible to be imported
            if not cmd_output_matches("/sbin/zpool import",
                    "pool: " + backup_pool):
                log("'" + backup_pool + "' is not available")

                # Maybe it has already been imported?
                if cmd_output_matches("/sbin/zpool status",
                        "pool: " + backup_pool):
                    do_backup(pool, backup_pool)

            # The pool is eligible to be imported.
            else:
                # Try to import the pool.
                # If the pool fails to import, log and do nothing else.
                if cmd_output_matches("/sbin/zpool import -N " + backup_pool,
                        "cannot import"):
                    log("Failed to import pool '" + backup_pool + "'.")
                    
                # We have successfully imported the pool.
                # Start the backup.
                else:
                    do_backup(pool, backup_pool)

def get_list_of_pools():

    # Get the raw output
    output = exec_in_shell("/sbin/zpool list")

    # Throw away the first line because it is just column labels
    output = output.split("\n")[1:-1]

    # Keep only the first part of each remaining line
    output = map(lambda x: x.split()[0], output)

    return output

def get_backup_pools(pool):

    # Get the raw output
    output = exec_in_shell("/sbin/zfs get zfs-auto-backup:backup-pools " + pool)

    # Throw away the first line because it is just column labels
    output = output.split("\n")[1]

    # Keep only the value
    value = output.split()[2]

    if value is "-":
        # No backup pools set. Return empty list.
        return []

    else:
        # Split on commas and return
        return value.split(",")

        
# Check if the given dataset exists
def dataset_exists(dataset):
    matches = cmd_output_matches("/sbin/zfs list -H -o name", "^" + dataset + "$")
    return len(matches) > 0

# Create the given filesystem
def create_filesystem(fs):
    exec_in_shell("/sbin/zfs create " + fs)

# Export the pool.
def export_pool():
    exec_in_shell("/sbin/zpool export " + BACKUP_POOL_NAME)

# Execute the command in the shell and get the output.
# Find and return all occurrences of the search string in the output.
def cmd_output_matches(cmd, string_to_match):
    shell_output = exec_in_shell(cmd)
    matches = re.findall(string_to_match, shell_output, re.MULTILINE)
    return matches

# Print a timestamped log message.
def log(msg):
    print str(int(time.time())) + ": " + msg

# Pre: The backup pool has been imported.
# Do a backup of the pool
def do_backup(local_dataset, backup_pool):
    # Find out the latest local snapshot. We start at the last hourly.
    local_snaps = exec_in_shell("/sbin/zfs list -H -t snapshot -S creation -o name -d 1 " + local_dataset)
    latest_local_snap = local_snaps.split("\n")[0].split("@")[1]

    backup_destination = backup_pool + "/" + local_dataset

    # Make sure the destination dataset exists. If it doesn't, create it.
    if (not dataset_exists(backup_destination)):
        create_filesystem(backup_destination)

    # Find remote snapshots.
    remote_snaps = exec_in_shell("/sbin/zfs list -H -t snapshot -S creation -o name -d 1 " + backup_destination)

    # If there are no remote snapshots, do a non-incremental backup.
    if not remote_snaps:
        # Log the fact that we are doing a non-incremental backup
        log("Starting non-incremental backup.")

        # Execute a non-incremental backup.
        cmd1 = "/sbin/zfs send -vR " + local_dataset + "@" + latest_local_snap
        cmd2 = "/sbin/zfs receive -vFu -d " + backup_pool + "/" + local_dataset 
        exec_pipe(cmd1, cmd2)
    
    # There are remote snapshots.
    else:
        # Get the latest remote snapshot.      
        latest_remote_snap = remote_snaps.split("\n")[0].split("@")[1]
        
        # If the backup already has the latest snapshot
        if latest_remote_snap == latest_local_snap:
            log("Nothing to do.  Backup pool already has latest snapshot '" + latest_remote_snap + "'.")
        
        # Backup pool does not have the latest local snapshot
        else:
            # Log that we are starting incremental backup
            log("Starting incremental backup from '" + latest_remote_snap
                    + "' to '" + latest_local_snap + "'.")

            # Construct and execute command to send incremental backup
            cmd1 = "/sbin/zfs send -vR -I " + local_dataset + "@" + latest_remote_snap + \
                    " " + local_dataset + "@" + latest_local_snap
            cmd2 = "/sbin/zfs receive -vFu -d " + backup_pool + "/" + local_dataset
            exec_pipe(cmd1, cmd2)
    export_pool()

def exec_in_shell(cmd):
    try:
        return subprocess.check_output(cmd.split())
    except subprocess.CalledProcessError, e:
        # Non-zero exit code, but we don't really care
        return e.output

def exec_pipe(cmd1, cmd2):
    p1 = subprocess.Popen(cmd1.split(), stdout=subprocess.PIPE)
    p2 = subprocess.Popen(cmd2.split(), stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()
    out, err = p2.communicate()

    return out 

if __name__ == '__main__':
    main()

