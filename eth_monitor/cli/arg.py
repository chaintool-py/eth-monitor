def process_args(argparser, args, flags):
    # session flags
    argparser.add_argument('--state-dir', dest='state_dir', type=str, help='Directory to store sync state')
    argparser.add_argument('--session-id', dest='session_id', type=str, help='Use state from specified session id')
    argparser.add_argument('--cache-dir', dest='cache_dir', type=str, help='Directory to store tx data')

    # address rules flags
    argparser.add_argument('--input', action='append', type=str, help='Add input (recipient) addresses to includes list')
    argparser.add_argument('--output', action='append', type=str, help='Add output (sender) addresses to includes list')
    argparser.add_argument('--exec', action='append', type=str, help='Add exec (contract) addresses to includes list')
    argparser.add_argument('--data', action='append', type=str, help='Add data prefix strings to include list')
    argparser.add_argument('--data-in', action='append', dest='data_in', type=str, help='Add data contain strings to include list')
    argparser.add_argument('--x-data', action='append', dest='x_data', type=str, help='Add data prefix string to exclude list')
    argparser.add_argument('--x-data-in', action='append', dest='x_data_in', type=str, help='Add data contain string to exclude list')
    argparser.add_argument('--address', action='append', type=str, help='Add addresses as input, output and exec to includes list')
    argparser.add_argument('--x-input', action='append', type=str, dest='x_input', help='Add input (recipient) addresses to excludes list')
    argparser.add_argument('--x-output', action='append', type=str, dest='x_output', help='Add output (sender) addresses to excludes list')
    argparser.add_argument('--x-exec', action='append', type=str, dest='x_exec', help='Add exec (contract) addresses to excludes list')
    argparser.add_argument('--x-address', action='append', type=str, dest='x_address', help='Add addresses as input, output and exec to excludes list')
    argparser.add_argument('--includes-file', type=str, dest='includes_file', help='Load include rules from file')
    argparser.add_argument('--excludes-file', type=str, dest='excludes_file', help='Load exclude rules from file')
    argparser.add_argument('--include-default', dest='include_default', action='store_true', help='Include all transactions by default')

    # filter flags
    argparser.add_argument('--renderer', type=str, action='append', default=[], help='Python modules to dynamically load for rendering of transaction output')
    argparser.add_argument('--filter', type=str, action='append', help='Add python module to tx filter path')
    argparser.add_argument('--block-filter', type=str, dest='block_filter', action='append', help='Add python module to block filter path')

    # cache flags
    argparser.add_argument('--store-tx-data', action='store_true', dest='store_tx_data', help='Store tx data in cache store')
    argparser.add_argument('--store-block-data', action='store_true', dest='store_block_data', help='Store block data in cache store')
    argparser.add_argument('--fresh', action='store_true', help='Do not read block and tx data from cache, even if available')
