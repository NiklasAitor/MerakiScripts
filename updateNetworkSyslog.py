import meraki
import time
import sys

# This script interacts with the Meraki Dashboard API to:
# 1. Retrieve and filter networks based on user-defined search criteria.
# 2. Update syslog server configurations. 
# 3. Provide feedback on the number of networks updated.

API_KEY = input("Input your API Key from the Meraki Dashboard:")
org_id = 594302
dashboard = meraki.DashboardAPI(API_KEY)

# Prompt the user for search criteria and return the processed keywords.
def searchNetworks():
    Search = input("Search for networks (Enter = All): ").split(' ')
    Filter = input("Enter keywords to filter from results (Enter = None): ").split(' ')
    Tags = input("Enter tags you want to include in your search: ").split(' ')

    search_keywords = [term.strip().lower() for term in Search if term]
    filter_keywords = [term.strip().lower() for term in Filter if term]
    tags_keywords = [term.strip().lower() for term in Tags if term]

    return list(search_keywords), list(filter_keywords), list(tags_keywords)


# Retrieve and filter networks based on the provided keywords.
def filterNetworks(org_id: int, search_keywords: list, filter_keywords: list, tags_keywords: list):
    network_results = []

    retry = True
    while retry:
        try:
            org_networks = dashboard.organizations.getOrganizationNetworks(org_id)
            retry = False
        except meraki.APIError as e:
            if e.status == 429:
                print("Rate limit exceeded, retrying in 10 seconds...")
                time.sleep(10)
            if e.status == 400:
                print(f"Error: {e}")
                retry = False 
            else:
                print(f"Error: {e}")
                retry = False

    filter_keywords_set = set(filter_keywords)
    tags_keywords_set = set(tags_keywords)

    for network in org_networks:
        network_name = network['name'].lower()
        network_tags = set(tag.lower() for tag in network.get('tags', []))

        name_matches = all(keyword in network_name for keyword in search_keywords)
        name_excludes = not any(filter_word in network_name for filter_word in filter_keywords_set)
        tags_match = tags_keywords_set.issubset(network_tags)

        if name_matches and name_excludes and (not tags_keywords or tags_match):
            network_results.append(network)
    
    networks = sorted(network_results, key=lambda x: x['name'])

    return list(networks)


def printNetworks(networks: list):
    for network in networks:
        print(network['name'])
        time.sleep(0.001)

    return None

# Update syslog server configurations
def updateSyslogServers(networks: list):
    updated_networks = []
    network_count = 0

    for network in networks:
        new_syslog_servers = [
            {'host': '10.245.36.5',
             'port': 514,
             'roles':['Air Marshal events',
                      'Flows',
                      'URLs', 
                      'Wireless event log',
                      'Switch event log', 
                      'Security events'
                      ]
                }
            ]
        target_host = new_syslog_servers[0]['host']
        network_tags = network.get('tags', [])

        retry = True
        while retry:
            try:
                time.sleep(1)
                syslog = dashboard.networks.getNetworkSyslogServers(network['id'])
                retry = False
            except meraki.APIError as e:
                if e.status == 429:
                    print("Rate limit exceeded, retrying in 10 seconds...")
                    time.sleep(10)
                if e.status == 400:
                    print(f"Error: {e}")
                    print(f"Error in {network['name']}")
                    retry = False 
                else:
                    print(f"Error: {e}")
                    print(f"Error in {network['name']}")
                    retry = False
        
        syslog_servers = syslog.get('servers')
        should_update = False

        if not syslog_servers:
            should_update = True
        else:
            for server in syslog_servers:
                if server['host'] != target_host:
                    new_syslog_servers.append(server) 
                    should_update = True
                else:
                    should_update = False
                    break

        if should_update:
            result = updateRequest(network, new_syslog_servers)
            if result:
                updated_networks.append(network['name'])
                network_count += 1
    
    for u in updated_networks:
        print(u)
    print(f"{network_count} networks have been updated.")
        
    return None

# Attempt to update syslog server configurations, adjusting roles on failure.
def updateRequest(network, new_syslog_servers):
    removed = 0
    while True:
        try:
            time.sleep(1)
            response = dashboard.networks.updateNetworkSyslogServers(network['id'], new_syslog_servers)
            return True
        except meraki.APIError as e:
            if e.status == 429:
                print("Rate limit exceeded, retrying in 10 seconds...")
                time.sleep(10)
            if e.status == 400:
                print(f"Error in {network['name']}")
                if removed > 6:
                    print(f"Error: {e}")
                    return False
                removeRoles(removed, new_syslog_servers)
                removed += 1
            else:
                print(f"Error: {e}")
                print(f"Error in {network['name']}")
                return False



# Adjust the roles assigned to syslog servers to mitigate update errors.
def removeRoles(removed, new_syslog_servers):
    roles = new_syslog_servers[0]['roles']
    if removed == 0:                        # Events: Air Marshal, Wireless, Security, Flows, URLs
        roles.remove('Switch event log')
    elif removed == 1:                      # Events: Switch, Security, Flows, URLs
        roles.append('Switch event log') 
        roles.remove('Wireless event log')
        roles.remove('Air Marshal events')
    elif removed == 2:                      # Events: Air Marshal, Wireless, Switch, Flows, URLs
        roles.append('Wireless event log')
        roles.append('Air Marshal events')
        roles.remove('Security events')
    elif removed == 3:                      # Events: Switch, Flows, URLs
        roles.remove('Wireless event log')
        roles.remove('Air Marshal events')
    elif removed == 4:                      # Events: Air Marshal, Wireless, Flows, URLs
        roles.append('Wireless event log')
        roles.append('Air Marshal events')
        roles.remove('Switch event log') 
    elif removed == 5:                      # Events: Security, Flows, URLs
        roles.append('Security events')
        roles.remove('Wireless event log')
        roles.remove('Air Marshal events')
    elif removed == 6:                      # Events: Flows, URLs
        roles.remove('Security events')

    return None


def main():
    Search, Filter, Tags = searchNetworks()
    networks = filterNetworks(org_id, Search, Filter, Tags)
    print("You are updating the following networks..\n")
    time.sleep(1)
    printNetworks(networks)
    valinta = input("\nDo you wish to continue (y/n): ")
    if valinta.lower() == "y":
        updateSyslogServers(networks)
    else:
        print("Program is now closing..")
        sys.exit(1)

    return None


if __name__ == "__main__":
    main()
