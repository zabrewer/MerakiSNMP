MerakiSNMP
-----------------  
- [Introduction](#Introduction)
- [Installation And Use](#installation-and-use)

# Introduction

MerakiSNMP will retrieve SNMP settings from one or more Meraki organizations and/or the individual network SNMP settings for the same organizations. 

Meraki dashboard has different SNMP MIBS that are supported at the organization level and other SNMP MIBS at the network level so org-level and network-level SNMP settings are seperate from one another.  

See this meraki KB article for details: 

https://documentation.meraki.com/General_Administration/Monitoring_and_Reporting/SNMP_Overview_and_Configuration

The result is a CSV and JSON file for all network Organization SNMP settings (if the --networks flag is passed) and a CSV and JSON file for all Organization SNMP settings.

# Installation And Use

## Installation

Note: Installing MerakiSNMP to a Python virtual environment is recommended

1) Create a Python virtual environment (recommended)
2) In the virtual environment folder (while activated):
``` 
git clone https://github.com/zabrewer/MerakiSNMP.git
``` 
3) With the virtual environment activated:
``` 
pip install .
``` 

Alternatively:
1) Create a Python virtual environment (recommended)
2) With the virtual environment activated:
```
 pip install "git+https://github.com/zabrewer/MerakiSNMP"
```
After successful installation, use the following command:

```
merakisnmp
```
you should see the default help output for merakisnmp

## Use

MerakiSNMP will take one or more dashboard organizations from one of several ways:
1) By passing organization names to the command line - this is the **orgs-cli** subcommand
2) All orgs that the given API key has access to (supports passing begins-with or contains filters) - this is the **all-orgs** subcommand
3) All orgs in a CSV file (supports passing begins-with or contains filters) - this is the **orgs-file** subcommand

***Note: if you installed via the methods mentioned in this readme, you should not have to use "python merakisnmp.py" but rather should simply be able to call merakisnmp directly (without the .py extension)***

ouput of merakisnmp --help
```
Usage: merakisnmp.py [OPTIONS] COMMAND [ARGS]...

  For detailed help for a subcomand use orgsnmp.py [CMD] --help

Options:
  -n, --networks  Flag to also get network level snmp for given orgs
  -d, --debug     Flag for debug
  --help          Show this message and exit.

Commands:
  all-orgs   Get snmp settings for all organizaitons the API key has access to (run "all-orgs --help" for org...
  orgs-cli   Get snmp settings for one or more organization names seperated by a space on the CLI
  orgs-file  Get snmp settings for all organizaitons by org ID or org Name in a csv file (run "orgs-file --help"...
```

Each subcommand supports various options such as filters.  To see all options for a given subcommand e.g.:
```
merakisnmp all-orgs --help
```

Example output of the orgs-file subcommand:
```
merakisnmp.py orgs-file --help


Usage: merakisnmp.py orgs-file [OPTIONS]

  Get snmp settings for all organizaitons by org ID or org Name in a csv file (run "orgs-file --help" for org filters)

Options:
  -k, --apikey [APIKEY]           API key with access to one or more organizations.  [required]
  -of, --orgfile [ORGFILE]        A CSV filename in the same directory as orgsnmp.py. It must have colums with label
                                  orgid or orgname (or both) containing organization IDs and Names  [required]
  -cf, --containsfilter [FILTER STRING]
                                  A filter to perform on any organization names that CONTAIN the given string (Case
                                  sensitive).
  -bf, --beginfilter [FILTER STRING]
                                  A filter to perform on any organization names that BEGIN WITH the given string (case
                                  ignored).
  --help                          Show this message and exit.
```


If the API key option is not passed (-k), merakiSNMP will automatically prompt for it.

If you want to get the SNMP settings for all networks in the given organiztions, the -n (--networks) flag must be passed after merakisnmp.py e.g.
```
merakisnmp --networks all-orgs
```

The above command will get all organizations that the API key has access to as well as SNMP settings for all networks in those networks.  The result will be an organization JSON and CSV file and a seperate network JSON and CSV file.

### Examples

1) Get snmp settings for all orgs and networks but use the startswith filter for only organization names starting with "myorg" (hint, you can use the startswith filter to do an exact match on one org by passing the entire organization name to the beginswith filter)

```
merakisnmp -n all-orgs -bf myorg 
```

2) Get snmp settings for organizations in the given csv file and networks but use the contains filter for only organization names with "test" in the name

(note that this will get ONLY org-level SNMP as no -n or --network flag is passed after merakisnmp)

```
merakisnmp orgs-file -of orgfile.csv -cf test
```
## Changelog

[Changelog](CHANGELOG.txt)

## License

[License](LICENSE)