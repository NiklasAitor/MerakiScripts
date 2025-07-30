import meraki # Needs Meraki Python SDK installed
import time
import sys

# This script interacts with the Cisco Meraki Dashboard API to search for networks within an organization,
# filter them by name and tags, and update the configuration of a specified SSID on those networks.
# Specifically, it enables and configures the SSID to use 802.1X RADIUS authentication with given RADIUS server details,
# and performs these updates in action batches to handle multiple networks efficiently.

API_KEY = input("Input your API Key from the Meraki Dashboard:")
org_id = X
dashboard = meraki.DashboardAPI(API_KEY)


def Haku():
    Search = input("Search for networks (Enter = All): ").split(' ')
    Filter = input("Enter keywords to filter from results (Enter = None): ").split(' ')
    Tags = input("Enter tags you want to include in your search:").split(' ')

    search_keywords = [term.strip() for term in Search if term]
    filter_keywords = [term.strip() for term in Filter if term]
    tags_keywords = [term.strip() for term in Tags if term]

    return list(search_keywords), list(filter_keywords), list(tags_keywords)


def SSID_conf():

    name =  input("Which SSID do you wish to update? (ie. Mtoimisto): ")
    radiusIp = input("Radius server IP: ")
    radiusSecret = input("Radius server secret/password: ")
    
    SSID_info = {
        "name": name,
        "enabled": True,
        "authMode": "8021x-radius", 
        "wpaEncryptionMode": "WPA2 only",
        "ipAssignmentMode": "Bridge mode",
        "radiusServers": [  
            {
            "host": radiusIp,
            "port": 1812,
            "secret": radiusSecret,
            }
        ],
        "dot11r": {
            "enabled": True,
            "adaptive": False
            }
        }

    return dict(SSID_info)


def filterNetworks(org_id: int, search_keywords: list, filter_keywords: list, tags_keywords):
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



def print_networks(NETWORKS: dict):
    for id in NETWORKS:
        print (NETWORKS[id])
        time.sleep(0.001)

    return None


def updateSSIDS(NETWORKS: dict, SSID_info: dict):
    action_batches_ssid = []
    counter = 0
    networkList = []
    new_radiusIp = SSID_info["radiusServers"][0]["host"]

    for network_id, network_name in NETWORKS.items():
        get_ssids = None
        retry = True
        while retry:
            try:
                get_ssids = dashboard.appliance.getNetworkApplianceSsids(network_id)
                time.sleep(0.4)
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

        ssid_number = None
        if get_ssids:
            for ssid in get_ssids:
                enabled = ssid.get('enabled')
                if SSID_info['name'].lower() == ssid['name'].lower() and enabled:
                    ssid_radius = ssid.get('radiusServers', [])
                    if ssid_radius:
                        for i in ssid_radius:
                            host = i.get('host')
                            if host != new_radiusIp:
                                ssid_number = ssid['number']
                                action = {
                                    "resource": f"/networks/{network_id}/appliance/ssids/{ssid_number}",
                                    "operation": "update",
                                    "body": SSID_info
                                    }
                                action_batches_ssid.append(action)
                                networkList.append(network_name)

        counter += 1  
        if len(action_batches_ssid) == 100 or counter == len(NETWORKS):
            try:   
                batch = dashboard.organizations.createOrganizationActionBatch(
                    org_id,
                    action_batches_ssid, 
                    confirmed=True, 
                    synchronous=False
                    )
                action_batches_ssid.clear()
                print("Action batch sent..")
                for x in networkList:
                    print(x)
            except meraki.APIError as e:
                print(f"Failed to send action batch: {e}")
                print(f"The program will now close.")
                sys.exit(1)
            
            while check_batch_status(org_id, batch['id']):
                time.sleep(10)

            break

    return None


def check_batch_status(org_id: int, batch_id: str):
    max_retries=30
    retries = 0
    while retries < max_retries:  
        try:
            status = dashboard.organizations.getOrganizationActionBatch(org_id, batch_id)
            print(f"Batch ID {batch_id} status: {status['status']}")

            if status['status'].get('completed', False):
                print(f"Batch {batch_id} completed successfully.")
                time.sleep(10)
                return False
            elif status['status'].get('failed', False):
                print(f"Batch {batch_id} failed with errors: {status['errors']}")
                time.sleep(10) 
                return True
            else:
                print(f"Batch {batch_id} is still in progress or pending. Checking again in 10 seconds.")
                time.sleep(10)
                retries += 1
        except meraki.APIError as e:
            print(f"Failed to retrieve status for batch {batch_id}: {e}")
            break
        
    print(f"Exceeded max retries for batch {batch_id}. The program will now close.")
    sys.exit(1)

    return True


def main():
    Search, Filter, Tags = Haku()
    SSID_info = SSID_conf()
    networks = filterNetworks(org_id, Search, Filter, Tags)
    print("You are configuring the following networks..\n")
    time.sleep(1)
    print_networks(networks)
    time.sleep(1)
    print("\nYou have given the following configurations..\n")
    time.sleep(1)
    for maaritys in SSID_info:
        print(f"{maaritys}: {SSID_info[maaritys]}")
        time.sleep(0.025)
    Valinta = input("\nWill you accept these changes? (Y/N)").lower()
    if Valinta == 'y':
        updateSSIDS(networks, SSID_info)
        print("All configurations are done.\n")
    elif Valinta == 'n':
        print("The program will close now.")
    
    return None


if __name__ == "__main__":
    main()

