#!/usr/bin/env python3
"""
COLOR_BLACK	Black
COLOR_BLUE	Blue
COLOR_CYAN	Cyan (light greenish blue)
COLOR_GREEN	Green
COLOR_MAGENTA	Magenta (purplish red)
COLOR_RED	Red
COLOR_WHITE	White
COLOR_YELLOW	Yellow
"""

import curses
import time
import sqlite3
import socket

from curses.textpad import rectangle
from curses import wrapper
from datetime import datetime
from sqlite3 import Error

stdscr = curses.initscr()
qsoew = 0
qso=[]
quit = False

BackSpace = 263
Escape = 27
QuestionMark = 63
EnterKey = 10
Space = 32

bands = ('160', '80', '40', '20', '15', '10', '6', '2')
modes = ('PH', 'CW', 'DI')

mycall = "YOURCALL"
myclass = "CLASS"
mysection = "SECT"
power = "0"
band = "40"
mode = "CW"
qrp = False
highpower = False
bandmodemult = 0
altpower = False
outdoors = False
notathome = False
satellite = False
cwcontacts = "0"
phonecontacts = "0"
digitalcontacts = "0"
contacts = ""
contactsOffset = 0
logNumber = 0
kbuf = ""
editbuf = ""
maxFieldLength = [17, 5, 7, 20, 4, 3, 4]
maxEditFieldLength = [10,17,5,4,20,4,3,4,10]
inputFieldFocus = 0
editFieldFocus = 1
hiscall = ""
hissection = ""
hisclass = ""

database = "WFD_Curses.db"
conn = ""
wrkdsections = []
scp = []
secPartial = {}
secName = {}
oldfreq = "0"
oldmode = ""
rigctrlhost = "127.0.0.1" #IP address for rigctld
rigctrlport = 4532
rigctrlsocket=socket.socket()
rigctrlsocket.settimeout(0.1)
rigonline = True
try:
	rigctrlsocket.connect((rigctrlhost, rigctrlport))
except:
	rigonline = False

def getband(freq):
	if freq.isnumeric():
		frequency = int(float(freq))
		if frequency > 1800000 and frequency < 2000000:
			return "160"
		if frequency > 3500000 and frequency < 4000000:
			return "80"
		if frequency > 7000000 and frequency < 7300000:
			return "40"
		if frequency > 10100000 and frequency < 10150000:
			return "30"
		if frequency > 14000000 and frequency < 14350000:
			return "20"
		if frequency > 18068000 and frequency < 18168000:
			return "17"
		if frequency > 21000000 and frequency < 21450000:
			return "15"
		if frequency > 24890000 and frequency < 24990000:
			return "12"
		if frequency > 28000000 and frequency < 29700000:
			return "10"
		if frequency > 50000000 and frequency < 54000000:
			return "6"
		if frequency > 144000000 and frequency < 148000000:
			return "2"
	else:
		return "0"

def getmode(rigmode):
	if rigmode == "CW":
		return "CW"
	if rigmode == "USB" or rigmode == "LSB" or rigmode == "FM" or rigmode == "AM":
		return "PH"
	return "DI" #All else digital
		
def pollRadio():
	global oldfreq, oldmode, rigctrlsocket, rigonline
	if rigonline:
		try:
			#rigctrlsocket.settimeout(0.5)
			rigctrlsocket.send(b'f\n')
			newfreq = rigctrlsocket.recv(1024).decode().strip()
			rigctrlsocket.send(b'm\n')
			newmode = rigctrlsocket.recv(1024).decode().strip().split()[0]
			if newfreq != oldfreq or newmode != oldmode:
				oldfreq = newfreq
				oldmode = newmode
				setband(str(getband(newfreq)))
				setmode(str(getmode(newmode)))
		except:
			rigonline = False

def checkRadio():
	global rigctrlsocket, rigonline
	rigctrlsocket.settimeout(0.1)
	rigonline = True
	try:
		rigctrlsocket.connect((rigctrlhost, rigctrlport))
	except:
		rigonline = False
		pass

