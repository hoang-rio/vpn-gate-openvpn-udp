
from pyquery import PyQuery
from urllib import request
import re
import csv
import base64
import time
import os
from datetime import datetime
import threading

ERROR_MSG = "Method: {0} throw exception: {1} at: {2}"

class VPNGateBase():
    def _get_url(self, url):
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
            print(ERROR_MSG.format(
                "_get_url", ex, datetime.now()))
            return None


class VPNGateItem(VPNGateBase, threading.Thread):
    def _set_data(self, *args, **kwargs):
        """
        Set class attribute
        """
        for key, value in kwargs.items():
            self.__setattr__(key, value)
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
            0).text().replace(' Mbps', '').replace(',', '')
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
        for _, match in enumerate(matches, start=1):
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
        server[12] = all_td.eq(8).find('b').eq(0).text().replace("By ", "").replace(",", "") # Remove , from operator
        # Message
        message = all_td.eq(8).find('i').eq(
            1).text().replace('"', '').replace(',', ' ')
        server[13] = re.sub(r"\n", " ", message)
        return server

    def __get_openvpn_config_base64(self, item_params):
        try:
            request_url = self.__getattribute__('__base_url') + \
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
            openvpn_config_string = self._get_url(request_url)
            if openvpn_config_string is None:
                return None
            openvpn_config_string = re.sub(
                r"#.+?$", "", openvpn_config_string, flags=re.MULTILINE)
            openvpn_config_string = re.sub(
                r"\n+", "\n", openvpn_config_string, flags=re.MULTILINE)
            openvpn_config_string = re.sub(
                r"(\n\r|\r\n)+", r"\1", openvpn_config_string, flags=re.MULTILINE)
            openvpn_config_string = re.sub(
                r"^\n\r\n", "", openvpn_config_string, flags=re.MULTILINE)
            base64_config = base64.b64encode(
                openvpn_config_string.encode('utf-8'))
            base64_config = base64_config.decode('utf-8')
            return base64_config
        except Exception as ex:
            print(ERROR_MSG.format(
                "__get_openvpn_config_base64", ex, datetime.now()))
            return None

    def __process_item(self):
        all_td = PyQuery(self.__getattribute__('__el')).find('td')
        a_tag = all_td.eq(6).find('a[href^="do_openvpn.aspx?"]')
        if a_tag.length == 0:
            print(f"Skipped server: no OpenVPN link for index {self.__getattribute__('__index')}")
            return
        href = a_tag.attr('href').replace('do_openvpn.aspx?', '')
        items = href.split('&')
        server = ['', '', '', '', '', '', '', '',
                  '', '', '', '', '', '', '', '', '', '0', '0']
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
        # L2TP support
        a_l2tp = all_td.eq(5).find('a[href="howto_l2tp.aspx"]')
        if a_l2tp.length > 0:
            # Is L2TP Support
            server[17] = '1'
        # SSTP Support
        a_sstp = all_td.eq(7).find('a[href="howto_sstp.aspx"]')
        if a_sstp.length > 0:
            server[18] = '1'
        if server[14] is None:
            print(f"Skipped server: failed to get config for {server[0]} {server[1]}")
            return  # openvpn_config_base64 is none skip this item
        if self.__getattribute__('__sleep_time') > 0:
            time.sleep(self.__getattribute__('__sleep_time'))
        self.lock.acquire()
        self.__getattribute__('__list_server').append(server)
        self.lock.release()

    def run(self):
        self.lock = threading.Lock()
        self.__process_item()


class VPNGate(VPNGateBase):

    def __init__(self, __base_urls, __file_path, __sleep_time):
        self.__base_urls = __base_urls
        self.__file_path = __file_path
        self.__sleep_time = __sleep_time
        self.__list_server = [
            ['*vpn_servers'],
            ['#HostName', 'IP', 'Score', 'Ping', 'Speed', 'CountryLong', 'CountryShort', 'NumVpnSessions', 'Uptime', 'TotalUsers', 'TotalTraffic', 'LogType', 'Operator', 'Message', 'OpenVPN_ConfigData_Base64', 'TcpPort', 'UdpPort', 'L2TP', 'SSTP']
        ]
        self._threads = []
        self.active_threads = []

    def _get_working_base_url(self):
        for url in self.__base_urls:
            html = self._get_url(url + '/en/')
            if html is not None:
                return (url, html)
        return (None, None)

    def __write_csv_file(self, __file_path):
        csv.register_dialect('myDialect', delimiter=',', lineterminator='\n')
        with open(__file_path, 'w', encoding='utf-8') as write_file:
            writer = csv.writer(write_file, dialect="myDialect")
            writer.writerows(self.__list_server)
        write_file.close()

    def __process_item(self, index, el):
        t = VPNGateItem()
        t._set_data(__index=index, __el=el, __base_url=self.__base_url, __file_path=self.__file_path,
                    __sleep_time=self.__sleep_time, __list_server=self.__list_server)
        self.active_threads.append(t)
        t.start()
        if len(self.active_threads) >= 10:
            self.active_threads[0].join()
            self.active_threads.pop(0)
        self._threads.append(t)

    def start_process(self, lock_file_path):
        try:
            with open(lock_file_path, 'w') as lock_file:
                lock_file.write("{0}".format(datetime.now()))
                lock_file.close()
            working_url, html = self._get_working_base_url()
            if working_url is None:
                print("No working base URL found.")
                return
            print(f"Selected working base url: '{working_url}'\n")
            self.__base_url = working_url
            if html is not None:
                pq = PyQuery(html)
                openvpn_links = pq('#vg_hosts_table_id').eq(2).find('tr')
                print("Total server tr found: {0}\n".format(openvpn_links.length - 1))
                # Process each item
                openvpn_links.each(self.__process_item)
                # Join thread
                for t in self._threads:
                    t.join()
                if len(self.__list_server) < 2:
                    print("Skip write file because empty server list")
                    return
                print("Total server processed: {0}\n".format(len(self.__list_server) - 2))
                self.__write_csv_file(self.__file_path)
        except Exception as ex:
            print(ERROR_MSG.format(
                "run", ex, datetime.now()))
        finally:
            if os.path.exists(lock_file_path):
                # Remove lock when complete
                os.remove(lock_file_path)

    def run(self):
        lock_file_path = 'vpngate.lock'
        if (os.path.exists(lock_file_path)):
            with open(lock_file_path, 'r') as lock_file:
                lock_time = datetime.strptime(
                    lock_file.read(), '%Y-%m-%d %H:%M:%S.%f')
                lock_file.close()
                time_from_last_lock = datetime.now() - lock_time
                if time_from_last_lock.total_seconds() > 60 * 20:
                    print("Lock file expired. Script coninue to run.\n")
                else:
                    print("Lock file found. Script currently runing.\n")
                    return
        self.start_process(lock_file_path)
