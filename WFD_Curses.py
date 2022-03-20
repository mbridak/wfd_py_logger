#!/usr/bin/env python3
# pylint: disable=too-many-lines
# pylint: disable=global-statement
# pylint: disable=redefined-outer-name
# pylint: disable=invalid-name
"""
Winter Field Day logger curses based.
"""

# rows, cols = stdscr.getmaxyx()

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

from math import degrees, radians, sin, cos, atan2, sqrt, asin, pi
from pathlib import Path
from curses.textpad import rectangle
from curses import wrapper
from json import dumps
import threading

import requests
from database import DataBase
from preferences import Preferences
from lookup import HamDBlookup, HamQTH, QRZlookup
from cat_interface import CAT


if Path("./debug").exists():
    logging.basicConfig(
        filename="debug.log",
        filemode="w",
        format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
        level=logging.DEBUG,
    )
    logging.debug("Debug started")


poll_time = datetime.datetime.now()
cloudlogapi = False
cloudlogurl = False
cloudlog_on = False
preference = None
rigonline = False

stdscr = curses.initscr()
height, width = stdscr.getmaxyx()
if height < 24 or width < 80:
    print("Terminal size needs to be at least 80x24")
    curses.endwin()
    sys.exit()
qsoew = 0
qso = []
quitprogram = False

BACK_SPACE = 263
ESCAPE = 27
QUESTIONMARK = 63
ENTERKEY = 10
SPACE = 32

modes = ("PH", "CW", "DI")
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
    "NT",
    "BC",
    "ONE",
    "GTA",
    "ONN",
    "MAR",
    "ONS",
    "MB",
    "QC",
    "NL",
    "SK",
    "PE",
]

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

database = "WFD_Curses.db"
wrkdsections = []
scp = []
secPartial = {}
secName = {}
secState = {}
oldfreq = "0"
oldmode = ""
oldpwr = 0


def lazy_lookup(acall: str) -> None:
    """looks up a callsign for name, gridsquare, distance and bearing"""
    grid, name, _, _ = look_up.lookup(acall)
    dist = 0
    berg = 0
    if grid:
        dist = distance("dm13at", grid)
        berg = bearing("dm13at", grid)
    displayinfo(f"{name} {grid} {round(dist)}km {round(berg)}deg")
    logging.debug("lazy lookup:%s %s", grid, name)


def gridtolatlon(maiden: str) -> tuple[float, float]:
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


