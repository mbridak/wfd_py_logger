#!/usr/bin/env python3
"""
K6GTE Winter Field Day logger curses based.
Email: michael.bridak@gmail.com
GPL V3
"""

# pylint: disable=too-many-lines
# pylint: disable=global-statement
# pylint: disable=redefined-outer-name
# pylint: disable=invalid-name
# pylint: disable=ungrouped-imports

# COLOR_BLACK	    Black
# COLOR_BLUE	    Blue
# COLOR_CYAN	    Cyan (light greenish blue)
# COLOR_GREEN	    Green
# COLOR_MAGENTA	Magenta (purplish red)
# COLOR_RED   	Red
# COLOR_WHITE 	White
# COLOR_YELLOW	Yellow

import os
import logging
import datetime
import curses
import time
import re
import sys

import pkgutil

from math import degrees, radians, sin, cos, atan2, sqrt, asin, pi
from pathlib import Path
from shutil import copyfile
from curses.textpad import rectangle
from curses import wrapper
from json import dumps, loads
import threading

import requests

try:
    from wfdcurses.lib.database import DataBase
    from wfdcurses.lib.preferences import Preferences
    from wfdcurses.lib.lookup import HamDBlookup, HamQTH, QRZlookup
    from wfdcurses.lib.cat_interface import CAT
    from wfdcurses.lib.edittextfield import EditTextField
    from wfdcurses.lib.settings import SettingsScreen
    from wfdcurses.lib.cwinterface import CW
    from wfdcurses.lib.version import __version__
    from wfdcurses.lib.versiontest import VersionTest
except ModuleNotFoundError:
    from lib.database import DataBase
    from lib.preferences import Preferences
    from lib.lookup import HamDBlookup, HamQTH, QRZlookup
    from lib.cat_interface import CAT
    from lib.edittextfield import EditTextField
    from lib.settings import SettingsScreen
    from lib.cwinterface import CW
    from lib.version import __version__
    from lib.versiontest import VersionTest


if Path("./debug").exists():
    logging.basicConfig(
        filename="debug.log",
        filemode="w",
        format=(
            "[%(asctime)s] %(levelname)s %(module)s - "
            "%(funcName)s Line %(lineno)d:\n%(message)s"
        ),
        datefmt="%H:%M:%S",
        level=logging.DEBUG,
    )
    logging.debug("Debug started")


poll_time = datetime.datetime.now()
look_up = None
cat_control = None
cloudlog_on = False
preference = None

stdscr = curses.initscr()
height, width = stdscr.getmaxyx()
if height < 24 or width < 80:
    print("Terminal size needs to be at least 80x24")
    curses.endwin()
    sys.exit()
settings_screen = None
qsoew = None
qso_edit_fields = None
qso = []
quitprogram = False

BACK_SPACE = 263
ESCAPE = 27
QUESTIONMARK = 63
ENTERKEY = 10
SPACE = 32

modes = ("PH", "CW", "DG")
bands = (
    "160",
    "80",
    "60",
    "40",
    "30",
    "20",
    "17",
    "15",
    "12",
    "10",
    "6",
    "2",
    "222",
    "432",
)
dfreqPH = {
    "160": "1.910",
    "80": "3.800",
    "60": "5.357",
    "40": "7.200",
    "30": "10.135",
    "20": "14.200",
    "17": "18.150",
    "15": "21.400",
    "12": "24.950",
    "10": "28.400",
    "6": "53.000",
    "2": "146.520",
    "222": "223.500",
    "432": "446.000",
    "SAT": "0.0",
    "None": "0.0",
}
dfreqCW = {
    "160": "1.810",
    "80": "3.550",
    "60": "5.357",
    "40": "7.025",
    "30": "10.125",
    "20": "14.025",
    "17": "18.068",
    "15": "21.100",
    "12": "24.910",
    "10": "28.150",
    "6": "50.050",
    "2": "144.050",
    "222": "223.500",
    "432": "425.000",
}

validSections = [
    "CT",
    "RI",
    "EMA",
    "VT",
    "ME",
    "WMA",
    "NH",
    "ENY",
    "NN",
    "NLI",
    "SNJ",
    "NNJ",
    "WNY",
    "DE",
    "MDC",
    "EPA",
    "EPA",
    "AL",
    "SC",
    "GA",
    "SFL",
    "KY",
    "TN",
    "NC",
    "VA",
    "NFL",
    "VI",
    "PR",
    "WCF",
    "AR",
    "NTX",
    "LA",
    "OK",
    "MS",
    "STX",
    "NM",
    "WTX",
    "EB",
    "SCV",
    "LAX",
    "SDG",
    "ORG",
    "SF",
    "PAC",
    "SJV",
    "SB",
    "SV",
    "AK",
    "NV",
    "AZ",
    "OR",
    "EWA",
    "UT",
    "ID",
    "WWA",
    "MT",
    "WY",
    "MI",
    "WV",
    "OH",
    "IL",
    "WI",
    "IN",
    "CO",
    "MO",
    "IA",
    "ND",
    "KS",
    "NE",
    "MN",
    "SD",
    "AB",
    "NB",
    "BC",
    "ONE",
    "GH",
    "ONN",
    "TER",
    "ONS",
    "MB",
    "QC",
    "NL",
    "SK",
    "PE",
    "MX",
]

contactlookup = {
    "call": "",
    "grid": "",
    "bearing": "",
    "name": "",
    "nickname": "",
    "error": "",
    "distance": "",
}

freq = "000000000"
band = "40"
mode = "CW"
contacts = ""
contactsOffset = 0
logNumber = 0
kbuf = ""
editbuf = ""
MAXFIELDLENGTH = [17, 5, 7, 20, 4, 3, 4]
MAXEDITFIELDLENGTH = [10, 17, 5, 4, 20, 4, 3, 4, 10]
inputFieldFocus = 0
editFieldFocus = 1
hiscall = ""
hissection = ""
hisclass = ""
mygrid = ""

database = "WFD_Curses.db"
wrkdsections = []
scp = []
secPartial = {}
secName = {}
secState = {}
oldfreq = "0"
oldmode = ""
oldpwr = 0
fkeys = {}
cw = None


def clearcontactlookup():
    """clearout the contact lookup"""
    contactlookup["call"] = ""
    contactlookup["grid"] = ""
    contactlookup["name"] = ""
    contactlookup["nickname"] = ""
    contactlookup["error"] = ""
    contactlookup["distance"] = ""
    contactlookup["bearing"] = ""


def lookupmygrid():
    """lookup my own gridsquare"""
    global mygrid
    if look_up:
        mygrid, _, _, _ = look_up.lookup(preference.preference.get("mycallsign"))
        logging.info("my grid: %s", mygrid)


def lazy_lookup(acall: str):
    """El Lookup De Lazy"""
    if look_up:
        if acall == contactlookup.get("call"):
            return
        contactlookup["call"] = acall
        (
            contactlookup["grid"],
            contactlookup["name"],
            contactlookup["nickname"],
            contactlookup["error"],
        ) = look_up.lookup(acall)
        if contactlookup.get("name") == "NOT_FOUND NOT_FOUND":
            contactlookup["name"] = "NOT_FOUND"
        if contactlookup.get("grid") == "NOT_FOUND":
            contactlookup["grid"] = ""
        if contactlookup.get("grid") and mygrid:
            contactlookup["distance"] = distance(mygrid, contactlookup.get("grid"))
            contactlookup["bearing"] = bearing(mygrid, contactlookup.get("grid"))
            displayinfo(f"{contactlookup.get('name')}", line=1)
            displayinfo(
                f"{contactlookup.get('grid')} "
                f"{round(contactlookup.get('distance'))}km "
                f"{round(contactlookup.get('bearing'))}deg"
            )
        logging.info("%s", contactlookup)


def gridtolatlon(maiden: str):
    """gridsquare to latitude and longitude"""
    maiden = str(maiden).strip().upper()

    N = len(maiden)
    if not 8 >= N >= 2 and N % 2 == 0:
        return 0, 0

    lon = (ord(maiden[0]) - 65) * 20 - 180
    lat = (ord(maiden[1]) - 65) * 10 - 90

    if N >= 4:
        lon += (ord(maiden[2]) - 48) * 2
        lat += ord(maiden[3]) - 48

    if N >= 6:
        lon += (ord(maiden[4]) - 65) / 12 + 1 / 24
        lat += (ord(maiden[5]) - 65) / 24 + 1 / 48

    if N >= 8:
        lon += (ord(maiden[6])) * 5.0 / 600
        lat += (ord(maiden[7])) * 2.5 / 600

    return lat, lon


def distance(grid1: str, grid2: str) -> float:
    """
    Takes two maidenhead gridsquares and returns the distance between the two in kilometers.
    """
    lat1, lon1 = gridtolatlon(grid1)
    lat2, lon2 = gridtolatlon(grid2)

    bearing = atan2(
        sin(lon2 - lon1) * cos(lat2),
        cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(lon2 - lon1),
    )
    bearing = degrees(bearing)
    bearing = (bearing + 360) % 360

    return haversine(lon1, lat1, lon2, lat2)


