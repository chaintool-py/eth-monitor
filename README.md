# NAME

eth-monitor - Cache, index and monitor transactions with an EVM node rpc

# SYNOPSIS

**eth-monitor** \[ --skip-history \] \[ --single \] \[ p *eth_provider*
\] \[ --includes-file *file* \] \[ -i chain_spec \] **eth-monitor** \[
--skip-history \] \[ --single \] \[ p *eth_provider* \] \[
--excludes-file *file* \] \[ --include-default \] \[ -i chain_spec \] 

# DESCRIPTION

The **eth-monitor** has fulfills three distinct but related functions:

> 1\. A customizable view of on transactions of interest.
>
> 2\. A block and transaction cache.
>
> 3\. Arbitrary code executions using a transaction (and its block) as
> input.

Using an EVM RPC endpoint, the **eth-monitor** tool will retrieve blocks
within a given range and provides arbitrary processing of each
transaction.

A collection of options is provided to control the behavior of which
block ranges to sync, which criteria to use for display and cache, and
what code to execute for matching transactions. Details on each topic
can be found in the **SYNCING**, **MATCHING ADDRESSES** and **DEFINING
FILTERS** sections below, respectively.

Example executions of the tool can be found in the **EXAMPLES** section.

## OPTIONS

**-0**  
Omit newline to output

**--address ***address*  
Add an address of interest to match any role. Complements
**--address-file***.*

**-c ***config_dir, ***--config ***config_dir*  
Load configuration files from given directory. All files with an .ini
extension will be loaded, of which all must contain valid ini file data.

**--dumpconfig ***format*  
Output configuration settings rendered from environment and inputs.
Valid arguments are *ini for ini file output, and env for environment
variable output. See ***CONFIGURATION***.*

**--env-prefix**  
Environment prefix for variables to overwrite configuration. Example: If
**--env-prefix*** is set to ***FOO*** then configuration variable
***BAR_BAZ*** would be set by environment variable ***FOO_BAZ_BAR***.
Also see ***ENVIRONMENT***.*

**--excludes-file ***file*  
Load address exclude matching rules from file. See **MATCHING
ADDRESSES***.*

**--exec ***address*  
Add an address of interest to executable address array. Complements
**--address-file***.*

**--filter ***module*  
Add code execution filter to all matched transactions. The argument must
be a python module path. Several filters may be added by supplying the
option multiple times. Filters will be executed in the order the options
are given. See **DEFINING FILTERS*** section of ***eth-monitor (1)***
for more details.*

**--height**  
Block height at which to query state for. Does not apply to
transactions.

**-i ***chain_spec, ***--chain-spec ***chain_spec*  
Chain specification string, in the format
\<engine\>:\<fork\>:\<chain_id\>:\<common_name\>. Example:
"evm:london:1:ethereum". Overrides the *RPC_CREDENTIALS configuration
setting.*

**--include-default **  
Match all addresses by default. Addresses may be excluded using
--excludes-file. If this is set, --input, --output, --exec and
--includes-file will have no effect.

**--includes-file ***file*  
Load address include matching rules from file. See **MATCHING
ADDRESSES***.*

**--input ***address*  
Add an address of interest to inputs (recipients) array. Complements
**--address-file***.*

**-n ***namespace, ***--namespace ***namespace*  
Load given configuration namespace. Configuration will be loaded from
the immediate configuration subdirectory with the same name.

**--no-logs**  
Turn of logging completely. Negates **-v*** and ***-vv**

**--output ***address*  
Add an address of interest to outputs (sender) array. Complements
**--address-file***.*

**-p***, ***--rpc-provider**  
Fully-qualified URL of RPC provider. Overrides the *RPC_PROVIDER
configuration setting.*

**--raw**  
Produce output most optimized for machines.

**--renderer ***module*  
Add output renderer filter to all matched transactions. The argument
must be a python module path. Several renderers may be added by
supplying the option multiple times. See **RENDERERS*** section of
***eth-monitor (1)*** for more details.*

**--rpc-dialect**  
RPC backend dialect. If specified it *may help with encoding and
decoding issues. Overrides the RPC_DIALECT configuration setting.*

**--store-block-data **  
Store block data in cache for matching transactions. Requires
**--cache-dir***.*

**--store-tx-data **  
Store transaction data in cache for matching transactions. Requires
**--cache-dir***.*

**-u***, ***--unsafe**  
Allow addresses that do not pass checksum.

**-v**  
Verbose. Show logs for important state changes.

