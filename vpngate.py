
from pyquery import PyQuery
from urllib import request
import re
import csv
import base64
import time
import os
from datetime import datetime


class VPNGate():

    def __init__(self, __base_url, __file_path, __sleep_time):
        self.__base_url = __base_url
        self.__file_path = __file_path
        self.__sleep_time = __sleep_time
        self.__list_server = [['*vpn_servers']]

    def __get_url(self, url):
        try:
            req = request.Request(url)
            with request.urlopen(req, timeout=8) as response:
                if response.headers.get_content_charset() == None:
                    encoding = 'utf-8'
                else:
                    encoding = response.headers.get_content_charset()
                html = response.read().decode(encoding)
            return html
        except Exception as ex:
            print("Method: {0} throw exception: {1} at: {2}".format(
                "__get_url", ex, datetime.now()))
            return None

    def __write_csv_file(self, __file_path):
        csv.register_dialect('myDialect', delimiter=',', lineterminator='\n')
        with open(__file_path, 'w', encoding='utf-8') as write_file:
            writer = csv.writer(write_file, dialect="myDialect")
            writer.writerows(self.__list_server)
        write_file.close()

    ##
    # Fill another value
    ##
    def __fill_other_value(self, all_td, server):
        # Score
        server[2] = int(all_td.eq(9).text().replace(',', ''))
        # Ping
        server[3] = all_td.eq(3).find('b').eq(1).text().replace(' ms', '')
        # Speed
        speed_text = all_td.eq(3).find('b').eq(
            0).text().replace(' Mbps', '')
        speed = float(speed_text)
        server[4] = int(speed * pow(1024, 2))
        # CountryLong
        server[5] = all_td.eq(0).text().strip()
        # CountryShort Ex image src ../images/flags/CO.png
        image_src = all_td.eq(0).find('img').eq(0).attr('src')
        server[6] = image_src[16:-4]
        # NumVpnSessions
        server[7] = all_td.eq(2).find('b').eq(
            0).text().replace(' sessions', '')
        # Uptime
        uptime_text = all_td.eq(2).find('span').eq(1).text()
        uptime_prop = uptime_text.split(' ')
        if len(uptime_prop) > 1:
            if uptime_prop[1] == 'days':
                uptime = int(uptime_prop[0]) * 24 * 60 * 60
            elif uptime_prop[1] == 'hours':
                uptime = int(uptime_prop[0]) * 60 * 60
            elif uptime_prop[1] == 'mins':
                uptime = int(uptime_prop[0]) * 60
            else:
                uptime = 0
        else:
            uptime = 0
        server[8] = uptime
        # TotalUsers
        total_user_text = all_td.eq(2).text()
        regex = r"Total\s([\d,]+)\susers"
        matches = re.finditer(regex, total_user_text)
        for matchNum, match in enumerate(matches, start=1):
            total_user = match.group(1)
            server[9] = int(total_user.replace(',', ''))
            break
        # TotalTraffic
        total_traffic_text = all_td.eq(3).find('b').eq(2).text()
        total_traffic_props = total_traffic_text.split(' ')
        if len(total_traffic_text) > 1:
            total_traffic_str = total_traffic_props[0].replace(',', '')
            if total_traffic_props[1] == 'GB':
                server[10] = int(float(total_traffic_str) * pow(1024, 3))
            elif total_traffic_props[1] == 'MB':
                server[10] = int(float(total_traffic_str) * pow(1024, 2))
            elif total_traffic_props[1] == 'KB':
                server[10] = int(float(total_traffic_str) * 1024)
            else:
                server[10] = int(total_traffic_str)
        # LogType
        server[11] = '2 Weeks'
        # Operator
        server[12] = all_td.eq(8).find('b').eq(0).text().replace("By ", "")
        # Message
        message = all_td.eq(8).find('i').eq(
            1).text().replace('"', '').replace(',', ' ')
        server[13] = re.sub(r"\n", " ", message)
        return server

    def __get_openvpn_config_base64(self, item_params):
        try:
            request_url = self.__base_url + \
                '/common/openvpn_download.aspx?sid=%s&%s&host=%s&port=%s&hid=%s&/vpngate_%s.ovpn'
            for item in item_params:
                props = item.split('=')
                if len(props) < 2:
                    continue
                elif props[0] == 'ip':
                    ip = props[1]
                elif props[0] == 'tcp':
                    tcp_port = props[1]
                elif props[0] == 'udp':
                    udp_port = props[1]
                elif props[0] == 'sid':
                    sid = props[1]
                elif props[0] == 'hid':
                    hid = props[1]
            if tcp_port != '0':
                request_url = request_url % (
                    sid, 'tcp=1', ip, tcp_port, hid, ip + '_tcp_'+tcp_port)
            elif udp_port != '0':
                request_url = request_url % (
                    sid, 'udp=1', ip, udp_port, hid, ip + '_udp_'+udp_port)
            openvpn_config_string = self.__get_url(request_url)
            if openvpn_config_string is None:
                return None
            openvpn_config_string =  re.sub(r"#.+?$", "", openvpn_config_string, flags=re.MULTILINE)
            openvpn_config_string = re.sub(r"\n+", "\n", openvpn_config_string, flags=re.MULTILINE)
            openvpn_config_string = re.sub(r"(\n\r|\r\n)+", r"\1", openvpn_config_string, flags=re.MULTILINE)
            openvpn_config_string = re.sub(r"^\n\r\n", "", openvpn_config_string, flags=re.MULTILINE)
            base64_config = base64.b64encode(
                openvpn_config_string.encode('utf-8'))
            base64_config = base64_config.decode('utf-8')
            return base64_config
        except Exception as ex:
            print("Method: {0} throw exception: {1} at: {2}".format(
                "__get_openvpn_config_base64", ex, datetime.now()))
            return None

    def __process_item(self, index, el):
        all_td = PyQuery(el).find('td')
        a_tag = all_td.eq(6).find('a[href^="do_openvpn.aspx?"]')
        if a_tag.length == 0:
            return
        href = a_tag.attr('href').replace('do_openvpn.aspx?', '')
        items = href.split('&')
        server = ['', '', '', '', '', '', '', '',
                  '', '', '', '', '', '', '', '', '']
        for item in items:
            props = item.split('=')
            if len(props) < 2:
                continue
            if props[0] == 'fqdn':
                server[0] = props[1].replace('.opengw.net', '')
            elif props[0] == 'ip':
                server[1] = props[1]
            elif props[0] == 'tcp':
                server[15] = props[1]
            elif props[0] == 'udp':
                server[16] = props[1]
        server = self.__fill_other_value(all_td, server)
        # OpenVPN_ConfigData_Base64
        server[14] = self.__get_openvpn_config_base64(items)
        if server[14] is None:
            return  # openvpn_config_base64 is none skip this item
        if self.__sleep_time > 0:
            time.sleep(self.__sleep_time)
        self.__list_server.append(server)

    def run(self):
        lock_file_path = 'vpngate.lock'
        can_run = True
        if (os.path.exists(lock_file_path)):
            with open(lock_file_path, 'r') as lock_file:
                lock_time = datetime.strptime(
                    lock_file.read(), '%Y-%m-%d %H:%M:%S.%f')
                lock_file.close()
                time_from_last_lock = datetime.now() - lock_time
                if time_from_last_lock.total_seconds() > 60 * 20:
                    can_run = True
                    print("Lock file expired. Script coninue to run.\n")
                else:
                    can_run = False
                    print("Lock file found. Script currently runing.\n")
        if can_run:
            try:
                with open(lock_file_path, 'w') as lock_file:
                    lock_file.write("{0}".format(datetime.now()))
                    lock_file.close()
                html = self.__get_url(self.__base_url+'/en/')
                if html is not None:
                    pq = PyQuery(html)
                    self.__list_server.append([
                        '#HostName', 'IP', 'Score', 'Ping', 'Speed', 'CountryLong', 'CountryShort', 'NumVpnSessions', 'Uptime', 'TotalUsers', 'TotalTraffic', 'LogType', 'Operator', 'Message', 'OpenVPN_ConfigData_Base64', 'TcpPort', 'UdpPort'
                    ])
                    openvpn_links = pq('#vg_hosts_table_id').eq(2).find('tr')
                    openvpn_links.each(self.__process_item)
                    if len(self.__list_server) < 2:
                        print("Skip write file because empty server list")
                        return
                    self.__write_csv_file(self.__file_path)
            except Exception as ex:
                print("Method: {0} throw exception: {1} at: {2}".format(
                    "run", ex, datetime.now()))
            finally:
                if os.path.exists(lock_file_path):
                    # Remove lock when complete
                    os.remove(lock_file_path)
