
import json
import csv
import datetime
import pathlib
from pprint import pprint

import meraki
import click
from merakisnmp.async_code import async_orgsnmp
from merakisnmp.async_code import async_getorgnetworks
from merakisnmp.async_code import async_networksnmp

__author__ = 'Zach Brewer'
__email__ = 'zbrewer@cisco.com'
__version__ = '0.1.0'
__license__ = 'MIT'

'''
USE:
orgsnmp.py [CMD] [OPTIONS]

For help on a specific command:
orgsnmp.py [CMD] -h
'''

# setup our path for results and create dir if it does not exist
cwd = pathlib.Path().absolute()
org_reports_dir = str(cwd) + '/orgsnmp_results'
pathlib.Path(org_reports_dir).mkdir(parents=True, exist_ok=True)

network_reports_dir = str(cwd) + '/networksnmp_results'
pathlib.Path(network_reports_dir).mkdir(parents=True, exist_ok=True)

def return_orgs(apikey, debug):
    """
    setup meraki api session and return all orgs (syncronous call because there is no benefit in making getOrganizations() async)
    """
    if debug:
        api_session = meraki.DashboardAPI(
        api_key=apikey,
        base_url='https://api.meraki.com/api/v1/',
        output_log=True,
        print_console=True,
        suppress_logging=False,
        )
    else:
        api_session = meraki.DashboardAPI(
        api_key=apikey,
        base_url='https://api.meraki.com/api/v1/',
        output_log=False,
        print_console=False,
        suppress_logging=True,
        )

    try:
        all_orgs = api_session.organizations.getOrganizations()
        return all_orgs

    except meraki.exceptions.APIError as e:
        print(f'Meraki API ERROR: {e}\n')
        exit(0)

    except Exception as e:
        print(f'Non Meraki-SDK ERROR: {e}')
        exit(0)

def clean_orgs(all_orgs, org_names=None, org_ids=None):
    cleaned_orgs = []

    if org_ids:
        cleaned_ids = []
        for org_id in org_ids:
            if type(org_id) != 'string':
                str(org_id)
            
            cleaned = org_id.strip()
            cleaned_ids.append(cleaned)
        
        for org in all_orgs:
            if org['id'] in org_ids:
                clean_orgs.append(org)
        return cleaned_orgs
    
    elif org_names:
        user_orgs = [x.strip().lower() for x in org_names]

        cleaned_orgs = []
        for org in all_orgs:
            if org['name'].lower() in user_orgs:
                cleaned_orgs.append(org)

        if cleaned_orgs:
            return cleaned_orgs
    else:
        click.secho(click.style('Must provide either org_names or org_ids.\n \n', fg='red', bold=True))

def write_csv(csv_data, current_time, output_dir):
    keys = csv_data[0].keys()

    f_name = 'snmp_settings_' + str(current_time) + '.csv'
    write_path = pathlib.Path(output_dir) / f_name

    with open(write_path, 'w', newline='') as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(csv_data)

    click.secho(
        f'snmp settings CSV results written to file: { write_path }', fg='green'
        )

def write_json(json_data, current_time, output_dir):
    f_name = 'snmp_settings_' + str(current_time) + '.json'
    write_path = pathlib.Path(output_dir) / f_name

    with open(write_path, 'w') as outfile:
        outfile.write(json.dumps(json_data, indent=4))

    click.secho(
        f'snmp settings JSON results written to file: { write_path }', fg='green'
        )

