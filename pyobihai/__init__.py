import logging
import requests
import xml.etree.ElementTree
import re
from urllib.parse import urljoin
from datetime import datetime, timedelta, timezone

DEFAULT_STATUS_PATH = 'DI_S_.xml'
DEFAULT_LINE_PATH = 'PI_FXS_1_Stats.xml'
DEFAULT_CALL_STATUS_PATH = 'callstatus.htm'

_LOGGER = logging.getLogger(__name__)

class PyObihai:

    def __init__(self, host, username, password):
        """Initialize connection."""
        self._username = username
        self._password = password
        if self._username == "user":
            host = host + "/user/"
        self._server = '{}://{}'.format('http', host)
        self._last_reboot = datetime.now(timezone.utc)

    def get_state(self):
        """Get the state for services sensors, phone sensor and last reboot."""

        url = urljoin(self._server, DEFAULT_STATUS_PATH)

        services = dict()
        try:
            resp = requests.get(url, auth=requests.auth.HTTPDigestAuth(self._username,self._password), timeout=2)
            root = xml.etree.ElementTree.fromstring(resp.text)
            for models in root.iter('model'):
                if models.attrib["reboot_req"]:
                    services["Reboot Required"] = models.attrib["reboot_req"]
            for o in root.findall("object"):
                name = o.attrib.get('name')
                if 'Service Status' in name:
                    if 'OBiTALK Service Status' in name:
                        for e in o.findall("./parameter[@name='Status']/value"):
                            state = e.attrib.get('current').split()[0]
                            services[name] = state
                    else:
                        for e in o.findall("./parameter[@name='Status']/value"):
                            state = e.attrib.get('current').split()[0]
                            if state != 'Service':
                                for x in o.findall("./parameter[@name='CallState']/value"):
                                    state = x.attrib.get('current').split()[0]
                                    services[name] = state
                if 'Product Information' in name:
                    for e in o.findall("./parameter[@name='UpTime']/value"):
                            days = e.attrib.get('current').split()[0]
                            days = int(days)
                            time = e.attrib.get('current').split()[2]
                            h, m, s = time.split(':')
                            h = int(h)
                            m = int(m)
                            s = int(s)
                            now = datetime.now(timezone.utc)
                            state = now - timedelta(days=days, hours=h, minutes=m, seconds=s, microseconds=now.microsecond)
                            if abs(self._last_reboot - state) > timedelta(seconds=5):
                                self._last_reboot = state
                            services["Last Reboot"] = self._last_reboot.isoformat()
        except requests.exceptions.RequestException as e:
            _LOGGER.error(e)
        return services

    def get_line_state(self):
        """Get the state of the port connection and last caller info."""

        url = urljoin(self._server, DEFAULT_LINE_PATH)
        services = dict()
        try: 
            resp = requests.get(url, auth=requests.auth.HTTPDigestAuth(self._username,self._password), timeout=2)
            if (resp.status_code != 200):
                return
            root = xml.etree.ElementTree.fromstring(resp.text)
            for o in root.findall("object"):
                name = o.attrib.get('name')
                subtitle = o.attrib.get('subtitle')
                if 'Port Status' in name:
                    for e in o.findall("./parameter[@name='State']/value"):
                        state = e.attrib.get('current')
                        services[subtitle] = state
                    for x in o.findall("./parameter[@name='LastCallerInfo']/value"):
                        state = x.attrib.get('current')
                        services[subtitle + " Last Caller Info"] = state
        except requests.exceptions.RequestException as e:
            _LOGGER.error(e)
        return services

    def get_device_mac(self):
        """Get the device mac address."""

        url = urljoin(self._server, DEFAULT_STATUS_PATH)
        mac = None
        try: 
            resp = requests.get(url, auth=requests.auth.HTTPDigestAuth(self._username,self._password), timeout=2)
            root = xml.etree.ElementTree.fromstring(resp.text)
            for o in root.findall("object"):
                name = o.attrib.get('name')
                if 'WAN Status' in name:
                    for e in o.findall("./parameter[@name='MACAddress']/value"):
                        mac = e.attrib.get('current')
        except requests.exceptions.RequestException as e:
            _LOGGER.error(e)
        return mac

    def get_device_serial(self):
        """Get the device serial number."""

        url = urljoin(self._server, DEFAULT_STATUS_PATH)
        serial = None
        try: 
            resp = requests.get(url, auth=requests.auth.HTTPDigestAuth(self._username,self._password), timeout=2)
            root = xml.etree.ElementTree.fromstring(resp.text)
            for o in root.findall("object"):
                name = o.attrib.get('name')
                if 'Product Information' in name:
                    for e in o.findall("./parameter[@name='SerialNumber']/value"):
                        serial = e.attrib.get('current')
        except requests.exceptions.RequestException as e:
            _LOGGER.error(e)
        return serial

    def get_call_direction(self):
        """Get the call direction."""

        url = urljoin(self._server, DEFAULT_CALL_STATUS_PATH)
        call_direction = dict()
        call_direction['Call Direction'] = 'No Active Calls'
        try:
            response = requests.get(url, auth=requests.auth.HTTPDigestAuth(self._username,self._password), timeout=2)
            lines = response.text
            start = lines.find("Number of Active Calls:")
            if start != -1:
                temp_str = lines[start + 24:]
                end = temp_str.find("</tr>")
                if end != -1:
                    call_status = str(temp_str[:end])
                    if call_status == "1":
                        start = lines.find("Inbound")
                        if start != -1:
                            call_direction['Call Direction'] = "Inbound Call"
                        else:
                            start = lines.find("Outbound")
                            if start != -1:
                                call_direction['Call Direction'] = "Outbound Call"
        except requests.exceptions.RequestException as e:
            _LOGGER.error(e)
        return call_direction

    def check_account(self):
        """Check account credentials."""

        url = urljoin(self._server, DEFAULT_STATUS_PATH)

        try:
            response = requests.get(url, auth=requests.auth.HTTPDigestAuth(self._username,self._password), timeout=2)
            if response.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            _LOGGER.error("Invalid credentials")
        return False
