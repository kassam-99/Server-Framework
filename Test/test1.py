import datetime
import random
import subprocess
import uuid
import requests
import time
import csv
import os
import socket
import struct
import ipaddress
import sys

# Ensure Core is importable for ReportGenerator's sibling-style imports.
_project_root = os.path.abspath(__file__)
_index = _project_root.find("Server-Framework")
if _index != -1:
    sys.path.append(os.path.join(_project_root[:_index + len("Server-Framework") + 1], "Web"))
from ReportGenerator import Report_Generator

# --- Optional heavy dependencies (feature-degrade gracefully when absent) ---
try:
    import netifaces
except ImportError:
    netifaces = None
try:
    import scapy.all as scapy
except ImportError:
    scapy = None
try:
    import networkx as nx
    nx.Graph  # verify the package is fully importable (guards partial installs)
except (ImportError, AttributeError):
    nx = None
try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None


DiscoverLogo = "\n\n\033[35m\n\n" + r"""
 /$$$$$$$  /$$
| $$__  $$|__/
| $$  \ $$ /$$  /$$$$$$$  /$$$$$$$  /$$$$$$  /$$    /$$ /$$$$$$   /$$$$$$
| $$  | $$| $$ /$$_____/ /$$_____/ /$$__  $$|  $$  /$$//$$__  $$ /$$__  $$
| $$  | $$| $$|  $$$$$$ | $$      | $$  \ $$ \  $$/$$/| $$$$$$$$| $$  \__/
| $$  | $$| $$ \____  $$| $$      | $$  | $$  \  $$$/ | $$_____/| $$
| $$$$$$$/| $$ /$$$$$$$/|  $$$$$$$|  $$$$$$/   \  $/  |  $$$$$$$| $$
|_______/ |__/|_______/  \_______/ \______/     \_/    \_______/|__/
""" + "\n\033[0m\n\n"






