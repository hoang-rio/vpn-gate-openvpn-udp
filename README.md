# VPN Gate OpenVPN UDP

Parse data from [www.vpngate.net](https://www.vpngate.net) and save it to csv file like VPN Gate Public API  ([www.vpngate.net/api/iphone/](https://www.vpngate.net/api/iphone/))

### Environment required
1. Python 3.x installed

### Installation
* Setup venv with `python -m venv venv` command
* Activate venv with `veve\Script\activate` on Windows or `source venv\bin\activate` on Linux, Unix
* Install required python library with `pip install -r requirements.txt`

### How to run?
Type `python .` command then hit Enter in root directory

### Configuration
You can change output csv location in line 7 in file `__main__.py` like this
```python
# csv output file
csv_file_path = "output/udp"
```
### Donate
* [Paypal](https://paypal.me/hoangrio)

Made with ♥️ by [Hoàng Rio](https://hoangnguyendong.dev)