def create_DB():
	""" create a database and table if it does not exist """
	global conn
	try:
		conn = sqlite3.connect(database)
		c = conn.cursor()
		sql_table = """ CREATE TABLE IF NOT EXISTS contacts (id INTEGER PRIMARY KEY, callsign text NOT NULL, class text NOT NULL, section text NOT NULL, date_time text NOT NULL, band text NOT NULL, mode text NOT NULL, power INTEGER NOT NULL); """
		c.execute(sql_table)
		sql_table = """ CREATE TABLE IF NOT EXISTS preferences (id INTEGER, mycallsign TEXT DEFAULT 'YOURCALL', myclass TEXT DEFAULT 'YOURCLASS', mysection TEXT DEFAULT 'YOURSECTION', power TEXT DEFAULT '0', altpower INTEGER DEFAULT 0, outdoors INTEGER DEFAULT 0, notathome INTEGER DEFAULT 0, satellite INTEGER DEFAULT 0); """
		c.execute(sql_table)
		conn.commit()
		conn.close()
	except Error as e:
		print(e)

def readpreferences():
	global mycall, myclass, mysection, power, altpower, outdoors, notathome, satellite
	try:
		conn = sqlite3.connect(database)
		c = conn.cursor()
		c.execute("select * from preferences where id = 1")
		pref = c.fetchall()
		if len(pref) > 0:
			for x in pref:
				_, mycall, myclass, mysection, power, altpower, outdoors, notathome, satellite = x
				altpower = bool(altpower)
				outdoors = bool(outdoors)
				notathome = bool(notathome)
				satellite = bool(satellite)
		else:
			sql = "INSERT INTO preferences(id, mycallsign, myclass, mysection, power, altpower, outdoors, notathome, satellite) VALUES(1,'" + mycall + "','" + myclass + "','" + mysection + "','" + power + "'," + str(
				int(altpower)) + "," + str(int(outdoors)) + "," + str(int(notathome)) + "," + str(int(satellite)) + ")"
			c.execute(sql)
			conn.commit()
		conn.close()
	except Error as e:
		print(e)

def writepreferences():
	try:
		conn = sqlite3.connect(database)
		sql = "UPDATE preferences SET mycallsign = '" + mycall + "', myclass = '" + myclass + "', mysection = '" + mysection + "', power = '" + power + "', altpower = " + str(
			int(altpower)) + ", outdoors = " + str(int(outdoors)) + ", notathome = " + str(
			int(notathome)) + ", satellite = " + str(int(satellite)) + " WHERE id = 1"
		cur = conn.cursor()
		cur.execute(sql)
		conn.commit()
		conn.close()
	except Error as e:
		pass

def log_contact(logme):
	try:
		conn = sqlite3.connect(database)
		sql = "INSERT INTO contacts(callsign, class, section, date_time, band, mode, power) VALUES(?,?,?,datetime('now'),?,?,?)"
		cur = conn.cursor()
		cur.execute(sql, logme)
		conn.commit()
		conn.close()
	except Error as e:
		displayinfo(e)
	workedSections()
	sections()
	stats()
	logwindow()

def delete_contact(contact):
	try:
		conn = sqlite3.connect(database)
		sql = "delete from contacts where id=" + str(int(contact))
		cur = conn.cursor()
		cur.execute(sql)
		conn.commit()
		conn.close()
	except Error as e:
		displayinfo(e)
	workedSections()
	sections()
	stats()
	logwindow()

def change_contact(qso):
	try:
		conn = sqlite3.connect(database)
		sql = "update contacts set callsign = '"+str(qso[1])+"', class = '"+str(qso[2])+"', section = '"+str(qso[3])+"', date_time = '"+str(qso[4])+"', band = '"+str(qso[5])+"', mode = '"+str(qso[6])+"', power = '"+str(qso[7])+"'  where id="+ str(qso[0])
		cur = conn.cursor()
		cur.execute(sql)
		conn.commit()
		conn.close()
	except Error as e:
		displayinfo(e)
		pass

def readSections():
	try:
		fd = open("arrl_sect.dat", "r")  # read section data
		while 1:
			ln = fd.readline().strip()  # read a line and put in db
			if not ln: break
			if ln[0] == '#': continue
			try:
				sec, st, canum, abbrev, name = str.split(ln, None, 4)
				secName[abbrev] = abbrev + ' ' + name + ' ' + canum
				for i in range(len(abbrev) - 1):
					p = abbrev[:-i - 1]
					secPartial[p] = 1
			except ValueError as e:
				print("rd arrl sec dat err, itm skpd: ", e)
		fd.close()
	except IOError as e:
		print("read error during readSections", e)

