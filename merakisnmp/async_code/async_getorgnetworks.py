import meraki
import meraki.aio
import asyncio
import tqdm.asyncio
from pprint import pprint

__author__ = 'Zach Brewer'
__email__ = 'zbrewer@cisco.com'
__version__ = '0.1.0'
__license__ = 'MIT'
'''
meraki - get_networks.py

NOTE: MODIFIED from original to include find and replace strings

small async tool that takes either an API key or organizations from getOrganizations Dashboard API call 
Returns a nested Python object with OrgName, OrgID, and other network data

Useful because Dashboard API does not include orgname in getOrgNetworks

Also useful to be able to return all given networks for all organizations (or a subset of organizations) and call them via python dict
'''
async def _get_orgnetworks(aiomeraki, organization):
    '''
    Async function that calls getOrganizationNetworks for a given organization
    '''

    try:
        # note, temporarily filtering out non SNMP relevant networks (cameras, MDM)
        relevant_products = ['appliance','cellularGateway','switch','wireless','wirelessController']
        networks = await aiomeraki.organizations.getOrganizationNetworks(
            organizationId=organization['id'], productTypes=relevant_products, total_pages=-1)

    except meraki.exceptions.AsyncAPIError as e:
        print(
            f'Meraki AIO API Error (OrgID "{ organization["id"] }", OrgName "{ organization["name"] }"): \n { e }'
        )
        networks = None
    except Exception as e:
        print(f'some other ERROR: {e}')
        networks = None

    if networks:
        rekeyed_dicts = []
        for network in networks:
            rename_idkey = {'networkId' if k == 'id' else k:v for k,v in network.items()}
            rename_url = {'networkUrl' if k == 'url' else k:v for k,v in rename_idkey.items()}
            rename_namekey = {'networkName' if k == 'name' else k:v for k,v in rename_url.items()}
            rekeyed_dicts.append(rename_namekey)

        org_networks = [{
            'organizationName': organization['name'],
            'organizationUrl': organization['url'],

            **network_dict,
        } for network_dict in rekeyed_dicts]

    else:
        org_networks = None
    
    return org_networks


async def _async_apicall(api_key, organizations, debug_values, cert_path):    
    # Instantiate a Meraki dashboard API session
    # NOTE: you have to use "async with" so that the session will be closed correctly at the end of the usage
    async with meraki.aio.AsyncDashboardAPI(
            api_key,
            base_url='https://api.meraki.com/api/v1',
            log_file_prefix=__file__[:-3],
            #log_path='logs/',
            maximum_concurrent_requests=10,
            maximum_retries= 100,
            wait_on_rate_limit=True,
            output_log=debug_values['output_log'],
            print_console=debug_values['output_console'],
            suppress_logging=debug_values['suppress_logging']
        ) as aiomeraki:

        all_orgnetworks = []

        network_tasks = [_get_orgnetworks(aiomeraki, organization) for organization in organizations]
        for task in tqdm.tqdm(
                asyncio.as_completed(network_tasks),
                total=len(network_tasks),
                colour='green',
        ):

            network_json = await task
            if network_json:
                all_orgnetworks.extend(iter(network_json))
        
        return all_orgnetworks

def asyncget_networks(api_key, organizations, debug_app=False, cert_path=None):
    if debug_app:
        debug_values = {'output_log' : True, 'output_console' : True, 'suppress_logging' : False}
    else:
        debug_values = {'output_log' : False, 'output_console' : False, 'suppress_logging' : True}

    #begin async loop
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_async_apicall(api_key, organizations, debug_values, cert_path))



