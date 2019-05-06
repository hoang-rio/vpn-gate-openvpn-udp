
from vpngate import VPNGate
from datetime import datetime
vpngate_base_url = "https://www.vpngate.net"
csv_file_path = "output/udp"

vpngate = VPNGate(vpngate_base_url, csv_file_path)
start_time = datetime.now()
vpngate.run()
end_time = datetime.now()
running_time = end_time - start_time
print("Running in {0} seconds".format(running_time.total_seconds()))
