import logging
import requests
import xml.etree.ElementTree
import re
from urllib.parse import urljoin

DEFAULT_STATUS_PATH = 'DI_S_.xml'
DEFAULT_LINE_PATH = 'PI_FXS_1_Stats.xml'

_LOGGER = logging.getLogger(__name__)

class PyObihai:


    def get_state(self, url, username, password) :

        server_origin = '{}://{}'.format('http', url)
        url = urljoin(server_origin, DEFAULT_STATUS_PATH)
        
        services = dict()
        try:
            resp = requests.get(url, auth=requests.auth.HTTPDigestAuth(username,password), timeout=2)
            root = xml.etree.ElementTree.fromstring(resp.text)
            for models in root.iter('model'):
                if models.attrib["reboot_req"]:
                    services["Reboot Required"] = models.attrib["reboot_req"]
            for o in root.findall("object") :
                name = o.attrib.get('name') 
                if 'Service Status' in name :
                    if 'OBiTALK Service Status' in name:
                        for e in o.findall("./parameter[@name='Status']/value") :
                            state = e.attrib.get('current').split()[0] # take the first word
                            services[name] = state
                    else:
                        for e in o.findall("./parameter[@name='Status']/value") :
                            state = e.attrib.get('current').split()[0] # take the first word
                            if state != 'Service':
                                for x in o.findall("./parameter[@name='CallState']/value") :
                                    state = x.attrib.get('current').split()[0] # take the first word
                                    services[name] = state
                if 'Product Information' in name:
                    for e in o.findall("./parameter[@name='UpTime']/value") :
                            state = e.attrib.get('current') # take the first word
                            services["UpTime"] = state
        except requests.exceptions.RequestException as e:
            _LOGGER.error(e)
        return services

    def get_line_state(self, url, username, password) :
        
        server_origin = '{}://{}'.format('http', url)
        url = urljoin(server_origin, DEFAULT_LINE_PATH)
        services = dict()
        try: 
            resp = requests.get(url, auth=requests.auth.HTTPDigestAuth(username,password), timeout=2)
            root = xml.etree.ElementTree.fromstring(resp.text)
            for o in root.findall("object") :
                name = o.attrib.get('name') 
                if 'Port Status' in name :
                    for e in o.findall("./parameter[@name='State']/value") :
                        state = e.attrib.get('current')# take the whole string
                        services[name] = state
                    for x in o.findall("./parameter[@name='LastCallerInfo']/value"):
                        state = x.attrib.get('current')
                        services["Last Caller Info"] = state
        except requests.exceptions.RequestException as e:
            _LOGGER.error(e)
        return services