def bearing(grid1: str, grid2: str) -> float:
    """Return bearing to contact given two gridsquares"""
    lat1, lon1 = gridtolatlon(grid1)
    lat2, lon2 = gridtolatlon(grid2)
    lat1 = radians(lat1)
    lon1 = radians(lon1)
    lat2 = radians(lat2)
    lon2 = radians(lon2)
    londelta = lon2 - lon1
    y = sin(londelta) * cos(lat2)
    x = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(londelta)
    brng = atan2(y, x)
    brng *= 180 / pi

    if brng < 0:
        brng += 360

    return brng


def haversine(lon1: str, lat1: str, lon2: str, lat2: str) -> float:
    """
    Calculate the great circle distance in kilometers between two points
    on the earth (specified in decimal degrees)
    """
    # convert degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    r = 6372.8  # Radius of earth in kilometers.
    return c * r


def getband(the_freq) -> str:
    """returns a string containing the band a frequency is on."""
    if the_freq.isnumeric():
        frequency = int(float(the_freq))
        if 2000000 > frequency > 1800000:
            return "160"
        if 4000000 > frequency > 3500000:
            return "80"
        if 5406000 > frequency > 5330000:
            return "60"
        if 7300000 > frequency > 7000000:
            return "40"
        if 10150000 > frequency > 10100000:
            return "30"
        if 14350000 > frequency > 14000000:
            return "20"
        if 18168000 > frequency > 18068000:
            return "17"
        if 21450000 > frequency > 21000000:
            return "15"
        if 24990000 > frequency > 24890000:
            return "12"
        if 29700000 > frequency > 28000000:
            return "10"
        if 54000000 > frequency > 50000000:
            return "6"
        if 148000000 > frequency > 144000000:
            return "2"
        if 225000000 > frequency > 222000000:
            return "222"
        if 450000000 > frequency > 420000000:
            return "432"
    else:
        return "OOB"


def getmode(rigmode: str) -> str:
    """converts the rigs mode into the contest mode."""
    if rigmode in ("CW", "CWR"):
        return "CW"
    if rigmode in ("USB", "LSB", "FM", "AM"):
        return "PH"
    return "DG"  # All else digital


def send_radio(cmd: str, arg: str) -> None:
    """sends commands to the radio"""
    if cat_control:
        if cmd == "B" and mode == "CW":
            if arg in dfreqCW:
                cat_control.set_vfo(f"{str(dfreqCW[arg].replace('.', ''))}000\n")
            else:
                setStatusMsg("Unknown band specified")
        elif cmd == "B":
            if arg in dfreqPH:
                cat_control.set_vfo(f"{str(dfreqPH[arg].replace('.', ''))}000\n")
        if cmd == "F":
            if arg.isnumeric() and int(arg) >= 1800000 and int(arg) <= 450000000:
                cat_control.set_vfo(f"{arg}")
                setfreq(f"{arg}")
            else:
                setStatusMsg("Specify frequency in Hz")
        elif cmd == "M":
            cat_control.set_mode(arg)
        elif cmd == "P":
            if arg.isnumeric() and int(arg) >= 1 and int(arg) <= 100:
                cat_control.set_power(arg)
    return


def poll_radio() -> None:
    """Polls the state of the radio."""
    global oldfreq, oldmode, cat_control  # pylint: disable=global-statement
    if cat_control is None:
        return
    if not cat_control.online:
        if preference.preference.get("useflrig"):
            cat_control = CAT(
                "flrig",
                preference.preference.get("CAT_ip"),
                preference.preference.get("CAT_port"),
            )
        if preference.preference.get("userigctld"):
            cat_control = CAT(
                "rigctld",
                preference.preference.get("CAT_ip"),
                preference.preference.get("CAT_port"),
            )

    if cat_control.online:
        newfreq = cat_control.get_vfo()
        newmode = cat_control.get_mode()
        # newpwr = cat_control.get_power()
        logging.info("F:%s M:%s", newfreq, newmode)
        # newpwr = int(float(rigctrlsocket.recv(1024).decode().strip()) * 100)
        if newfreq and newfreq != oldfreq:
            oldfreq = newfreq
            setband(str(getband(newfreq)))
            setfreq(str(newfreq))
        if newmode and newmode != oldmode:
            oldmode = newmode
            setmode(str(getmode(newmode)))


def read_cw_macros():
    """
    Reads in the CW macros, firsts it checks to see if the file exists. If it does not,
    and this has been packaged with pyinstaller it will copy the default file from the
    temp directory this is running from... In theory.
    """
    if not Path("./cwmacros.txt").exists():
        logging.info("copying default macro file.")
        try:
            path = os.path.dirname(__loader__.get_filename())
            logging.info("the path : %s", path)
            copyfile(path + "/data/cwmacros.txt", "./cwmacros.txt")
        except AttributeError:
            copyfile("wfdcurses/data/cwmacros.txt", "./cwmacros.txt")
    with open("./cwmacros.txt", "r", encoding="utf-8") as file_descriptor:
        for line in file_descriptor:
            try:
                fkey, buttonname, cwtext = line.split("|")
                fkeys[fkey.strip()] = (buttonname.strip(), cwtext.strip())
            except ValueError as err:
                logging.info("%s", err)


def process_macro(macro):
    """process string substitutions"""
    macro = macro.upper()
    macro = macro.replace("{MYCALL}", preference.preference.get("mycallsign"))
    macro = macro.replace("{MYCLASS}", preference.preference.get("myclass"))
    macro = macro.replace("{MYSECT}", preference.preference.get("mysection"))
    macro = macro.replace("{HISCALL}", hiscall)
    return macro


def check_function_keys(key):
    """Sends a CW macro if a function key was pressed."""
    if cw:
        if key == curses.KEY_F1 and "F1" in fkeys:
            cw.sendcw(process_macro(fkeys["F1"][1]))
        elif key == curses.KEY_F2 and "F2" in fkeys:
            cw.sendcw(process_macro(fkeys["F2"][1]))
        elif key == curses.KEY_F3 and "F3" in fkeys:
            cw.sendcw(process_macro(fkeys["F3"][1]))
        elif key == curses.KEY_F4 and "F4" in fkeys:
            cw.sendcw(process_macro(fkeys["F4"][1]))
        elif key == curses.KEY_F5 and "F5" in fkeys:
            cw.sendcw(process_macro(fkeys["F5"][1]))
        elif key == curses.KEY_F6 and "F6" in fkeys:
            cw.sendcw(process_macro(fkeys["F6"][1]))
        elif key == curses.KEY_F7 and "F7" in fkeys:
            cw.sendcw(process_macro(fkeys["F7"][1]))
        elif key == curses.KEY_F8 and "F8" in fkeys:
            cw.sendcw(process_macro(fkeys["F8"][1]))
        elif key == curses.KEY_F9 and "F9" in fkeys:
            cw.sendcw(process_macro(fkeys["F9"][1]))
        elif key == curses.KEY_F10 and "F10" in fkeys:
            cw.sendcw(process_macro(fkeys["F10"][1]))
        elif key == curses.KEY_F11 and "F11" in fkeys:
            cw.sendcw(process_macro(fkeys["F11"][1]))
        elif key == curses.KEY_F12 and "F12" in fkeys:
            cw.sendcw(process_macro(fkeys["F12"][1]))
        elif key == 43 and cw.servertype == 1:
            cw.speed += 1
            cw.sendcw(f"\x1b2{cw.speed}")
            statusline()
        elif key == 45 and cw.servertype == 1:
            cw.speed -= 1
            if cw.speed < 5:
                cw.speed = 5
            cw.sendcw(f"\x1b2{cw.speed}")
            statusline()


def readpreferences() -> None:
    """Reads in preferences"""
    preference.readpreferences()
    register_services()
    if look_up and preference.preference.get("mycallsign") != "":
        _thethread = threading.Thread(
            target=lookupmygrid,
            daemon=True,
        )
        _thethread.start()


def writepreferences() -> None:
    """Yup writes preferences to the preferences table"""
    preference.writepreferences()


def log_contact(logme) -> None:
    """Inserts a contact into the db."""
    database.log_contact(logme)
    workedSections()
    sections()
    stats()
    logwindow()
    postcloudlog()


def delete_contact(contact) -> None:
    """Deletes a contact from the db."""
    if contact:
        database.delete_contact(contact)
        workedSections()
        sections()
        stats()
        logwindow()
    else:
        setStatusMsg("Must specify a contact number")


def change_contact(__qso) -> None:
    """Updates an edited contact."""
    database.change_contact(__qso)


def read_sections() -> None:
    """
    Reads in the ARRL sections into some internal dictionaries.
    """
    global secName, secState, secPartial
    try:
        # path = os.path.dirname(pkgutil.get_loader("wfdcurses").get_filename())
        # logging.info("the path : %s", path)
        secName = loads(pkgutil.get_data(__name__, "data/secname.json").decode("utf8"))
    except ValueError:
        with open(
            "wfdcurses/data/secname.json", "rt", encoding="utf-8"
        ) as file_descriptor:
            secName = loads(file_descriptor.read())
    try:
        secState = loads(
            pkgutil.get_data(__name__, "data/secstate.json").decode("utf8")
        )
    except ValueError:
        with open(
            "wfdcurses/data/secstate.json", "rt", encoding="utf-8"
        ) as file_descriptor:
            secState = loads(file_descriptor.read())
    try:
        secPartial = loads(
            pkgutil.get_data(__name__, "data/secpartial.json").decode("utf8")
        )
    except ValueError:
        with open(
            "wfdcurses/data/secpartial.json", "rt", encoding="utf-8"
        ) as file_descriptor:
            secPartial = loads(file_descriptor.read())


