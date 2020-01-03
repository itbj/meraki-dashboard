import csv
from datetime import datetime
import os

import meraki

# Either input your API key below (insecure), or set an environment variable (preferred)
# for example, in Terminal on macOS:  export MERAKI_DASHBOARD_API_KEY=093b24e85df15a3e66f1fc359f4c48493eaa1b73
# api_key = '093b24e85df15a3e66f1fc359f4c48493eaa1b73'


def main():
    # Instantiate a Meraki dashboard API session
    dashboard = meraki.DashboardAPI(api_key='', base_url='https://api.meraki.com/api/v0/', log_file_prefix=__file__[:-3], print_console=False)

    # Get list of organizations to which API key has access
    organizations = dashboard.organizations.getOrganizations()

    # Iterate through list of orgs
    for org in organizations:
        print(f'\nAnalyzing organization {org["name"]}:')
        org_id = org['id']

        # Get list of networks in organization
        try:
            networks = dashboard.networks.getOrganizationNetworks(org_id)
        except meraki.APIError as e:
            print(f'Meraki API error: {e}')
            continue
        except Exception as e:
            print(f'some other error: {e}')
            continue
        
        # Create local folder
        todays_date = f'{datetime.now():%Y-%m-%d}'
        folder_name = f'Org {org_id} clients {todays_date}'
        if folder_name not in os.listdir():
            os.mkdir(folder_name)

        # Iterate through networks
        total = len(networks)
        counter = 1
        print(f'  - iterating through {total} networks in organization {org_id}')
        for net in networks:
            print(f'Finding clients in network {net["name"]} ({counter} of {total})')
            try:
                # Get list of clients on network, filtering on timespan of last 14 days
                clients = dashboard.clients.getNetworkClients(net['id'], timespan=60*60*24*14, perPage=1000, total_pages='all')
            except meraki.APIError as e:
                print(f'Meraki API error: {e}')
            except Exception as e:
                print(f'some other error: {e}')
            else:
                if clients:
                    # Write to file
                    file_name = f'{net["name"]}.csv'
                    output_file = open(f'{folder_name}/{file_name}', mode='w', newline='\n')
                    field_names = clients[0].keys()
                    csv_writer = csv.DictWriter(output_file, field_names, delimiter=',', quotechar='"',
                                                quoting=csv.QUOTE_ALL)
                    csv_writer.writeheader()
                    csv_writer.writerows(clients)
                    output_file.close()
                    print(f'  - found {len(clients)}')

            counter += 1

        # Stitch together one consolidated CSV per org
        output_file = open(f'{folder_name}.csv', mode='w', newline='\n')
        field_names = list(field_names)
        field_names.insert(0, 'Network Name')
        field_names.insert(1, 'Network ID')
        csv_writer = csv.DictWriter(output_file, field_names, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
        csv_writer.writeheader()
        for net in networks:
            file_name = f'{net["name"]}.csv'
            if file_name in os.listdir(folder_name):
                with open(f'{folder_name}/{file_name}') as input_file:
                    csv_reader = csv.DictReader(input_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
                    next(csv_reader)
                    for row in csv_reader:
                        row['Network Name'] = net['name']
                        row['Network ID'] = net['id']
                        csv_writer.writerow(row)


if __name__ == '__main__':
    start_time = datetime.now()
    main()
    end_time = datetime.now()
    print(f'\nScript complete, total runtime {end_time - start_time}')