def sectionCheck(sec):
	if sec == "": sec = "^"
	seccheckwindow = curses.newpad(20, 33)
	rectangle(stdscr, 11, 0, 21, 34)
	x = list(secName.keys())
	xx = list(filter(lambda y: y.startswith(sec), x))
	count = 0
	for xxx in xx:
		seccheckwindow.addstr(count, 1, secName[xxx])
		count += 1
	stdscr.refresh()
	seccheckwindow.refresh(0, 0, 12, 1, 20, 33)

readSections()

def readSCP():
	global scp
	f = open("MASTER.SCP")
	scp = f.readlines()
	f.close()
	scp = list(map(lambda x: x.strip(), scp))

readSCP()

def superCheck(acall):
	return list(filter(lambda x: x.startswith(acall), scp))

def contacts():
	global stdscr
	rectangle(stdscr, 0, 0, 7, 55)
	contactslabel = "Recent Contacts"
	contactslabeloffset = (49 / 2) - len(contactslabel) / 2
	stdscr.addstr(0, int(contactslabeloffset), contactslabel)

def stats():
	global bandmodemult
	y, x = stdscr.getyx()
	conn = sqlite3.connect(database)
	# conn.row_factory = sqlite3.Row
	c = conn.cursor()
	c.execute("select count(*) from contacts where mode = 'CW'")
	cwcontacts = str(c.fetchone()[0])
	c.execute("select count(*) from contacts where mode = 'PH'")
	phonecontacts = str(c.fetchone()[0])
	c.execute("select count(*) from contacts where mode = 'DI'")
	digitalcontacts = str(c.fetchone()[0])
	c.execute("select distinct band, mode from contacts")
	bandmodemult = len(c.fetchall())
	c.execute("SELECT count(*) FROM contacts where datetime(date_time) >=datetime('now', '-15 Minutes')")
	last15 = str(c.fetchone()[0])
	c.execute("SELECT count(*) FROM contacts where datetime(date_time) >=datetime('now', '-1 Hours')")
	lasthour = str(c.fetchone()[0])
	conn.close()
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
	stdscr.addstr(1, 79 - len(cwcontacts), cwcontacts)
	stdscr.addstr(2, 79 - len(phonecontacts), phonecontacts)
	stdscr.addstr(3, 79 - len(digitalcontacts), digitalcontacts)
	stdscr.addstr(4, 79 - len(str(score())), str(score()))
	stdscr.addstr(5, 79 - len(lasthour), lasthour)
	stdscr.addstr(6, 79 - len(last15), last15)
	stdscr.move(y, x)

def score():
	global bandmodemult
	qrpcheck()
	conn = sqlite3.connect(database)
	c = conn.cursor()
	c.execute("select count(*) as cw from contacts where mode = 'CW'")
	cw = str(c.fetchone()[0])
	c.execute("select count(*) as ph from contacts where mode = 'PH'")
	ph = str(c.fetchone()[0])
	c.execute("select count(*) as di from contacts where mode = 'DI'")
	di = str(c.fetchone()[0])
	c.execute("select distinct band, mode from contacts")
	bandmodemult = len(c.fetchall())
	conn.close()
	score = (int(cw) * 2) + int(ph) + (int(di) * 2)
	if qrp:
		score = score * 4
	elif not (highpower):
		score = score * 2
	score = score * bandmodemult
	score = score + (1500 * altpower) + (1500 * outdoors) + (1500 * notathome) + (1500 * satellite)
	return score

def qrpcheck():
	global qrp, highpower
	conn = sqlite3.connect(database)
	c = conn.cursor()
	c.execute("select count(*) as qrpc from contacts where mode = 'CW' and power > 5")
	log = c.fetchall()
	qrpc = list(log[0])[0]
	c.execute("select count(*) as qrpp from contacts where mode = 'PH' and power > 10")
	log = c.fetchall()
	qrpp = list(log[0])[0]
	c.execute("select count(*) as qrpd from contacts where mode = 'DI' and power > 10")
	log = c.fetchall()
	qrpd = list(log[0])[0]
	c.execute("select count(*) as highpower from contacts where power > 100")
	log = c.fetchall()
	highpower = bool(list(log[0])[0])
	conn.close()
	qrp = not (qrpc + qrpp + qrpd)

