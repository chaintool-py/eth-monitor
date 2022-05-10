def process_config(config, args, flags):
    config.add(getattr(args, 'session_id'), '_SESSION_ID', False)
    config.add(getattr(args, 'cache_dir'), '_CACHE_DIR', False)

    return config
