import logging
import requests
import xml.etree.ElementTree
import re
from urllib.parse import urljoin
from datetime import datetime, timedelta

DEFAULT_STATUS_PATH = 'DI_S_.xml'
DEFAULT_LINE_PATH = 'PI_FXS_1_Stats.xml'

_LOGGER = logging.getLogger(__name__)

class PyObihai:

    def get_state(self, url, username, password):

        server_origin = '{}://{}'.format('http', url)
        url = urljoin(server_origin, DEFAULT_STATUS_PATH)

        services = dict()
        try:
            resp = requests.get(url, auth=requests.auth.HTTPDigestAuth(username,password), timeout=2)
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
                            state = datetime.utcnow() - timedelta(days=days, hours=h, minutes=m, seconds=s)
                            services["Last Reboot"] = state.isoformat()
        except requests.exceptions.RequestException as e:
            _LOGGER.error(e)
        return services

    def get_line_state(self, url, username, password):

        server_origin = '{}://{}'.format('http', url)
        url = urljoin(server_origin, DEFAULT_LINE_PATH)
        services = dict()
        try: 
            resp = requests.get(url, auth=requests.auth.HTTPDigestAuth(username,password), timeout=2)
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
