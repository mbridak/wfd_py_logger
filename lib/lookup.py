"""
callsign lookup classes for:
QRZ
HamDB
HamQTH
"""

import logging
from bs4 import BeautifulSoup as bs
import requests


class HamDBlookup:
    """
    Class manages HamDB lookups.
    """

    def __init__(self) -> None:
        self.url = "https://api.hamdb.org/"
        self.error = False

    def lookup(self, call: str) -> tuple:
        """
        Lookup a call on QRZ

        <?xml version="1.0" encoding="utf-8"?>
        <hamdb version="1.0">
        <callsign>
        <call>K6GTE</call>
        <class>G</class>
        <expires>11/07/2027</expires>
        <grid>DM13at</grid>
        <lat>33.8254731</lat>
        <lon>-117.9875229</lon>
        <status>A</status>
        <fname>Michael</fname>
        <mi>C</mi>
        <name>Bridak</name>
        <suffix/>
        <addr1>2854 W Bridgeport Ave</addr1>
        <addr2>Anaheim</addr2>
        <state>CA</state>
        <zip>92804</zip>
        <country>United States</country>
        </callsign>
        <messages>
        <status>OK</status>
        </messages>
        </hamdb>
        """

        logging.info("%s", call)
        grid = False
        name = False
        error_text = False
        nickname = False

        try:
            self.error = False
            query_result = requests.get(
                self.url + call + "/xml/wfd_logger", timeout=10.0
            )
        except requests.exceptions.Timeout as exception:
            self.error = True
            return grid, name, nickname, exception
        if query_result.status_code == 200:
            self.error = False
            root = bs(query_result.text, "xml")
            logging.info("\n\n%s\n\n", root)
            if root.messages.find("status"):
                error_text = root.messages.status.text
                logging.debug("HamDB: %s", error_text)
                if error_text != "OK":
                    self.error = False
            if root.find("callsign"):
                logging.debug("HamDB: found callsign field")
                if root.callsign.find("grid"):
                    grid = root.callsign.grid.text
                if root.callsign.find("fname"):
                    name = root.callsign.fname.text
                if root.callsign.find("name"):
                    if not name:
                        name = root.callsign.find("name").string
                    else:
                        name = f"{name} {root.find('name').string}"
                if root.callsign.find("nickname"):
                    nickname = root.callsign.nickname.text
        else:
            self.error = True
            error_text = str(query_result.status_code)
        logging.info("HamDB-lookup: %s %s %s %s", grid, name, nickname, error_text)
        return grid, name, nickname, error_text