def read_csv(filename):
    try:
        with open(filename, mode ='r', encoding='utf-8-sig') as csv_file:    
            csv_dict = csv.DictReader(csv_file)
            headers = csv_dict.fieldnames

            valid_headers = ['orgname', 'orgid']
            common_headers = [header for header in valid_headers if header in headers]

            is_valid = any(common_headers)
            if is_valid:
                org_ids = []
                org_names = []

                if common_headers == valid_headers:
                    click.secho(click.style(f'The csv file {filename} has both headers orgname and orgid. orgname is ignored if both headers and data are present (only orgid is used) \n \n', fg='yellow', bold=True))
                    for col in csv_dict:
                        # account for empty csv rows sometimes done by excel and others when opening CSV
                        if col['orgid'] != '':
                            org_ids.append(col['orgid'])

                        if col['orgname'] != '':
                            org_names.append(col['orgname'])
                            
                elif 'orgid' in headers:
                    for col in csv_dict:
                        if col['orgid'] != '':
                            org_ids.append(col['orgid'])
                    
                elif 'orgname' in headers:
                    for col in csv_dict:
                        if col['orgname'] != '':
                            org_names.append(col['orgname'])

                else:
                    print('could not fine orgname or orgid headers')
                    exit(0)
                
                target_orgs = {'orgids': org_ids, 'orgnames': org_names}
                return target_orgs
            
            else:
                click.secho(click.style(f'The csv file {filename} must have at least one column of data with at least one of the following headers: {valid_headers}\n \n', fg='red', bold=True))
                exit(0)
    
    except OSError as e:
        print(e)
        cwd = pathlib.Path().absolute()
        if e.errno == 2:
            click.secho(click.style(f'could not find the file "{filename}" in the directory "{cwd}". Verify the path and file name.\n \n', fg='red', bold=True))

# begin command group snmp_settings
ignore_option_case = dict(token_normalize_func=lambda x: x.lower())
@click.group(context_settings=ignore_option_case)
@click.pass_context
@click.option('-n', '--networks', is_flag=True, help='Flag to also get network level snmp for given orgs')
@click.option('-d', '--debug', is_flag=True, help='Flag for debug')
def snmp_settings(ctx, networks, debug):
    '''
    For detailed help for a subcomand use orgsnmp.py [CMD] --help
    '''
    ctx.ensure_object(dict)
    ctx.obj['debug_value'] = debug
    ctx.obj['network_value'] = networks

# snmp_settings command group: orgs-cli command
@snmp_settings.command()
@click.pass_context
@click.option(
    '-k',
    '--apikey', 
    prompt=True, 
    hide_input=True,
    required=True,  
    metavar='[APIKEY]',
    help='API key with access to one or more organizations.',
    )
@click.argument('orgnames', nargs=-1)
def orgs_cli(ctx, apikey, orgnames):
    '''
    Get snmp settings for one or more organization names seperated by a space on the CLI
    '''

    click.secho(click.style('\nGetting all organizations...\n \n', fg='green', bold=True))
    all_orgs = return_orgs(apikey=apikey, debug=ctx.obj['debug_value'])

    filtered_orgs = clean_orgs(all_orgs=all_orgs, org_names=orgnames)
    click.secho(click.style('\nGetting snmp settings for the following organizations:\n \n', fg='green', bold=True))
    for org in filtered_orgs:
        click.secho(click.style(f'{org["name"]}', fg='green', bold=True))
    if click.confirm(f'\nIf one or more of the org names are not present, please double check spelling. Organization names with spaces must have quotes around the name on the CLI. Continue?'):
        org_snmp_settings = async_orgsnmp.async_get_snmp(api_key=apikey, organizations=filtered_orgs, debug_app=ctx.obj['debug_value'])

    else:
        exit(0)
    
    # write json and csv results
    ct = str(datetime.datetime.now())
    write_json(json_data=org_snmp_settings, current_time=ct, output_dir=org_reports_dir)
    write_csv(csv_data=org_snmp_settings, current_time=ct, output_dir=org_reports_dir)

    # check for networks flag to get network level snmp settings
    if ctx.obj['network_value']:
        click.secho(click.style('\nNetwork flag set, getting networks for organizations.\n \n', fg='green', bold=True))
        all_orgnetworks = async_getorgnetworks.asyncget_networks(api_key=apikey, organizations=filtered_orgs, debug_app=ctx.obj['debug_value'])
        network_snmp_settings = async_networksnmp.async_get_snmp(api_key=apikey, networks=all_orgnetworks, debug_app=ctx.obj['debug_value'])

        write_json(json_data=network_snmp_settings, current_time=ct, output_dir=network_reports_dir)
        write_csv(csv_data=network_snmp_settings, current_time=ct, output_dir=network_reports_dir)

