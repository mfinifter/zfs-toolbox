#! /usr/bin/env python

import re
import subprocess
import sys
import time

# TODO: Do a complete pass through the program to add appropriate logging.

# TODO: externalize configuration into config file or, if few enough args, as
# command-line args

LOCAL_POOL_NAME = "tank"
BACKUP_POOL_NAME = "backup_portable"

# Find out whether the specified backup drive is attached.
# If it is, do backups to it, incremental where possible.
def main():

    # If the pool is ineligible to be imported
    if not cmd_output_matches("zpool import", "pool: " + BACKUP_POOL_NAME):
        log("'" + BACKUP_POOL_NAME + "' is not available")

    # The pool is eligible to be imported.
    else:
        # Try to import the pool.
        # If the pool fails to import
        if cmd_output_matches("zpool import -N " + BACKUP_POOL_NAME, "cannot import"):
            
            # Log the failure and exit
            log("Failed to import pool '" + BACKUP_POOL_NAME + "'.")
            
        # We have successfully imported the pool.
        # Start the backup.
        else:
            doBackup()
            export_pool()

# Export the pool.
def export_pool():
    exec_in_shell("zpool export " + BACKUP_POOL_NAME)

# Execute the command in the shell and get the output.
# Find and return all occurrences of the search string in the output.
def cmd_output_matches(cmd, string_to_match):
    shell_output = exec_in_shell(cmd)
    matches = re.findall(string_to_match, shell_output, re.MULTILINE)
    return matches

# Print a timestamped log message.
def log(msg):
    print int(time.time()) + ": " + msg

# Pre: The backup pool has been imported.
# Do a backup of the pool
def doBackup():
    # Find out the latest local snapshot.
    local_snaps = cmd_output_matches("zfs list -r -t snapshot " + LOCAL_POOL_NAME,
            "^" + LOCAL_POOL_NAME + r"@\S*")
    latest_local_snap = local_snaps[-1].split("@")[1]

    # Find remote snapshots.
    remote_snaps = cmd_output_matches("zfs list -r -t snapshot " + BACKUP_POOL_NAME,
            "^" + BACKUP_POOL_NAME + "/" + LOCAL_POOL_NAME + r"@\S*")

    # If there are no remote snapshots, do a non-incremental backup.
    if not remote_snaps:
        # Log the fact that we are doing a non-incremental backup
        log("Starting non-incremental backup.")

        # Execute a non-incremental backup.
        cmd = "zfs send -vR " + LOCAL_POOL_NAME + "@" + latest_local_snap +
                " | zfs receive -vFu -d " + BACKUP_POOL_NAME + "/" + LOCAL_POOL_NAME
        exec_in_shell(cmd)
    
    # There are remote snapshots.
    else:
        # Get the latest remote snapshot.      
        latest_remote_snap = remote_snaps[-1].split("@")[1]

        # Log that we are starting incremental backup
        log("Starting incremental backup from '" + latest_remote_snap
                + "' to '" + latest_local_snap + "'.")

        # TODO need some logic here for if the latest remote snap
        # is the same as the latest local snap

        # Construct and execute command to send incremental backup
        cmd = "zfs send -vR -I " + LOCAL_POOL_NAME + "@" + latest_remote_snap +
                " " + LOCAL_POOL_NAME + "@" + latest_local_snap +
                " | zfs receive -vFu -d " + BACKUP_POOL_NAME + "/" + LOCAL_POOL_NAME
        exec_in_shell(cmd)

def exec_in_shell(cmd):
    return subprocess.check_output(cmd, shell=True)

if __name__ == '__main__':
    main()

