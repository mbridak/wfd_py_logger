## K6GTE Winter Field Day logger

The logger is written in Python 3, and uses the curses lib. This means it will work with Linux, maybe Mac, but not Windows. You windows guys have enough loggers already.

The log is stored in an sqlite3 database. The screen size expected by the program is an 80 x 24 character terminal. Nothing needs to be installed, compiled etc... Just make WFD_Curses.py executable and run it within the same folder.

I decided to write this after the 2018 Winter Field Day when I couldn't find a simple Linux logger for the event. I didn't need multiuser logging or GPS disciplined time servers..

![Alt text](https://github.com/mbridak/wfd_py_logger/raw/master/logger.png)

## Caveats
This is a simple logger ment for one person. It's not usable for clubs. It's
ment for A guy/girl setting up for Winter Field Day in in their backyard wanting
a simple logger.
It currently generates a rudimentary Cabrillo log.

## Commands:
Commands start with a period character in the callsign field and are immediately followed by any
information needed by the command.

```
.H displays a short list of commands.
.Q Quit the program.
.Kyourcall Sets your callsign. .KK6GTE will set it to K6GTE.
.Cyourclass Sets your class. .C1O wil set your class to 1O.
.Syoursection Sets your section. .SORG sets your section to ORG.
.P# Sets the power level, .P5 will set the power to 5 watts.
.MCW .MPH .MDI Sets the mode. CW Morse, PH Phone, DI Digital.
.B# sets the band, .B40 for 40 meters.
.D# Deletes log entry. .D26 will delete the log line starting with 026.
.L Generate Cabrillo log file for submission.
.1 Claim Alt-Power Bonus
.2 Claim Outdoors Bonus
.3 Claim Away from Home Bonus
.4 Claim Satellite Bonus
[esc] abort input, clear all fields.
```

After the command is entered press the TAB key to execute it.

## Initial Setup
When run for the first time, you will need to set your callsign, class, section, band, mode and power used for the contacts.

So when I initially start the program I would enter the following:

```
.KK6GTE
.C1O
.SORG
.P5
.B40
.MCW
``` 
For claimed bonuses, since I'll be using battery and solar and I'll be outdoors and away from home, but I don't plan on making any Satellite contacts I'd also enter the following.
```
.1
.2
.3
```

## Features

#### Editing an existing contact
Use the mouse to scroll the contact into view and double left click on the contact to edit.
Once done press the Enter key to save,
or the escape key to exit.

#### Super Check Partial
If you type more than two characters in the callsign field the program will filter the input through a
"Super Check Partial" routine and show you possible matches to known contesting call signs. Is this useful? Doubt it.

#### Section partial check
As you type the section abbreviation you are presented with a list of all possible sections that start with what you have typed.

#### DUP checking
Once you type a complete callsign and press TAB to advance to the next field. The callsign is checked
against previous callsigns in your log. It will list any prior contact made with the band and mode of
the contact. If the band and mode are the same as the one you are currently using, the listing will be
highlighted to alert you that this is a DUP.

#### Autofill
If you have worked this person before on another band/mode the program will load the class and section
used previously for this call so you will not have to enter this info again.

## TODO
  * Enter a contact at a specific time.

Let me know if you think of something else.