def cabrillo():

	bonuses = 0
	conn = sqlite3.connect(database)
	c = conn.cursor()
	c.execute("select * from contacts order by date_time ASC")
	log = c.fetchall()
	conn.close()
	catpower = ""
	if qrp:
		catpower = "QRP"
	elif highpower:
		catpower = "HIGH"
	else:
		catpower = "LOW"
	print("START-OF-LOG: 3.0", end='\r\n', file=open("WFDLOG.txt", "w"))
	print("CREATED-BY: K6GTE Winter Field Day Logger", end='\r\n', file=open("WFDLOG.txt", "a"))
	print("CONTEST: WFD", end='\r\n', file=open("WFDLOG.txt", "a"))
	print("CALLSIGN:", mycall, end='\r\n', file=open("WFDLOG.txt", "a"))
	print("LOCATION:", end='\r\n', file=open("WFDLOG.txt", "a"))
	print("ARRL-SECTION:", mysection, end='\r\n', file=open("WFDLOG.txt", "a"))
	print("CATEGORY:", myclass, end='\r\n', file=open("WFDLOG.txt", "a"))
	print("CATEGORY-POWER: " + catpower, end='\r\n', file=open("WFDLOG.txt", "a"))
	if altpower:
		print("SOAPBOX: 1,500 points for not using commercial power", end='\r\n', file=open("WFDLOG.txt", "a"))
		bonuses = bonuses + 1500
	if outdoors:
		print("SOAPBOX: 1,500 points for setting up outdoors", end='\r\n', file=open("WFDLOG.txt", "a"))
		bonuses = bonuses + 1500
	if notathome:
		print("SOAPBOX: 1,500 points for setting up away from home", end='\r\n', file=open("WFDLOG.txt", "a"))
		bonuses = bonuses + 1500
	if satellite:
		print("SOAPBOX: 1,500 points for working satellite", end='\r\n', file=open("WFDLOG.txt", "a"))
		bonuses = bonuses + 1500
	print("SOAPBOX: BONUS Total " + str(bonuses), end='\r\n', file=open("WFDLOG.txt", "a"))

	print("CLAIMED-SCORE: " + str(score()), end='\r\n', file=open("WFDLOG.txt", "a"))
	print("OPERATORS:", mycall, end='\r\n', file=open("WFDLOG.txt", "a"))
	print("NAME: ", end='\r\n', file=open("WFDLOG.txt", "a"))
	print("ADDRESS: ", end='\r\n', file=open("WFDLOG.txt", "a"))
	print("ADDRESS-CITY: ", end='\r\n', file=open("WFDLOG.txt", "a"))
	print("ADDRESS-STATE: ", end='\r\n', file=open("WFDLOG.txt", "a"))
	print("ADDRESS-POSTALCODE: ", end='\r\n', file=open("WFDLOG.txt", "a"))
	print("ADDRESS-COUNTRY: ", end='\r\n', file=open("WFDLOG.txt", "a"))
	print("EMAIL: ", end='\r\n', file=open("WFDLOG.txt", "a"))
	counter = 0
	for x in log:
		logid, hiscall, hisclass, hissection, datetime, band, mode, power = x
		loggeddate = datetime[:10]
		loggedtime = datetime[11:13] + datetime[14:16]
		# print(value1, ..., sep=' ', end='\r\n', file=sys.stdout, flush=False)
		print("QSO:", band + "M", mode, loggeddate, loggedtime, mycall, myclass, mysection, hiscall, hisclass,
			  hissection, sep=' ', end='\r\n', file=open("WFDLOG.txt", "a"))
	print("END-OF-LOG:", end='\r\n', file=open("WFDLOG.txt", "a"))

	oy, ox = stdscr.getyx()
	window = curses.newpad(10, 33)
	rectangle(stdscr, 11, 0, 21, 34)
	window.addstr(0, 0, "Log written to: WFDLOG.txt")
	stdscr.refresh()
	window.refresh(0, 0, 12, 1, 20, 33)
	stdscr.move(oy, ox)
	writepreferences()
	statusline()
	stats()

