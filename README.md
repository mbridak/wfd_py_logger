# K6GTE Winter Field Day logger (Curses)

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg?style=for-the-badge)](https://www.gnu.org/licenses/gpl-3.0) [![Python: 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg?logo=python&style=for-the-badge)](https://www.python.org/downloads/)  [![Made With: Ancient Technology](https://img.shields.io/badge/Made%20with-Ancient%20technology-red?style=for-the-badge)][def] ![PyPI - Downloads](https://img.shields.io/pypi/dm/wfdcurses?label=PYPI-Downloads&logo=pypi&style=for-the-badge)

![logo](https://github.com/mbridak/wfd_py_logger/raw/master/wfdcurses/data/k6gte.wfdcurses.svg)

[Winter Field Day](https://www.winterfieldday.org/) is a once a year 24hr
emergency preparidness event for radio amateurs (Hams). During the event, we try
and make as many radio contacts with other Hams in a 24 hour period. Bonus
points are awarded for operating outside or using alternate power sources, such
as battery/solar/wind. You can find out more about Winter Field Day by visiting
the [WFDA](https://winterfieldday.org/). You can find out more about amateur radio
by visiting the [ARRL](https://www.arrl.org/).

The logger is written in Python 3, and uses the curses lib. It will work with Linux and Mac, but since the Windows curses lib is lacking it will not work properly in Windows.

The log is stored in an sqlite3 database file 'wfd.db'. If you need to wipe everything and start clean, just delete this file. The screen size expected by the program is an 80 x 24 character terminal.

I decided to write this after the 2018 Winter Field Day when I couldn't find a simple Linux logger for the event. Just a simple logger with dup checking that could generate a cabrillo log for submission.

![Alt text](https://github.com/mbridak/wfd_py_logger/raw/master/pics/logger.png)

## TOC

- [K6GTE Winter Field Day logger (Curses)](#k6gte-winter-field-day-logger-curses)
  - [TOC](#toc)
  - [Installation and running](#installation-and-running)
  - [Recent Changes](#recent-changes)
  - [Caveats](#caveats)
  - [Initial Setup](#initial-setup)
  - [Commands](#commands)
  - [Logging](#logging)
  - [Features](#features)
    - [Radio Polling via rigctld or flrig](#radio-polling-via-rigctld-or-flrig)
    - [QRZ, HamQTH, HamDB](#qrz-hamqth-hamdb)
    - [Cloudlog](#cloudlog)
    - [Bearing to contact](#bearing-to-contact)
    - [Editing an existing contact](#editing-an-existing-contact)
    - [Super Check Partial](#super-check-partial)
    - [Section partial check](#section-partial-check)
    - [DUP checking](#dup-checking)
    - [Autofill](#autofill)
    - [CW Keying and Macros](#cw-keying-and-macros)
    - [cwdaemon use](#cwdaemon-use)
  - [TODO](#todo)

## Installation and running

The project is now on pypi. So now to install and run the package, you would:

```bash
#install it with
pip install wfdcurses

#update with
pip install --upgrade wfdcurses

#run it with
wfdcurses
```

## Recent Changes

- [24.1.27] Removed some deprecations.
- [23.1.14] CAT, fixing flrig.
- [23.1.14] Snazzy new app icon.
- [22.12.28] Dropped BeautifulSoup and lxml, replaced with xmltodict.
- [22.12.27] Digital modes are now DG not DI.
- [22.12.18] You can now install via `pip install wfdcurses`
- [22.12.16] The RAC sections have been updated for 2023
- [22.11.12] Updated for 2023 WFD rules.
- [22.6.29] Added CW macros

## Caveats

This is a simple logger meant for a single op, it's not usable for clubs. There's no networking between logging machines etc.

## Initial Setup

After launching the program you may want to access the new Edit Settings screen by using the command listed in the next section. Here you can setup your call/class/section, CAT, callsign lookup, Cloudlog intigration, CW keyer.

![Settings Screen](https://github.com/mbridak/wfd_py_logger/raw/master/pics/settings.png)

Navigate the screen by pressing either `TAB` or `Shift-TAB`. Settings with brackets `[_]` are boolean. `[_]` means disabled and `[X]` is enabled. They can either be toggled with the `SPACE` key, or pressing either one of these `XxYy1` to enable, or one of these `Nn0` to disable it.

After you make your changes, either press the `Enter` key to save your changes, or the `Esc` key to abort any changes and exit the screen.

## Commands

Commands start with a period character in the callsign field and are immediately followed by any information needed by the command.

```text
.H displays a short list of commands.
.Q Quit the program.
.S Access the settings screen
.P# Sets the power level, .P5 will set the power to 5 watts.
.MCW .MPH .MDI Sets the mode. CW Morse, PH Phone, DI Digital.
.B# sets the band, .B40 for 40 meters.
.D# Deletes log entry. .D26 will delete the log line starting with 026.
.E# Edits log entry. .E26 will edit the log line starting with 026.
.L Generate Cabrillo log file for submission.

[esc] abort input, clear all fields.
```

After the command is entered press the ENTER key to execute it.

## Logging

Okay you've made a contact. Enter the call in the call field. As you type it in, it will do a super check partial (see below). Press TAB or SPACE to advance to the next field. Once the call is complete it will do a DUP check (see below). It will try and Autofill the next fields (see below). When entering the section, it will do a section partial check (see below). Press the ENTER key to submit the contact to the log. If it's a busted call or a dup, press the ESC key to clear all inputs and start again.

## Features

### Radio Polling via rigctld or flrig

You can enable/disable the use of rigctld or flrig in the settings screen. The flrig default port is 12345, and the default rigctld port is 4532.

The radio will be polled for band/mode updates automatically. There is an indicator at the bottom of the logging window to indicate polling status. Dim if no connection or timeout, and highlighted if all okay.

![Alt text](https://github.com/mbridak/wfd_py_logger/raw/master/pics/rigctld.png)

### QRZ, HamQTH, HamDB

You can enable callsign lookups by enabling them in the settings screen. If you choose either QRZ or HamQTH place you credentials for that service in the username and password fields provided.

### Cloudlog

You can enable automatic logging to Cloudlog in the settings screen. Here you can enter your API key and URL to the service, along with a station ID if needed.

### Bearing to contact

Once you put in your own call and choose a lookup provider, the program looks up your gridsquare. I did this because I didn't want to change the settings screen... I'm not kidding. After this, and after it looks up the grid for the other person, it'll show you the bearing and distance to the contact.  

![screen clip of bearing](https://github.com/mbridak/wfd_py_logger/raw/master/pics/bearing.png)

### Editing an existing contact

Use the Up/Down arrow keys or PageUp/PageDown to scroll the contact into view. Your mouse scroll wheel may work as well. Double left click on the contact to edit, or use the '.E' command. Use the TAB or Up/Down arrow keys to move between fields. Backspace to erase and retype what you need.
Once done press the Enter key to save, or the Escape key to exit.

![Alt text](https://github.com/mbridak/wfd_py_logger/raw/master/pics/editcontact.png)

### Super Check Partial

If you type more than two characters in the callsign field the program will filter the input through a "Super Check Partial" routine and show you possible matches to known contesting call signs. Is this useful? Doubt it.

![Alt text](https://github.com/mbridak/wfd_py_logger/raw/master/pics/scp.png)

### Section partial check

As you type the section abbreviation you are presented with a list of all possible sections that start with what you have typed.

![Alt text](https://github.com/mbridak/wfd_py_logger/raw/master/pics/sectioncheckpartial.png)

### DUP checking

Once you type a complete callsign and press TAB or SPACE to advance to the next field. The callsign is checked against previous callsigns in your log. It will list any prior contact made showing the band and mode of the contact. If the band and mode are the same as the one you are currently using, the listing will be highlighted, the screen will flash, a bell will sound to alert you that this is a DUP. At this point you and the other OP can argue back and forth about who's wrong. In the end you'll put your big boy pants on and make a decision if you'll enter the call or not.

![Alt text](https://github.com/mbridak/wfd_py_logger/raw/master/pics/dupe_check.png)

### Autofill

If you have worked this person before on another band/mode the program will load the class and section used previously for this call so you will not have to enter this info again.

### CW Keying and Macros

You can use either cwdaemon or PyWinkeyer as a keying interface. After you run the program and choose your keyer interface you will find a file called cwmacros.txt in the base directory that you launched the logger from. The file has 12 lines, corresponding to the 12 function keys on most keyboards. The format of the file is simple:

F1|CQ|CQ WFD {MYCALL} {MYCALL} WFD

Three fields separated by a `|` character. The first field is the function key to map. The second is the name of the macro being sent. Which in this case does not make a whole lot of sense, because you can't see the name... Just go with it. The last field is the macro to send.

There are 4 substitution macros provided: {MYCALL} {HISCALL} {MYCLASS} {MYSECT}
They send pretty much excatly what you think it should send.

So if your're running, you might want a macro like:

F2|exchange|{HISCALL} {MYCLASS} {MYSECT}

Who knows... Go wild. The world is your very limited, Oddly specific oyster.

### cwdaemon use

If you use cwdaemon for your keyer, you can use the plus and minus on the keyboard to increase/decrease the sending speed by 1 wpm each time you press it. Pressing Escape aborts the sending.

## TODO

- Enter a contact at a specific time.

Let me know if you think of something else.

[def]: https://en.wikipedia.org/wiki/Curses_%28programming_library%29