def section_check(sec: str) -> None:
    """checks if a string is part of a section name"""
    oy, ox = stdscr.getyx()
    if sec == "":
        sec = "^"
    seccheckwindow = curses.newpad(20, 33)
    rectangle(stdscr, 11, 0, 21, 34)
    list_of_keys = list(secName.keys())
    matches = list(filter(lambda y: y.startswith(sec), list_of_keys))
    for count, match in enumerate(matches):
        seccheckwindow.addstr(count, 1, secName[match])
    stdscr.refresh()
    seccheckwindow.refresh(0, 0, 12, 1, 20, 33)
    stdscr.move(oy, ox)


def read_scp() -> list:
    """reads in the super check partion data into a list"""
    try:
        data = pkgutil.get_data(__name__, "data/MASTER.SCP").decode("utf8")
        lines = data.splitlines()
    except ValueError:
        with open(
            "wfdcurses/data/MASTER.SCP", "r", encoding="utf-8"
        ) as file_descriptor:
            lines = file_descriptor.readlines()
    return list(map(lambda x: x.strip(), lines))


def super_check(acall: str) -> list:
    """returns a list of matches for acall against known contesters."""
    return list(filter(lambda x: x.startswith(acall), scp))


def contacts_label():
    """
    Centers a string to create a label for the Recent contacts window.
    Seems stupid but it's used like 4 times.
    """
    rectangle(stdscr, 0, 0, 7, 55)
    contactslabel = f"Recent Contacts v[{__version__}]"
    contactslabeloffset = (55 / 2) - len(contactslabel) / 2
    stdscr.addstr(0, int(contactslabeloffset), contactslabel)


def stats() -> None:
    """calculates and displays the current statistics."""
    y, x = stdscr.getyx()
    db_stats = database.stats()

    cwcontacts = db_stats.get("cwcontacts")
    phonecontacts = db_stats.get("phonecontacts")
    digitalcontacts = db_stats.get("digitalcontacts")
    last15 = db_stats.get("last15")
    lasthour = db_stats.get("lasthour")

    rectangle(stdscr, 0, 57, 7, 79)
    statslabel = "Score Stats"
    statslabeloffset = (25 / 2) - len(statslabel) / 2
    stdscr.addstr(0, 57 + int(statslabeloffset), statslabel)
    stdscr.addstr(1, 58, "Total CW:")
    stdscr.addstr(2, 58, "Total PHONE:")
    stdscr.addstr(3, 58, "Total DIGITAL:")
    stdscr.addstr(4, 58, "QSO POINTS:          ")
    stdscr.addstr(5, 58, "QSOs LAST HOUR:")
    stdscr.addstr(6, 58, "QSOs LAST 15MIN:")
    stdscr.addstr(1, 75, cwcontacts.rjust(4))
    stdscr.addstr(2, 75, phonecontacts.rjust(4))
    stdscr.addstr(3, 75, digitalcontacts.rjust(4))
    stdscr.addstr(4, 70, str(score()).rjust(9))
    stdscr.addstr(5, 76, lasthour.rjust(3))
    stdscr.addstr(6, 76, last15.rjust(3))
    stdscr.move(y, x)


def score() -> int:
    """generates current score, returns an int"""
    results = database.stats()
    cw = results.get("cwcontacts")
    ph = results.get("phonecontacts")
    di = results.get("digitalcontacts")
    bandmodemult = results.get("bandmodemult")
    highpower = results.get("highpower")
    qrp = results.get("qrp")
    __score = (int(cw) * 2) + int(ph) + (int(di) * 2)
    if qrp:
        __score = __score * 2
    elif not highpower:
        __score = __score * 1
    __score = __score * bandmodemult

    if preference.preference.get("altpower"):
        __score += 500
    if preference.preference.get("outdoors"):
        __score += 500
    if preference.preference.get("notathome"):
        __score += 500
    if preference.preference.get("satellite"):
        __score += 500
    if preference.preference.get("antenna"):
        __score += 500

    return __score


def getBandModeTally(band, mode):
    """Needs Doc String"""
    return database.get_band_mode_tally(band, mode)


def getbands():
    """Needs Doc String"""
    bandlist = []
    for bands in database.get_bands():
        bandlist.append(bands.get("band"))
    return bandlist


def generateBandModeTally():
    """Needs Doc String"""
    blist = getbands()
    bmtfn = "Statistics.txt"
    with open(bmtfn, "w", encoding="utf-8") as f:
        print("\t\tCW\tPWR\tDG\tPWR\tPH\tPWR", end="\r\n", file=f)
        print("-" * 60, end="\r\n", file=f)
        for b in bands:
            if b in blist:
                cwt = getBandModeTally(b, "CW")
                dit = getBandModeTally(b, "DG")
                pht = getBandModeTally(b, "PH")
                print(
                    f"Band:\t{b}\t{cwt.get('tally')}\t{cwt.get('mpow')}\t"
                    f"{dit.get('tally')}\t{dit.get('mpow')}\t"
                    f"{pht.get('tally')}\t{pht.get('mpow')}",
                    end="\r\n",
                    file=f,
                )
                print("-" * 60, end="\r\n", file=f)


def get_state(section):
    """returns the state of a section"""
    try:
        state = secState.get(section)
        if state != "--":
            return state
    except IndexError:
        return False
    return False


def adif():
    """generates an ADIF file from your contacts"""
    logname = "WFD.adi"
    log = database.fetch_all_contacts_asc()
    with open(logname, "w", encoding="utf-8") as file_descriptor:
        print("<ADIF_VER:5>2.2.0", end="\r\n", file=file_descriptor)
        print("<EOH>", end="\r\n", file=file_descriptor)
        for contact in log:
            hiscall = contact.get("callsign")
            hisclass = contact.get("class")
            hissection = contact.get("section")
            datetime = contact.get("date_time")
            band = contact.get("band")
            mode = contact.get("mode")
            grid = contact.get("grid")
            name = contact.get("opname")

            if mode == "DG":
                mode = "RTTY"
            if mode == "PH":
                mode = "SSB"
            if mode == "CW":
                rst = "599"
            else:
                rst = "59"
            loggeddate = datetime[:10]
            loggedtime = datetime[11:13] + datetime[14:16]
            print(
                f"<QSO_DATE:{len(''.join(loggeddate.split('-')))}:d>"
                f"{''.join(loggeddate.split('-'))}",
                end="\r\n",
                file=file_descriptor,
            )
            print(
                f"<TIME_ON:{len(loggedtime)}>{loggedtime}",
                end="\r\n",
                file=file_descriptor,
            )
            print(
                f"<CALL:{len(hiscall)}>{hiscall}",
                end="\r\n",
                file=file_descriptor,
            )
            print(f"<MODE:{len(mode)}>{mode}", end="\r\n", file=file_descriptor)
            print(
                f"<BAND:{len(band)+1}>{band}M",
                end="\r\n",
                file=file_descriptor,
            )
            try:
                print(
                    f"<FREQ:{len(dfreqPH[band])}>{dfreqPH[band]}",
                    end="\r\n",
                    file=file_descriptor,
                )
            except IndexError:
                pass
            print(f"<RST_SENT:{len(rst)}>{rst}", end="\r\n", file=file_descriptor)
            print(f"<RST_RCVD:{len(rst)}>{rst}", end="\r\n", file=file_descriptor)
            mcas = f"{preference.preference['myclass']} {preference.preference['mysection']}"
            print(
                f"<STX_STRING:{len(mcas)}>{mcas}",
                end="\r\n",
                file=file_descriptor,
            )
            hcas = f"{hisclass} {hissection}"
            print(
                f"<SRX_STRING:{len(hcas)}>{hcas}",
                end="\r\n",
                file=file_descriptor,
            )
            print(
                f"<ARRL_SECT:{len(hissection)}>{hissection}",
                end="\r\n",
                file=file_descriptor,
            )
            print(
                f"<CLASS:{len(hisclass)}>{hisclass}",
                end="\r\n",
                file=file_descriptor,
            )
            state = get_state(hissection)
            if state:
                print(
                    f"<STATE:{len(state)}>{state}",
                    end="\r\n",
                    file=file_descriptor,
                )
            if grid:
                print(
                    f"<GRIDSQUARE:{len(grid)}>{grid}",
                    end="\r\n",
                    file=file_descriptor,
                )
            if name:
                print(f"<NAME:{len(name)}>{name}", end="\r\n", file=file_descriptor)
            print("<COMMENT:19>WINTER-FIELD-DAY", end="\r\n", file=file_descriptor)
            print("<EOR>", end="\r\n", file=file_descriptor)
            print("", end="\r\n", file=file_descriptor)
    yy, xx = stdscr.getyx()
    stdscr.move(15, 1)
    stdscr.addstr("Done.                     ")
    stdscr.move(yy, xx)
    stdscr.refresh()


