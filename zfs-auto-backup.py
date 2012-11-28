#! /usr/bin/env python2.7

#  This program is free software. It comes without any warranty, to
#  the extent permitted by applicable law. You can redistribute it
#  and/or modify it under the terms of the Do What The Fuck You Want
#  To Public License, Version 2, as published by Sam Hocevar. See
#  http://sam.zoy.org/wtfpl/COPYING for more details.

from datetime import datetime

import argparse
import re
import subprocess
import sys

# Backup each dataset (or don't) according to the value of its
# "zfs-auto-backup:backup-pools" property
def main():
    global VERBOSE, DRY_RUN
    parser = argparse.ArgumentParser(description='Automatically backup each zfs filesystem to the pool(s) specified in its "zfs-auto-backup:backup-pools" property.')
    parser.add_argument('--verbose', help="print lots of log messages", default=False, action='store_true')
    parser.add_argument('--dry-run', help="don't actually perform any of the constructive/destructive operations", default=False, action='store_true')
    args = vars(parser.parse_args())
    VERBOSE = args['verbose']
    DRY_RUN = args['dry_run']

    list_of_datasets = get_list_of_datasets()
    for dataset in list_of_datasets:
        backup_pools = get_backup_pools(dataset)
        for backup_pool in backup_pools:
            if import_pool(backup_pool):
                do_backup(dataset, backup_pool)
                export_pool(backup_pool)

# Returns True if the pool is accessible (i.e., it was already imported or it
# has just now been successfully imported), False otherwise
def import_pool(pool):
    ret = False
    # If the pool is ineligible to be imported
    if not cmd_output_matches("/sbin/zpool import",
            "pool: " + pool):
        # Maybe it has already been imported?
        if cmd_output_matches("/sbin/zpool status", "pool: " + pool):
            ret = True

    # The pool is eligible to be imported.
    else:
        # Try to import the pool.
        # If the pool fails to import, log and do nothing else.
        if cmd_output_matches("/sbin/zpool import -N " + pool,
                "cannot import"):
            log("Failed to import pool '" + pool + "'.")
            
        # We have successfully imported the pool.
        else:
            ret = True
    return ret

# Returns a string for the current time of the form YYYY-mm-dd-HHMM
def get_timestamp_string():
    return datetime.now().strftime("%Y-%m-%d-%H%M")

# Sets up a global name for the snapshots so they are all named the same
snapname = "zfs-auto-backup-" + get_timestamp_string()

# Given a dataset, returns the name of the latest snapshot that is of the form
# "zfs-auto-backup-YYYY-mm-dd-HHMM"
# If no such snapshot, returns None
def get_latest_backed_up_zfsautobackup_snap(dataset):
    regex = dataset + r"@zfs-auto-backup-\d\d\d\d-\d\d-\d\d-\d\d\d\d"
    cmd = "/sbin/zfs list -H -t snapshot -S creation -o name -d 1 " + dataset
    matches = cmd_output_matches(cmd, regex)
    if len(matches) is 0:
        return None
    return matches[0].split("@")[1]

# Given a dataset, takes a new zfs-auto-backup snapshot
# The new snapshot has the name "zfs-auto-backup-YYYY-mm-dd-HHMM" where the
# timestamp is the current time
# Return the name of the new snapshot, or None if it couldn't be created
def create_zfsautobackup_snap(dataset):
    cmd = "/sbin/zfs snapshot " + dataset + "@" + snapname
    if DRY_RUN:
        return snapname
    if cmd_output_matches(cmd, "cannot create snapshot"):
        return None
    return snapname

def get_list_of_datasets():
    output = exec_in_shell("/sbin/zfs list -H -o name")
    return output.strip().split("\n")

def get_backup_pools(dataset):
    output = exec_in_shell("/sbin/zfs get -H -o value zfs-auto-backup:backup-pools " + dataset).strip()

    if output is "-":
        # No backup pools set. Return empty list.
        return []
    else:
        # Split on commas and return
        return output.split(",")
        
# Check if the given dataset exists
def dataset_exists(dataset):
    matches = cmd_output_matches("/sbin/zfs list -H -o name", "^" + dataset + "$")
    return len(matches) > 0

# Create the given filesystem
def create_filesystem(fs):
    if not DRY_RUN:
        exec_in_shell("/sbin/zfs create -p " + fs)

