"""library to handle cat control"""
import logging
import socket
import xmlrpc.client


class CAT:
    """CAT control rigctld or flrig"""

    def __init__(self, interface: str, host: str, port: int) -> None:
        """initializes cat"""
        self.server = None
        self.rigctrlsocket = None
        self.interface = interface.lower()
        self.host = host
        self.port = port
        if self.interface == "flrig":
            target = f"http://{host}:{port}"
            logging.debug("cat_init: %s", target)
            self.server = xmlrpc.client.ServerProxy(target)
        if self.interface == "rigctld":
            self.__initialize_rigctrld()

    def __initialize_rigctrld(self):
        try:
            self.rigctrlsocket = socket.socket()
            self.rigctrlsocket.settimeout(0.1)
            self.rigctrlsocket.connect((self.host, self.port))
        except ConnectionRefusedError as exception:
            self.rigctrlsocket = None
            logging.debug("CAT __initialize_rigctrld: %s", exception)

    def get_vfo(self) -> str:
        """Poll the radio for current vfo using the interface"""
        vfo = ""
        if self.interface == "flrig":
            vfo = self.__getvfo_flrig()
            logging.debug("get_vfo: %s", vfo)
        if self.interface == "rigctld":
            vfo = self.__getvfo_rigctld()
            logging.debug("get_vfo: %s", vfo)
        return vfo

    def __getvfo_flrig(self) -> str:
        """Poll the radio using flrig"""
        try:
            return self.server.rig.get_vfo()
        except ConnectionRefusedError as exception:
            logging.debug("getvfo_flrig: %s", exception)
        return ""

    def __getvfo_rigctld(self) -> str:
        """Returns VFO freq returned from rigctld"""
        if self.rigctrlsocket:
            try:
                self.rigctrlsocket.settimeout(0.5)
                self.rigctrlsocket.send(b"f\n")
                return self.rigctrlsocket.recv(1024).decode().strip()
            except socket.error as exception:
                logging.debug("getvfo_rigctld: %s", exception)
                self.rigctrlsocket = None
            return ""

        self.__initialize_rigctrld()
        return ""

    def get_mode(self) -> str:
        """Returns the current mode filter width of the radio"""
        if self.interface == "flrig":
            return self.__getmode_flrig()
        if self.interface == "rigctld":
            return self.__getmode_rigctld()
        return ""

    def __getmode_flrig(self) -> str:
        """Returns mode via flrig"""
        try:
            return self.server.rig.get_mode()
        except ConnectionRefusedError as exception:
            logging.debug("getmode_flrig: %s", exception)
        return ""

    def __getmode_rigctld(self) -> str:
        """Returns mode vai rigctld"""
        if self.rigctrlsocket:
            try:
                self.rigctrlsocket.settimeout(0.5)
                self.rigctrlsocket.send(b"m\n")
                return self.rigctrlsocket.recv(1024).decode().strip().split()[0]
            except socket.error as exception:
                logging.debug("getmode_rigctld: %s", exception)
                self.rigctrlsocket = None
            return ""
        self.__initialize_rigctrld()
        return ""

    def get_power(self):
        """Get power level from rig"""
        if self.interface == "flrig":
            return self.__getpower_flrig()
        if self.interface == "rigctld":
            return self.__getpower_rigctld()
        return False

    def __getpower_flrig(self):
        try:
            return self.server.rig.get_power()
        except ConnectionRefusedError as exception:
            logging.debug("getpower_flrig: %s", exception)
            return ""

    def __getpower_rigctld(self):
        if self.rigctrlsocket:
            try:
                self.rigctrlsocket.settimeout(0.5)
                self.rigctrlsocket.send(b"l RFPOWER\n")
                return int(float(self.rigctrlsocket.recv(1024).decode().strip()) * 100)
            except socket.error as exception:
                logging.debug("getpower_rigctld: %s", exception)
                self.rigctrlsocket = None
            return ""

    def set_vfo(self, freq: str) -> bool:
        """Sets the radios vfo"""
        if self.interface == "flrig":
            return self.__setvfo_flrig(freq)
        if self.interface == "rigctld":
            return self.__setvfo_rigctld(freq)
        return False

    def __setvfo_flrig(self, freq: str) -> bool:
        """Sets the radios vfo"""
        try:
            return self.server.rig.set_frequency(float(freq))
        except ConnectionRefusedError as exception:
            logging.debug("setvfo_flrig: %s", exception)
        return False

    def __setvfo_rigctld(self, freq: str) -> bool:
        """sets the radios vfo"""
        if self.rigctrlsocket:
            try:
                self.rigctrlsocket.settimeout(0.5)
                self.rigctrlsocket.send(bytes(f"F {freq}\n", "utf-8"))
                _ = self.rigctrlsocket.recv(1024).decode().strip()
                return True
            except socket.error as exception:
                logging.debug("setvfo_rigctld: %s", exception)
                self.rigctrlsocket = None
                return False
        self.__initialize_rigctrld()
        return False

    def set_mode(self, mode: str) -> bool:
        """Sets the radios mode"""
        if self.interface == "flrig":
            return self.__setmode_flrig(mode)
        if self.interface == "rigctld":
            return self.__setmode_rigctld(mode)
        return False

    def __setmode_flrig(self, mode: str) -> bool:
        """Sets the radios mode"""
        try:
            return self.server.rig.set_mode(mode)
        except ConnectionRefusedError as exception:
            logging.debug("setmode_flrig: %s", exception)
        return False

    def __setmode_rigctld(self, mode: str) -> bool:
        """sets the radios mode"""
        if self.rigctrlsocket:
            try:
                self.rigctrlsocket.settimeout(0.5)
                self.rigctrlsocket.send(bytes(f"M {mode} 0\n", "utf-8"))
                _ = self.rigctrlsocket.recv(1024).decode().strip()
                return True
            except socket.error as exception:
                logging.debug("setmode_rigctld: %s", exception)
                self.rigctrlsocket = None
                return False
        self.__initialize_rigctrld()
        return False

    def set_power(self, power):
        """Sets the radios power"""
        if self.interface == "flrig":
            return self.__setpower_flrig(power)
        if self.interface == "rigctld":
            return self.__setpower_rigctld(power)
        return False

    def __setpower_flrig(self, power):
        try:
            return self.server.rig.set_power(power)
        except ConnectionRefusedError as exception:
            logging.debug("setmode_flrig: %s", exception)
            return False

    def __setpower_rigctld(self, power):
        if power.isnumeric() and int(power) >= 1 and int(power) <= 100:
            rig_cmd = bytes(f"L RFPOWER {str(float(power) / 100)}\n", "utf-8")
            try:
                self.rigctrlsocket.send(rig_cmd)
                _ = self.rigctrlsocket.recv(1024).decode().strip()
            except socket.error:
                self.rigctrlsocket = None
