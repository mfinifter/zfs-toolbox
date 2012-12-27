BASHCOMPDIR=/etc/bash_completion.d
COMPSRC=zfs-toolbox.complete
COMPFILE=zfs-toolbox
COMPDEST=$(BASHCOMPDIR)/$(COMPFILE)

CMDDIR=/usr/bin
CMDSRC=zfs-toolbox
CMDFILE=zfs-toolbox
CMDDEST=$(CMDDIR)/$(CMDFILE)

.PHONY: install
install: | $(BASHCOMPDIR) $(CMDDIR)
	cp $(COMPSRC) $(COMPDEST)
	cp $(CMDSRC) $(CMDDEST)

.PHONY: uninstall
uninstall: | $(BASHCOMPDIR) $(CMDDIR)
	rm -f $(COMPDEST)
	rm -f $(CMDDEST)