# snmp_settings command group: all-orgs command
@snmp_settings.command()
@click.pass_context
@click.option(
    '-k',
    '--apikey', 
    prompt=True, 
    hide_input=True,
    required=True,  
    metavar='[APIKEY]',
    help='API key with access to one or more organizations.',
    )
@click.option(
            '-cf', 
            '--containsfilter',
            metavar='[FILTER STRING]', 
            required=False,  
            help='A filter to perform on any organization names that CONTAIN the given string (Case sensitive).'
            )
@click.option(
            '-bf', 
            '--beginfilter',
            metavar='[FILTER STRING]', 
            required=False,  
            help='A filter to perform on any organization names that BEGIN WITH the given string (case ignored).'
            )
def all_orgs(ctx, apikey, containsfilter, beginfilter):
    '''
    Get snmp settings for all organizaitons the API key has access to (run "all-orgs --help" for org filters) 
    '''

    click.secho(click.style('\nGetting all organizations...\n \n', fg='green', bold=True))
    all_orgs = return_orgs(apikey=apikey, debug=ctx.obj['debug_value'])

    # begin filter option conditionals
    if containsfilter and beginfilter:
        click.secho(click.style('\nYou have provided both contains and begin filters ("-cf" and "-bf").  Note that the contains filter runs FIRST and the begins with filter runs SECOND.\n', fg='yellow', bold=True))
        click.pause()

        contains_filter_orgs = []
        filtered_orgs = []
        for org in all_orgs:
            if containsfilter.lower() in org['name'].lower():
                contains_filter_orgs.append(org)
        
        for org in contains_filter_orgs:
            if org['name'].lower().startswith(beginfilter.lower()):
                filtered_orgs.append(org)

    elif containsfilter:
        filtered_orgs = []
        for org in all_orgs:
            if containsfilter.lower() in org['name'].lower():
                filtered_orgs.append(org)

    elif beginfilter:
        filtered_orgs = []
        for org in all_orgs:
            if org['name'].lower().startswith(beginfilter.lower()):
                filtered_orgs.append(org)
    else:
        filtered_orgs = all_orgs

        
    click.secho(click.style('\nGetting snmp settings for the following organizations:\n \n', fg='green', bold=True))
    for org in filtered_orgs:
        click.secho(click.style(f'{org["name"]}', fg='green', bold=True))
    if click.confirm(f'\nIf one or more expected orgs are not present, please verify the contains filter (-cf) and beginsfilter (-bf) options. Continue?'):
        org_snmp_settings = async_orgsnmp.async_get_snmp(api_key=apikey, organizations=filtered_orgs, debug_app=ctx.obj['debug_value'])

    else:
        exit(0)
    
    # write json and csv results
    ct = str(datetime.datetime.now())
    write_json(json_data=org_snmp_settings, current_time=ct, output_dir=org_reports_dir)
    write_csv(csv_data=org_snmp_settings, current_time=ct, output_dir=org_reports_dir)

    # check for networks flag to get network level snmp settings
    if ctx.obj['network_value']:
        click.secho(click.style('\nNetwork flag set, getting networks for organizations.\n \n', fg='green', bold=True))
        all_orgnetworks = async_getorgnetworks.asyncget_networks(api_key=apikey, organizations=filtered_orgs, debug_app=ctx.obj['debug_value'])
        network_snmp_settings = async_networksnmp.async_get_snmp(api_key=apikey, networks=all_orgnetworks, debug_app=ctx.obj['debug_value'])

        write_json(json_data=network_snmp_settings, current_time=ct, output_dir=network_reports_dir)
        write_csv(csv_data=network_snmp_settings, current_time=ct, output_dir=network_reports_dir)

# snmp_settings command group: orgs-file command
@snmp_settings.command()
@click.pass_context
@click.option(
    '-k',
    '--apikey', 
    prompt=True, 
    hide_input=True,
    required=True,  
    metavar='[APIKEY]',
    help='API key with access to one or more organizations.',
    )
@click.option(
    '-of',
    '--orgfile', 
    required=True,  
    metavar='[ORGFILE]',
    help='A CSV filename in the same directory as orgsnmp.py. It must have colums with label orgid or orgname (or both) containing organization IDs and Names',
    )