class QRZlookup:
    """
    Class manages QRZ lookups. Pass in a username and password at instantiation.
    """

    def __init__(self, username: str, password: str) -> None:
        self.session = False
        self.expiration = False
        self.error = (
            False  # "password incorrect", "session timeout", and "callsign not found".
        )
        self.username = username
        self.password = password
        self.qrzurl = "https://xmldata.qrz.com/xml/134/"
        self.message = False
        self.lastresult = False
        self.getsession()

    def getsession(self) -> None:
        """
        Get QRZ session key.
        Stores key in class variable 'session'
        Error messages returned by QRZ will be in class variable 'error'
        Other messages returned will be in class variable 'message'

        <?xml version="1.0" ?>
        <QRZDatabase version="1.34">
        <Session>
            <Key>2331uf894c4bd29f3923f3bacf02c532d7bd9</Key>
            <Count>123</Count>
            <SubExp>Wed Jan 1 12:34:03 2013</SubExp>
            <GMTime>Sun Aug 16 03:51:47 2012</GMTime>
        </Session>
        </QRZDatabase>

        Session section fields
        Field	Description
        Key	a valid user session key
        Count	Number of lookups performed by this user in the current 24 hour period
        SubExp	time and date that the users subscription will expire - or - "non-subscriber"
        GMTime	Time stamp for this message
        Message	An informational message for the user
        Error	XML system error message
        """
        logging.info("QRZlookup-getsession:")
        self.error = False
        self.message = False
        self.session = False
        try:
            payload = {"username": self.username, "password": self.password}
            query_result = requests.get(self.qrzurl, params=payload, timeout=10.0)
            root = bs(query_result.text, "xml")
            logging.info("\n\n%s\n\n", root)
            if root.Session.find("Key"):
                self.session = root.Session.Key.text
            if root.Session.find("SubExp"):
                self.expiration = root.Session.SubExp.text
            if root.Session.find("Error"):
                self.error = root.Session.Error.text
            if root.Session.find("Message"):
                self.message = root.Session.Message.text
            logging.info(
                "key:%s error:%s message:%s",
                self.session,
                self.error,
                self.message,
            )
        except requests.exceptions.RequestException as exception:
            logging.info("%s", exception)
            self.session = False
            self.error = f"{exception}"

    def lookup(self, call: str) -> tuple:
        """
        Lookup a call on QRZ
        """
        logging.info("%s", call)
        grid = False
        name = False
        error_text = False
        nickname = False
        if self.session:
            payload = {"s": self.session, "callsign": call}
            try:
                query_result = requests.get(self.qrzurl, params=payload, timeout=10.0)
            except requests.exceptions.Timeout as exception:
                self.error = True
                return grid, name, nickname, exception
            root = bs(query_result.text, "xml")
            logging.info("\n\n%s\n\n", root)
            if not root.Session.Key:  # key expired get a new one
                logging.info("no key, getting new one.")
                self.getsession()
                if self.session:
                    payload = {"s": self.session, "callsign": call}
                    query_result = requests.get(
                        self.qrzurl, params=payload, timeout=3.0
                    )
            grid, name, nickname, error_text = self.parse_lookup(query_result)
        logging.info("%s %s %s %s", grid, name, nickname, error_text)
        return grid, name, nickname, error_text

    def parse_lookup(self, query_result):
        """
        Returns gridsquare and name for a callsign looked up by qrz or hamdb.
        Or False for both if none found or error.

        <?xml version="1.0" encoding="utf-8"?>
        <QRZDatabase version="1.34" xmlns="http://xmldata.qrz.com">
        <Callsign>
        <call>K6GTE</call>
        <aliases>KM6HQI</aliases>
        <dxcc>291</dxcc>
        <nickname>Mike</nickname>
        <fname>Michael C</fname>
        <name>Bridak</name>
        <addr1>2854 W Bridgeport Ave</addr1>
        <addr2>Anaheim</addr2>
        <state>CA</state>
        <zip>92804</zip>
        <country>United States</country>
        <lat>33.825460</lat>
        <lon>-117.987510</lon>
        <grid>DM13at</grid>
        <county>Orange</county>
        <ccode>271</ccode>
        <fips>06059</fips>
        <land>United States</land>
        <efdate>2021-01-13</efdate>
        <expdate>2027-11-07</expdate>
        <class>G</class>
        <codes>HVIE</codes>
        <email>michael.bridak@gmail.com</email>
        <u_views>1569</u_views>
        <bio>6399</bio>
        <biodate>2022-02-26 00:51:44</biodate>
        <image>https://cdn-xml.qrz.com/e/k6gte/qsl.png</image>
        <imageinfo>285:545:99376</imageinfo>
        <moddate>2021-04-08 21:41:07</moddate>
        <MSA>5945</MSA>
        <AreaCode>714</AreaCode>
        <TimeZone>Pacific</TimeZone>
        <GMTOffset>-8</GMTOffset>
        <DST>Y</DST>
        <eqsl>0</eqsl>
        <mqsl>1</mqsl>
        <cqzone>3</cqzone>
        <ituzone>6</ituzone>
        <born>1967</born>
        <lotw>1</lotw>
        <user>K6GTE</user>
        <geoloc>geocode</geoloc>
        <name_fmt>Michael C "Mike" Bridak</name_fmt>
        </Callsign>
        <Session>
        <Key>42d5c9736525b485e8edb782b101c74b</Key>
        <Count>4140</Count>
        <SubExp>Tue Feb 21 07:01:49 2023</SubExp>
        <GMTime>Sun May  1 20:00:36 2022</GMTime>
        <Remark>cpu: 0.022s</Remark>
        </Session>
        </QRZDatabase>

        """
        logging.info("QRZlookup-parse_lookup:")
        grid = False
        name = False
        error_text = False
        nickname = False
        if query_result.status_code == 200:
            root = bs(query_result.text, "xml")
            logging.info("\n\n%s\n\n", root)
            if root.Session.find("Error"):
                error_text = root.Session.Error.text
                self.error = error_text
            if root.find("Callsign"):
                if root.Callsign.find("grid"):
                    grid = root.Callsign.grid.text
                if root.Callsign.find("fname"):
                    name = root.Callsign.fname.text
                if root.find("name"):
                    if not name:
                        name = root.find("name").string
                    else:
                        name = f"{name} {root.find('name').string}"
                if root.Callsign.find("nickname"):
                    nickname = root.Callsign.nickname.text
        logging.info("%s %s %s %s", grid, name, nickname, error_text)
        return grid, name, nickname, error_text