def logwindow():
	global contacts, contactsOffset, logNumber
	contactsOffset = 0  # clears scroll position
	callfiller = "          "
	classfiller = "   "
	sectfiller = "   "
	bandfiller = "   "
	modefiller = "  "
	zerofiller = "000"
	contacts = curses.newpad(1000, 80)
	conn = sqlite3.connect(database)
	c = conn.cursor()
	c.execute("select * from contacts order by date_time desc")
	log = c.fetchall()
	conn.close()
	logNumber = 0
	for x in log:
		logid, hiscall, hisclass, hissection, datetime, band, mode, power = x
		logid = zerofiller[:-len(str(logid))] + str(logid)
		hiscall = hiscall + callfiller[:-len(hiscall)]
		hisclass = hisclass + classfiller[:-len(hisclass)]
		hissection = hissection + sectfiller[:-len(hissection)]
		band = band + sectfiller[:-len(band)]
		mode = mode + modefiller[:-len(mode)]
		logline = logid + " " + hiscall + " " + hisclass + " " + hissection + " " + datetime + " " + band + " " + mode + " " + str(
			power)
		contacts.addstr(logNumber, 0, logline)
		logNumber += 1
	stdscr.refresh()
	contacts.refresh(0, 0, 1, 1, 6, 54)

def logup():
	global contacts, contactsOffset, logNumber
	contactsOffset += 1
	if contactsOffset > (logNumber - 6): contactsOffset = (logNumber - 6)
	contacts.refresh(contactsOffset, 0, 1, 1, 6, 54)

def logpagedown():
	global contacts, contactsOffset, logNumber
	contactsOffset += 10
	if contactsOffset > (logNumber - 6): contactsOffset = (logNumber - 6)
	contacts.refresh(contactsOffset, 0, 1, 1, 6, 54)

def logpageup():
	global contacts, contactsOffset
	contactsOffset -= 10
	if contactsOffset < 0: contactsOffset = 0
	contacts.refresh(contactsOffset, 0, 1, 1, 6, 54)

def logdown():
	global contacts, contactsOffset
	contactsOffset -= 1
	if contactsOffset < 0: contactsOffset = 0
	contacts.refresh(contactsOffset, 0, 1, 1, 6, 54)

def dupCheck(acall):
	global hisclass, hissection
	oy, ox = stdscr.getyx()
	scpwindow = curses.newpad(1000, 33)
	rectangle(stdscr, 11, 0, 21, 34)

	conn = sqlite3.connect(database)
	c = conn.cursor()
	c.execute(
		"select callsign, class, section, band, mode from contacts where callsign like '" + acall + "' order by band")
	log = c.fetchall()
	conn.close()
	counter = 0
	for x in log:
		decorate = ""
		hiscall, hisclass, hissection, hisband, hismode = x
		if hisband == band and hismode == mode:
			decorate = curses.A_BOLD
			curses.flash()
			curses.beep()
		else:
			decorate = curses.A_NORMAL
		scpwindow.addstr(counter, 0, hiscall + ": " + hisband + " " + hismode, decorate)
		counter = counter + 1
	stdscr.refresh()
	scpwindow.refresh(0, 0, 12, 1, 20, 33)
	stdscr.move(oy, ox)

def displaySCP(matches):
	scpwindow = curses.newpad(1000, 33)
	rectangle(stdscr, 11, 0, 21, 34)
	for x in matches:
		wy, wx = scpwindow.getyx()
		if (33 - wx) < len(str(x)): scpwindow.move(wy + 1, 0)
		scpwindow.addstr(str(x) + " ")
	stdscr.refresh()
	scpwindow.refresh(0, 0, 12, 1, 20, 33)

def workedSections():
	global wrkdsections
	conn = sqlite3.connect(database)
	c = conn.cursor()
	c.execute("select distinct section from contacts")
	all_rows = c.fetchall()
	wrkdsections = str(all_rows)
	wrkdsections = wrkdsections.replace("('", "").replace("',), ", ",").replace("',)]", "").replace('[', '').split(',')

def workedSection(section):
	if section in wrkdsections:
		return curses.A_BOLD
	else:
		return curses.A_NORMAL

