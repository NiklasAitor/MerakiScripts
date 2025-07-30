import meraki 
import time
import sys

# Purpose: Script to update SSIDs with authmode RADIUS to Meraki networks via the Meraki Dashboard API.
# Usage: This script allows users to search and filter networks, update SSID entries based on user inputs.
# Requirements: Requires an API key for the Meraki Dashboard API and the Meraki Python SDK.
# Note: Please review all configurations carefully before deploying.

API_KEY = input("Input your API Key from the Meraki Dashboard:")
org_id = X
dashboard = meraki.DashboardAPI(API_KEY)


def Haku():
    Search = input("Search for networks(Enter = All): ").lower().split(' ')
    Filter = input("Enter keywords to filter from results (comma-separated): ").lower().split(' ')

    Search_keywords = [term.strip() for term in Search if term]
    Filter_keywords = [term.strip() for term in Filter if term]

    return list(Search_keywords), list(Filter_keywords)


def SSID_conf(): 
    name =  input("Give the SSID a name: ")
    id = input("Give the SSID an ID for VLAN tagging: ")
    tagging = input("Do you want to enable VLAN tagging?(Y/N)").lower()
    
    if tagging == 'y':
        tagging = True
        vlanid = id
    else:
        tagging = False
        vlanid = None

    SSID_info = {
        "name": name,
        "enabled": True,
        "authMode": "open-with-radius", 
        "defaultVlanId": id,
        "encryptionMode": "wpa",
        "wpaEncryptionMode": "WPA2 only",
        "ipAssignmentMode": "Bridge mode",
        "useVlanTagging": tagging,
        "defaultVlanId": vlanid,
        "radiusServers": [  
            {
            "host": "0.0.0.0",
            "port": 3000,
            "secret": "secret-string",
            "radsecEnabled": True,
            "openRoamingCertificateId": 2,
            }
        ]
        }

    return dict(SSID_info)


def get_networks(org_id: int, Search_keywords: list, Filter_keywords: list):  
    NETWORKS = {}
    org_networks = dashboard.organizations.getOrganizationNetworks(org_id)

    for network in org_networks:
        network_name = network['name'].lower()
        network_id = network['id']

        if all(keyword in network_name for keyword in Search_keywords):
            if not any(filter_word in network_name for filter_word in Filter_keywords):
                    NETWORKS[network_id] = network_name

    return dict(NETWORKS) 


def print_networks(NETWORKS: dict):
    for id in NETWORKS:
        print (NETWORKS[id])
        time.sleep(0.05)

    return None


def add_ssids(NETWORKS: dict, SSID_info: dict): 
    action_batches_ssid = []
    counter = 0
    batch_ids = []

    for network_id in NETWORKS:

        retry = True
        while retry:
            try:
                get_ssids = dashboard.wireless.getNetworkWirelessSsids(network_id)
                time.sleep(0.2)
                retry = False
            except meraki.APIError as e:
                if e.status == 429:
                    print("Rate limit exceeded, retrying in 5 seconds...")
                    time.sleep(5)
                else:
                    print(f"Error: {e}")
                    retry = False

        ssid_number = None

        for ssid in get_ssids:
            ssid_name = ssid['name'].lower()

            if  SSID_info['name'].lower() == ssid_name:
                ssid_number = ssid['number']
                action = {
                    "resource": f"/networks/{network_id}/wireless/ssids/{ssid_number}",
                    "operation": "update",
                    "body": SSID_info
                    }
                action_batches_ssid.append(action)
                counter += 1
                break 
        
        if len(action_batches_ssid) == 100 or counter == len(NETWORKS):
            try:   
                batch = dashboard.organizations.createOrganizationActionBatch(
                    org_id,
                    action_batches_ssid, 
                    confirmed=True, 
                    synchronous=False
                    )
                action_batches_ssid.clear()
                print("Action batch sent.. continuing in 10 seconds")
                time.sleep(10)
                batch_id = batch['id']
                batch_ids.append(batch_id)
            except meraki.APIError as e:
                print(f"Failed to send action batch: {e}")

        status = check_batch_status(org_id, batch_ids)
        time.sleep(10)
        while status:
            status = check_batch_status(org_id, batch_ids)
            time.sleep(10)

    return None


def check_batch_status(org_id: int, batch_ids: list, max_retries=30):
    for batch_id in batch_ids:
        retries = 0
        while True:  
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
    Search, Filter = Haku()
    SSID_info = SSID_conf()
    NETWORKS = get_networks(org_id, Search, Filter)
    print("You are configuring the following networks..\n")
    time.sleep(1)
    print_networks(NETWORKS)
    time.sleep(1)
    print("\nYou have given the following configurations..\n")
    time.sleep(1)
    for maaritys in SSID_info:
        print(f"{maaritys}: {SSID_info[maaritys]}")
        time.sleep(0.025)
    Valinta = input("\nWill you accept these changes? (Y/N)").lower()
    if Valinta == 'y':
        batch_ids = add_ssids(NETWORKS, SSID_info)
        print("All configurations are done.\n")
    elif Valinta == 'n':
        print("The program will close now.")
    
    return None


if __name__ == "__main__":
    main()