def parsecallsign(callsign):
    """it parses a callsign"""
    try:
        callelements = callsign.split("/")
    except AttributeError:
        return callsign
    if len(callelements) == 3:
        return callelements[1]
    if len(callelements) == 2:
        regex = re.compile("^([0-9])?[A-Za-z]{1,2}[0-9]{1,3}[A-Za-z]{1,4}$")
        if re.match(regex, callelements[0]):
            return callelements[0]
        return callelements[1]
    return callsign


def postcloudlog():
    """posts a contact to cloudlog"""
    if not cloudlog_on:
        return
    contact = database.fetch_last_contact()
    hiscall = contact.get("callsign")
    hisclass = contact.get("class")
    hissection = contact.get("section")
    datetime = contact.get("date_time")
    band = contact.get("band")
    mode = contact.get("mode")
    grid = contact.get("grid")
    name = contact.get("opname")
    if mode == "CW":
        rst = "599"
    else:
        rst = "59"
    loggeddate = datetime[:10]
    loggedtime = datetime[11:13] + datetime[14:16]
    adifq = (
        f"<QSO_DATE:{len(''.join(loggeddate.split('-')))}:d>{''.join(loggeddate.split('-'))}"
        f"<TIME_ON:{len(loggedtime)}>{loggedtime}"
        f"<CALL:{len(hiscall)}>{hiscall}"
        f"<MODE:{len(mode)}>{mode}"
        f"<BAND:{len(band + 'M')}>{band + 'M'}"
        f"<FREQ:{len(dfreqPH[band])}>{dfreqPH[band]}"
        f"<RST_SENT:{len(rst)}>{rst}"
        f"<RST_RCVD:{len(rst)}>{rst}"
    )
    value2 = (
        preference.preference.get("myclass")
        + " "
        + preference.preference.get("mysection")
    )
    value1 = len(value2)
    adifq += (
        f"<STX_STRING:{value1}>{value2}"
        f"<SRX_STRING:{len(hisclass + ' ' + hissection)}>{hisclass + ' ' + hissection}"
        f"<ARRL_SECT:{len(hissection)}>{hissection}"
        f"<CLASS:{len(hisclass)}>{hisclass}"
    )
    state = get_state(hissection)
    if state:
        adifq += f"<STATE:{len(state)}>{state}"
    if grid:
        adifq += f"<GRIDSQUARE:{len(grid)}>{grid}"
    if name:
        adifq += f"<NAME:{len(name)}>{name}"
    adifq += "<COMMENT:16>WINTER-FIELD-DAY" "<EOR>"

    payload = {
        "key": preference.preference.get("cloudlogapi"),
        "type": "adif",
        "string": adifq,
    }

    jsonData = dumps(payload)
    logging.debug(jsonData)
    qsoUrl = preference.preference.get("cloudlogurl") + "/qso"
    try:
        _ = requests.post(qsoUrl, jsonData, timeout=3.0)
    except requests.exceptions.Timeout:
        logging.debug("Timeout")


def cabrillo():
    """generates a cabrillo log"""
    bonuses = 0
    catpower = ""
    db_stats = database.stats()
    bandmodemult = db_stats.get("bandmodemult")
    highpower = db_stats.get("highpower")
    qrp = db_stats.get("qrp")

    if qrp:
        catpower = "QRP"
    elif highpower:
        catpower = "HIGH"
    else:
        catpower = "LOW"
    with open("WFDLOG.txt", "w", encoding="ascii") as file_descriptor:
        print("START-OF-LOG: 3.0", end="\r\n", file=file_descriptor)
        print(
            "CREATED-BY: K6GTE Winter Field Day Logger",
            end="\r\n",
            file=file_descriptor,
        )
        print("CONTEST: WFD", end="\r\n", file=file_descriptor)
        print(
            "CALLSIGN:",
            preference.preference.get("mycallsign"),
            end="\r\n",
            file=file_descriptor,
        )
        print("LOCATION:", end="\r\n", file=file_descriptor)
        print(
            "ARRL-SECTION:",
            preference.preference.get("mysection"),
            end="\r\n",
            file=file_descriptor,
        )
        print(
            "CATEGORY:",
            preference.preference.get("myclass"),
            end="\r\n",
            file=file_descriptor,
        )
        print("CATEGORY-POWER: " + catpower, end="\r\n", file=file_descriptor)
        if preference.preference.get("altpower"):
            print(
                "SOAPBOX: 500 points for not using commercial power",
                end="\r\n",
                file=file_descriptor,
            )
            bonuses += 500
        if preference.preference.get("outdoors"):
            print(
                "SOAPBOX: 500 points for setting up outdoors",
                end="\r\n",
                file=file_descriptor,
            )
            bonuses += 500
        if preference.preference.get("notathome"):
            print(
                "SOAPBOX: 500 points for setting up away from home",
                end="\r\n",
                file=file_descriptor,
            )
            bonuses += 500
        if preference.preference.get("satellite"):
            print(
                "SOAPBOX: 500 points for working satellite",
                end="\r\n",
                file=file_descriptor,
            )
            bonuses += 500
        if preference.preference.get("antenna"):
            print(
                "SOAPBOX: 500 points for WFD antenna setup",
                end="\r\n",
                file=file_descriptor,
            )
            bonuses += 500
        print(f"SOAPBOX: BONUS Total {bonuses}", end="\r\n", file=file_descriptor)

        if bandmodemult:
            print(
                f"SOAPBOX: Band Mode Multiplier: {bandmodemult}",
                end="\r\n",
                file=file_descriptor,
            )

        print(f"CLAIMED-SCORE: {score()}", end="\r\n", file=file_descriptor)
        print(
            f"OPERATORS:{preference.preference.get('mycallsign')}",
            end="\r\n",
            file=file_descriptor,
        )
        print("NAME: ", end="\r\n", file=file_descriptor)
        print("ADDRESS: ", end="\r\n", file=file_descriptor)
        print("ADDRESS-CITY: ", end="\r\n", file=file_descriptor)
        print("ADDRESS-STATE: ", end="\r\n", file=file_descriptor)
        print("ADDRESS-POSTALCODE: ", end="\r\n", file=file_descriptor)
        print("ADDRESS-COUNTRY: ", end="\r\n", file=file_descriptor)
        print("EMAIL: ", end="\r\n", file=file_descriptor)
        log = database.fetch_all_contacts_asc()
        for contact in log:
            hiscall = contact.get("callsign")
            hisclass = contact.get("class")
            hissection = contact.get("section")
            datetime = contact.get("date_time")
            band = contact.get("band")
            mode = contact.get("mode")
            loggeddate = datetime[:10]
            loggedtime = datetime[11:13] + datetime[14:16]
            print(
                f"QSO: {band}M {mode} {loggeddate} {loggedtime} "
                f"{preference.preference.get('mycallsign')} "
                f"{preference.preference.get('myclass')} "
                f"{preference.preference.get('mysection')} {hiscall} {hisclass} {hissection}",
                end="\r\n",
                file=file_descriptor,
            )
        print("END-OF-LOG:", end="\r\n", file=file_descriptor)

    generateBandModeTally()

    oy, ox = stdscr.getyx()
    window = curses.newpad(10, 33)
    rectangle(stdscr, 11, 0, 21, 34)
    window.addstr(0, 0, "Log written to: WFDLOG.txt")
    window.addstr(1, 0, "Stats written to: Statistics.txt")
    window.addstr(2, 0, "ADIF written to: WFD.adi")
    stdscr.refresh()
    window.refresh(0, 0, 12, 1, 20, 33)
    stdscr.move(oy, ox)
    adif()
    preference.writepreferences()
    statusline()
    stats()


def logwindow():
    """updates the log window with contacts"""
    global contacts, contactsOffset, logNumber
    contactsOffset = 0  # clears scroll position
    contacts = curses.newpad(1000, 80)
    log = database.fetch_all_contacts_desc()
    logNumber = 0
    for contact in log:
        logid = contact.get("id")
        hiscall = contact.get("callsign")
        hisclass = contact.get("class")
        hissection = contact.get("section")
        datetime = contact.get("date_time")
        band = contact.get("band")
        mode = contact.get("mode")
        power = contact.get("power")

        logline = (
            f"{str(logid).rjust(3,'0')} "
            f"{hiscall.ljust(10)} "
            f"{hisclass.rjust(3)} "
            f"{hissection.rjust(3)} "
            f"{datetime} "
            f"{band.rjust(3)} "
            f"{mode.rjust(2)} "
            f"{power}"
        )
        contacts.addstr(logNumber, 0, logline)
        logNumber += 1
    stdscr.refresh()
    contacts.refresh(0, 0, 1, 1, 6, 54)


def logup():
    """scroll the log up"""
    global contactsOffset
    contactsOffset += 1
    if contactsOffset > (logNumber - 6):
        contactsOffset = logNumber - 6
    contacts.refresh(contactsOffset, 0, 1, 1, 6, 54)


def logpagedown():
    """scroll the log down"""
    global contactsOffset
    contactsOffset += 10
    if contactsOffset > (logNumber - 6):
        contactsOffset = logNumber - 6
    contacts.refresh(contactsOffset, 0, 1, 1, 6, 54)


def logpageup():
    """scroll the log up by a page"""
    global contactsOffset
    contactsOffset -= 10
    if contactsOffset < 0:
        contactsOffset = 0
    contacts.refresh(contactsOffset, 0, 1, 1, 6, 54)


