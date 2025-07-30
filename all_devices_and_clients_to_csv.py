import meraki 
import time
import csv

# This script interacts with the Meraki Dashboard API to fetch network, client and device data.
# Exports the information to CSV files.

API_KEY = input("Input your API Key from the Meraki Dashboard:")
org_id = X
dashboard = meraki.DashboardAPI(API_KEY)


def searchNetworks():
    Search = input("Search for networks (Enter = All): ").lower().split(' ')
    Filter = input("Enter keywords to filter from results (Enter = None): ").lower().split(' ')
    Tags = input("Enter tags you want to include in your search:").lower().split(' ')

    search_keywords = [term.strip() for term in Search if term]
    filter_keywords = [term.strip() for term in Filter if term]
    tags_keywords = [term.strip() for term in Tags if term]

    return list(search_keywords), list(filter_keywords), list(tags_keywords)


def filterNetworks(org_id: int, search_keywords: list, filter_keywords: list, tags_keywords):
    network_results = []

    org_networks = dashboard.organizations.getOrganizationNetworks(org_id)

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


def print_networks(networks: dict):
    for id in networks:
        print (networks[id])
        time.sleep(0.001)

    return None


def CreateFileHeaders(file_name: str, headers: list):
    with open(file_name, 'w', newline='', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file, delimiter=';')
        writer.writerow(headers)

    return None

    
def Datatocsv(file_name: str, dataList: list):
    with open(file_name, 'a', newline='', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file, delimiter=';')
        for Info in dataList:
            writer.writerow(Info.values())

    return None


def get_devices(network_id: str):
    devicesList = []
    retry = True
    while retry:
        try:
            devices = dashboard.networks.getNetworkDevices(network_id)
            time.sleep(0.2)
            retry = False
        except meraki.APIError as e:
            if e.status == 429:
                print("Rate limit exceeded, retrying in 5 seconds...")
                time.sleep(5)
            else:        
                print(f"Error {e}")
                retry = False
    print(devices)
    for device in devices:
        devicesDict = {
        'name': 'None',
        'model': 'None',
        'serial': 'None',
        'firmware': 'None',
        'mac': 'None',
        'lanIp': 'None',
        'wan1Ip': 'None',
        'wan2Ip': 'None'
        } 
        for i in device:
            if i in devicesDict:
                devicesDict[i] = device[i]
        devicesList.append(devicesDict)

    return list(devicesList)


def get_clients(network_id: str, network_name: str):
    clientsList = []
    retry = True
    while retry:
        try:
            clients = dashboard.networks.getNetworkClients(network_id, timespan=2678400, total_pages='all')
            time.sleep(0.2)
            retry = False
        except meraki.APIError as e:
            if e.status == 429:
                print("Rate limit exceeded, retrying in 5 seconds...")
                time.sleep(5)
            else:        
                print(f"Error {e}")
                retry = False

    for client in clients:
        clientsDict = {
            'network': network_name,
            'id': 'None',
            'description': 'None',
            'mac': 'None',
            'ip': 'None',
            'ip6': 'None',
            'user': 'None',
            'firstSeen': 'None',
            'lastSeen': 'None',
            'os': 'None',
            'ssid': 'None'
        }
        for i in client:
            if i in clientsDict:
                clientsDict[i] = client[i]
        clientsList.append(clientsDict)

    return list(clientsList)


def main():
    HeadersDevices = ["Name", "Model", "Serial", "Firmware", "Mac", "LanIP", "Wan1IP", "Wan2IP"]
    HeadersClients = ["Network", "ID", "Description", "Mac", "IPv4", "IPv6", "User", "First Seen", "Last Seen", "Os", "SSID"]

    Search, Filter, Tags = searchNetworks()
    networks = filterNetworks(org_id, Search, Filter, Tags)
    print("Getting data from the following networks..\n")
    time.sleep(1)
    print_networks(networks)
    Valinta = input("Do you wish to continue?(Y/N)").lower()

    if Valinta == 'y':
        print("Importing Meraki data to a csv file.")
        CreateFileHeaders('mehi_devices.csv', HeadersDevices)
        CreateFileHeaders('mehi_clients.csv', HeadersClients)
        for network_id, network_name in networks.items():
            devicesList = get_devices(network_id)
            Datatocsv('mehi_devices.csv', devicesList)
            clientsList = get_clients(network_id, network_name)
            Datatocsv('mehi_clients.csv', clientsList)
    elif Valinta == 'n':
        print("The program will close now.")

    return None


if __name__ == "__main__":
    main()
