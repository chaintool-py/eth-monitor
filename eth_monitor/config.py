# standard imports
import re
import logging


logg = logging.getLogger(__name__)


re_env='^ETHMONITOR_({}_(.+))$'


def __override_env(config, config_stem, env):
    re_env_instance = re_env.format(config_stem)
    for k in env:
        r = re.search(re_env_instance, k)
        if r != None:
            logg.debug('match renderer environment variable: {} '.format(r.group(1)))
            config.add(env[k], r.group(1), True)


def __override_arg(config, config_stem, args):
    if args == None:
        return

    args_array = getattr(args, config_stem.lower())
    if args_array == None:
        return

    i = 0
    for a in args_array:
        s = config_stem + '_ARG_' + str(i)
        config.add(a, s, True)
        i += 1


def override(config, keyword, env={}, args=None):
    config_stem = keyword.upper()
    __override_arg(config, config_stem, args)
    __override_env(config, config_stem, env)



def list_from_prefix(config, keyword):
    re_config = keyword.upper() + '_'
    k_default = re_config + 'DEFAULT'
    r = []
    for k in config.all():
        if re.match(re_config, k):
            v = config.get(k)
            if k == k_default:
                try:
                    v = v.split(',')
                except AttributeError:
                    continue
            r.append(v)
    return r