def logdown():
    """scroll the log down py a page"""
    global contactsOffset
    contactsOffset -= 1
    if contactsOffset < 0:
        contactsOffset = 0
    contacts.refresh(contactsOffset, 0, 1, 1, 6, 54)


def dupCheck(acall):
    """check for duplicates"""
    global hisclass, hissection
    oy, ox = stdscr.getyx()
    scpwindow = curses.newpad(1000, 33)
    rectangle(stdscr, 11, 0, 21, 34)
    log = database.dup_check(acall)
    for counter, contact in enumerate(log):
        decorate = ""
        hiscall = contact.get("callsign")
        hisclass = contact.get("class")
        hissection = contact.get("section")
        hisband = contact.get("band")
        hismode = contact.get("mode")
        if hissection_field.text() == "":
            hissection_field.set_text(hissection)
            hissection_field.get_focus()
        if hisclass_field.text() == "":
            hisclass_field.set_text(hisclass)
            hisclass_field.get_focus()
        if hisband == band and hismode == mode:
            decorate = curses.color_pair(1)
            curses.flash()
            curses.beep()
        else:
            decorate = curses.A_NORMAL
        scpwindow.addstr(counter, 0, f"{hiscall}: {hisband} {hismode}", decorate)
    stdscr.refresh()
    scpwindow.refresh(0, 0, 12, 1, 20, 33)
    stdscr.move(oy, ox)


def displaySCP(matches):
    """show super check partial matches"""
    oy, ox = stdscr.getyx()
    scpwindow = curses.newpad(1000, 33)
    rectangle(stdscr, 11, 0, 21, 34)
    for x in matches:
        wy, wx = scpwindow.getyx()
        if (33 - wx) < len(str(x)):
            scpwindow.move(wy + 1, 0)
        scpwindow.addstr(str(x) + " ")
    stdscr.refresh()
    scpwindow.refresh(0, 0, 12, 1, 20, 33)
    stdscr.move(oy, ox)


def workedSections():
    """gets the worked sections"""
    wrkdsections.clear()
    all_rows = database.sections()
    for section in all_rows:
        wrkdsections.append(section.get("section"))


def workedSection(section):
    """highlights the worked sections"""
    if section in wrkdsections:
        return curses.color_pair(1)
    return curses.A_DIM


def sectionsCol1():
    """display section column 1"""
    rectangle(stdscr, 8, 35, 21, 43)
    stdscr.hline(8, 36, curses.ACS_HLINE, 7)
    stdscr.addstr(8, 39, "DX")
    stdscr.addstr(9, 36, "DX", workedSection("DX"))
    stdscr.addstr(9, 41, "MX", workedSection("MX"))
    stdscr.addch(10, 35, curses.ACS_LTEE)
    stdscr.hline(10, 36, curses.ACS_HLINE, 7)
    stdscr.addch(10, 43, curses.ACS_RTEE)
    stdscr.addstr(10, 39, "1")
    stdscr.addstr(11, 36, "CT", workedSection("CT"))
    stdscr.addstr(11, 41, "RI", workedSection("RI"))
    stdscr.addstr(12, 36, "EMA", workedSection("EMA"))
    stdscr.addstr(12, 41, "VT", workedSection("VT"))
    stdscr.addstr(13, 36, "ME", workedSection("ME"))
    stdscr.addstr(13, 40, "WMA", workedSection("WMA"))
    stdscr.addstr(14, 36, "NH", workedSection("NH"))
    stdscr.addch(15, 35, curses.ACS_LTEE)
    stdscr.hline(15, 36, curses.ACS_HLINE, 7)
    stdscr.addch(15, 43, curses.ACS_RTEE)
    stdscr.addstr(15, 39, "2")
    stdscr.addstr(16, 36, "ENY", workedSection("ENY"))
    stdscr.addstr(16, 40, "NNY", workedSection("NNY"))
    stdscr.addstr(17, 36, "NLI", workedSection("NLI"))
    stdscr.addstr(17, 40, "SNJ", workedSection("SNJ"))
    stdscr.addstr(18, 36, "NNJ", workedSection("NNJ"))
    stdscr.addstr(18, 40, "WNY", workedSection("WNY"))


def sectionsCol2():
    """display section column 2"""
    rectangle(stdscr, 8, 44, 21, 52)
    stdscr.hline(8, 45, curses.ACS_HLINE, 7)
    stdscr.addstr(8, 48, "3")
    stdscr.addstr(9, 45, "DE", workedSection("DE"))
    stdscr.addstr(9, 49, "MDC", workedSection("MDC"))
    stdscr.addstr(10, 45, "EPA", workedSection("EPA"))
    stdscr.addstr(10, 49, "WPA", workedSection("WPA"))
    stdscr.addch(11, 44, curses.ACS_LTEE)
    stdscr.hline(11, 45, curses.ACS_HLINE, 7)
    stdscr.addch(11, 52, curses.ACS_RTEE)
    stdscr.addstr(11, 48, "4")
    stdscr.addstr(12, 45, "AL", workedSection("AL"))
    stdscr.addstr(12, 50, "SC", workedSection("SC"))
    stdscr.addstr(13, 45, "GA", workedSection("GA"))
    stdscr.addstr(13, 49, "SFL", workedSection("SFL"))
    stdscr.addstr(14, 45, "KY", workedSection("KY"))
    stdscr.addstr(14, 50, "TN", workedSection("TN"))
    stdscr.addstr(15, 45, "NC", workedSection("NC"))
    stdscr.addstr(15, 50, "VA", workedSection("VA"))
    stdscr.addstr(16, 45, "NFL", workedSection("NFL"))
    stdscr.addstr(16, 50, "VI", workedSection("VI"))
    stdscr.addstr(17, 45, "PR", workedSection("PR"))
    stdscr.addstr(17, 49, "WCF", workedSection("WCF"))


def sectionsCol3():
    """display section column 3"""
    rectangle(stdscr, 8, 53, 21, 61)
    stdscr.hline(8, 54, curses.ACS_HLINE, 7)
    stdscr.addstr(8, 57, "5")
    stdscr.addstr(9, 54, "AR", workedSection("AR"))
    stdscr.addstr(9, 58, "NTX", workedSection("NTX"))
    stdscr.addstr(10, 54, "LA", workedSection("LA"))
    stdscr.addstr(10, 59, "OK", workedSection("OK"))
    stdscr.addstr(11, 54, "MS", workedSection("MS"))
    stdscr.addstr(11, 58, "STX", workedSection("STX"))
    stdscr.addstr(12, 54, "NM", workedSection("NM"))
    stdscr.addstr(12, 58, "WTX", workedSection("WTX"))
    stdscr.addch(13, 53, curses.ACS_LTEE)
    stdscr.hline(13, 54, curses.ACS_HLINE, 7)
    stdscr.addch(13, 61, curses.ACS_RTEE)
    stdscr.addstr(13, 57, "6")
    stdscr.addstr(14, 54, "EB", workedSection("EB"))
    stdscr.addstr(14, 58, "SCV", workedSection("SCV"))
    stdscr.addstr(15, 54, "LAX", workedSection("LAX"))
    stdscr.addstr(15, 58, "SDG", workedSection("SDG"))
    stdscr.addstr(16, 54, "ORG", workedSection("ORG"))
    stdscr.addstr(16, 59, "SF", workedSection("SF"))
    stdscr.addstr(17, 54, "PAC", workedSection("PAC"))
    stdscr.addstr(17, 58, "SJV", workedSection("SJV"))
    stdscr.addstr(18, 54, "SB", workedSection("SB"))
    stdscr.addstr(18, 59, "SV", workedSection("SV"))


def sectionsCol4():
    """display section column 4"""
    rectangle(stdscr, 8, 62, 21, 70)
    stdscr.hline(8, 63, curses.ACS_HLINE, 7)
    stdscr.addstr(8, 66, "7")
    stdscr.addstr(9, 63, "AK", workedSection("AK"))
    stdscr.addstr(9, 68, "NV", workedSection("NV"))
    stdscr.addstr(10, 63, "AZ", workedSection("AZ"))
    stdscr.addstr(10, 68, "OR", workedSection("OR"))
    stdscr.addstr(11, 63, "EWA", workedSection("EWA"))
    stdscr.addstr(11, 68, "UT", workedSection("UT"))
    stdscr.addstr(12, 63, "ID", workedSection("ID"))
    stdscr.addstr(12, 67, "WWA", workedSection("WWA"))
    stdscr.addstr(13, 63, "MT", workedSection("MT"))
    stdscr.addstr(13, 68, "WY", workedSection("WY"))
    stdscr.addch(14, 62, curses.ACS_LTEE)
    stdscr.hline(14, 63, curses.ACS_HLINE, 7)
    stdscr.addch(14, 70, curses.ACS_RTEE)
    stdscr.addstr(14, 66, "8")
    stdscr.addstr(15, 63, "MI", workedSection("MI"))
    stdscr.addstr(15, 68, "WV", workedSection("WV"))
    stdscr.addstr(16, 63, "OH", workedSection("OH"))
    stdscr.addch(17, 62, curses.ACS_LTEE)
    stdscr.hline(17, 63, curses.ACS_HLINE, 7)
    stdscr.addch(17, 70, curses.ACS_RTEE)
    stdscr.addstr(17, 66, "9")
    stdscr.addstr(18, 63, "IL", workedSection("IL"))
    stdscr.addstr(18, 68, "WI", workedSection("WI"))
    stdscr.addstr(19, 63, "IN", workedSection("IN"))


