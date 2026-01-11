
from vpngate import VPNGate
from datetime import datetime
# Edit it to use with mirror sites (fallback priority top down)
vpngate_base_urls = ["https://www.vpngate.net"]
# csv output file
csv_file_path = "output/udp"
sleep_time = 0

vpngate = VPNGate(vpngate_base_urls, csv_file_path, sleep_time)
start_time = datetime.now()
print("Script start at: {0}\n".format(start_time))
vpngate.run()
end_time = datetime.now()
print("Script finish at: {0}\n".format(end_time))
running_time = end_time - start_time
print("Running in {0} seconds".format(running_time.total_seconds()))