class HamQTH:
    """HamQTH lookup"""

    def __init__(self, username: str, password: str) -> None:
        """initialize HamQTH lookup"""
        self.username = username
        self.password = password
        self.url = "https://www.hamqth.com/xml.php"
        self.session = False
        self.error = False
        self.getsession()

    def getsession(self) -> None:
        """get a session key"""
        logging.info("Getting session")
        self.error = False
        self.session = False
        payload = {"u": self.username, "p": self.password}
        try:
            query_result = requests.get(self.url, params=payload, timeout=10.0)
        except requests.exceptions.Timeout:
            self.error = True
            return
        logging.info("resultcode: %s", query_result.status_code)
        root = bs(query_result.text, "xml")
        if root.find("session"):
            if root.session.find("session_id"):
                self.session = root.session.session_id.text
            if root.session.find("error"):
                self.error = root.session.error.text
        logging.info("session: %s", self.session)

    def lookup(self, call: str) -> tuple:
        """
        Lookup a call on HamQTH
        """
        grid, name, nickname, error_text = False, False, False, False
        if self.session:
            payload = {"id": self.session, "callsign": call, "prg": "wfd_curses"}
            try:
                query_result = requests.get(self.url, params=payload, timeout=10.0)
            except requests.exceptions.Timeout as exception:
                self.error = True
                return grid, name, nickname, exception
            logging.info("resultcode: %s", query_result.status_code)
            root = bs(query_result.text, "xml")
            if not root.find("search"):
                if root.find("session"):
                    if root.session.find("error"):
                        if root.session.error.text == "Callsign not found":
                            error_text = root.session.error.text
                            return grid, name, nickname, error_text
                        if (
                            root.session.error.text
                            == "Session does not exist or expired"
                        ):
                            self.getsession()
                            query_result = requests.get(
                                self.url, params=payload, timeout=10.0
                            )
            grid, name, nickname, error_text = self.parse_lookup(query_result)
        logging.info("%s %s %s %s", grid, name, nickname, error_text)
        return grid, name, nickname, error_text

    def parse_lookup(self, query_result) -> tuple:
        """
        Returns gridsquare and name for a callsign looked up by qrz or hamdb.
        Or False for both if none found or error.
        """
        grid, name, nickname, error_text = False, False, False, False
        root = bs(query_result.text, "xml")
        if root.find("session"):
            if root.session.find("error"):
                error_text = root.session.error.text
        if root.find("search"):
            if root.search.find("grid"):
                grid = root.search.grid.text
            if root.search.find("nick"):
                nickname = root.search.nick.text
            if root.search.find("adr_name"):
                name = root.search.adr_name.text
        return grid, name, nickname, error_text

def main():
    """Just in case..."""
    print("I'm not a program.")

if __name__ == "__main__":
    main()
    