def sectionsCol5():
    """display section column 5"""
    rectangle(stdscr, 8, 71, 21, 79)
    stdscr.hline(8, 72, curses.ACS_HLINE, 7)
    stdscr.addstr(8, 75, "0")
    stdscr.addstr(9, 72, "CO", workedSection("CO"))
    stdscr.addstr(9, 77, "MO", workedSection("MO"))
    stdscr.addstr(10, 72, "IA", workedSection("IA"))
    stdscr.addstr(10, 77, "ND", workedSection("ND"))
    stdscr.addstr(11, 72, "KS", workedSection("KS"))
    stdscr.addstr(11, 77, "NE", workedSection("NE"))
    stdscr.addstr(12, 72, "MN", workedSection("MN"))
    stdscr.addstr(12, 77, "SD", workedSection("SD"))
    stdscr.addch(13, 71, curses.ACS_LTEE)
    stdscr.hline(13, 72, curses.ACS_HLINE, 7)
    stdscr.addch(13, 79, curses.ACS_RTEE)
    stdscr.addstr(13, 72, "CANADA")
    stdscr.addstr(14, 72, "AB", workedSection("AB"))
    stdscr.addstr(15, 72, "BC", workedSection("BC"))
    stdscr.addstr(16, 72, "GH", workedSection("GH"))
    stdscr.addstr(17, 72, "MB", workedSection("MB"))
    stdscr.addstr(18, 72, "NB", workedSection("NB"))
    stdscr.addstr(19, 72, "NL", workedSection("NL"))
    stdscr.addstr(20, 72, "NS", workedSection("NS"))
    stdscr.addstr(14, 77, "PE", workedSection("PE"))
    stdscr.addstr(15, 76, "ONE", workedSection("ONE"))
    stdscr.addstr(16, 76, "ONN", workedSection("ONN"))
    stdscr.addstr(17, 76, "ONS", workedSection("ONS"))
    stdscr.addstr(18, 77, "QC", workedSection("QC"))
    stdscr.addstr(19, 77, "SK", workedSection("SK"))
    stdscr.addstr(20, 76, "TER", workedSection("TER"))


def sections():
    """display all the sections"""
    workedSections()
    sectionsCol1()
    sectionsCol2()
    sectionsCol3()
    sectionsCol4()
    sectionsCol5()
    stdscr.refresh()


def entry():
    """draws the main input fields"""
    rectangle(stdscr, 8, 0, 10, 18)
    stdscr.addstr(8, 1, "CALL")
    rectangle(stdscr, 8, 19, 10, 25)
    stdscr.addstr(8, 20, "Class")
    rectangle(stdscr, 8, 26, 10, 34)
    stdscr.addstr(8, 27, "Section")


def clearentry():
    """clears the main input fields"""
    global inputFieldFocus, hiscall, hissection, hisclass, kbuf
    hiscall = ""
    hissection = ""
    hisclass = ""
    kbuf = ""
    y, x = stdscr.getyx()
    stdscr.addstr(9, 16, " ")
    stdscr.move(y, x)
    inputFieldFocus = 0
    hissection_field.set_text("")
    hissection_field.get_focus()
    hisclass_field.set_text("")
    hisclass_field.get_focus()
    hiscall_field.set_text("")
    hiscall_field.get_focus()
    clearcontactlookup()


def YorN(boolean):
    """returns y or n"""
    if boolean:
        return "Y"
    return "N"


def highlightBonus(bonus):
    """returns a highlight color pair if true"""
    if bonus:
        return curses.color_pair(1)
    return curses.A_DIM


def setStatusMsg(msg):
    """displays a status message"""
    oy, ox = stdscr.getyx()
    window = curses.newpad(10, 33)
    rectangle(stdscr, 11, 0, 21, 34)
    window.addstr(0, 0, str(msg))
    stdscr.refresh()
    window.refresh(0, 0, 12, 1, 20, 33)
    stdscr.move(oy, ox)


def statusline() -> None:
    """displays a status line..."""
    y, x = stdscr.getyx()
    now = datetime.datetime.now().isoformat(" ")[5:19].replace("-", "/")
    utcnow = datetime.datetime.now(datetime.UTC).isoformat(" ")[5:19].replace("-", "/")

    try:
        stdscr.addstr(22, 62, "LOC " + now)
        stdscr.addstr(23, 62, "UTC " + utcnow)
    except curses.error:
        # curses will throw an error if printing to the last cell in the bottom right
        pass  # pylint: disable=bare-except

    strfreq = freq.rjust(9)
    strfreq = f"{strfreq[0:3]}.{strfreq[3:6]}.{strfreq[6:9]}"

    strband = band
    if band is None or band == "None":
        strband = "OOB"

    if strband == "222":
        strband = "1.25"
    elif strband == "432":
        strband = "70"

    suffix = ""

    if freq != "":
        if strband == "OOB":
            suffix = ""
        elif int(freq) > 225000000:
            suffix = "cm"
        else:
            suffix = "m"

    strband += suffix

    if len(strband) < 4:
        strband += " "

    stdscr.addstr(23, 0, "Band       Freq             Mode   ")
    stdscr.addstr(23, 5, strband.rjust(5), highlightBonus(True))
    stdscr.addstr(23, 16, strfreq, highlightBonus(True))
    stdscr.addstr(23, 33, mode, highlightBonus(True))
    stdscr.addstr(22, 37, "                         ")
    stdscr.addstr(
        22,
        37,
        f" {preference.preference.get('mycallsign')}|"
        f"{preference.preference.get('myclass')}|"
        f"{preference.preference.get('mysection')}|"
        f"{preference.preference.get('power')}w ",
        highlightBonus(True),
    )
    stdscr.addstr(22, 0, "Bonus")
    stdscr.addstr(
        22, 6, "AltPwr", highlightBonus(preference.preference.get("altpower"))
    )
    stdscr.addch(curses.ACS_VLINE)
    stdscr.addstr("Outdoor", highlightBonus(preference.preference.get("outdoors")))
    stdscr.addch(curses.ACS_VLINE)
    stdscr.addstr("NotHome", highlightBonus(preference.preference.get("notathome")))
    stdscr.addch(curses.ACS_VLINE)
    stdscr.addstr("Sat", highlightBonus(preference.preference.get("satellite")))
    stdscr.addch(curses.ACS_VLINE)
    stdscr.addstr("Ant", highlightBonus(preference.preference.get("antenna")))
    stdscr.addstr(23, 37, "                        ")

    if cat_control:
        stdscr.addstr(
            23, 37, cat_control.interface.ljust(7), highlightBonus(cat_control.online)
        )

    if preference.preference["usehamdb"]:
        stdscr.addstr(23, 46, "HamDB", highlightBonus(not look_up.error))

    if preference.preference["usehamqth"]:
        stdscr.addstr(23, 46, "HamQTH", highlightBonus(look_up.session))

    if preference.preference["useqrz"]:
        stdscr.addstr(23, 46, "QRZ", highlightBonus(look_up.session))

    if preference.preference["cloudlog"]:
        stdscr.addstr(23, 53, "CloudLog", highlightBonus(cloudlog_on))

    stdscr.move(y, x)


def setpower(p):
    """I'm assuming it sets the power"""
    logging.info("setpower: %s%s", type(p), p)
    try:
        int(p)
    except ValueError:
        p = "0"
    if p is None or p == "":
        p = "0"
    if int(p) > 0 and int(p) < 101:
        preference.preference["power"] = str(p)
        writepreferences()
        statusline()
    else:
        setStatusMsg("Must be 1 <= Power <= 100")


def setband(b: str) -> None:
    """Needs Doc String"""
    global band
    band = b
    statusline()


def setmode(m: str) -> None:
    """Needs Doc String"""
    global mode
    mode = m
    statusline()


def setfreq(f: str) -> None:
    """Needs Doc String"""
    global freq
    freq = f
    statusline()


def displayHelp():
    """Display help menu"""
    rectangle(stdscr, 11, 0, 21, 34)
    wy, wx = stdscr.getyx()
    help_screen = [
        ".H Prints this message",
        ".Q quits the program",
        ".S Settings menu",
        ".E### Edit Log entry ",
        ".D### Delte Log entry  ",
        ".B## Change operating band",
        ".M[CW,PH,DG] Change mode logged",
        ".P## Change power logged",
        ".L Generate Logs",
    ]
    stdscr.move(12, 1)
    for count, line in enumerate(help_screen):
        stdscr.addstr(12 + count, 1, line)
    stdscr.move(wy, wx)
    stdscr.refresh()


def displayinfo(info, line=2):
    """Displays a line of text at the bottom of the info window"""
    y, x = stdscr.getyx()
    stdscr.move(18 + line, 1)
    stdscr.addstr(str(info))
    stdscr.move(y, x)
    stdscr.refresh()


