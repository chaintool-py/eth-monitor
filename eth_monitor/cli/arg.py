def process_flags(argparser, flags):
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
    argparser.add_argument('--x-data', action='append', dest='xdata', type=str, help='Add data prefix string to exclude list')
    argparser.add_argument('--x-data-in', action='append', dest='xdata_in', type=str, help='Add data contain string to exclude list')
    argparser.add_argument('--address', action='append', type=str, help='Add addresses as input, output and exec to includes list')
    argparser.add_argument('--x-input', action='append', type=str, dest='xinput', help='Add input (recipient) addresses to excludes list')
    argparser.add_argument('--x-output', action='append', type=str, dest='xoutput', help='Add output (sender) addresses to excludes list')
    argparser.add_argument('--x-exec', action='append', type=str, dest='xexec', help='Add exec (contract) addresses to excludes list')
    argparser.add_argument('--x-address', action='append', type=str, dest='xaddress', help='Add addresses as input, output and exec to excludes list')
    argparser.add_argument('--includes-file', type=str, dest='includes_file', help='Load include rules from file')
    argparser.add_argument('--excludes-file', type=str, dest='excludes_file', help='Load exclude rules from file')
    argparser.add_argument('--include-default', dest='include_default', action='store_true', help='Include all transactions by default')
