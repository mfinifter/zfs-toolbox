BASHCOMPDIR=/etc/bash_completion.d
COMPSRC=zfs-toolbox.complete
COMPFILE=zfs-toolbox
COMPDEST=$(BASHCOMPDIR)/$(COMPFILE)

CMDDIR=/usr/bin
CMDSRC=zfs-toolbox
CMDFILE=zfs-toolbox
CMDDEST=$(CMDDIR)/$(CMDFILE)

SCRIPTSDIR=/usr/bin
SCRIPTSSRC= zfs-auto-backup zfs-delete-snapshots zfs-rollback zfs-snap-full
SCRIPTSDEST=$(SCRIPTSSRC:%=$(SCRIPTSDIR)/%)

.PHONY: install
install: | $(BASHCOMPDIR) $(CMDDIR)
	cp $(COMPSRC) $(COMPDEST)
	cp $(CMDSRC) $(CMDDEST)
	cp $(SCRIPTSSRC) $(SCRIPTSDIR)

.PHONY: uninstall
uninstall: | $(BASHCOMPDIR) $(CMDDIR)
	rm -f $(COMPDEST)
	rm -f $(CMDDEST)
	rm -f $(SCRIPTSDEST)