def relpath(filename: str) -> str:
    """
    Checks to see if program has been packaged with pyinstaller.
    If so base dir is in a temp folder.
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base_path = getattr(sys, "_MEIPASS")
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, filename)


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
    return "DI"  # All else digital


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
        if preference.preference["useflrig"]:
            cat_control = CAT(
                "flrig",
                preference.preference["CAT_ip"],
                preference.preference["CAT_port"],
            )
        if preference.preference["userigctld"]:
            cat_control = CAT(
                "rigctld",
                preference.preference["CAT_ip"],
                preference.preference["CAT_port"],
            )

    if cat_control.online:
        newfreq = cat_control.get_vfo()
        newmode = cat_control.get_mode()
        newpwr = cat_control.get_power()
        logging.info("F:%s M:%s P:%s", newfreq, newmode, newpwr)
        # newpwr = int(float(rigctrlsocket.recv(1024).decode().strip()) * 100)
        if newfreq != oldfreq or newmode != oldmode:  # or newpwr != oldpwr
            oldfreq = newfreq
            oldmode = newmode
            # oldpwr = newpwr
            setband(str(getband(newfreq)))
            setmode(str(getmode(newmode)))
            # setpower(str(newpwr))
            setfreq(str(newfreq))


def readpreferences() -> None:
    """Reads in preferences"""
    preference.readpreferences()


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
    """Reads in ARRL section data into a list"""
    try:
        with open(
            relpath("arrl_sect.dat"), "r", encoding="utf-8"
        ) as file_descriptor:  # read section data
            while 1:
                line = file_descriptor.readline().strip()  # read a line and put in db
                if not line:
                    break
                if line[0] == "#":
                    continue
                try:
                    _, state, canum, abbrev, name = str.split(line, None, 4)
                    secName[abbrev] = abbrev + " " + name + " " + canum
                    secState[abbrev] = state
                    for i in range(len(abbrev) - 1):
                        p = abbrev[: -i - 1]
                        secPartial[p] = 1
                except ValueError as value_exception:
                    logging.debug("read_sections: Value error %s", value_exception)
    except IOError as exception:
        logging.debug("read_sections: IO Error %s", exception)


def section_check(sec: str) -> None:
    """checks if a string is part of a section name"""
    if sec == "":
        sec = "^"
    seccheckwindow = curses.newpad(20, 33)
    rectangle(stdscr, 11, 0, 21, 34)
    list_of_keys = list(secName.keys())
    matches = list(filter(lambda y: y.startswith(sec), list_of_keys))
    count = 0
    for match in matches:
        seccheckwindow.addstr(count, 1, secName[match])
        count += 1
    stdscr.refresh()
    seccheckwindow.refresh(0, 0, 12, 1, 20, 33)


def read_scp() -> list:
    """reads in the super check partion data into a list"""
    with open(relpath("MASTER.SCP"), "r", encoding="utf-8") as file_descriptor:
        lines = file_descriptor.readlines()
    return list(map(lambda x: x.strip(), lines))


def super_check(acall: str) -> list:
    """returns a list of matches for acall against known contesters."""
    return list(filter(lambda x: x.startswith(acall), scp))


def contacts_label():
    """
    all it does is centers a string to create a label for a window...
    why is this it's own function?
    I'm sure there is a reason. I just don't remember.
    """
    rectangle(stdscr, 0, 0, 7, 55)
    contactslabel = "Recent Contacts"
    contactslabeloffset = (49 / 2) - len(contactslabel) / 2
    stdscr.addstr(0, int(contactslabeloffset), contactslabel)


def stats() -> None:
    """calculates and displays the current statistics."""
    y, x = stdscr.getyx()
    (
        cwcontacts,
        phonecontacts,
        digitalcontacts,
        _,
        last15,
        lasthour,
        _,
        _,
    ) = database.stats()
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
    cw, ph, di, bandmodemult, _, _, highpower, qrp = database.stats()
    __score = (int(cw) * 2) + int(ph) + (int(di) * 2)
    if qrp:
        __score = __score * 4
    elif not highpower:
        __score = __score * 2
    __score = __score * bandmodemult
    __score = (
        __score
        + (500 * preference.preference["altpower"])
        + (500 * preference.preference["outdoors"])
        + (500 * preference.preference["notathome"])
        + (500 * preference.preference["satellite"])
    )
    return __score


def getBandModeTally(band, mode):
    """Needs Doc String"""
    return database.get_band_mode_tally(band, mode)


def getbands():
    """Needs Doc String"""
    bandlist = []
    x = database.get_bands()
    if x:
        for count in x:
            bandlist.append(count[0])
        return bandlist
    return []


def generateBandModeTally():
    """Needs Doc String"""
    blist = getbands()
    bmtfn = "Statistics.txt"
    with open(bmtfn, "w", encoding="utf-8") as f:
        print("\t\tCW\tPWR\tDI\tPWR\tPH\tPWR", end="\r\n", file=f)
        print("-" * 60, end="\r\n", file=f)
        for b in bands:
            if b in blist:
                cwt = getBandModeTally(b, "CW")
                dit = getBandModeTally(b, "DI")
                pht = getBandModeTally(b, "PH")
                print(
                    f"Band:\t{b}\t{cwt[0]}\t{cwt[1]}\t{dit[0]}\t{dit[1]}\t{pht[0]}\t{pht[1]}",
                    end="\r\n",
                    file=f,
                )
                print("-" * 60, end="\r\n", file=f)


def get_state(section):
    """returns the state of a section"""
    try:
        state = secState[section]
        if state != "--":
            return state
    except IndexError:
        return False
    return False


def adif():
    """generates an ADIF file from your contacts"""
    logname = "WFD.adi"
    log = database.fetch_all_contacts_asc()
    counter = 0
    grid = False
    with open(logname, "w", encoding="utf-8") as file_descriptor:
        print("<ADIF_VER:5>2.2.0", end="\r\n", file=file_descriptor)
        print("<EOH>", end="\r\n", file=file_descriptor)
        for contact in log:
            _, hiscall, hisclass, hissection, datetime, band, mode, _ = contact
            if mode == "DI":
                mode = "RTTY"
            if mode == "PH":
                mode = "SSB"
            if mode == "CW":
                rst = "599"
            else:
                rst = "59"
            loggeddate = datetime[:10]
            loggedtime = datetime[11:13] + datetime[14:16]
            yy, xx = stdscr.getyx()
            stdscr.move(15, 1)
            stdscr.addstr(f"QRZ Gridsquare Lookup: {counter}")
            stdscr.move(yy, xx)
            stdscr.refresh()
            grid = False
            name = False
            if look_up:
                grid, name, _, _ = look_up.lookup(hiscall)
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
    if not cloudlogapi:
        return
    q = database.fetch_last_contact()
    _, hiscall, hisclass, hissection, datetime, band, mode, _ = q
    grid = False
    name = False
    strippedcall = parsecallsign(hiscall)
    if look_up:
        grid, name, _, _ = look_up.lookup(strippedcall)
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
    value2 = preference.preference["myclass"] + " " + preference.preference["mysection"]
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

    payload = {"key": cloudlogapi, "type": "adif", "string": adifq}

    jsonData = dumps(payload)
    logging.debug(jsonData)
    qsoUrl = cloudlogurl + "/qso"
    _ = requests.post(qsoUrl, jsonData)


def cabrillo():
    """generates a cabrillo log"""
    bonuses = 0
    catpower = ""
    _, _, _, _, _, _, highpower, qrp = database.stats()
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
            preference.preference["mycallsign"],
            end="\r\n",
            file=file_descriptor,
        )
        print("LOCATION:", end="\r\n", file=file_descriptor)
        print(
            "ARRL-SECTION:",
            preference.preference["mysection"],
            end="\r\n",
            file=file_descriptor,
        )
        print(
            "CATEGORY:",
            preference.preference["myclass"],
            end="\r\n",
            file=file_descriptor,
        )
        print("CATEGORY-POWER: " + catpower, end="\r\n", file=file_descriptor)
        if preference.preference["altpower"]:
            print(
                "SOAPBOX: 500 points for not using commercial power",
                end="\r\n",
                file=file_descriptor,
            )
            bonuses = bonuses + 500
        if preference.preference["outdoors"]:
            print(
                "SOAPBOX: 500 points for setting up outdoors",
                end="\r\n",
                file=file_descriptor,
            )
            bonuses = bonuses + 500
        if preference.preference["notathome"]:
            print(
                "SOAPBOX: 500 points for setting up away from home",
                end="\r\n",
                file=file_descriptor,
            )
            bonuses = bonuses + 500
        if preference.preference["satellite"]:
            print(
                "SOAPBOX: 500 points for working satellite",
                end="\r\n",
                file=file_descriptor,
            )
            bonuses = bonuses + 500
        print(f"SOAPBOX: BONUS Total {bonuses}", end="\r\n", file=file_descriptor)

        print(f"CLAIMED-SCORE: {score()}", end="\r\n", file=file_descriptor)
        print(
            f"OPERATORS:{preference.preference['mycallsign']}",
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
        for x in log:
            _, hiscall, hisclass, hissection, datetime, band, mode, _ = x
            loggeddate = datetime[:10]
            loggedtime = datetime[11:13] + datetime[14:16]
            print(
                f"QSO: {band}M {mode} {loggeddate} {loggedtime} "
                f"{preference.preference['mycallsign']} "
                f"{preference.preference['myclass']} "
                f"{preference.preference['mysection']} {hiscall} {hisclass} {hissection}",
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
        logid, hiscall, hisclass, hissection, datetime, band, mode, power = contact
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
    # global hisclass, hissection
    oy, ox = stdscr.getyx()
    scpwindow = curses.newpad(1000, 33)
    rectangle(stdscr, 11, 0, 21, 34)
    log = database.dup_check(acall)
    counter = 0
    for contact in log:
        decorate = ""
        hiscall, _, _, hisband, hismode = contact
        if hisband == band and hismode == mode:
            decorate = curses.color_pair(1)
            curses.flash()
            curses.beep()
        else:
            decorate = curses.A_NORMAL
        scpwindow.addstr(counter, 0, f"{hiscall}: {hisband} {hismode}", decorate)
        counter = counter + 1
    stdscr.refresh()
    scpwindow.refresh(0, 0, 12, 1, 20, 33)
    stdscr.move(oy, ox)


def displaySCP(matches):
    """show super check partial matches"""
    scpwindow = curses.newpad(1000, 33)
    rectangle(stdscr, 11, 0, 21, 34)
    for x in matches:
        wy, wx = scpwindow.getyx()
        if (33 - wx) < len(str(x)):
            scpwindow.move(wy + 1, 0)
        scpwindow.addstr(str(x) + " ")
    stdscr.refresh()
    scpwindow.refresh(0, 0, 12, 1, 20, 33)


def workedSections():
    """gets the worked sections"""
    global wrkdsections
    all_rows = database.sections()
    wrkdsections = str(all_rows)
    wrkdsections = (
        wrkdsections.replace("('", "")
        .replace("',), ", ",")
        .replace("',)]", "")
        .replace("[", "")
        .split(",")
    )


def workedSection(section):
    """highlights the worked sections"""
    if section in wrkdsections:
        # return curses.A_BOLD
        return curses.color_pair(1)
    return curses.A_DIM


def sectionsCol1():
    """display section column 1"""
    rectangle(stdscr, 8, 35, 21, 43)
    stdscr.addstr(8, 36, "   DX  ", curses.A_REVERSE)
    stdscr.addstr(9, 36, "   DX  ", workedSection("DX"))
    stdscr.addstr(10, 36, "   1   ", curses.A_REVERSE)
    stdscr.addstr(11, 36, "CT", workedSection("CT"))
    stdscr.addstr(11, 41, "RI", workedSection("RI"))
    stdscr.addstr(12, 36, "EMA", workedSection("EMA"))
    stdscr.addstr(12, 41, "VT", workedSection("VT"))
    stdscr.addstr(13, 36, "ME", workedSection("ME"))
    stdscr.addstr(13, 40, "WMA", workedSection("WMA"))
    stdscr.addstr(14, 36, "NH", workedSection("NH"))
    stdscr.addstr(15, 36, "   2   ", curses.A_REVERSE)
    stdscr.addstr(16, 36, "ENY", workedSection("ENY"))
    stdscr.addstr(16, 40, "NNY", workedSection("NNY"))
    stdscr.addstr(17, 36, "NLI", workedSection("NLI"))
    stdscr.addstr(17, 40, "SNJ", workedSection("SNJ"))
    stdscr.addstr(18, 36, "NNJ", workedSection("NNJ"))
    stdscr.addstr(18, 40, "WNY", workedSection("WNY"))


def sectionsCol2():
    """display section column 2"""
    rectangle(stdscr, 8, 44, 21, 52)
    stdscr.addstr(8, 45, "   3   ", curses.A_REVERSE)
    stdscr.addstr(9, 45, "DE", workedSection("DE"))
    stdscr.addstr(9, 49, "MDC", workedSection("MDC"))
    stdscr.addstr(10, 45, "EPA", workedSection("EPA"))
    stdscr.addstr(10, 49, "WPA", workedSection("WPA"))
    stdscr.addstr(11, 45, "   4   ", curses.A_REVERSE)
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
    stdscr.addstr(8, 54, "   5   ", curses.A_REVERSE)
    stdscr.addstr(9, 54, "AR", workedSection("AR"))
    stdscr.addstr(9, 58, "NTX", workedSection("NTX"))
    stdscr.addstr(10, 54, "LA", workedSection("LA"))
    stdscr.addstr(10, 59, "OK", workedSection("OK"))
    stdscr.addstr(11, 54, "MS", workedSection("MS"))
    stdscr.addstr(11, 58, "STX", workedSection("STX"))
    stdscr.addstr(12, 54, "NM", workedSection("NM"))
    stdscr.addstr(12, 58, "WTX", workedSection("WTX"))
    stdscr.addstr(13, 54, "   6   ", curses.A_REVERSE)
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
    stdscr.addstr(8, 63, "   7   ", curses.A_REVERSE)
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
    stdscr.addstr(14, 63, "   8   ", curses.A_REVERSE)
    stdscr.addstr(15, 63, "MI", workedSection("MI"))
    stdscr.addstr(15, 68, "WV", workedSection("WV"))
    stdscr.addstr(16, 63, "OH", workedSection("OH"))
    stdscr.addstr(17, 63, "   9   ", curses.A_REVERSE)
    stdscr.addstr(18, 63, "IL", workedSection("IL"))
    stdscr.addstr(18, 68, "WI", workedSection("WI"))
    stdscr.addstr(19, 63, "IN", workedSection("IN"))


def sectionsCol5():
    """display section column 5"""
    rectangle(stdscr, 8, 71, 21, 79)
    stdscr.addstr(8, 72, "   0   ", curses.A_REVERSE)
    stdscr.addstr(9, 72, "CO", workedSection("CO"))
    stdscr.addstr(9, 77, "MO", workedSection("MO"))
    stdscr.addstr(10, 72, "IA", workedSection("IA"))
    stdscr.addstr(10, 77, "ND", workedSection("ND"))
    stdscr.addstr(11, 72, "KS", workedSection("KS"))
    stdscr.addstr(11, 77, "NE", workedSection("NE"))
    stdscr.addstr(12, 72, "MN", workedSection("MN"))
    stdscr.addstr(12, 77, "SD", workedSection("SD"))
    stdscr.addstr(13, 72, "CANADA ", curses.A_REVERSE)
    stdscr.addstr(14, 72, "AB", workedSection("AB"))
    stdscr.addstr(14, 77, "NT", workedSection("NT"))
    stdscr.addstr(15, 72, "BC", workedSection("BC"))
    stdscr.addstr(15, 76, "ONE", workedSection("ONE"))
    stdscr.addstr(16, 72, "GTA", workedSection("GTA"))
    stdscr.addstr(16, 76, "ONN", workedSection("ONN"))
    stdscr.addstr(17, 72, "MAR", workedSection("MAR"))
    stdscr.addstr(17, 76, "ONS", workedSection("ONS"))
    stdscr.addstr(18, 72, "MB", workedSection("MB"))
    stdscr.addstr(18, 77, "QC", workedSection("QC"))
    stdscr.addstr(19, 72, "NL", workedSection("NL"))
    stdscr.addstr(19, 77, "SK", workedSection("SK"))
    stdscr.addstr(20, 72, "PE", workedSection("PE"))


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
    inputFieldFocus = 0
    displayInputField(2)
    displayInputField(1)
    displayInputField(0)


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
    window.addstr(0, 0, msg)
    stdscr.refresh()
    window.refresh(0, 0, 12, 1, 20, 33)
    stdscr.move(oy, ox)


def statusline():
    """displays a status line..."""
    y, x = stdscr.getyx()
    now = datetime.datetime.now().isoformat(" ")[5:19].replace("-", "/")
    utcnow = datetime.datetime.utcnow().isoformat(" ")[5:19].replace("-", "/")

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
    stdscr.addstr(23, 5, strband.rjust(5), curses.A_REVERSE)
    stdscr.addstr(23, 16, strfreq, curses.A_REVERSE)
    stdscr.addstr(23, 33, mode, curses.A_REVERSE)
    stdscr.addstr(22, 37, "                         ")
    stdscr.addstr(
        22,
        37,
        f" {preference.preference['mycallsign']}|"
        f"{preference.preference['myclass']}|"
        f"{preference.preference['mysection']}|"
        f"{preference.preference['power']}w ",
        curses.A_REVERSE,
    )
    stdscr.addstr(22, 0, "Bonus")
    stdscr.addstr(22, 6, "AltPwr", highlightBonus(preference.preference["altpower"]))
    stdscr.addch(curses.ACS_VLINE)
    stdscr.addstr("Outdoor", highlightBonus(preference.preference["outdoors"]))
    stdscr.addch(curses.ACS_VLINE)
    stdscr.addstr("NotHome", highlightBonus(preference.preference["notathome"]))
    stdscr.addch(curses.ACS_VLINE)
    stdscr.addstr("Sat", highlightBonus(preference.preference["satellite"]))
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


def setband(b):
    """Needs Doc String"""
    global band
    band = b
    statusline()


def setmode(m):
    """Needs Doc String"""
    global mode
    mode = m
    statusline()


def setfreq(f: str) -> None:
    """Needs Doc String"""
    global freq
    freq = f
    statusline()


def setcallsign(c):
    """Needs Doc String"""
    regex = re.compile(r"^([0-9])?[A-z]{1,2}[0-9]{1,3}[A-Za-z]{1,4}$")
    if re.match(regex, str(c)):
        preference.preference["mycallsign"] = str(c)
        writepreferences()
        statusline()
    else:
        setStatusMsg("Must be valid call sign")


def setclass(c):
    """Needs Doc String"""
    regex = re.compile(r"^[0-9]{1,2}[HhIiOo]$")
    if re.match(regex, str(c)):
        preference.preference["myclass"] = str(c)
        writepreferences()
        statusline()
    else:
        setStatusMsg("Must be valid station class")


def setsection(s):
    """validates users section"""
    if s and str(s) in validSections:
        preference.preference["mysection"] = str(s)
        writepreferences()
        statusline()
    else:
        setStatusMsg("Must be valid section")


def setrigctrlhost(o):
    """Needs Doc String"""
    preference.preference["CAT_ip"] = str(o)
    writepreferences()
    statusline()


def setrigctrlport(r):
    """Needs Doc String"""
    preference.preference["CAT_port"] = int(str(r))
    writepreferences()
    statusline()


def claimAltPower():
    """Needs Doc String"""
    if preference.preference["altpower"]:
        preference.preference["altpower"] = False
    else:
        preference.preference["altpower"] = True
    setStatusMsg("Alt Power set to: " + str(preference.preference["altpower"]))
    writepreferences()
    statusline()
    stats()


def claimOutdoors():
    """Needs Doc String"""
    if preference.preference["outdoors"]:
        preference.preference["outdoors"] = False
    else:
        preference.preference["outdoors"] = True
    setStatusMsg("Outdoor bonus set to: " + str(preference.preference["outdoors"]))
    writepreferences()
    statusline()
    stats()


def claimNotHome():
    """Needs Doc String"""
    if preference.preference["notathome"]:
        preference.preference["notathome"] = False
    else:
        preference.preference["notathome"] = True
    setStatusMsg("Away bonus set to: " + str(preference.preference["notathome"]))
    writepreferences()
    statusline()
    stats()


def claimSatellite():
    """Needs Doc String"""
    if preference.preference["satellite"]:
        preference.preference["satellite"] = False
    else:
        preference.preference["satellite"] = True
    setStatusMsg("Satellite bonus set to: " + str(preference.preference["satellite"]))
    writepreferences()
    statusline()
    stats()


def displayHelp():
    """Display help menu"""
    rectangle(stdscr, 11, 0, 21, 34)
    wy, wx = stdscr.getyx()
    help_screen = [
        ".H this message  |.2 Outdoors    ",
        ".Q quit program  |.3 AwayFromHome",
        ".Kyourcall       |.4 Satellite   ",
        ".Cyourclass      |.E### edit QSO ",
        ".Syoursection    |.D### del QSO  ",
        ".B## change bands|.L Generate Log",
        ".M[CW,PH,DI] mode|               ",
        ".P## change power|               ",
        ".1 Alt Power     |[esc] abort inp",
    ]
    stdscr.move(12, 1)
    for count, line in enumerate(help_screen):
        stdscr.addstr(12 + count, 1, line)
        count = count + 1
    stdscr.move(wy, wx)
    stdscr.refresh()


def displayinfo(info):
    """Needs Doc String"""
    y, x = stdscr.getyx()
    stdscr.move(20, 1)
    stdscr.addstr(info)
    stdscr.move(y, x)
    stdscr.refresh()


def displayLine():
    """Needs Doc String"""
    filler = "                        "
    line = kbuf + filler[: -len(kbuf)]
    stdscr.move(9, 1)
    stdscr.addstr(line)
    stdscr.move(9, len(kbuf) + 1)
    stdscr.refresh()


def displayInputField(field):
    """Needs Doc String"""
    filler = "                 "
    if field == 0:
        filler = "                 "
        y = 1
    elif field == 1:
        filler = "     "
        y = 20
    elif field == 2:
        filler = "       "
        y = 27
    stdscr.move(9, y)
    if kbuf == "":
        stdscr.addstr(filler)
    else:
        line = kbuf + filler[: -len(kbuf)]
        stdscr.addstr(line.upper())
    stdscr.move(9, len(kbuf) + y)
    stdscr.refresh()


def processcommand(cmd):
    """Needs Doc String"""
    global quitprogram
    cmd = cmd[1:].upper()
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
            if cmd[1:] == "CW" or cmd[1:] == "PH" or cmd[1:] == "DI":
                setmode(cmd[1:])
            else:
                setStatusMsg("Must be CW, DI, PH")
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
    if cmd[:1] == "0":  # Print Rig Control Help
        # displayHelp(2)
        return
    if cmd[:1] == "K":  # Set your Call Sign
        setcallsign(cmd[1:])
        return
    if cmd[:1] == "C":  # Set your class
        setclass(cmd[1:])
        return
    if cmd[:1] == "S":  # Set your section
        setsection(cmd[1:])
        return
    if cmd[:1] == "I":  # Set rigctld host
        regex1 = re.compile("localhost")
        regex2 = re.compile(r"[0-9]*\.[0-9]*\.[0-9]*\.[0-9]*")
        if re.match(regex1, cmd[1:].lower()) or re.match(regex2, cmd[1:].lower()):
            setrigctrlhost(cmd[1:])
        else:
            setStatusMsg("Must be IP or localhost")
        return
    if cmd[:1] == "R":  # Set rigctld port
        regex = re.compile("[0-9]{1,5}")
        if (
            re.match(regex, cmd[1:].lower())
            and int(cmd[1:]) > 1023
            and int(cmd[1:]) < 65536
        ):
            setrigctrlport(cmd[1:])
        else:
            setStatusMsg("Must be 1024 <= Port <= 65535")
        return
    if cmd[:1] == "L":  # Generate Cabrillo Log
        cabrillo()
        return
    if cmd[:1] == "1":  # Claim Alt Power Bonus
        claimAltPower()
        return
    if cmd[:1] == "2":  # Claim Outdoor Bonus
        claimOutdoors()
        return
    if cmd[:1] == "3":  # Claim Not Home Bonus
        claimNotHome()
        return
    if cmd[:1] == "4":  # Claim Satellite Bonus
        claimSatellite()
        return
    curses.flash()
    curses.beep()


def proc_key(key):
    """Needs Doc String"""
    global inputFieldFocus, hiscall, hissection, hisclass, kbuf
    if key == 9 or key == SPACE:
        inputFieldFocus += 1
        if inputFieldFocus > 2:
            inputFieldFocus = 0
        if inputFieldFocus == 0:
            hissection = kbuf  # store any input to previous field
            stdscr.move(9, 1)  # move focus to call field
            kbuf = hiscall  # load current call into buffer
            stdscr.addstr(kbuf)
        if inputFieldFocus == 1:
            hiscall = kbuf  # store any input to previous field
            dupCheck(hiscall)
            x = threading.Thread(target=lazy_lookup, args=(hiscall,), daemon=True)
            x.start()
            stdscr.move(9, 20)  # move focus to class field
            kbuf = hisclass  # load current class into buffer
            stdscr.addstr(kbuf)
        if inputFieldFocus == 2:
            hisclass = kbuf  # store any input to previous field
            stdscr.move(9, 27)  # move focus to section field
            kbuf = hissection  # load current section into buffer
            stdscr.addstr(kbuf)
        return
    elif key == BACK_SPACE:
        if kbuf != "":
            kbuf = kbuf[0:-1]
            if inputFieldFocus == 0 and len(kbuf) < 3:
                displaySCP(super_check("^"))
            if inputFieldFocus == 0 and len(kbuf) > 2:
                displaySCP(super_check(kbuf))
            if inputFieldFocus == 2:
                section_check(kbuf)
        displayInputField(inputFieldFocus)
        return
    elif key == ENTERKEY:
        if inputFieldFocus == 0:
            hiscall = kbuf
        elif inputFieldFocus == 1:
            hisclass = kbuf
        elif inputFieldFocus == 2:
            hissection = kbuf
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
                int(preference.preference["power"]),
            )
            log_contact(contact)
            clearentry()
        else:
            setStatusMsg("Must be valid call sign")
        return
    elif key == ESCAPE:
        clearentry()
        return
    elif key == SPACE:
        return
    elif key == 258:  # key down
        logup()
    elif key == 259:  # key up
        logdown()
    elif key == 338:  # page down
        logpagedown()
    elif key == 339:  # page up
        logpageup()
    elif curses.ascii.isascii(key):
        if len(kbuf) < MAXFIELDLENGTH[inputFieldFocus]:
            kbuf = kbuf.upper() + chr(key).upper()
            if inputFieldFocus == 0 and len(kbuf) > 2:
                displaySCP(super_check(kbuf))
            if inputFieldFocus == 2 and len(kbuf) > 0:
                section_check(kbuf)
    displayInputField(inputFieldFocus)


def edit_key(key):
    """Needs Doc String"""
    global editFieldFocus, quitprogram
    if key == 9:
        editFieldFocus += 1
        if editFieldFocus > 7:
            editFieldFocus = 1
        qsoew.move(editFieldFocus, 10)  # move focus to call field
        qsoew.addstr(qso[editFieldFocus])
        return
    if key == BACK_SPACE:
        if qso[editFieldFocus] != "":
            qso[editFieldFocus] = qso[editFieldFocus][0:-1]
        displayEditField(editFieldFocus)
        return
    if key == ENTERKEY:
        change_contact(qso)
        qsoew.erase()
        stdscr.clear()
        rectangle(stdscr, 0, 0, 7, 55)
        contactslabel = "Recent Contacts"
        contactslabeloffset = (49 / 2) - len(contactslabel) / 2
        stdscr.addstr(0, int(contactslabeloffset), contactslabel)
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
        rectangle(stdscr, 0, 0, 7, 55)
        contactslabel = "Recent Contacts"
        contactslabeloffset = (49 / 2) - len(contactslabel) / 2
        stdscr.addstr(0, int(contactslabeloffset), contactslabel)
        logwindow()
        sections()
        stats()
        displayHelp()
        entry()
        stdscr.move(9, 1)
        quitprogram = True
        return
    if key == SPACE:
        return
    if key == 258:  # arrow down
        editFieldFocus += 1
        if editFieldFocus > 7:
            editFieldFocus = 1
        qsoew.move(editFieldFocus, 10)  # move focus to call field
        qsoew.addstr(qso[editFieldFocus])
        return
    if key == 259:  # arrow up
        editFieldFocus -= 1
        if editFieldFocus < 1:
            editFieldFocus = 7
        qsoew.move(editFieldFocus, 10)  # move focus to call field
        qsoew.addstr(qso[editFieldFocus])
        return
    if curses.ascii.isascii(key):
        # displayinfo("eff:"+str(editFieldFocus)+" mefl:"+str(MAXEDITFIELDLENGTH[editFieldFocus]))
        if len(qso[editFieldFocus]) < MAXEDITFIELDLENGTH[editFieldFocus]:
            qso[editFieldFocus] = qso[editFieldFocus].upper() + chr(key).upper()
    displayEditField(editFieldFocus)


def displayEditField(field):
    """Needs Doc String"""
    filler = "                 "
    if field == 1:
        filler = "                 "
    elif field == 2:
        filler = "     "
    elif field == 3:
        filler = "       "
    qsoew.move(field, 10)
    if qso[field] == "":
        qsoew.addstr(filler)
    else:
        line = qso[field] + filler[: -len(qso[field])]
        qsoew.addstr(line.upper())
    qsoew.move(field, len(qso[field]) + 10)
    qsoew.refresh()


def EditClickedQSO(line):
    """Needs Doc String"""
    global qsoew, qso, quitprogram
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
    qsoew.addstr(1, 1, "Call   : " + qso[1])
    qsoew.addstr(2, 1, "Class  : " + qso[2])
    qsoew.addstr(3, 1, "Section: " + qso[3])
    qsoew.addstr(4, 1, "At     : " + qso[4])
    qsoew.addstr(5, 1, "Band   : " + qso[5])
    qsoew.addstr(6, 1, "Mode   : " + qso[6])
    qsoew.addstr(7, 1, "Powers : " + qso[7])
    qsoew.addstr(8, 1, "[Enter] to save          [Esc] to exit")
    displayEditField(1)
    while 1:
        statusline()
        stdscr.refresh()
        qsoew.refresh()
        c = qsoew.getch()
        if c != -1:
            edit_key(c)
        else:
            time.sleep(0.1)
        if quitprogram:
            quitprogram = False
            break


def editQSO(q):
    """Needs Doc String"""
    if q is False or q == "":
        setStatusMsg("Must specify a contact number")
        return
    global qsoew, qso, quitprogram
    log = database.contact_by_id(q)
    if not log:
        return
    qso = ["", "", "", "", "", "", "", ""]
    qso[0], qso[1], qso[2], qso[3], qso[4], qso[5], qso[6], qso[7] = log[0]
    qsoew = curses.newwin(10, 40, 6, 10)
    qsoew.keypad(True)
    qsoew.nodelay(True)
    qsoew.box()
    qsoew.addstr(1, 1, "Call   : " + qso[1])
    qsoew.addstr(2, 1, "Class  : " + qso[2])
    qsoew.addstr(3, 1, "Section: " + qso[3])
    qsoew.addstr(4, 1, "At     : " + qso[4])
    qsoew.addstr(5, 1, "Band   : " + qso[5])
    qsoew.addstr(6, 1, "Mode   : " + qso[6])
    qsoew.addstr(7, 1, "Powers : " + str(qso[7]))
    qsoew.addstr(8, 1, "[Enter] to save          [Esc] to exit")
    displayEditField(1)
    while 1:
        statusline()
        stdscr.refresh()
        qsoew.refresh()
        c = qsoew.getch()
        if c != -1:
            edit_key(c)
        else:
            time.sleep(0.1)
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
        curses.init_pair(1, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.noecho()
    curses.cbreak()
    stdscr.keypad(True)
    stdscr.nodelay(True)
    curses.mousemask(curses.ALL_MOUSE_EVENTS)
    stdscr.attrset(curses.color_pair(0))
    stdscr.clear()
    contacts_label()
    sections()
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
            time.sleep(0.1)
        if quitprogram:
            break
        if datetime.datetime.now() > poll_time:
            poll_radio()
            poll_time = datetime.datetime.now() + datetime.timedelta(seconds=1)


if __name__ == "__main__":
    database = DataBase("wfd.db")
    preference = Preferences()
    readpreferences()
    look_up = None
    cat_control = None
    if preference.preference["useqrz"]:
        look_up = QRZlookup(
            preference.preference["qrzusername"], preference.preference["qrzpassword"]
        )
    if preference.preference["usehamdb"]:
        look_up = HamDBlookup()
    if preference.preference["usehamqth"]:
        look_up = HamQTH(
            preference.preference["hamqthusername"],
            preference.preference["hamqthpassword"],
        )
    if preference.preference["useflrig"]:
        cat_control = CAT(
            "flrig", preference.preference["CAT_ip"], preference.preference["CAT_port"]
        )
    if preference.preference["userigctld"]:
        cat_control = CAT(
            "rigctld",
            preference.preference["CAT_ip"],
            preference.preference["CAT_port"],
        )

    if preference.preference["cloudlog"]:
        __payload = "/validate/key=" + preference.preference["cloudlogapi"]
        try:
            result = requests.get(
                preference.preference["cloudlogurl"] + __payload, timeout=5
            )

            if result.status_code == 200 or result.status_code == 400:
                cloudlog_on = True
        except requests.exceptions.ConnectionError as exception:
            logging.warning("cloudlog authentication: %s", exception)

    read_sections()
    scp = read_scp()

    wrapper(main)
