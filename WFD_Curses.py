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

# select distinct band, mode from contacts order by band; to get band modem multiplier

import curses, sys, time, re, string, sqlite3
from curses.textpad import Textbox, rectangle
from curses import wrapper
from datetime import datetime
from sqlite3 import Error

stdscr = curses.initscr()
quit = False

BackSpace = 263
Escape = 27
QuestionMark = 63
EnterKey = 10
Space= 32

bands = ('160','80','40','20','15','10','6')
modes = ('PH','CW','DI')

mycall = "YOURCALL"
myclass = "CLASS"
mysection = "SECT"
power = "0"
band = "40"
mode = "CW"
qrp = False
bandmodemult = 0
cwcontacts = "0"
phonecontacts = "0"
digitalcontacts = "0"

LogNumber=0
kbuf = ""
maxFieldLength = [17,5,7]

inputFieldFocus = 0
hiscall = ""
hissection = ""
hisclass = ""

database = "WFD_Curses.db"
conn = ""
wrkdsections = []
scp = []
secPartial = {}
secName = {}

#stdscr = curses.initscr()

def create_DB():
	""" create a database and table if it does not exist """
	global conn
	try:
		conn = sqlite3.connect(database)
		c = conn.cursor()
		sql_table = """ CREATE TABLE IF NOT EXISTS contacts (id INTEGER PRIMARY KEY, callsign text NOT NULL, class text NOT NULL, section text NOT NULL, date_time text NOT NULL, band text NOT NULL, mode text NOT NULL, power INTEGER NOT NULL); """
		c.execute(sql_table)
		sql_table = """ CREATE TABLE IF NOT EXISTS preferences (id INTEGER, mycallsign TEXT DEFAULT 'YOURCALL', myclass TEXT DEFAULT 'YOURCLASS', mysection TEXT DEFAULT 'YOURSECTION', power TEXT DEFAULT '0'); """
		c.execute(sql_table)
		conn.commit()
		conn.close()
	except Error as e:
		print(e)

def readpreferences():
	global mycall, myclass, mysection, power
	try:
		conn = sqlite3.connect(database)
		c = conn.cursor()
		c.execute("select * from preferences where id = 1")
		pref = c.fetchall()
		if len(pref) > 0 :
			for x in pref:
				_, mycall, myclass, mysection, power = x
		else:
			sql = "INSERT INTO preferences(id, mycallsign, myclass, mysection, power) VALUES(1,'"+mycall+"','"+myclass+"','"+mysection+"','"+power+"')"
			c.execute(sql)
			conn.commit()
		conn.close()
	except Error as e:
		print(e)

def writepreferences():
	try:
		conn = sqlite3.connect(database)
		sql = "UPDATE preferences SET mycallsign = '"+mycall+"', myclass = '"+myclass+"', mysection = '"+mysection+"', power = '"+power+"' WHERE id = 1"
		cur = conn.cursor()
		cur.execute(sql)
		conn.commit()
		conn.close()
	except Error as e:
		pass
		# print(e)

def log_contact(logme):
	try:
		conn = sqlite3.connect(database)
		sql = "INSERT INTO contacts(callsign, class, section, date_time, band, mode, power) VALUES(?,?,?,datetime('now'),?,?,?)"
		#displayinfo(sql)
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
		sql = "delete from contacts where id="+str(int(contact))
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

def readSections():
	try:
		fd = open("arrl_sect.dat","r")  # read section data
		while 1:
			ln = fd.readline().strip()          # read a line and put in db
			if not ln: break
			if ln[0] == '#': continue
			try:
				sec,st,canum,abbrev,name = str.split(ln,None,4)
				secName[abbrev] = abbrev + ' ' + name + ' ' + canum
				for i in range(len(abbrev)-1):
					p = abbrev[:-i-1]
					secPartial[p] = 1
			except ValueError as e:
				print("rd arrl sec dat err, itm skpd: ",e)
		fd.close()
	except IOError as e:
		print("read error during readSections", e)

