#! /usr/bin/env python

#  This program is free software. It comes without any warranty, to
#  the extent permitted by applicable law. You can redistribute it
#  and/or modify it under the terms of the Do What The Fuck You Want
#  To Public License, Version 2, as published by Sam Hocevar. See
#  http://sam.zoy.org/wtfpl/COPYING for more details.

import argparse
import subprocess
import sys

def main():
    parser = argparse.ArgumentParser(description='Delete all snapshots up to and including the named snapshot.')
    parser.add_argument('--dry-run', help="don't actually destroy anything", default=False, action='store_true')
    parser.add_argument('dataset', help='the dataset')
    parser.add_argument('snapshot', help='the name of the snapshot')
    args = vars(parser.parse_args())
    dataset = args['dataset']
    snapshot = args['snapshot']
    dry_run = args['dry_run']
    
    cmd = "/sbin/zfs list -H -t snapshot -s creation -o name -d 1 " + dataset
    output = exec_in_shell(cmd)
    snaps = output.split('\n')
    try:
        index = snaps.index("%s@%s" % (dataset, snapshot))
        snaps_to_destroy = snaps[0:index+1]
        print "The following snapshots will be destroyed:"
        for snap in snaps_to_destroy:
            print "    " + snap
        print "Proceed?",
        choice = raw_input().lower()
        if choice == 'y':
            destroy_snapshots(snaps_to_destroy, dry_run)
        else:
            print "No snapshots destroyed. Exiting."
    except ValueError:
        print "Snapshot %s@%s not found. Exiting." % (dataset, snapshot)

def destroy_snapshots(snapshots, dry_run):
    print "Destroying snapshots."
    for snap in snapshots:
        destroy_snapshot(snap, dry_run)
    print "Finished destroying snapshots. Exiting."

def destroy_snapshot(snapshot, dry_run):
    cmd = "/sbin/zfs destroy %s" % snapshot
    print "Running command: %s" % cmd
    if not dry_run:
        exec_in_shell(cmd)

def exec_in_shell(cmd):
    try:
        return subprocess.check_output(cmd.split())
    except subprocess.CalledProcessError, e:
        # Non-zero exit code, but we don't really care
        return e.output

if __name__ == '__main__':
    main()