def sectionsCol1():
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
	stdscr.addstr(14, 50, "TY", workedSection("TY"))
	stdscr.addstr(15, 45, "NC", workedSection("NC"))
	stdscr.addstr(15, 50, "VA", workedSection("VA"))
	stdscr.addstr(16, 45, "NFL", workedSection("NFL"))
	stdscr.addstr(16, 50, "VI", workedSection("VI"))
	stdscr.addstr(17, 45, "PR", workedSection("PR"))
	stdscr.addstr(17, 49, "WCF", workedSection("WCF"))

def sectionsCol3():
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
	workedSections()
	sectionsCol1()
	sectionsCol2()
	sectionsCol3()
	sectionsCol4()
	sectionsCol5()
	stdscr.refresh()

def entry():
	rectangle(stdscr, 8, 0, 10, 18)
	stdscr.addstr(8, 1, "CALL")
	rectangle(stdscr, 8, 19, 10, 25)
	stdscr.addstr(8, 20, "class")
	rectangle(stdscr, 8, 26, 10, 34)
	stdscr.addstr(8, 27, "Section")

def clearentry():
	global inputFieldFocus, hiscall, hissection, hisclass, kbuf
	hiscall = ""
	hissection = ""
	hisclass = ""
	kbuf = ""
	inputFieldFocus = 0
	displayInputField(2)
	displayInputField(1)
	displayInputField(0)

def highlightBonus(bonus):
	if bonus:
		return curses.A_BOLD
	else:
		return curses.A_DIM

def statusline():
	y, x = stdscr.getyx()
	now = datetime.now().isoformat(' ')[5:19].replace('-', '/')
	utcnow = datetime.utcnow().isoformat(' ')[5:19].replace('-', '/')
	try:
		stdscr.addstr(22, 59, "Local: " + now)
		stdscr.addstr(23, 61, "UTC: " + utcnow)
	except curses.error as e:
		pass

	stdscr.addstr(23, 1, "Band:        Mode:")
	stdscr.addstr(23, 7, "  " + band + "  ", curses.A_REVERSE)
	stdscr.addstr(23, 20, "  " + mode + "  ", curses.A_REVERSE)
	stdscr.addstr(23, 27, "                            ")
	stdscr.addstr(23, 27, " " + mycall + "|" + myclass + "|" + mysection + "|" + power + "w ", curses.A_REVERSE)
	stdscr.addstr(22, 1, "Bonuses:")
	stdscr.addstr(22, 10, "Alt Power", highlightBonus(altpower))
	stdscr.addch(curses.ACS_VLINE)
	stdscr.addstr("Outdoors", highlightBonus(outdoors))
	stdscr.addch(curses.ACS_VLINE)
	stdscr.addstr("Not At Home", highlightBonus(notathome))
	stdscr.addch(curses.ACS_VLINE)
	stdscr.addstr("Satellite", highlightBonus(satellite))
	stdscr.addstr(23,50,"Rig", highlightBonus(rigonline))

	stdscr.move(y, x)

def setpower(p):
	global power
	power = p
	writepreferences()
	statusline()

def setband(b):
	global band
	band = b
	statusline()

def setmode(m):
	global mode
	mode = m
	statusline()

def setcallsign(c):
	global mycall
	mycall = str(c)
	writepreferences()
	statusline()

def setclass(c):
	global myclass
	myclass = str(c)
	writepreferences()
	statusline()

def setsection(s):
	global mysection
	mysection = str(s)
	writepreferences()
	statusline()

def claimAltPower():
	global altpower
	if altpower:
		altpower = False
	else:
		altpower = True
	oy, ox = stdscr.getyx()
	window = curses.newpad(10, 33)
	rectangle(stdscr, 11, 0, 21, 34)
	window.addstr(0, 0, "Alt Power set to: " + str(altpower))
	stdscr.refresh()
	window.refresh(0, 0, 12, 1, 20, 33)
	stdscr.move(oy, ox)
	writepreferences()
	statusline()
	stats()

def claimOutdoors():
	global outdoors
	if outdoors:
		outdoors = False
	else:
		outdoors = True
	oy, ox = stdscr.getyx()
	window = curses.newpad(10, 33)
	rectangle(stdscr, 11, 0, 21, 34)
	window.addstr(0, 0, "Outdoor bonus set to: " + str(outdoors))
	stdscr.refresh()
	window.refresh(0, 0, 12, 1, 20, 33)
	stdscr.move(oy, ox)
	writepreferences()
	statusline()
	stats()

