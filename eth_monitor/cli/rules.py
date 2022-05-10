rules_address_args = [
        'input',
        'output',
        'exec',
        'address',
        ]

rules_data_args = [
        'data',
        'data_in',
            ]


def to_config_names(v):
    v = v.upper()
    return ('ETHMONITOR_' + v, 'ETHMONITOR_X_' + v)


