# local imports
from .rules import (
        rules_address_args,
        rules_data_args,
        to_config_names,
        )

def process_config(config, arg, args, flags):
    arg_override = {}

    rules_args = rules_address_args + rules_data_args

    for rules_arg in rules_args:
        (vy, vn) = to_config_names(rules_arg)
        arg = getattr(args, rules_arg)
        if arg == None:
            v = config.get(vy)
            if bool(v):
                arg_override[vy] = v.split(',')
        else:
            arg_override[vy] = arg

        arg = getattr(args, 'x_' + rules_arg)
        if arg == None:
            v = config.get(vn)
            if bool(v):
                arg_override[vn] = v.split(',')
        else:
            arg_override[vn] = arg

    arg_override['ETHMONITOR_INCLUDES_FILE'] = getattr(args, 'includes_file')
    arg_override['ETHMONITOR_EXCLUDES_FILE'] = getattr(args, 'excludes_file')
    arg_override['ETHMONITOR_INCLUDE_DEFAULT'] = getattr(args, 'include_default')

    arg_override['ETHMONITOR_RENDERER'] = getattr(args, 'renderer')
    arg_override['ETHMONITOR_FILTER'] = getattr(args, 'filter')
    arg_override['ETHMONITOR_BLOCK_FILTER'] = getattr(args, 'block_filter')

    arg_override['ETHMONITOR_STATE_DIR'] = getattr(args, 'state_dir')

    arg_override['ETHCACHE_STORE_BLOCK'] = getattr(args, 'store_block_data')
    arg_override['ETHCACHE_STORE_TX'] = getattr(args, 'store_tx_data')

    config.dict_override(arg_override, 'local cli args')

    for rules_arg in rules_args:
        (vy, vn) = to_config_names(rules_arg)
        if config.get(vy) == None:
            config.add([], vy, True)
        if config.get(vn) == None:
            config.add([], vn, True)

    config.add(getattr(args, 'session_id'), '_SESSION_ID', False)
    config.add(getattr(args, 'cache_dir'), '_CACHE_DIR', False)
    config.add(getattr(args, 'fresh'), '_FRESH', False)

    return config