readSections()

def readSCP():
	global scp
	f = open("MASTER.SCP")
	scp = f.readlines()
	f.close()
	scp = list(map(lambda x:x.strip(),scp))

readSCP()

def superCheck(acall):
	return list(filter(lambda x:x.startswith(acall),scp))
	#return list(filter(lambda x:acall in x,scp))

def contacts():
	rectangle(stdscr, 0,0, 7, 55)
	contactslabel = "Recent Contacts"
	contactslabeloffset = (49/2) - len(contactslabel) / 2
	stdscr.addstr(0,int(contactslabeloffset) ,contactslabel)

def stats():
	global bandmodemult
	y, x = stdscr.getyx()
	conn = sqlite3.connect(database)
	#conn.row_factory = sqlite3.Row
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
	qrpcheck()
	score = (int(cwcontacts) * 2) + int(phonecontacts) + (int(digitalcontacts) * 2)
	if qrp: score = score * 4
	score = score * bandmodemult
	rectangle(stdscr, 0,57, 7, 79)
	statslabel = "Score Stats"
	statslabeloffset = (25/2) - len(statslabel) / 2
	stdscr.addstr(0,57+int(statslabeloffset) ,statslabel)
	stdscr.addstr(1, 58, "Total CW:")
	stdscr.addstr(2, 58, "Total PHONE:")
	stdscr.addstr(3, 58, "Total DIGITAL:")
	stdscr.addstr(4, 58, "QSO POINTS:          ")
	stdscr.addstr(5, 58, "QSO PER HOUR:")
	stdscr.addstr(6, 58, "QPH Last 15min:")
	stdscr.addstr(1,79-len(cwcontacts),cwcontacts)
	stdscr.addstr(2,79-len(phonecontacts),phonecontacts)
	stdscr.addstr(3,79-len(digitalcontacts),digitalcontacts)
	stdscr.addstr(4,79-len(str(score)),str(score))
	stdscr.addstr(5,79-len(lasthour),lasthour)
	stdscr.addstr(6,79-len(last15),last15)
	stdscr.move(y,x)

def score():
	qrpcheck()
	conn = sqlite3.connect(database)
	c = conn.cursor()
	c.execute("select count(*) as cw from contacts where mode = 'CW'")
	cw = str(c.fetchone()[0])
	c.execute("select count(*) as ph from contacts where mode = 'PH'")
	ph = str(c.fetchone()[0])
	c.execute("select count(*) as di from contacts where mode = 'DI'")
	di = str(c.fetchone()[0])
	conn.close()
	score = (int(cw)*2)+int(ph)+(int(di)*2)
	if qrp: score = score * 4
	score = score * bandmodemult
	return score

def qrpcheck():
    global qrp
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
    conn.close()
    qrp=not(qrpc+qrpp+qrpd)

