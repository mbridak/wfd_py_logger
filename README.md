wfd_py_logger
K6GTE Winter Field Day logger
The logger is written in Python 3, and uses the curses lib. This means it will work with Linux, maybe Mac, but not Windows. You windows guys have enough loggers already.

Commands:
Commands start with a period character in the callsign field and are immediately followed by any information needed by the command.

.H displays a short list of commands.
.Q Quit the program.
.P# Sets the power level, .P5 will set the power to 5 watts.
.MCW .MPH .MDI Sets the mode. CW Morse, PH Phone, DI Digital.
.B# sets the band, .B40 for 40 meters.
.D# Deletes log entry. .D26 will delete the log line starting with 026.

After the command is entered press the TAB key to execute it.

If you type more than two characters in the callsign field the program will filter the input through a "Super Check Partial" routing and show you possible matches to known contesting call signs.
Once you type a complete callsign and press TAB to advance to the next field. The callsign is checked against previous callsigns in your log. It will list any prior contact made with the band and mode of the contact. If the band and mode are the same as the one you are currently using, the listing will be highlighted to alert you that this is a DUP.
If you have worked this person before on another band/mode the program will load the class and section used previously for this call so you will not have to enter this info again.
 