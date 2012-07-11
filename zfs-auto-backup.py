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

SETTINGS_LOCATION = '/etc/zfs/zfs-auto-backup.conf'

# Find out whether the specified backup drive is attached.
# If it is, do backups to it, incremental where possible.
def main():

    # Load settings
    global LOCAL_POOL_NAME, BACKUP_POOL_NAME
    settings = {}
    with open(SETTINGS_LOCATION, 'r') as settings_file:
        for line in settings_file:
            line_split = line.strip().split('=')
            settings[line_split[0]] = line_split[1]
        LOCAL_POOL_NAME = settings['local_pool_name']
        BACKUP_POOL_NAME = settings['backup_pool_name']
    # TODO: fail safely when the settings file is in the wrong format or can't
    # be found

    # If the pool is ineligible to be imported
    if not cmd_output_matches("/sbin/zpool import", "pool: " + BACKUP_POOL_NAME):
        log("'" + BACKUP_POOL_NAME + "' is not available")

        # Maybe it has already been imported?
        if cmd_output_matches("/sbin/zpool status", "pool: " + BACKUP_POOL_NAME):
            do_backup()

    # The pool is eligible to be imported.
    else:
        # Try to import the pool.
        # If the pool fails to import, log and do nothing else.
        if cmd_output_matches("/sbin/zpool import -N " + BACKUP_POOL_NAME, "cannot import"):
            log("Failed to import pool '" + BACKUP_POOL_NAME + "'.")
            
        # We have successfully imported the pool.
        # Start the backup.
        else:
            do_backup()

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
    print int(time.time()) + ": " + msg

# Pre: The backup pool has been imported.
# Do a backup of the pool
def do_backup():
    # Find out the latest local snapshot.
    local_snaps = cmd_output_matches("/sbin/zfs list -r -t snapshot " + LOCAL_POOL_NAME,
            "^" + LOCAL_POOL_NAME + r"@\S*")
    latest_local_snap = local_snaps[-1].split("@")[1]

    # Find remote snapshots.
    remote_snaps = cmd_output_matches("/sbin/zfs list -r -t snapshot " + BACKUP_POOL_NAME,
            "^" + BACKUP_POOL_NAME + "/" + LOCAL_POOL_NAME + r"@\S*")

    # If there are no remote snapshots, do a non-incremental backup.
    if not remote_snaps:
        # Log the fact that we are doing a non-incremental backup
        log("Starting non-incremental backup.")

        # Execute a non-incremental backup.
        cmd = "/sbin/zfs send -vR " + LOCAL_POOL_NAME + "@" + latest_local_snap + \
                " | /sbin/zfs receive -vFu -d " + BACKUP_POOL_NAME + "/" + LOCAL_POOL_NAME
        exec_in_shell(cmd)
    
    # There are remote snapshots.
    else:
        # Get the latest remote snapshot.      
        latest_remote_snap = remote_snaps[-1].split("@")[1]
        
        # If the backup already has the latest snapshot
        if latest_remote_snap == latest_local_snap:
            log("Nothing to do.  Backup pool already has latest snapshot '" + latest_remote_snap + "'.")
        
        # Backup pool does not have the latest local snapshot
        else:
            # Log that we are starting incremental backup
            log("Starting incremental backup from '" + latest_remote_snap
                    + "' to '" + latest_local_snap + "'.")

            # Construct and execute command to send incremental backup
            cmd = "/sbin/zfs send -vR -I " + LOCAL_POOL_NAME + "@" + latest_remote_snap + \
                    " " + LOCAL_POOL_NAME + "@" + latest_local_snap + \
                    " | /sbin/zfs receive -vFu -d " + BACKUP_POOL_NAME + "/" + LOCAL_POOL_NAME
            exec_in_shell(cmd)
    export_pool()

def exec_in_shell(cmd):
    try:
        return subprocess.check_output(cmd.split())
    except subprocess.CalledProcessError, e:
        print "fail: " + e.output
        sys.exit()


if __name__ == '__main__':
    main()