def cabrillo():
    conn = sqlite3.connect(database)
    c = conn.cursor()
    c.execute("select * from contacts order by date_time ASC")
    log = c.fetchall()
    conn.close()
    print("START-OF-LOG: 3.0", end='\n',file=open("WFDLOG.txt", "w"))
    print("CREATED-BY: K6GTE Winter Field Day Logger", end='\n',file=open("WFDLOG.txt", "a"))
    print("CONTEST: WFD", end='\n',file=open("WFDLOG.txt", "a"))
    print("LOCATION:",mysection, end='\n',file=open("WFDLOG.txt", "a"))
    print("CALLSIGN:",mycall, end='\n',file=open("WFDLOG.txt", "a"))
    print("CATEGORY:",myclass, end='\n',file=open("WFDLOG.txt", "a"))
    print("CATEGORY-ASSISTED: NON-ASSISTED", end='\n',file=open("WFDLOG.txt", "a"))
    print("CATEGORY-BAND: ALL", end='\n',file=open("WFDLOG.txt", "a"))
    print("CATEGORY-MODE: MIXED", end='\n',file=open("WFDLOG.txt", "a"))
    print("CATEGORY-OPERATOR: SINGLE-OP", end='\n',file=open("WFDLOG.txt", "a"))
    print("CATEGORY-POWER: QRP", end='\n',file=open("WFDLOG.txt", "a"))
    print("CATEGORY-STATION: PORTABLE", end='\n',file=open("WFDLOG.txt", "a"))
    print("CATEGORY-TRANSMITTER: ONE", end='\n',file=open("WFDLOG.txt", "a"))
    print("SOAPBOX:", end='\n',file=open("WFDLOG.txt", "a"))
    print("CLAIMED-SCORE: "+str(score()), end='\n',file=open("WFDLOG.txt", "a"))
    print("OPERATORS:",mycall, end='\n',file=open("WFDLOG.txt", "a"))
    print("CLUB: none", end='\n',file=open("WFDLOG.txt", "a"))
    print("NAME: ", end='\n',file=open("WFDLOG.txt", "a"))
    print("ADDRESS: ", end='\n',file=open("WFDLOG.txt", "a"))
    print("EMAIL: ", end='\n',file=open("WFDLOG.txt", "a"))
    counter=0
    for x in log:
        logid, hiscall, hisclass, hissection, datetime, band, mode, power = x
        loggeddate = datetime[:10]
        loggedtime = datetime[11:13]+datetime[14:16]
        #print(value1, ..., sep=' ', end='\n', file=sys.stdout, flush=False)
        print("QSO:",band+"M",mode,loggeddate,loggedtime,mycall,myclass,mysection,hiscall,hisclass,hissection,sep=' ', end='\n',file=open("WFDLOG.txt", "a"))
    print("END-OF-LOG:", end='\n',file=open("WFDLOG.txt", "a"))

def logwindow():
	callfiller = "          "
	classfiller = "   "
	sectfiller = "   "
	bandfiller= "   "
	modefiller="  "
	zerofiller = "000"
	contacts = curses.newpad(1000,80)
	conn = sqlite3.connect(database)
	c = conn.cursor()
	c.execute("select * from contacts order by date_time desc")
	log = c.fetchall()
	conn.close()
	counter=0
	for x in log:
		logid, hiscall, hisclass, hissection, datetime, band, mode, power = x
		logid = zerofiller[:-len(str(logid))]+str(logid)
		hiscall = hiscall + callfiller[:-len(hiscall)]
		hisclass = hisclass + classfiller[:-len(hisclass)]
		hissection = hissection + sectfiller[:-len(hissection)]
		band = band + sectfiller[:-len(band)]
		mode = mode + modefiller[:-len(mode)]
		logline = logid+" "+hiscall+" "+hisclass+" "+hissection+" "+datetime+" "+band+" "+mode+" "+str(power)
		contacts.addstr(counter,0,logline)
		counter = counter +1
	stdscr.refresh()
	contacts.refresh(0,0,1,1,6,54)

def dupCheck(acall):
	global hisclass, hissection
	oy, ox = stdscr.getyx()
	scpwindow = curses.newpad(1000,33)
	rectangle(stdscr, 11,0, 21, 34)

	conn = sqlite3.connect(database)
	c = conn.cursor()
	c.execute("select callsign, class, section, band, mode from contacts where callsign like '"+acall+"'")
	log = c.fetchall()
	conn.close()
	counter=0
	for x in log:
		decorate = ""
		hiscall, hisclass, hissection, hisband, hismode = x
		if hisband == band and hismode == mode: decorate = curses.A_BOLD
		else: decorate = curses.A_NORMAL
		scpwindow.addstr(counter, 0,hiscall+": "+hisband+" "+hismode, decorate)
		counter = counter + 1
	stdscr.refresh()
	scpwindow.refresh(0,0,12,1,20,33)
	stdscr.move(oy,ox)

