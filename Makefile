BASHCOMPDIR=/etc/bash_completion.d
BASHCOMPSRC=ztools.bash.complete
BASHCOMPFILE=ztools
BASHCOMPDEST=$(BASHCOMPDIR)/$(BASHCOMPFILE)

ZSHCOMPDIR=/usr/local/share/zsh/site-functions
ZSHCOMPSRC=ztools.zsh.complete
ZSHCOMPFILE=_ztools
ZSHCOMPDEST=$(ZSHCOMPDIR)/$(ZSHCOMPFILE)

CMDDIR=/usr/bin
CMDSRC=ztools
CMDFILE=ztools
CMDDEST=$(CMDDIR)/$(CMDFILE)

SCRIPTSDIR=/usr/bin
SCRIPTSSRC= zfs-auto-backup zfs-delete-snapshots zfs-rollback zfs-snap-full
SCRIPTSDEST=$(SCRIPTSSRC:%=$(SCRIPTSDIR)/%)

mkdirs:
	echo mkdir -p $(BASHCOMPDIR) $(ZSHCOMPDIR) $(CMDDIR) $(SCRIPTSDIR)

.PHONY: install
install: mkdirs
	cp $(BASHCOMPSRC) $(BASHCOMPDEST)
	cp $(ZSHCOMPSRC) $(ZSHCOMPDEST)
	cp $(CMDSRC) $(CMDDEST)
	cp $(SCRIPTSSRC) $(SCRIPTSDIR)

.PHONY: uninstall
uninstall:
	rm -f $(BASHCOMPDEST)
	rm -f $(ZSHCOMPDEST)
	rm -f $(CMDDEST)
	rm -f $(SCRIPTSDEST)
