import meraki
import meraki.aio
import asyncio
import tqdm.asyncio

_author_ = 'Zach Brewer'
_email_ = 'zbrewer@cisco.com'
_version_ = '0.0.2'
_license_ = 'MIT'

'''
simple code that returns snmp settings for one or more orgs
'''
async def _get_snmp(aiomeraki, organization):
    '''  Async function that gets org snmp '''

    try:
        snmp_config = await aiomeraki.organizations.getOrganizationSnmp(organizationId=organization['id'])

    except meraki.exceptions.AsyncAPIError as e:
        print(f'Meraki AIO API Error (Org: { organization["name"] }): \n { e }')
        snmp_config = None

    except Exception as e:
        print(f'some other ERROR: {e}')
        snmp_config = None

    if snmp_config:
        # replace community string value from dict
        snmp_config['v2CommunityString'] = '*****'            
        snmp_data = [{
            'organizationName': organization['name'],
            'organizationId': organization['id'],
            'organizationURL' : organization['url'], 
            **snmp_config}]
    else:
        snmp_config = None
        snmp_data = None


    return snmp_data

async def _async_apicall(api_key, organizations, debug_values):
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

        admin_tasks = [_get_snmp(aiomeraki, organization) for organization in organizations]
        for task in tqdm.tqdm(
                asyncio.as_completed(admin_tasks),
                total = len(admin_tasks),
                colour='green',
                ):

            snmp_json = await task
            for organization in snmp_json:
                all_snmp.append(organization)
        
        return all_snmp


def async_get_snmp(api_key, organizations, debug_app=False):
    if debug_app:
        debug_values = {'output_log' : True, 'output_console' : True, 'suppress_logging' : False}
    else:
        debug_values = {'output_log' : False, 'output_console' : False, 'suppress_logging' : True}

    #begin async loop
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_async_apicall(api_key, organizations, debug_values))