def claimNotHome():
	global notathome
	if notathome:
		notathome = False
	else:
		notathome = True
	oy, ox = stdscr.getyx()
	window = curses.newpad(10, 33)
	rectangle(stdscr, 11, 0, 21, 34)
	window.addstr(0, 0, "Away bonus set to: " + str(notathome))
	stdscr.refresh()
	window.refresh(0, 0, 12, 1, 20, 33)
	stdscr.move(oy, ox)
	writepreferences()
	statusline()
	stats()

def claimSatellite():
	global satellite
	if satellite:
		satellite = False
	else:
		satellite = True
	oy, ox = stdscr.getyx()
	window = curses.newpad(10, 33)
	rectangle(stdscr, 11, 0, 21, 34)
	window.addstr(0, 0, "Satellite bonus set to: " + str(satellite))
	stdscr.refresh()
	window.refresh(0, 0, 12, 1, 20, 33)
	stdscr.move(oy, ox)
	writepreferences()
	statusline()
	stats()

def displayHelp():
	rectangle(stdscr, 11, 0, 21, 34)
	wy, wx = stdscr.getyx()
	help = [".H this message  |.2 Outdoors",
			".Q quit program  |.3 AwayFromHome",
			".Kyourcall       |.4 Satellite",
			".Cyourclass      |.E### edit QSO",
			".Syoursection    |.D### del QSO",
			".B## change bands|.L Generate Log",
			".M[CW,PH,DI] mode|[esc] abort inp",
			".P## change power|",
			".1 Alt Power     |"]
	stdscr.move(12, 1)
	count = 0
	for x in help:
		stdscr.addstr(12 + count, 1, x)
		count = count + 1
	stdscr.move(wy, wx)
	stdscr.refresh()

def displayinfo(info):
	y, x = stdscr.getyx()
	stdscr.move(20, 1)
	stdscr.addstr(info)
	stdscr.move(y, x)
	stdscr.refresh()

def displayLine():
	filler = "                        "
	line = kbuf + filler[:-len(kbuf)]
	stdscr.move(9, 1)
	stdscr.addstr(line)
	stdscr.move(9, len(kbuf) + 1)
	stdscr.refresh()

def displayInputField(field):
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
		line = kbuf + filler[:-len(kbuf)]
		stdscr.addstr(line.upper())
	stdscr.move(9, len(kbuf) + y)
	stdscr.refresh()

def processcommand(cmd):
	global band, mode, power, quit
	cmd = cmd[1:].upper()
	if cmd == "Q":  # Quit
		quit = True
		return
	if cmd[:1] == "B":  # Change Band
		setband(cmd[1:])
		return
	if cmd[:1] == "M":  # Change Mode
		if cmd[1:] == "CW" or cmd[1:] == "PH" or cmd[1:] == "DI":
			setmode(cmd[1:])
		else:
			curses.flash()
			curses.beep()
		return
	if cmd[:1] == "P":  # Change Power
		setpower(cmd[1:])
		return
	if cmd[:1] == "D":  # Delete Contact
		delete_contact(cmd[1:])
		return
	if cmd[:1] == "E": # Edit QSO
		editQSO(cmd[1:])
		return
	if cmd[:1] == "H":  # Print Help
		displayHelp()
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
	global inputFieldFocus, hiscall, hissection, hisclass, kbuf
	if key == 9:
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
			stdscr.move(9, 20)  # move focus to class field
			kbuf = hisclass  # load current class into buffer
			stdscr.addstr(kbuf)
		if inputFieldFocus == 2:
			hisclass = kbuf  # store any input to previous field
			stdscr.move(9, 27)  # move focus to section field
			kbuf = hissection  # load current section into buffer
			stdscr.addstr(kbuf)
		return
	elif key == BackSpace:
		if kbuf != "":
			kbuf = kbuf[0:-1]
			if inputFieldFocus == 0 and len(kbuf) < 3: displaySCP(superCheck("^"))
			if inputFieldFocus == 0 and len(kbuf) > 2: displaySCP(superCheck(kbuf))
			if inputFieldFocus == 2: sectionCheck(kbuf)
		displayInputField(inputFieldFocus)
		return
	elif key == EnterKey:
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
		contact = (hiscall, hisclass, hissection, band, mode, int(power))
		log_contact(contact)
		clearentry()
		return
	elif key == Escape:
		clearentry()
		return
	elif key == Space:
		return
	elif key == 258:  # key down
		logup()
		pass
	elif key == 259:  # key up
		logdown()
		pass
	elif key == 338: #page down
		logpagedown()
		pass
	elif key == 339: #page up
		logpageup()
		pass
	elif curses.ascii.isascii(key):
		if len(kbuf) < maxFieldLength[inputFieldFocus]:
			kbuf = kbuf.upper() + chr(key).upper()
			if inputFieldFocus == 0 and len(kbuf) > 2: displaySCP(superCheck(kbuf))
			if inputFieldFocus == 2 and len(kbuf) > 0: sectionCheck(kbuf)
	displayInputField(inputFieldFocus)

