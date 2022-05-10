def process_config(config, args, flags):
    arg_override = {}
    arg_override['ETHMONITOR_INPUTS'] = getattr(args, 'input')
    arg_override['ETHMONITOR_OUTPUTS'] = getattr(args, 'output')
    arg_override['ETHMONITOR_EXEC'] = getattr(args, 'exec')
    arg_override['ETHMONITOR_ADDRESS'] = getattr(args, 'address')
    arg_override['ETHMONITOR_X_INPUTS'] = getattr(args, 'xinput')
    arg_override['ETHMONITOR_X_OUTPUTS'] = getattr(args, 'xoutput')
    arg_override['ETHMONITOR_X_EXEC'] = getattr(args, 'xexec')
    arg_override['ETHMONITOR_X_ADDRESS'] = getattr(args, 'xaddress')
    arg_override['ETHMONITOR_INCLUDE_DEFAULT'] = getattr(args, 'include_default')

    config.dict_override(arg_override, 'local cli args')

    config.add(getattr(args, 'session_id'), '_SESSION_ID', False)
    config.add(getattr(args, 'cache_dir'), '_CACHE_DIR', False)

    return config