def displaySCP(matches):
	scpwindow = curses.newpad(1000,33)
	rectangle(stdscr, 11,0, 21, 34)
	for x in matches:
		wy, wx = scpwindow.getyx()
		if (33 - wx) < len(str(x)): scpwindow.move(wy+1,0)
		scpwindow.addstr(str(x)+" ")
	stdscr.refresh()
	scpwindow.refresh(0,0,12,1,20,33)

def workedSections():
	global wrkdsections
	conn = sqlite3.connect(database)
	c = conn.cursor()
	c.execute("select distinct section from contacts")
	all_rows = c.fetchall()
	wrkdsections = str(all_rows)
	wrkdsections = wrkdsections.replace("('","").replace("',), ",",").replace("',)]","").replace('[','').split(',')

def workedSection(section):
	if section in wrkdsections: return curses.A_BOLD
	else: return curses.A_NORMAL

def sectionsCol1():
	rectangle(stdscr, 8,35, 21, 43)
	stdscr.addstr(9,36,"   DX  ", curses.A_REVERSE)
	stdscr.addstr(10,36,"   DX  ", workedSection("DX"))
	stdscr.addstr(11,36,"   1   ", curses.A_REVERSE)
	stdscr.addstr(12,36,"CT", workedSection("CT"))
	stdscr.addstr(12,41,"RI", workedSection("RI"))
	stdscr.addstr(13,36,"EMA", workedSection("EMA"))
	stdscr.addstr(13,41,"VT", workedSection("VT"))
	stdscr.addstr(14,36,"ME", workedSection("ME"))
	stdscr.addstr(14,40,"WMA", workedSection("WMA"))
	stdscr.addstr(15,36,"NH", workedSection("NH"))
	stdscr.addstr(16,36,"   2   ", curses.A_REVERSE)
	stdscr.addstr(17,36,"ENY", workedSection("ENY"))
	stdscr.addstr(17,40,"NNY", workedSection("NNY"))
	stdscr.addstr(18,36,"NLI", workedSection("NLI"))
	stdscr.addstr(18,40,"SNJ", workedSection("SNJ"))
	stdscr.addstr(19,36,"NNJ", workedSection("NNJ"))
	stdscr.addstr(19,40,"WNY", workedSection("WNY"))

def sectionsCol2():
	rectangle(stdscr, 8,44, 21, 52)
	stdscr.addstr(9,45,"   3   ", curses.A_REVERSE)
	stdscr.addstr(10,45,"DE", workedSection("DE"))
	stdscr.addstr(10,49,"MDC", workedSection("MDC"))
	stdscr.addstr(11,45,"EPA", workedSection("EPA"))
	stdscr.addstr(11,49,"WPA", workedSection("WPA"))
	stdscr.addstr(12,45,"   4   ", curses.A_REVERSE)
	stdscr.addstr(13,45,"AL", workedSection("AL"))
	stdscr.addstr(13,50,"SC", workedSection("SC"))
	stdscr.addstr(14,45,"GA", workedSection("GA"))
	stdscr.addstr(14,49,"SFL", workedSection("SFL"))
	stdscr.addstr(15,45,"KY", workedSection("KY"))
	stdscr.addstr(15,50,"TY", workedSection("TY"))
	stdscr.addstr(16,45,"NC", workedSection("NC"))
	stdscr.addstr(16,50,"VA", workedSection("VA"))
	stdscr.addstr(17,45,"NFL", workedSection("NFL"))
	stdscr.addstr(17,50,"VI", workedSection("VI"))
	stdscr.addstr(18,45,"PR", workedSection("PR"))
	stdscr.addstr(18,49,"WCF", workedSection("WCF"))

