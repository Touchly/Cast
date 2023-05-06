from cheroot import wsgi
from wsgidav.wsgidav_app import WsgiDAVApp

import os
import socket
if (os.name != "nt"):
    import fcntl
    import struct

import threading


class Server:
    def __init__(self, path=""):
        self.state = "Preparing..."
        self.path = path
        self.mapping = {}
        self.appdata = os.getenv("APPDATA")
        self.appdata = self.appdata.replace("\\", "/")
        if not os.path.exists(self.appdata+"/TouchlyCast"):
            os.mkdir(self.appdata+"/TouchlyCast")

    def clear_mounts(self):
        self.mapping = {}

    def get_state(self):
        return self.state
    
    def add_mount(self, path, name):
        #Root is new empty folder in appdata
        self.mapping["/"] = self.appdata+"/TouchlyCast"
        # Add mount
        self.mapping[name.lower()] = path

    def start_server_thread(self, server_args):
        self.server = wsgi.Server(**server_args)
        self.server.start()
    
    def stop(self):
        self.server.stop()
        self.state = "Server stopped"
    
    def start(self, port=8080, user="", password=""):
        self.state = "Starting server..."

        if user == "" and password == "":
            user_mapping = {'*': True}
        else:
            user_mapping = {'*': {user: {'password': password}}}
        
        footer = "Touchly Cast Server v0.1 - Available mounts: <ul>" + "".join([f"\n<li><a href='{k}'>{k}</a></li>" for k in self.mapping.keys()]) + "</ul>"
        
        config = {
            "host": "0.0.0.0",
            "port": port,
            "provider_mapping": self.mapping,
            "verbose": 2,
            "dir_browser": {"response_trailer": footer, "htdocs_path": self.path+"/htdocs"},
            "simple_dc": {'user_mapping': user_mapping},
        }

        # Template for a custom provider

        app = WsgiDAVApp(config)

        server_args = {
            "bind_addr": (config["host"], config["port"]),
            "wsgi_app": app,
            "server_name": "TouchlyLink"
        }
        
        try:
            self.server = wsgi.Server(**server_args)
            self.server_thread = threading.Thread(target=self.start_server_thread , args=(server_args,))
            self.server_thread.start()
            self.state = "Running server at http://"+self.get_lan_ip()+":"+str(port)+"/"
        except Exception as e:
            self.state = "Error starting server: "+ str(e)

    def get_interface_ip(self, ifname):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s',
                                ifname[:15]))[20:24])
    
    def get_lan_ip(self):
        ip = socket.gethostbyname(socket.gethostname())
        if ip.startswith("127.") and os.name != "nt":
            interfaces = [
                "eth0",
                "eth1",
                "eth2",
                "wlan0",
                "wlan1",
                "wifi0",
                "ath0",
                "ath1",
                "ppp0",
                ]
            for ifname in interfaces:
                try:
                    ip = get_interface_ip(ifname)
                    break
                except IOError:
                    pass
        return ip

if __name__ == "__main__":
    server = Server()
    ip = server.get_lan_ip()
    print("Server running at http://"+ip+":8080")
    server.add_mount("C:/Users/Pablo/Videos", "/videos")
    server.add_mount("C:/Users/Pablo/Downloads", "/downloads")
    server.start()