PREFIX ?= /usr/local
BUILD_DIR = build/$(PREFIX)/share/man

man:
	mkdir -vp $(BUILD_DIR)
	chainlib-man.py -b 0xbf -v -n eth-monitor -d $(BUILD_DIR)/ man
	chainlib-man.py -b 0xbf -v -n eth-monitor-list -d $(BUILD_DIR)/ man
	chainlib-man.py -b 0xbf -v -n eth-monitor-import -d $(BUILD_DIR)/ man

.PHONY: man