**-vv**  
Very verbose. Show logs with debugging information.

**--x-address ***address*  
Add an address of interest to match any role.

**--x-exec ***address*  
Add an address of disinterest to executable address array.

**--x-input ***address*  
Add an address of disinterest to inputs (recipients) array.

**--x-output ***address*  
Add an address of disinterest to outputs (sender) array.

# CONFIGURATION

All configuration settings may be overriden both by environment
variables, or by overriding settings with the contents of ini-files in
the directory defined by the **-c*** option.*

The active configuration, with values assigned from environment and
arguments, can be output using the **--dumpconfig*** format option. Note
that entries having keys prefixed with underscore (e.g. \_SEQ) are not
actual configuration settings, and thus cannot be overridden with
environment variables.*

To refer to a configuration setting by environment variables, the
*section and key are concatenated together with an underscore, and
transformed to upper-case. For example, the configuration variable
FOO_BAZ_BAR refers to an ini-file entry as follows:*

    [foo]
    bar_baz = xyzzy

In the **ENVIRONMENT*** section below, the relevant configuration
settings for this tool is listed along with a short description of its
meaning.*

Some configuration settings may also be overriden by command line
options. Also note that the use of the **-n*** and ***--env-prefix***
options affect how environment and configuration is read. The effects of
options on how configuration settings are affective is described in the
respective ***OPTIONS*** section.*

# MATCHING ADDRESSES

By default, addresses to match against transactions need to be
explicitly specified. This behavior can be reversed with the
**--include-default*** option. Addresses to match are defined using the
***--input***, ***--output*** and ***--exec*** options. Addresses
specified multiple times will be deduplicated.*

Inclusion rules may also be loaded from file by specifying the
**--includes-file*** and ***--excludes-file*** options. Each file must
specify the outputs, inputs and exec addresses as comma separated lists
respectively, separated by tabs.*

In the current state of this tool, address matching will affect all
parts of the processing; cache, code execution and rendering.

# SYNCING

When a sync is initiated, the state of this sync is persisted. This way,
previous syncs that did not complete for some reason will be resumed
where they left off.

A special sync type **--head*** starts syncing at the current head of
the chain, and continue to sync until interrupted. When resuming sync, a
new sync range between the current block head and the block height at
which the previous ***--head*** sync left off will automatically be
created.*

Syncs can be forced to (re)run for ranges regardless of previous state
by using the **--single*** option. However, there is no protection in
place from preventing code filters from being executed again on the same
transaction when this is done. See ***DEFINING FILTERS*** below.*

# CACHE

When syncing, the hash of a block and transaction matching the address
criteria will be stored in the cache. The hashes can be used for future
data lookups.

If **--store-block-data*** and/or ***--store-tx-data*** is set, a copy
of the block and/or transaction data will also be stored, respectively.*

# RENDERING

Rendering in the context of **eth-monitor*** refers to a formatted
output stream that occurs independently of caching and code execution.*

Filters for rendering may be specified by specifying python modules to
the **--renderer*** option. This option may be specified multiple
times.*

Rendering filters will be executed in order, and the first filter to
return *False*

# DEFINING FILTERS

A python module used for filter must fulfill two conditions:

> 1\. It must provide a class named *Filter in the package base
> namespace.*
>
> 2\. The *Filter class must include a method named filter with the
> signature def filter(self, conn, block, tx, db_session=None). *

Filters will strictly be executed in the order which they are defined on
the command line.

# FURTHER READING

Refer to the **chainsyncer*** chapter n info chaintool for in-depth
information on the subjects of syncing and filtering.*

# ENVIRONMENT

*CHAIN_SPEC*  
String specifying the type of chain connected to, in the format
*\<engine\>:\<fork\>:\<network_id\>:\<common_name\>. For EVM nodes the
engine value will always be evm.*

*RPC_DIALECT*  
Enables translations of EVM node specific formatting and response codes.

*RPC_PROVIDER*  
Fully-qualified URL to the RPC endpoint of the blockchain node.

# LICENSE

This documentation and its source is licensed under the Creative Commons
Attribution-Sharealike 4.0 International license.

The source code of the tool this documentation describes is licensed
under the GNU General Public License 3.0.

# COPYRIGHT

Louis Holbrook \<dev@holbrook.no\> (https://holbrook.no) PGP:
59A844A484AC11253D3A3E9DCDCBD24DD1D0E001

# SOURCE CODE

https://git.defalsify.org
