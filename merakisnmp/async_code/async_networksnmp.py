import meraki
import meraki.aio
import asyncio
import tqdm.asyncio

_author_ = 'Zach Brewer'
_email_ = 'zbrewer@cisco.com'
_version_ = '0.0.2'
_license_ = 'MIT'
meraki.aio.AsyncNetworks.getNetworkSnmp
'''
simple code that returns snmp settings for networks in one or more orgs
'''
async def _get_snmp(aiomeraki, network):
    '''  Async function that gets network snmp '''
    try:
        snmp_config = await aiomeraki.networks.getNetworkSnmp(networkId=network['networkId'])

    except meraki.exceptions.AsyncAPIError as e:
        print(f'Meraki AIO API Error (Org: { network["networkName"] }): \n { e }')
        snmp_config = {}

    except Exception as e:
        print(f'some other ERROR: {e}') 
        snmp_config = {}

    if snmp_config:
        '''
         networks, getNetworkSnmp - 400 Bad Request, {'errors': ['This network does not support SNMP configuration']}

        '''
        # default our snmp version to None (disabled)
        snmp_version = None

        # hide community string from output and set version to v1/v2c if enabled
        if snmp_config['communityString']:
            community_string = '****'
            snmp_version = 'v1/v2c'
        else:
            community_string = None

        # remove user passwords if set and set version to v3 if enabled
        if snmp_config['users']:
            snmp_version = 'v3'
            snmp_users = []
            for user in snmp_config['users']:
                snmp_users.append({'username': user['username'], 'passphrase': '****'})
        else:
            snmp_users = snmp_config['users']

        # none is returned as a strung, we want a None value (null in JSON/JS)
        if snmp_config['access'] == 'none':
            snmp_access = None
        else:
            snmp_access = snmp_config['access']

        snmp_data = [{
            'networkName': network['networkName'],
            'networkId': network['networkId'],
            'networkUrl' : network['networkUrl'], 
            'organizationName': network['organizationName'], 
            'organizationId': network['organizationId'],
            'organizationUrl' : network['organizationUrl'],
            'snmpVersion': snmp_version,
            'snmpAccess': snmp_access,
            'snmpCommunitystring': community_string,
            'snmpUsers': snmp_users
            }]

    else:
        snmp_config = {}
        snmp_data = {}

    return snmp_data

async def _async_apicall(api_key, networks, debug_values):
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
        
        all_snmp = []

        admin_tasks = [_get_snmp(aiomeraki, network) for network in networks]
        for task in tqdm.tqdm(
                asyncio.as_completed(admin_tasks),
                total = len(admin_tasks),
                colour='green',
                ):

            snmp_json = await task
            for network in snmp_json:
                all_snmp.append(network)
        
        return all_snmp


def async_get_snmp(api_key, networks, debug_app=False):
    if debug_app:
        debug_values = {'output_log' : True, 'output_console' : True, 'suppress_logging' : False}
    else:
        debug_values = {'output_log' : False, 'output_console' : False, 'suppress_logging' : True}

    #begin async loop
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_async_apicall(api_key, networks, debug_values))