# Export the pool.
def export_pool(backup_pool_name):
    exec_in_shell("/sbin/zpool export " + backup_pool_name)

# Execute the command in the shell and get the output.
# Find and return all occurrences of the search string in the output.
def cmd_output_matches(cmd, string_to_match):
    shell_output = exec_in_shell(cmd)
    matches = re.findall(string_to_match, shell_output, re.MULTILINE)
    return matches

# Print a timestamped log message.
def log(msg):
    global VERBOSE
    if VERBOSE:
        print "    " + get_timestamp_string() + ": " + msg

# Strip off all but the first element of the path.
# E.g., "foo/bar/baz" becomes "foo" and "tank" becomes "tank"
def strip_all_but_first_path_element(path):
    first_slash = path.find('/')
    if first_slash is -1:
        return path
    else:
        return path[0:first_slash]

# Perform a non-incremental backup to backup_pool/local_dataset@snap
def do_nonincremental_backup(local_dataset, snap, backup_pool):
    global DRY_RUN

    # Log the fact that we are doing a non-incremental backup
    log("Starting non-incremental backup from %s@%s to %s." % (local_dataset, snap, backup_pool))

    # For the zfs receive, we need to strip off all but the first part of the path  
    local_dataset_stripped = strip_all_but_first_path_element(local_dataset)

    # Execute a non-incremental backup.
    cmd1 = "/sbin/zfs send -v " + local_dataset + "@" + snap
    cmd2 = "/sbin/zfs receive -vFu -d " + backup_pool + '/' + local_dataset_stripped
    log("Executing: '%s | %s'." % (cmd1, cmd2))
    if not DRY_RUN:
        exec_pipe(cmd1, cmd2)

# Perform an incremental backup
# From backup_pool/local_dataset@remote_snap to backup_pool/local_dataset@snap
def do_incremental_backup(local_dataset, snap, backup_pool, remote_snap):
    global DRY_RUN

    log("Starting incremental backup of %s to %s from @%s to @%s ." % (local_dataset, backup_pool, remote_snap, snap))

    # For the zfs receive, we need to strip off all but the first part of the path  
    local_dataset_stripped = strip_all_but_first_path_element(local_dataset)

    # Construct and execute command to send incremental backup
    cmd1 = "/sbin/zfs send -v -I " + local_dataset + "@" + remote_snap + " " + \
            local_dataset + "@" + snap
    cmd2 = "/sbin/zfs receive -vFu -d " + backup_pool + '/' + local_dataset_stripped
    log("Executing: '%s | %s'." % (cmd1, cmd2))
    if not DRY_RUN:
        exec_pipe(cmd1, cmd2)

# Pre: The backup pool has been imported.
# Do a backup of the pool
def do_backup(local_dataset, backup_pool):
    # Take a new snapshot of the local dataset
    local_snap = create_zfsautobackup_snap(local_dataset)
    if local_snap is None:
        log("Unable to create snapshot on dataset %s" % local_dataset)
    else:
        backup_destination = backup_pool + "/" + local_dataset

        # Make sure the destination dataset exists. If it doesn't, create it.
        if not dataset_exists(backup_destination):
            create_filesystem(backup_destination)

        latest_remote = get_latest_backed_up_zfsautobackup_snap(backup_destination)
        
        if latest_remote is None:
            # No zfs-auto-backup snap has ever been backed up. Proceed with
            # non-incremental backup for this dataset.
            do_nonincremental_backup(local_dataset, local_snap, backup_pool)
        else:
            # Proceed with incremental backup.
            do_incremental_backup(local_dataset, local_snap, backup_pool,
                    latest_remote)

# Execute a command in the shell. Disregard exit code. Return output.
def exec_in_shell(cmd):
    try:
        return subprocess.check_output(cmd.split())
    except subprocess.CalledProcessError, e:
        # Non-zero exit code, but we don't really care
        return e.output

# Execute a pipe in the shell.
def exec_pipe(cmd1, cmd2):
    p1 = subprocess.Popen(cmd1.split(), stdout=subprocess.PIPE)
    p2 = subprocess.Popen(cmd2.split(), stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()
    out, err = p2.communicate()

    return out 

if __name__ == '__main__':
    main()

