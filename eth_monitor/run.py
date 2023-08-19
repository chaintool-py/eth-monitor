# standard imports
import os
import logging

logg = logging.getLogger(__name__)


def cleanup_run(settings):
    if not settings.get('RUN_OUT'):
        return
    lockfile = os.path.join(settings.get('RUN_DIR'), '.lock')
    os.unlink(lockfile)
    logg.debug('freed rundir {}'.format(settings.get('RUN_DIR')))


def cleanup(settings):
    cleanup_run(settings)