def edit_key(key):
	global editFieldFocus, qso, quit
	if key == 9:
		editFieldFocus += 1
		if editFieldFocus > 7:
			editFieldFocus = 1
		qsoew.move(editFieldFocus, 10)  # move focus to call field
		qsoew.addstr(qso[editFieldFocus])
		return
	elif key == BackSpace:
		if qso[editFieldFocus] != "":
			qso[editFieldFocus] = qso[editFieldFocus][0:-1]
		displayEditField(editFieldFocus)
		return
	elif key == EnterKey:
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
		quit = True
		return
	elif key == Escape:
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
		quit = True
		return
	elif key == Space:
		return
	elif key == 258:  # arrow down
		editFieldFocus += 1
		if editFieldFocus > 7:
			editFieldFocus = 1
		qsoew.move(editFieldFocus, 10)  # move focus to call field
		qsoew.addstr(qso[editFieldFocus])
		return
	elif key == 259:  # arrow up
		editFieldFocus -= 1
		if editFieldFocus < 1:
			editFieldFocus = 7
		qsoew.move(editFieldFocus, 10)  # move focus to call field
		qsoew.addstr(qso[editFieldFocus])
		return
	elif curses.ascii.isascii(key):
		#displayinfo("eff:"+str(editFieldFocus)+" mefl:"+str(maxEditFieldLength[editFieldFocus]))
		if len(qso[editFieldFocus]) < maxEditFieldLength[editFieldFocus]:
			qso[editFieldFocus] = qso[editFieldFocus].upper() + chr(key).upper()
	displayEditField(editFieldFocus)

def displayEditField(field):
	global qso
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
		line = qso[field] + filler[:-len(qso[field])]
		qsoew.addstr(line.upper())
	qsoew.move(field, len(qso[field]) + 10)
	qsoew.refresh()

def EditClickedQSO(line):
	global qsoew, qso, quit
	record = contacts.instr((line - 1) + contactsOffset, 0, 55).decode("utf-8").strip().split()
	if record == []: return
	qso = [record[0], record[1], record[2], record[3], record[4]+" "+record[5], record[6], record[7], record[8]]
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
		if quit:
			quit = False
			break

def editQSO(q):
	global qsoew, qso, quit
	conn = sqlite3.connect(database)
	c = conn.cursor()
	c.execute("select * from contacts where id=" + q)
	log = c.fetchall()
	conn.close()
	if not log: return
	qso=['','','','','','','','']
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
		if quit:
			quit = False
			break

def main(s):
	global stdscr, conn
	conn = create_DB()
	curses.start_color()
	curses.use_default_colors()
	curses.noecho()
	curses.cbreak()
	stdscr.keypad(True)
	stdscr.nodelay(True)
	curses.mousemask(curses.ALL_MOUSE_EVENTS)
	stdscr.clear()
	contacts()
	sections()
	entry()
	logwindow()
	readpreferences()
	stats()
	displayHelp()
	stdscr.refresh()
	stdscr.move(9, 1)
	while 1:
		statusline()
		stdscr.refresh()
		ch = stdscr.getch()
		if ch == curses.KEY_MOUSE:
			buttons=""
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
			pass
		elif ch != -1:
			proc_key(ch)
		else:
			time.sleep(0.1)
		if quit: break
		if rigonline == False:
			checkRadio()
		else:
			pollRadio()

wrapper(main)
