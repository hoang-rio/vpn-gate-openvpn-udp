
from pyquery import PyQuery
from urllib import request

vpngate_base_url = "https://www.vpngate.net/en/"
csv_file_path = "file.csv"


def get_html(url):
    req = request.Request(url)
    with request.urlopen(req) as response:
        html = response.read().decode(response.headers.get_content_charset())
    return html


def to_csv(data):
    csv = ''
    for row in data:
        csv += ','.join([str(x) for x in row]) + "\n"

    return csv


def write_to_file(file_path, content):
    with open(file_path, 'w', encoding='utf-8') as write_to_file:
        write_to_file.write(content)


def main():
    html = get_html(vpngate_base_url)
    pq = PyQuery(html)
    _list_server = []
    _list_server.append([
        '#HostName', 'IP', 'TcpPort', 'UdpPort',
    ])
    openvpn_links = pq('a[href^="do_openvpn.aspx"]')
    for a in openvpn_links:
        href = a.attrib['href']
        href = href.replace('do_openvpn.aspx?', '')
        items = href.split('&')
        server = []
        for item in items:
            prop = item.split('=')
            server.append(prop[1])
        _list_server.append(server)
    write_to_file(csv_file_path, to_csv(_list_server))


main()