@click.option(
            '-cf', 
            '--containsfilter',
            metavar='[FILTER STRING]', 
            required=False,  
            help='A filter to perform on any organization names that CONTAIN the given string (Case sensitive).'
            )
@click.option(
            '-bf', 
            '--beginfilter',
            metavar='[FILTER STRING]', 
            required=False,  
            help='A filter to perform on any organization names that BEGIN WITH the given string (case ignored).'
            )

def orgs_file(ctx, apikey, orgfile, containsfilter, beginfilter):
    '''
    Get snmp settings for all organizaitons by org ID or org Name in a csv file (run "orgs-file --help" for org filters) 
    '''
    click.secho(click.style('\nGetting all organizations...\n \n', fg='green', bold=True))
    all_orgs = return_orgs(apikey=apikey, debug=ctx.obj['debug_value'])
    orgs_dict = read_csv(filename=orgfile)

    csv_orgs = []
    if orgs_dict['orgids']:
        #remove duplicates and strip leading/trailing spaces
        orgids_stripped = set([x.strip() for x in orgs_dict['orgids']])
        for org in all_orgs:
            if org['id'] in orgids_stripped:
                csv_orgs.append(org)

    elif orgs_dict['orgnames']:
        #remove duplicates and strip leading/trailing spaces
        orgnames_stripped = set([x.strip().lower() for x in orgs_dict['orgnames']])
        for org in all_orgs:
            if org['name'].lower() in orgnames_stripped:
                csv_orgs.append(org)

    # begin filter option conditionals
    if containsfilter and beginfilter:
        click.secho(click.style('\nYou have provided both contains and begin filters ("-cf" and "-bf").  Note that the contains filter runs FIRST and the begins with filter runs SECOND.\n', fg='yellow', bold=True))
        click.pause()

        contains_filter_orgs = []
        filtered_orgs = []
        for org in csv_orgs:
            if containsfilter.lower() in org['name'].lower():
                contains_filter_orgs.append(org)
        
        for org in contains_filter_orgs:
            if org['name'].lower().startswith(beginfilter.lower()):
                filtered_orgs.append(org)

    elif containsfilter:
        filtered_orgs = []
        for org in csv_orgs:
            if containsfilter.lower() in org['name'].lower():
                filtered_orgs.append(org)

    elif beginfilter:
        filtered_orgs = []
        for org in csv_orgs:
            if org['name'].lower().startswith(beginfilter.lower()):
                filtered_orgs.append(org)
    else:
        filtered_orgs = csv_orgs

        
    click.secho(click.style('\nGetting snmp settings for the following organizations:\n \n', fg='green', bold=True))
    for org in filtered_orgs:
        click.secho(click.style(f'{org["name"]}', fg='green', bold=True))

    if click.confirm(f'\nIf one or more expected orgs are not present, please verify the contains filter (-cf) and beginsfilter (-bf) options. Continue?'):
        org_snmp_settings = async_orgsnmp.async_get_snmp(api_key=apikey, organizations=filtered_orgs, debug_app=ctx.obj['debug_value'])

    else:
        exit(0)
    
    # write json and csv results
    ct = str(datetime.datetime.now())
    write_json(json_data=org_snmp_settings, current_time=ct, output_dir=org_reports_dir)
    write_csv(csv_data=org_snmp_settings, current_time=ct, output_dir=org_reports_dir)

    # check for networks flag to get network level snmp settings
    if ctx.obj['network_value']:
        click.secho(click.style('\nNetwork flag set, getting networks for organizations.\n \n', fg='green', bold=True))
        all_orgnetworks = async_getorgnetworks.asyncget_networks(api_key=apikey, organizations=filtered_orgs, debug_app=ctx.obj['debug_value'])
        network_snmp_settings = async_networksnmp.async_get_snmp(api_key=apikey, networks=all_orgnetworks, debug_app=ctx.obj['debug_value'])

        write_json(json_data=network_snmp_settings, current_time=ct, output_dir=network_reports_dir)
        write_csv(csv_data=network_snmp_settings, current_time=ct, output_dir=network_reports_dir)


if __name__ == '__main__':
    snmp_settings(max_content_width=120)