def sectionsCol3():
	rectangle(stdscr, 8,53, 21, 61)
	stdscr.addstr(9,54,"   5   ", curses.A_REVERSE)
	stdscr.addstr(10,54,"AR", workedSection("AR"))
	stdscr.addstr(10,58,"NTX", workedSection("NTX"))
	stdscr.addstr(11,54,"LA", workedSection("LA"))
	stdscr.addstr(11,59,"OK", workedSection("OK"))
	stdscr.addstr(12,54,"MS", workedSection("MS"))
	stdscr.addstr(12,58,"STX", workedSection("STX"))
	stdscr.addstr(13,54,"NM", workedSection("NM"))
	stdscr.addstr(13,58,"WTX", workedSection("WTX"))
	stdscr.addstr(14,54,"   6   ", curses.A_REVERSE)
	stdscr.addstr(15,54,"EB", workedSection("EB"))
	stdscr.addstr(15,58,"SCV", workedSection("SCV"))
	stdscr.addstr(16,54,"LAX", workedSection("LAX"))
	stdscr.addstr(16,58,"SDG", workedSection("SDG"))
	stdscr.addstr(17,54,"ORG", workedSection("ORG"))
	stdscr.addstr(17,59,"SF", workedSection("SF"))
	stdscr.addstr(18,54,"PAC", workedSection("PAC"))
	stdscr.addstr(18,58,"SJV", workedSection("SJV"))
	stdscr.addstr(19,54,"SB", workedSection("SB"))
	stdscr.addstr(19,59,"SV", workedSection("SV"))

def sectionsCol4():
	rectangle(stdscr, 8,62, 21, 70)
	stdscr.addstr(9,63,"   7   ", curses.A_REVERSE)
	stdscr.addstr(10,63,"AK", workedSection("AK"))
	stdscr.addstr(10,68,"NV", workedSection("NV"))
	stdscr.addstr(11,63,"AZ", workedSection("AZ"))
	stdscr.addstr(11,68,"OR", workedSection("OR"))
	stdscr.addstr(12,63,"EWA", workedSection("EWA"))
	stdscr.addstr(12,68,"UT", workedSection("UT"))
	stdscr.addstr(13,63,"ID", workedSection("ID"))
	stdscr.addstr(13,67,"WWA", workedSection("WWA"))
	stdscr.addstr(14,63,"MT", workedSection("MT"))
	stdscr.addstr(14,68,"WY", workedSection("WY"))
	stdscr.addstr(15,63,"   8   ", curses.A_REVERSE)
	stdscr.addstr(16,63,"MI", workedSection("MI"))
	stdscr.addstr(16,68,"WV", workedSection("WV"))
	stdscr.addstr(17,63,"OH", workedSection("OH"))
	stdscr.addstr(18,63,"   9   ", curses.A_REVERSE)
	stdscr.addstr(19,63,"IL", workedSection("IL"))
	stdscr.addstr(19,68,"WI", workedSection("WI"))
	stdscr.addstr(20,63,"IN", workedSection("IN"))

def sectionsCol5():
	rectangle(stdscr, 8,71, 21, 79)
	stdscr.addstr(9,72,"   0   ", curses.A_REVERSE)
	stdscr.addstr(10,72,"CO", workedSection("CO"))
	stdscr.addstr(10,77,"MD", workedSection("MD"))
	stdscr.addstr(11,72,"IA", workedSection("IA"))
	stdscr.addstr(11,77,"ND", workedSection("ND"))
	stdscr.addstr(12,72,"KS", workedSection("KS"))
	stdscr.addstr(12,77,"NE", workedSection("NE"))
	stdscr.addstr(13,72,"MN", workedSection("MN"))
	stdscr.addstr(13,77,"SD", workedSection("SD"))
	stdscr.addstr(14,72,"CANADA ", curses.A_REVERSE)
	stdscr.addstr(15,72,"AB", workedSection("AB"))
	stdscr.addstr(15,77,"NT", workedSection("NT"))
	stdscr.addstr(16,72,"BC", workedSection("BC"))
	stdscr.addstr(16,76,"ONE", workedSection("ONE"))
	stdscr.addstr(17,72,"GTA", workedSection("GTA"))
	stdscr.addstr(17,76,"ONN", workedSection("ONN"))
	stdscr.addstr(18,72,"MAR", workedSection("MAR"))
	stdscr.addstr(18,76,"ONS", workedSection("ONS"))
	stdscr.addstr(19,72,"MB", workedSection("MB"))
	stdscr.addstr(19,77,"QC", workedSection("QC"))
	stdscr.addstr(20,72,"NL", workedSection("NL"))
	stdscr.addstr(20,77,"SK", workedSection("SK"))