def processcommand(cmd):
    """Process Dot commands"""
    global quitprogram, look_up, cat_control
    cmd = cmd[1:].upper()
    if cmd == "S":
        editsettings = SettingsScreen(preference.preference)
        changes = editsettings.show()
        if changes:
            preference.preference = changes
            preference.writepreferences()
            look_up = None
            cat_control = None
            readpreferences()
        stdscr.clear()
        contacts_label()
        logwindow()
        sections()
        stats()
        displayHelp()
        entry()
        stdscr.move(9, 1)
        return
    if cmd == "Q":  # quitprogram
        quitprogram = True
        return
    if cmd[:1] == "F":  # Set Radio Frequency
        send_radio(cmd[:1], cmd[1:])
        return
    if cmd[:1] == "B":  # Change Band
        if cmd[1:] and cmd[1:] in bands:
            if cat_control:
                send_radio(cmd[:1], cmd[1:])
                return
            setband(cmd[1:])
        else:
            setStatusMsg("Specify valid band")
        return
    if cmd[:1] == "M":  # Change Mode
        if not cat_control:
            if cmd[1:] == "CW" or cmd[1:] == "PH" or cmd[1:] == "DG":
                setmode(cmd[1:])
            else:
                setStatusMsg("Must be CW, DG, PH")
        else:
            if (
                cmd[1:] == "USB"
                or cmd[1:] == "LSB"
                or cmd[1:] == "CW"
                or cmd[1:] == "RTTY"
                or cmd[1:] == "AM"
                or cmd[1:] == "FM"
            ):
                send_radio(cmd[:1], cmd[1:])
            else:
                setStatusMsg("Must be AM, FM, CW, *SB, RTTY")
        return
    if cmd[:1] == "P":  # Change Power
        if cat_control:
            send_radio(cmd[:1], cmd[1:])
            setpower(cmd[1:])
        else:
            setpower(cmd[1:])
        return
    if cmd[:1] == "D":  # Delete Contact
        delete_contact(cmd[1:])
        return
    if cmd[:1] == "E":  # Edit QSO
        editQSO(cmd[1:])
        return
    if cmd[:1] == "H":  # Print Help
        displayHelp()
        return
    if cmd[:1] == "L":  # Generate Cabrillo Log
        cabrillo()
        return
    curses.flash()
    curses.beep()


def proc_key(key):
    """Processes key presses"""
    global inputFieldFocus, hiscall, hissection, hisclass
    input_field = [hiscall_field, hisclass_field, hissection_field]
    if key == ESCAPE:
        clearentry()
        if cw is not None:  # abort cw output
            if cw.servertype == 1:
                cw.sendcw("\x1b4")
        return
    if key == 9 or key == SPACE:
        inputFieldFocus += 1
        if inputFieldFocus > 2:
            inputFieldFocus = 0
        if inputFieldFocus == 0:  # cllsign input
            hissection = hissection_field.text()
            hiscall_field.get_focus()
        if inputFieldFocus == 1:  # class input
            logging.debug(
                "checking for dupe and grid %s - %s", hiscall, hiscall_field.text()
            )
            if hiscall != hiscall_field.text():
                if len(hiscall_field.text()) > 2 and hiscall_field.text()[:1] != ".":
                    dupCheck(hiscall_field.text())
                    logging.debug("Call the lazy")
                    x = threading.Thread(
                        target=lazy_lookup, args=(hiscall_field.text(),), daemon=True
                    )
                    x.start()
                hiscall = hiscall_field.text()
            hisclass_field.get_focus()
        if inputFieldFocus == 2:  # section input
            hisclass = hisclass_field.text()
            hissection_field.get_focus()
        return
    if key == ENTERKEY:
        if inputFieldFocus == 0:
            hiscall = hiscall_field.text()
        elif inputFieldFocus == 1:
            hisclass = hisclass_field.text()
        elif inputFieldFocus == 2:
            hissection = hissection_field.text()
        if hiscall[:1] == ".":  # process command
            processcommand(hiscall)
            clearentry()
            return
        if hiscall == "" or hisclass == "" or hissection == "":
            return
        isCall = re.compile(
            "^(([0-9])?[A-z]{1,2}[0-9]/)?[A-Za-z]{1,2}[0-9]{1,3}[A-Za-z]{1,4}(/[A-Za-z0-9]{1,3})?$"
        )
        if re.match(isCall, hiscall):
            contact = (
                hiscall,
                hisclass,
                hissection,
                band,
                mode,
                int(preference.preference.get("power")),
                contactlookup.get("grid"),
                contactlookup.get("name"),
            )
            log_contact(contact)
            clearentry()
        else:
            setStatusMsg("Must be valid call sign")
        return
    if key == 258:  # key down
        logup()
        return
    if key == 259:  # key up
        logdown()
        return
    if key == 338:  # page down
        logpagedown()
        return
    if key == 339:  # page up
        logpageup()
        return
    input_field[inputFieldFocus].getchar(key)
    if inputFieldFocus == 0 and len(hiscall_field.text()) > 2:
        displaySCP(super_check(hiscall_field.text()))
    if inputFieldFocus == 2:
        section_check(hissection_field.text())
    check_function_keys(key)


def edit_key(key):
    """While editing qso record, control is passed here to process key presses."""
    global editFieldFocus, quitprogram
    if key == 9:
        editFieldFocus += 1
        if editFieldFocus > 8:
            editFieldFocus = 1
        qso_edit_fields[editFieldFocus - 1].get_focus()
        return

    if key == ENTERKEY:
        qso[1] = qso_edit_fields[0].text()
        qso[2] = qso_edit_fields[1].text()
        qso[3] = qso_edit_fields[2].text()
        qso[4] = f"{qso_edit_fields[3].text()} {qso_edit_fields[4].text()}"
        qso[5] = qso_edit_fields[5].text()
        qso[6] = qso_edit_fields[6].text()
        qso[7] = qso_edit_fields[7].text()
        change_contact(qso)
        qsoew.erase()
        stdscr.clear()
        contacts_label()
        logwindow()
        sections()
        stats()
        displayHelp()
        entry()
        stdscr.move(9, 1)
        quitprogram = True
        return
    if key == ESCAPE:
        qsoew.erase()
        stdscr.clear()
        contacts_label()
        logwindow()
        sections()
        stats()
        displayHelp()
        entry()
        stdscr.move(9, 1)
        quitprogram = True
        return
    if key == 258:  # arrow down
        editFieldFocus += 1
        if editFieldFocus > 8:
            editFieldFocus = 1
        qso_edit_fields[editFieldFocus - 1].get_focus()
        return
    if key == 259:  # arrow up
        editFieldFocus -= 1
        if editFieldFocus < 1:
            editFieldFocus = 8
        qso_edit_fields[editFieldFocus - 1].get_focus()
        return

    qso_edit_fields[editFieldFocus - 1].getchar(key)


def EditClickedQSO(line: int) -> None:
    """Control is passed here when a contact in the log window is double clicked."""
    global qsoew, qso, quitprogram, qso_edit_fields, editFieldFocus
    editFieldFocus = 1
    record = (
        contacts.instr((line - 1) + contactsOffset, 0, 55)
        .decode("utf-8")
        .strip()
        .split()
    )
    if record == []:
        return
    qso = [
        record[0],
        record[1],
        record[2],
        record[3],
        record[4] + " " + record[5],
        record[6],
        record[7],
        record[8],
    ]
    qsoew = curses.newwin(10, 40, 6, 10)
    qsoew.keypad(True)
    qsoew.nodelay(True)
    qsoew.box()

    qso_edit_field_1 = EditTextField(qsoew, 1, 10, 14)
    qso_edit_field_2 = EditTextField(qsoew, 2, 10, 3)
    qso_edit_field_3 = EditTextField(qsoew, 3, 10, 3)
    qso_edit_field_4 = EditTextField(qsoew, 4, 10, 10)
    qso_edit_field_5 = EditTextField(qsoew, 4, 21, 8)
    qso_edit_field_6 = EditTextField(qsoew, 5, 10, 3)
    qso_edit_field_7 = EditTextField(qsoew, 6, 10, 2)
    qso_edit_field_8 = EditTextField(qsoew, 7, 10, 3)

    qso_edit_field_1.set_text(record[1])
    qso_edit_field_2.set_text(record[2])
    qso_edit_field_3.set_text(record[3])
    qso_edit_field_4.set_text(record[4])
    qso_edit_field_5.set_text(record[5])
    qso_edit_field_6.set_text(record[6])
    qso_edit_field_7.set_text(record[7])
    qso_edit_field_8.set_text(str(record[8]))

    qso_edit_fields = [
        qso_edit_field_1,
        qso_edit_field_2,
        qso_edit_field_3,
        qso_edit_field_4,
        qso_edit_field_5,
        qso_edit_field_6,
        qso_edit_field_7,
        qso_edit_field_8,
    ]

    qsoew.addstr(1, 1, "Call   : ")
    qsoew.addstr(2, 1, "Class  : ")
    qsoew.addstr(3, 1, "Section: ")
    qsoew.addstr(4, 1, "At     : ")
    qsoew.addstr(5, 1, "Band   : ")
    qsoew.addstr(6, 1, "Mode   : ")
    qsoew.addstr(7, 1, "Powers : ")
    qsoew.addstr(8, 1, "[Enter] to save          [Esc] to exit")

    for displayme in qso_edit_fields:
        displayme.get_focus()
    qso_edit_fields[0].get_focus()

    while 1:
        statusline()
        stdscr.refresh()
        qsoew.refresh()
        c = qsoew.getch()
        if c != -1:
            edit_key(c)
        else:
            time.sleep(0.01)
        if quitprogram:
            quitprogram = False
            break


