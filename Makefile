PREFIX ?= /usr/local
#BUILD_DIR = build/$(PREFIX)/share/man
MAN_DIR = man

man:
	mkdir -vp $(MAN_DIR)/build
	chainlib-man.py -b 0xbf -v -n eth-monitor -d $(MAN_DIR)/build $(MAN_DIR)
	cp -v $(MAN_DIR)/build/eth-monitor.1 $(MAN_DIR)/build/eth-monitor-sync.1
	chainlib-man.py -b 0xbf -v -n eth-monitor-list -d $(MAN_DIR)/build $(MAN_DIR)
	chainlib-man.py -b 0xbf -v -n eth-monitor-import -d $(MAN_DIR)/build $(MAN_DIR)

.PHONY: man