def sections():
	workedSections()
	#rectangle(stdscr, 7,40, 21, 79)
	sectionsCol1()
	sectionsCol2()
	sectionsCol3()
	sectionsCol4()
	sectionsCol5()
	stdscr.refresh()

def entry():
	rectangle(stdscr, 8,0,10,18)
	stdscr.addstr(8,1,"CALL")
	rectangle(stdscr, 8,19,10,25)
	stdscr.addstr(8,20,"class")
	rectangle(stdscr, 8,26,10,34)
	stdscr.addstr(8,27,"Section")

def clearentry():
	global inputFieldFocus,hiscall,hissection,hisclass,kbuf
	hiscall = ""
	hissection = ""
	hisclass = ""
	kbuf = ""
	inputFieldFocus = 0
	displayInputField(2)
	displayInputField(1)
	displayInputField(0)

def statusline():
	y, x = stdscr.getyx()
	now=datetime.now().isoformat(' ')[11:19]
	utcnow=datetime.utcnow().isoformat(' ')[11:19]
	try:
		stdscr.addstr(22,60,"Local Time: " + now)
		stdscr.addstr(23,62,"UTC Time: " + utcnow)
	except curses.error as e:
		pass

	stdscr.addstr(23,1,"Band:        Mode:")
	stdscr.addstr(23,7,"  "+band+"  ", curses.A_REVERSE)
	stdscr.addstr(23,20,"  "+mode+"  ", curses.A_REVERSE)
	stdscr.addstr(23,27, "                                  ")
	stdscr.addstr(23,27, " "+mycall+"|"+myclass+"|"+mysection+"|"+power+"w ", curses.A_REVERSE)
	stdscr.move(y,x)

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

def displayHelp():
	wy, wx = stdscr.getyx()
	help = [".H this message |.L Generate Log",
		".Q quit program",
		".B## change bands",
		".M[CW,PH,DI] change mode",
		".P## change power",
		".D### delete a contact",
		".Kyourcall",
		".Cyourclass",
		".Syoursection"]
	stdscr.move(12,1)
	count = 0
	for x in help:
		stdscr.addstr(12+count, 1, x)
		count = count + 1
	stdscr.move(wy,wx)
	stdscr.refresh()

def displayinfo(info):
	y, x = stdscr.getyx()
	stdscr.move(20,1)
	stdscr.addstr(info)
	stdscr.move(y,x)
	stdscr.refresh()

def displayLine():
	filler = "                        "
	line = kbuf + filler[:-len(kbuf)]
	stdscr.move(9,1)
	stdscr.addstr(line)
	stdscr.move(9,len(kbuf)+1)
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
	stdscr.move(9,y)
	if kbuf == "":
		stdscr.addstr(filler)
	else:
		line = kbuf + filler[:-len(kbuf)]
		stdscr.addstr(line.upper())
	stdscr.move(9,len(kbuf)+y)
	stdscr.refresh()