def editQSO(q):
    """Control is passed here when a .E command is used to edit a contact."""
    if q is False or q == "":
        setStatusMsg("Must specify a contact number")
        return
    global qsoew, qso, quitprogram, qso_edit_fields, editFieldFocus
    log = database.contact_by_id(q)
    if not log:
        return
    qso = ["", "", "", "", "", "", "", ""]
    qso[0] = log.get("id")
    qso[1] = log.get("callsign")
    qso[2] = log.get("class")
    qso[3] = log.get("section")
    qso[4] = log.get("date_time")
    qso[5] = log.get("band")
    qso[6] = log.get("mode")
    qso[7] = log.get("power")

    # qso[0], qso[1], qso[2], qso[3], qso[4], qso[5], qso[6], qso[7], _, _ = log[0]
    qsoew = curses.newwin(10, 40, 6, 10)
    qsoew.keypad(True)
    qsoew.nodelay(True)
    qsoew.box()
    editFieldFocus = 1
    qso_edit_field_1 = EditTextField(qsoew, 1, 10, 14)
    qso_edit_field_2 = EditTextField(qsoew, 2, 10, 3)
    qso_edit_field_3 = EditTextField(qsoew, 3, 10, 3)
    qso_edit_field_4 = EditTextField(qsoew, 4, 10, 10)
    qso_edit_field_5 = EditTextField(qsoew, 4, 21, 8)
    qso_edit_field_6 = EditTextField(qsoew, 5, 10, 3)
    qso_edit_field_7 = EditTextField(qsoew, 6, 10, 2)
    qso_edit_field_8 = EditTextField(qsoew, 7, 10, 3)

    qso_edit_field_1.set_text(log.get("callsign"))
    qso_edit_field_2.set_text(log.get("class"))
    qso_edit_field_3.set_text(log.get("section"))
    dt = log.get("date_time").split()
    qso_edit_field_4.set_text(dt[0])
    qso_edit_field_5.set_text(dt[1])
    qso_edit_field_6.set_text(log.get("band"))
    qso_edit_field_7.set_text(log.get("mode"))
    qso_edit_field_8.set_text(str(log.get("power")))

    qso_edit_fields = [
        qso_edit_field_1,
        qso_edit_field_2,
        qso_edit_field_3,
        qso_edit_field_4,
        qso_edit_field_5,
        qso_edit_field_6,
        qso_edit_field_7,
        qso_edit_field_8,
    ]

    qsoew.addstr(1, 1, "Call   : ")
    qsoew.addstr(2, 1, "Class  : ")
    qsoew.addstr(3, 1, "Section: ")
    qsoew.addstr(4, 1, "At     : ")
    qsoew.addstr(5, 1, "Band   : ")
    qsoew.addstr(6, 1, "Mode   : ")
    qsoew.addstr(7, 1, "Powers : ")
    qsoew.addstr(8, 1, "[Enter] to save          [Esc] to exit")

    for displayme in qso_edit_fields:
        displayme.get_focus()
    qso_edit_fields[0].get_focus()
    while 1:
        statusline()
        stdscr.refresh()
        qsoew.refresh()
        c = qsoew.getch()
        if c != -1:
            edit_key(c)
        else:
            time.sleep(0.01)
        if quitprogram:
            quitprogram = False
            break


def main(s) -> None:
    """It's the main loop."""
    logging.debug("main: %s", s)
    global poll_time
    curses.start_color()
    curses.use_default_colors()
    if curses.can_change_color():
        curses.init_color(curses.COLOR_MAGENTA, 1000, 640, 0)
        curses.init_color(curses.COLOR_BLACK, 0, 0, 0)
        curses.init_color(curses.COLOR_CYAN, 500, 500, 500)
        curses.init_pair(1, curses.COLOR_MAGENTA, -1)
        curses.init_pair(2, curses.COLOR_RED, -1)
        curses.init_pair(3, curses.COLOR_CYAN, -1)
    curses.noecho()
    curses.cbreak()
    stdscr.keypad(True)
    stdscr.nodelay(True)
    curses.mousemask(curses.ALL_MOUSE_EVENTS)
    stdscr.attrset(curses.color_pair(0))
    stdscr.clear()
    version_check = VersionTest(__version__)
    if version_check.test():
        version_dialog = curses.newwin(7, 36, 7, 24)
        version_dialog.keypad(True)
        version_dialog.nodelay(True)
        version_dialog.box()
        version_dialog.addstr(
            1, 2, f"A newer version exists: {version_check.newest_release}"
        )
        version_dialog.addstr(2, 2, "You can install it with:")
        version_dialog.addstr(3, 2, "pip install --upgrade wfdcurses")
        version_dialog.addstr(5, 5, "Press any key to dismiss")

        while 1:
            statusline()
            stdscr.refresh()
            version_dialog.refresh()
            c = version_dialog.getch()
            if c != -1:
                version_dialog.erase()
                stdscr.clear()
                break
            else:
                time.sleep(0.01)
    contacts_label()
    sections()
    read_cw_macros()
    entry()
    logwindow()
    stats()
    displayHelp()
    stdscr.refresh()
    stdscr.move(9, 1)
    while 1:
        statusline()
        stdscr.refresh()
        ch = stdscr.getch()
        if ch == curses.KEY_MOUSE:
            buttons = ""
            try:
                _, x, y, _, buttons = curses.getmouse()
                if buttons == 65536:
                    logdown()
                if buttons == 2097152:
                    logup()
                if buttons == 8 and 0 < y < 7 and 0 < x < 56:
                    EditClickedQSO(y)
            except curses.error:
                pass
        elif ch != -1:
            proc_key(ch)
        else:
            time.sleep(0.01)
        if quitprogram:
            break
        if datetime.datetime.now() > poll_time:
            poll_radio()
            poll_time = datetime.datetime.now() + datetime.timedelta(seconds=1)


def register_services():
    """setup services"""
    global look_up, cat_control, cloudlog_on, cw
    cw = None
    look_up = None
    cat_control = None
    cloudlog_on = False

    if preference.preference.get("cwtype"):
        cw = CW(
            int(preference.preference.get("cwtype")),
            preference.preference.get("CW_IP"),
            int(preference.preference.get("CW_port")),
        )
        cw.speed = 20
        if preference.preference.get("cwtype") == 1:
            cw.sendcw("\x1b220")

    if preference.preference.get("useqrz"):
        look_up = QRZlookup(
            preference.preference.get("lookupusername"),
            preference.preference.get("lookuppassword"),
        )
    if preference.preference.get("usehamdb"):
        look_up = HamDBlookup()
    if preference.preference.get("usehamqth"):
        look_up = HamQTH(
            preference.preference.get("lookupusername"),
            preference.preference.get("lookuppassword"),
        )
    if preference.preference.get("useflrig"):
        cat_control = CAT(
            "flrig",
            preference.preference.get("CAT_ip"),
            preference.preference.get("CAT_port"),
        )
    if preference.preference.get("userigctld"):
        cat_control = CAT(
            "rigctld",
            preference.preference.get("CAT_ip"),
            preference.preference.get("CAT_port"),
        )

    if preference.preference.get("cloudlog"):
        # <auth>
        # <status>Valid</status>
        # <rights>rw</rights>
        # </auth>

        # <auth>
        # <message>Key Invalid - either not found or disabled</message>
        # </auth>

        __payload = "/auth/" + preference.preference.get("cloudlogapi")

        try:
            result = requests.get(
                preference.preference.get("cloudlogurl") + __payload, timeout=5
            )

            if result.status_code == 200 and "<status>Valid</status>" in result.text:
                logging.debug("Cloudlog: Auth: %s", result.text)
                cloudlog_on = True
        except requests.exceptions.ConnectionError as exception:
            logging.warning("cloudlog authentication: %s", exception)


database = DataBase("wfd.db")
preference = Preferences()
readpreferences()
register_services()
read_sections()
scp = read_scp()
hiscall_field = EditTextField(stdscr, y=9, x=1, length=14)
hisclass_field = EditTextField(stdscr, y=9, x=20, length=4)
hissection_field = EditTextField(stdscr, y=9, x=27, length=3)


def run():
    """main entry point"""
    PATH = os.path.dirname(__loader__.get_filename())
    os.system(
        "xdg-icon-resource install --size 64 --context apps --mode user "
        f"{PATH}/data/k6gte.wfdcurses-32.png k6gte-wfdcurses"
    )
    os.system(
        "xdg-icon-resource install --size 64 --context apps --mode user "
        f"{PATH}/data/k6gte.wfdcurses-64.png k6gte-wfdcurses"
    )
    os.system(
        "xdg-icon-resource install --size 64 --context apps --mode user "
        f"{PATH}/data/k6gte.wfdcurses-128.png k6gte-wfdcurses"
    )
    os.system(f"xdg-desktop-menu install {PATH}/data/k6gte-wfdcurses.desktop")
    wrapper(main)


if __name__ == "__main__":
    wrapper(main)
