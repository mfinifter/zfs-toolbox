BASHCOMPDIR=/etc/bash_completion.d
COMPSRC=zfs-toolbox.complete
COMPFILE=zfs-toolbox
COMPDEST=$(BASHCOMPDIR)/$(COMPFILE)

.PHONY: install
install: | $(BASHCOMPDIR)
	cp $(COMPSRC) $(COMPDEST)

.PHONY: uninstall
uninstall: | $(BASHCOMPDIR)
	rm -f $(COMPDEST)
