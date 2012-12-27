BASHCOMPDIR=/etc/bash_completion.d
COMPSRC=ztools.complete
COMPFILE=ztools
COMPDEST=$(BASHCOMPDIR)/$(COMPFILE)

CMDDIR=/usr/bin
CMDSRC=ztools
CMDFILE=ztools
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
