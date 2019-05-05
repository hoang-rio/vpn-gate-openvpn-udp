
from vpngate import VPNGate
vpngate_base_url = "https://www.vpngate.net/en/"
csv_file_path = "file.csv"

vpngate = VPNGate(vpngate_base_url, csv_file_path)
vpngate.run()