class Discover:
    def __init__(
        self, NetworkIP_CiderIPv4: str = None, NetworkIP: str = None, 
        SubnetCiderNotation: int = None, subnet_mask: str = None, 
        NetworkInterface: str = None, WaitingTimeDelay: int = 3,
        Orginal_MAC: str = None, MOCK_MAC: list = None,
        MACsite: str = None, mac_csv_path: str = None
        ):

        self.Reporter = Report_Generator()
        self.NetworkIP_CiderIPv4 = NetworkIP_CiderIPv4
        self.NetworkIP = NetworkIP
        self.SubnetCiderNotation = SubnetCiderNotation
        self.subnet_mask = subnet_mask
        self.WaitingTime = WaitingTimeDelay
        self.Orginal_MAC = Orginal_MAC
        self.MOCK_MAC = MOCK_MAC
        self.NetworkInterface = NetworkInterface
        self.MACsite = MACsite or "https://macvendorlookup.com/api/v2/"
        self.private_IPv4 = None
        # Optional MAC vendor CSV lookup table; skipped when no path is provided.
        self.mac_vendor_data = self.read_mac_vendor_csv(mac_csv_path) if mac_csv_path else {}
        self.network_graph = nx.Graph() if nx is not None else None
             
        self.DiscoveredData = []
        self.HostData = {
            "No.": None,
            "IP": None,
            "MAC": None,
            "Vendor": None,
            "Network IP": None,
            "Network Subnet": None,
            "Protocol": None,
            "Time & Date" : None
        }
    
    
    def read_mac_vendor_csv(self, csv_file):
        """
        This function reads the MAC vendor data from a CSV file.
        You should provide the path of that file.
        The CSV file should have these columns -
        Registry, Assignment, Organization Name, Organization Address
        """
        try:
            mac_vendor_data = {}
            with open(csv_file, 'r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    mac_prefix = row.get('Assignment')[:4].upper() 
                    vendor = row.get('Organization Name')
                    if mac_prefix and vendor:
                        mac_vendor_data[mac_prefix] = vendor
            return mac_vendor_data
        except Exception as e:
            print(f"[!] Error reading MAC vendor CSV file: {e}")
            return {}


    def get_vendor_info(self, macaddress):
        """
        This function retrieves the vendor information for a given MAC address.
        """
        try:
            test = macaddress
            mac_prefix = test[:8].replace(':', '').upper()[:4]
            vendor = self.mac_vendor_data.get(mac_prefix)
            if vendor is not None:
                return vendor + " from MAC.csv"
            else:
                if self.MACsite != None:
                    macsend = self.MACsite + macaddress
                    response = requests.get(macsend, timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        if data:
                            company_info = data[0]
                            company_name = company_info.get('company', 'Unknown')
                            return company_name + " from MacVendorLookup API"
                        elif response.status_code == 204:
                            return "No vendor information available - 204"
                        else:
                            return f"Error: {response.status_code}"
                    else:
                        return f"Error: {response.status_code}"
                else:
                    return "Unknown"
        except requests.exceptions.RequestException as e:
            return f"Error while getting vendor from URL"


    def change_mac(self, RandomMAC=False, NetworkInterface=None, MAC=None, Reverse_Mode=False):
        """
        This function changes the MAC address of the network interface.
        """
        
        try:
            if Reverse_Mode == False:
                if RandomMAC == True:
                    new_mac = ":".join(["{:02x}".format(random.randint(0, 255)) for _ in range(6)])
                else:
                    new_mac = MAC
                
                if not new_mac:
                    print("[!] No MAC address provided.")
                    return
                
                interface = self.NetworkInterface or NetworkInterface
                if not interface:
                    print("[!] No network interface provided.")
                    return
                
                self.MOCK_MAC = new_mac
                print(f"[>] Changing MAC address of {interface} to {new_mac}")
                subprocess.call(["sudo", "ifconfig", interface, "down"])
                subprocess.call(["sudo", "ifconfig", interface, "hw", "ether", new_mac])
                subprocess.call(["sudo", "ifconfig", interface, "up"])
                
            else:
                interface = self.NetworkInterface or NetworkInterface
                if not interface:
                    print("[!] No network interface provided.")
                    return
                self.change_mac(RandomMAC=False, NetworkInterface=interface, MAC=self.Orginal_MAC, Reverse_Mode=False)
                
        except Exception as e:
            print(f"[!] Error changing MAC address: {e}")


    def GetNetworkData(self, PrintDetails=False, save_to_file=False):
        """
        This function retrieves the network data, including the private IP address, 
        network interface, subnet mask, network address, and other details.
        """
        if netifaces is None:
            print("[!] netifaces is not installed; network data discovery is unavailable.")
            return None
        try:
            interfaces = netifaces.interfaces()
            for iface in interfaces:
                if iface == 'lo':
                    continue
                addresses = netifaces.ifaddresses(iface)
                if netifaces.AF_INET in addresses:
                    ipv4_info = addresses[netifaces.AF_INET][0]
                    ip_address = ipv4_info['addr']
                    if ipaddress.IPv4Address(ip_address).is_private:
                        private_IPv4 = ip_address
                        public_IPv4 = subprocess.run(['curl', 'ifconfig.me'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                        network_interface = iface
                        subnet_mask_str = ipv4_info['netmask']
                        subnet_cidr = sum(bin(int(x)).count('1') for x in subnet_mask_str.split('.'))
                        subnet_mask = ipaddress.IPv4Address(subnet_mask_str)
                        Network_AddressCiderIPv4 = ipaddress.IPv4Network(ip_address + '/' + str(subnet_cidr), strict=False)
                        broadcast_address = Network_AddressCiderIPv4.broadcast_address
                        usable_hosts = list(Network_AddressCiderIPv4.hosts())
                        total_hosts = len(usable_hosts) + 2  # +1 for network address, +1 for broadcast address
                        usable_host_ip_range = f"{usable_hosts[0]} - {usable_hosts[-1]}"
                        network_IPv4 = Network_AddressCiderIPv4.network_address
                        mac_address = addresses[netifaces.AF_LINK][0]['addr']
                        break
            if PrintDetails == True:
                print(f"[>] Current network data of {Network_AddressCiderIPv4}")
                print(f"[-] Network address: {network_IPv4}")
                print(f"[-] Subnet CIDR: {subnet_cidr}")
                print(f"[-] Current Subnet: {subnet_mask}")
                print(f"[-] Broadcast Address: {broadcast_address}")
                print(f"[-] Your private IPv4: {private_IPv4}")
                print(f"[-] Your public IPv4: {public_IPv4.stdout.strip()}")
                print(f"[-] Total Number of Hosts: {total_hosts}")
                print(f"[-] Number of Usable Hosts: {len(usable_hosts)}")
                print(f"[-] Usable Host IPv4 Range: {usable_host_ip_range}")
                print(f"[-] Network Interface: {network_interface}")
                print(f"[-] MAC Address: {mac_address}")

            if save_to_file == True:
                NetworkData = {
                    "Network": str(Network_AddressCiderIPv4),
                    "Subnet": str(subnet_mask),
                    "Broadcast": str(broadcast_address),
                    "Private_IPv4": private_IPv4,
                    "Public_IPv4": public_IPv4.stdout.strip(),
                    "Total_Hosts": total_hosts,
                    "Usable_Hosts": len(usable_hosts),
                    "Usable_Hosts_Range": usable_host_ip_range,
                    "Network_Interface": network_interface,
                    "MAC_Address": mac_address
                }
                NetworkList = [NetworkData]
            
                self.Reporter.CSV_GenerateReport(Data=NetworkList)
                self.Reporter.TXT_GenerateReport(Data=NetworkList)
            
            self.NetworkIP_CiderIPv4 = Network_AddressCiderIPv4 
            self.NetworkIP = network_IPv4 
            self.SubnetCiderNotation = subnet_cidr
            self.subnet_mask = subnet_mask
            self.private_IPv4 = private_IPv4
            self.NetworkInterface = network_interface
            if self.Orginal_MAC == None:
                self.Orginal_MAC = mac_address 
            
            return (
                Network_AddressCiderIPv4,
                network_IPv4,
                subnet_cidr,
                subnet_mask,
                broadcast_address,
                private_IPv4,
                public_IPv4.stdout.strip(),
                total_hosts,
                len(usable_hosts),
                usable_host_ip_range,
                network_interface,
                mac_address
            )

        except Exception as e:
            print(f"[!] An error occurred: {e}")
            return None, None, None, None, None, None, None, None, None, None


    def ARP_DiscoverHosts(self, maxHostgroup=5, verbose=False, mapping=False, save_to_file=False):
        if scapy is None:
            print("[!] scapy is not installed; ARP discovery is unavailable.")
            return
        try:
            network_data = self.GetNetworkData(PrintDetails=verbose)
            if network_data is None:
                print("[!] Failed to get network data.")
                return
            print("[>] ARP - Scanning network for active hosts...\n")
            arp_request = scapy.ARP(pdst=f"{self.NetworkIP_CiderIPv4}")
            broadcast = scapy.Ether(dst="ff:ff:ff:ff:ff:ff")
            IPorder = 1

            while IPorder <= maxHostgroup:
                request_broadcast = broadcast / arp_request
                answered_packets, _ = scapy.srp(request_broadcast, timeout=1, verbose=False)

                for sent_packet, received_packet in answered_packets:
                    if received_packet:
                        duplicate_found = False
                        for data in self.DiscoveredData:
                            if data.get("IP") == received_packet.psrc:
                                duplicate_found = True
                                break
                        if not duplicate_found:
                            vendor_info = self.get_vendor_info(received_packet.hwsrc)
                            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            self.HostData = {
                                "No.": IPorder,
                                "IP": received_packet.psrc,
                                "MAC": received_packet.hwsrc,
                                "Vendor": vendor_info,
                                "Network IP": self.NetworkIP,
                                "Network Subnet": self.SubnetCiderNotation,
                                "Protocol": "ARP",
                                "Time & Date": timestamp
                            }
                            self.DiscoveredData.append(self.HostData)
                            if verbose == True:
                                print(f"[{IPorder}] {timestamp}\n[-] {received_packet.psrc}\n[-] {received_packet.hwsrc}\n[-] {vendor_info}\n")
                            
                            IPorder += 1
                            if IPorder > maxHostgroup:
                                break
                            
                time.sleep(self.WaitingTime)
            
            print("[$] Done!, scanning using ARP method")
            
            if save_to_file == True:
                self.Reporter.CSV_GenerateReport(Data=self.DiscoveredData)
                self.Reporter.TXT_GenerateReport(Data=self.DiscoveredData)

            if mapping == True:
                self.NetworkMapper()
                              
        except Exception as e:
            print(f"[!] Error during ARP host discovery: {e}")
            

    def ICMP_DiscoverHosts(self, maxHostgroup=5, verbose=False, mapping=False, save_to_file=False):
        try:
            network_data = self.GetNetworkData(PrintDetails=verbose)
            if network_data is None:
                print("[!] Failed to get network data.")
                return
            
            print("[>] ICMP - Scanning network for active hosts...\n")
            
            ping = 'timeout 0.2 ping -c 1 '
            IPorder = 1
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            for decimal_ip in range(int(self.NetworkIP_CiderIPv4.network_address) + 1, int(self.NetworkIP_CiderIPv4.broadcast_address)):
                if decimal_ip == self.private_IPv4:
                    continue
                
                accion = ping + str(decimal_ip)
                output = os.popen(accion).read()
                
                if 'ttl=64' in output or 'ttl=128' in output:
                    dotted_ip = socket.inet_ntoa(struct.pack('!L', decimal_ip))
                    self.HostData = {
                        "No.": IPorder,
                        "IP": dotted_ip,
                        "MAC": None,
                        "Vendor": None,
                        "Network IP": self.NetworkIP,
                        "Network Subnet": self.SubnetCiderNotation,
                        "Protocol": "ICMP",
                        "Time & Date": timestamp
                    }
                    self.DiscoveredData.append(self.HostData)
                    if verbose == True:
                        print(f"[{IPorder}] {timestamp}\n[-] IP: {dotted_ip}\n")
                    IPorder += 1
                    if IPorder > maxHostgroup:
                        break
                    time.sleep(self.WaitingTime)

            print("[$] Done!, scanning using ICMP method")
            
            if save_to_file == True:
                self.Reporter.CSV_GenerateReport(Data=self.DiscoveredData)
                self.Reporter.TXT_GenerateReport(Data=self.DiscoveredData)

            if mapping == True:
                self.NetworkMapper()
                     
        except Exception as e:
            print(f"[!] Error during ICMP host discovery: {e}")
    
    
    def ICMP_DiscoverHost(self, target, ping_count=4, verbose=False, mapping=False, save_to_file=False):
        try:
            network_data = self.GetNetworkData(PrintDetails=verbose)
            if network_data is None:
                print("[!] Failed to get network data.")
                return
            
            if verbose==True:
                print("[>] ICMP - Scanning network for active host...\n")
            ping_command = f'timeout 0.2 ping -c 1 {target}'
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            for i in range(ping_count):
                output = os.popen(ping_command).read()
                if verbose==True:
                    print(output)
                if "1 received" in output or "1 packets received" in output:
                    status = "Host is active"
                else:
                    status = "Host is inactive or unreachable"
                if verbose==True:
                    print(f"Ping attempt {i + 1}/{ping_count}: {status}")
            
            self.HostData = {
                "No.": str(uuid.uuid4()),
                "IP": target,
                "MAC": None,
                "Vendor": None,
                "Network IP": self.NetworkIP,
                "Network Subnet": self.SubnetCiderNotation,
                "Protocol": "ICMP",
                "Time & Date": timestamp,
                "Status": status
            }
            self.DiscoveredData.append(self.HostData)

            print(f"[$] Done!, scanning using ICMP method {target}")

            if save_to_file == True:
                self.Reporter.CSV_GenerateReport(Data=self.DiscoveredData)
                self.Reporter.TXT_GenerateReport(Data=self.DiscoveredData)
            
            if mapping == True:
                self.NetworkMapper()
        except Exception as e:
            print(f"[!] Error during ICMP host discovery: {e}")
                    

    def NetworkMapper(self):
        if nx is None or plt is None:
            print("[!] networkx/matplotlib not installed; network mapping is unavailable.")
            return
        try:
            self.network_graph.clear()
            for host in self.DiscoveredData:
                self.network_graph.add_node(host['IP'], label=f"\n\n{host['No.']}\n\n{host['MAC']}\n{host['Time & Date']}\n{host['Vendor']}")
                self.network_graph.add_edge(self.NetworkIP, host['IP'])

            plt.figure(figsize=(10, 8))
            pos = nx.spring_layout(self.network_graph)
            labels = nx.get_node_attributes(self.network_graph, 'label')
            nx.draw(self.network_graph, pos, with_labels=True, node_size=700, node_color='skyblue')
            nx.draw_networkx_labels(self.network_graph, pos, labels, font_size=10)
            plt.title('Network Map')
            plt.show()

        except Exception as e:
            print(f"[!] Error updating network graph: {e}")
            

    def traceroute(self, destination=None, max_hops=30, timeout=2, verbose=False):
        """
        Traces the route to a destination IP address.
        """
        if destination is None:
            print("[!] Failed to trace .")
            return
        if scapy is None:
            print("[!] scapy is not installed; traceroute is unavailable.")
            return

        try:
            port = 33434
            ttl = 1
            if verbose==True:
                print("Traceroute to", destination, "(", socket.gethostbyname(destination), "),", max_hops, "hops max")
            hop_ips = []  # List to store hop IP addresses
            while True:
                ip_packet = scapy.IP(dst=destination, ttl=ttl)
                udp_packet = scapy.UDP(dport=port)
                packet = ip_packet / udp_packet
                reply = scapy.sr1(packet, timeout=timeout, verbose=0)
                if reply is None:
                    if verbose==True:
                        print(f"{ttl}\t*")
                        
                elif reply.type == 3:
                    hop_ip = reply.src
                    hop_ips.append(hop_ip)
                    if verbose==True:
                        print(f"{ttl}\t{hop_ip}")
                    break
                else:
                    hop_ip = reply.src
                    hop_ips.append(hop_ip)
                    if verbose==True:
                        print(f"{ttl}\t{hop_ip}")
                ttl += 1
                if ttl > max_hops:
                    if verbose==True:
                        print("Max hops exceeded.")
                    break

            if verbose==True:
                print("Hop IP addresses:")
            for i, hop_ip in enumerate(hop_ips, start=1):
                if verbose==True:
                    print(f"{i}. {hop_ip}")
                    
            print(f"[$] Done!, tracing route, {destination}")
        except Exception as e:
            print(f"[!] Error during traceroute: {e}")


    def dns_lookup(self, domain_name=None, verbose=False):
        """
        Performs a DNS lookup for a given domain name.
        """
        try:
            if domain_name is None:
                print("[!] Failed to lookup .")
                return
            result = socket.gethostbyname(domain_name)
            if verbose:
                print(f"DNS lookup for {domain_name}: {result}")
            print(f"[$] Done! DNS lookup for {domain_name}")
            return result
        except socket.error as e:
            print(f"[!] Error during DNS lookup: {e}")
            return None


    def os_fingerprinting(self, target_ip=None, verbose=False):
        """
        Performs OS fingerprinting on a target IP address to identify the operating system.
        """
        try:
            if target_ip is None:
                print("[!] Failed to check fingerprint .")
                return
            if scapy is None:
                print("[!] scapy is not installed; OS fingerprinting is unavailable.")
                return
            os_signatures = {
                "Linux": {"ttl": 64, "window": 5840},
                "Windows": {"ttl": 128, "window": 8192},
                "FreeBSD": {"ttl": 64, "window": 65535},
                "MacOS": {"ttl": 64, "window": 65535},
            }
            
            pkt = scapy.IP(dst=target_ip) / scapy.TCP(dport=80, flags="S")
            response = scapy.sr1(pkt, timeout=1, verbose=0)
            
            if response:
                ttl = response[scapy.IP].ttl
                window = response[scapy.TCP].window
                for os, signature in os_signatures.items():
                    if ttl == signature["ttl"] and window == signature["window"]:
                        if verbose:
                            print(f"[+] OS detected: {os}")
                        return os
                if verbose:
                    print("[+] OS not recognized from the signature database.")
            else:
                if verbose:
                    print("[!] No response received from the target.")
            return None
        
        except Exception as e:
            print(f"[!] Error during OS fingerprinting: {e}")
            return None






class EngineDisover(Discover):
    def __init__(self):
        super().__init__()
        
        # Define menu options with their corresponding methods and default parameters
        self.MainMenu = {
            "1": ("Get Network Data", self.GetNetworkData, {
                "PrintDetails": True,
                "save_to_file": False
            }),
            "2": ("Change MAC Address", self.change_mac, {
                "RandomMAC": False,
                "NetworkInterface": None,
                "MAC": None,
                "Reverse_Mode": False
            }),
            "3": ("Discover Hosts (ARP)", self.ARP_DiscoverHosts, {
                "maxHostgroup": 5,
                "verbose": False,
                "mapping": False,
                "save_to_file": False
            }),

            "4": ("Discover Hosts (ICMP)", self.ICMP_DiscoverHosts, {
                "maxHostgroup": 5,
                "verbose": False,
                "mapping": False,
                "save_to_file": False
            }),
            "5": ("ICMP Discover Host", self.ICMP_DiscoverHost, {
                "target": None,
                "ping_count": 4,
                "verbose": False,
                "mapping": False,
                "save_to_file": False
            }),
            "6": ("Traceroute", self.traceroute, {
                "destination": None,
                "max_hops": 30,
                "timeout": 2,
                "verbose": False
            }),
            "7": ("DNS Lookup", self.dns_lookup, {
                "domain_name": None,
                "verbose": False
            }),
            "8": ("OS Fingerprinting", self.os_fingerprinting, {
                "target_ip": None,
                "verbose": False
            }),
            "9": ("Exit", lambda: exit(0), {})
        }

    def get_user_input(self, param_name, default_value=None):
        """Get user input with validation and type conversion"""
        while True:
            try:
                user_input = input(f"[\033[36m>\033[0m] Enter value for {param_name} (default: {default_value}): ").strip()
                if not user_input:
                    return default_value
                if isinstance(default_value, bool):
                    return user_input.lower() in ['true', 'yes', '1', 'y']
                elif isinstance(default_value, int):
                    return int(user_input)
                elif isinstance(default_value, float):
                    return float(user_input)
                return user_input
            except ValueError:
                print("[\033[31m!\033[0m] Invalid input. Please enter a valid value.")

    def display_menu(self):
        """Display the main menu"""
        print("\n\033[35m=== Network Discovery Tool ===\033[0m")
        for key, (title, _, _) in sorted(self.MainMenu.items()):
            print(f"\033[34m{key}\033[0m) {title}")
        print("==============================")

    def run_option(self, choice):
        """Execute the selected menu option"""
        if choice in self.MainMenu:
            title, func, defaults = self.MainMenu[choice]
            print(f"[\u001b[34m+\u001b[0m] Selected mode is: \033[32m{title}\033[0m")
            params = {}
            for param, default in defaults.items():
                params[param] = self.get_user_input(param, default)
            func(**params)
        else:
            print(f"[\033[31m!\033[0m] Invalid option: {choice}")





def main():
    engine = EngineDisover()
    print(DiscoverLogo)
    while True:
        try:
            engine.display_menu()
            choice = input("\n[\033[36m>\033[0m] Enter your choice (or 'exit' to quit): ").strip().lower()
            if choice == 'exit' or choice == '9':
                print("\033[32mGoodbye!\033[0m")
                break
            engine.run_option(choice)
        except KeyboardInterrupt:
            print("\n\033[32mProgram terminated by user\033[0m")
            break
        except Exception as e:
            print(f"[\033[31m!\033[0m] An error occurred: {e}")





if __name__ == "__main__":
    main()