def processcommand(cmd):
	global band, mode, power, quit
	cmd=cmd[1:].upper()
	if cmd=="Q":
		quit= True
		return
	if cmd[:1] == "B":
		setband(cmd[1:])
		return
	if cmd[:1] == "M":
		if cmd[1:] == "CW" or cmd[1:] == "PH" or cmd[1:] == "DI": setmode(cmd[1:])
		else:
			curses.flash()
			curses.beep()
		return
	if cmd[:1] == "P":
		setpower(cmd[1:])
		return
	if cmd[:1] == "D":
		delete_contact(cmd[1:])
		return
	if cmd[:1] == "H":
		displayHelp()
		return
	if cmd[:1] == "K":
		setcallsign(cmd[1:])
		return
	if cmd[:1] == "C":
		setclass(cmd[1:])
		return
	if cmd[:1] == "S":
		setsection(cmd[1:])
		return
	if cmd[:1] == "L":
		cabrillo()
		return
	curses.flash()
	curses.beep()

def proc_key(key):
	global inputFieldFocus,hiscall,hissection,hisclass,kbuf
	if key == 9:
		inputFieldFocus += 1
		if inputFieldFocus > 2:
			inputFieldFocus = 0
		if inputFieldFocus == 0:
			hissection = kbuf #store any input to previous field
			stdscr.move(9,1) #move focus to call field
			kbuf = hiscall #load current call into buffer
			stdscr.addstr(kbuf)
		if inputFieldFocus == 1:
			hiscall = kbuf #store any input to previous field
			dupCheck(hiscall)
			stdscr.move(9,20) #move focus to class field
			kbuf = hisclass #load current class into buffer
			stdscr.addstr(kbuf)
		if inputFieldFocus == 2:
			hisclass = kbuf #store any input to previous field
			stdscr.move(9,27) #move focus to section field
			kbuf = hissection #load current section into buffer
			stdscr.addstr(kbuf)
		return
	elif key == BackSpace:
		if kbuf !="":
			kbuf = kbuf[0:-1]
			if inputFieldFocus == 0 and len(kbuf) < 3: displaySCP(superCheck("^"))
			if inputFieldFocus == 0 and len(kbuf) > 2: displaySCP(superCheck(kbuf))
		displayInputField(inputFieldFocus)
		return
	elif key == EnterKey:
		if inputFieldFocus == 0:
			hiscall = kbuf
		elif inputFieldFocus == 1:
			hisclass = kbuf
		elif inputFieldFocus == 2:
			hissection = kbuf
		if hiscall[:1]==".": # process command
			processcommand(hiscall)
			clearentry()
			return
		if hiscall == "" or hisclass == "" or hissection == "":
			return
		utcnow=datetime.utcnow().isoformat(' ')[:16]
		contact = (hiscall, hisclass, hissection, band, mode, int(power))
		log_contact(contact)
		clearentry()
		return
	elif key == Escape:
		clearentry()
		return
	elif key == Space:
		return
	else:
		if len(kbuf) < maxFieldLength[inputFieldFocus]:
			kbuf = kbuf.upper() + chr(key).upper()
			if inputFieldFocus == 0 and len(kbuf) > 2: displaySCP(superCheck(kbuf))
	displayInputField(inputFieldFocus)

def main(s):
	global stdscr, conn

	conn = create_DB()
	curses.start_color()
	curses.use_default_colors()
	curses.noecho()
	curses.cbreak()
	stdscr.keypad(True)
	stdscr.nodelay(True)
	curses.mousemask(1)
	stdscr.clear()
	contacts()
	sections()
	stats()
	entry()
	logwindow()
	readpreferences()
	rectangle(stdscr, 11,0, 21, 34)
	displayHelp()
	stdscr.refresh()
	stdscr.move(9,1)
	while 1:
		statusline()
		stdscr.refresh()
		ch=stdscr.getch()
		#try:
		if ch == curses.KEY_MOUSE:
			_, x, y, _, bstate = curses.getmouse()
				#op=str(x)+", "+str(y)
				#stdscr.addstr(op+"  ")
				#stdscr.refresh()
		elif ch != -1:
			proc_key(ch)
				#stdscr.addstr(str(ch))
		else:
			time.sleep(0.1)
		#except:
		#	pass
		if quit == True: break

wrapper(main)