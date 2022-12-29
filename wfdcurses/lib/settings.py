"""SettingsScreen class"""
# pylint: disable=invalid-name
# pylint: disable=too-many-function-args

import curses
import time

try:
    from wfdcurses.lib.edittextfield import EditTextField
except ModuleNotFoundError:
    from lib.edittextfield import EditTextField


class SettingsScreen:
    """Yup it's the settings screen"""

    BACK_SPACE = 263
    TAB = 9
    SHIFT_TAB = 353
    ESCAPE = 27
    QUESTIONMARK = 63
    ENTERKEY = 10
    SPACE = 32
    WIDTH = 76
    HEIGHT = 22
    WINY = 1
    WINX = 2
    TITLE = "EDIT SETTINGS"
    MENU = [
        "",
        " My Call:                My Class:     My Section:     Output Watts:    ",
        "",
        "                              CALLSIGN LOOKUP",
        " Use HamDB: [ ]            Use QRZ: [ ]              Use HamQTH: [ ]",
        " Username:                 Password:",
        "",
        "                                RIG CONTROL",
        " Use rigctld: [ ]     Use flrig: [ ]",
        " CAT IP/Hostname:                      CAT Port:",
        "",
        "                                 CLOUDLOG",
        " Use Cloudlog: [ ]",
        " Cloudlog API:",
        " Cloudlog URL:",
        " Cloudlog StationID:",
        "",
        "                 CW                                   BONUSES",
        "    cwdaemon: [ ]  PyWinkeyer [ ]         Alt-Power: [ ]    Outdoors: [ ]",
        " Host:                      Port:       NotAtHome: [ ]  Sat: [ ] Ant: [ ]",
    ]

    def __init__(self, preference):
        """setup settings screen"""
        self.preference = preference
        self.input_field_focus = 0
        self.screen = curses.newwin(self.HEIGHT, self.WIDTH, self.WINY, self.WINX)
        self.screen.keypad(True)
        self.screen.nodelay(True)
        self.screen.box()
        self._title()
        self.mycallsign = EditTextField(self.screen, 2, 11, 14, curses.A_UNDERLINE)
        self.mycallsign.set_text(
            preference.get("mycallsign") if preference.get("mycallsign") else ""
        )
        self.myclass = EditTextField(self.screen, 2, 36, 3, curses.A_UNDERLINE)
        self.myclass.set_text(
            preference.get("myclass") if preference.get("myclass") else ""
        )
        self.mysection = EditTextField(self.screen, 2, 52, 3, curses.A_UNDERLINE)
        self.mysection.set_text(
            preference.get("mysection") if preference.get("mysection") else ""
        )
        self.power = EditTextField(self.screen, 2, 70, 3, curses.A_UNDERLINE)
        self.power.set_text(preference.get("power") if preference.get("power") else "")
        self.usehamdb = EditTextField(self.screen, 5, 14, 1, curses.A_UNDERLINE)
        self.usehamdb.set_bool(True)
        self.usehamdb.set_state(bool(preference.get("usehamdb")))
        self.useqrz = EditTextField(self.screen, 5, 38, 1, curses.A_UNDERLINE)
        self.useqrz.set_bool(True)
        self.useqrz.set_state(bool(preference["useqrz"]))
        self.usehamqth = EditTextField(self.screen, 5, 67, 1, curses.A_UNDERLINE)
        self.usehamqth.set_bool(True)
        self.usehamqth.set_state(bool(preference["usehamqth"]))
        self.lookupusername = EditTextField(self.screen, 6, 12, 15, curses.A_UNDERLINE)
        self.lookupusername.lowercase(True)
        self.lookupusername.set_text(
            preference.get("lookupusername") if preference.get("lookupusername") else ""
        )
        self.lookuppassword = EditTextField(self.screen, 6, 38, 20, curses.A_UNDERLINE)
        self.lookuppassword.lowercase(True)
        self.lookuppassword.set_text(
            preference.get("lookuppassword") if preference.get("lookuppassword") else ""
        )
        self.userigctld = EditTextField(self.screen, 9, 16, 1, curses.A_UNDERLINE)
        self.userigctld.set_bool(True)
        self.userigctld.set_state(bool(preference["userigctld"]))
        self.useflrig = EditTextField(self.screen, 9, 35, 1, curses.A_UNDERLINE)
        self.useflrig.set_bool(True)
        self.useflrig.set_state(bool(preference["useflrig"]))
        self.CAT_ip = EditTextField(self.screen, 10, 19, 20, curses.A_UNDERLINE)
        self.CAT_ip.lowercase(True)
        self.CAT_ip.set_text(
            preference.get("CAT_ip") if preference.get("CAT_ip") else ""
        )
        self.CAT_port = EditTextField(self.screen, 10, 50, 5, curses.A_UNDERLINE)
        self.CAT_port.set_text(
            str(preference.get("CAT_port") if preference.get("CAT_port") else "")
        )
        self.cloudlog = EditTextField(self.screen, 13, 17, 1, curses.A_UNDERLINE)
        self.cloudlog.set_bool(True)
        self.cloudlog.set_state(bool(preference["cloudlog"]))
        self.cloudlogapi = EditTextField(self.screen, 14, 16, 25, curses.A_UNDERLINE)
        self.cloudlogapi.lowercase(True)
        self.cloudlogapi.set_text(
            preference.get("cloudlogapi") if preference.get("cloudlogapi") else ""
        )
        self.cloudlogurl = EditTextField(self.screen, 15, 16, 58, curses.A_UNDERLINE)
        self.cloudlogurl.lowercase(True)
        self.cloudlogurl.set_text(
            preference.get("cloudlogurl") if preference.get("cloudlogurl") else ""
        )
        self.cloudlogstationid = EditTextField(
            self.screen, 16, 23, 20, curses.A_UNDERLINE
        )
        self.cloudlogstationid.lowercase(True)
        self.cloudlogstationid.set_text(
            preference.get("cloudlogstationid")
            if preference.get("cloudlogstationid")
            else ""
        )
        self.altpower = EditTextField(self.screen, 19, 55, 1, curses.A_UNDERLINE)
        self.altpower.set_bool(True)
        self.outdoors = EditTextField(self.screen, 19, 72, 1, curses.A_UNDERLINE)
        self.outdoors.set_bool(True)
        self.notathome = EditTextField(self.screen, 20, 53, 1, curses.A_UNDERLINE)
        self.notathome.set_bool(True)
        self.satellite = EditTextField(self.screen, 20, 63, 1, curses.A_UNDERLINE)
        self.satellite.set_bool(True)
        self.antenna = EditTextField(self.screen, 20, 72, 1, curses.A_UNDERLINE)
        self.antenna.set_bool(True)
        self.altpower.set_state(bool(preference["altpower"]))
        self.outdoors.set_state(bool(preference["outdoors"]))
        self.notathome.set_state(bool(preference["notathome"]))
        self.satellite.set_state(bool(preference["satellite"]))
        self.antenna.set_state(bool(preference.get("antenna")))

        self.cwdaemon = EditTextField(self.screen, 19, 16, 1, curses.A_UNDERLINE)
        self.cwdaemon.set_bool(True)
        self.pywinkeyer = EditTextField(self.screen, 19, 32, 1, curses.A_UNDERLINE)
        self.pywinkeyer.set_bool(True)
        cwd = preference["cwtype"]
        self.cwdaemon.set_state(bool(cwd == 1))
        self.pywinkeyer.set_state(bool(cwd == 2))
        self.CW_IP = EditTextField(self.screen, 20, 8, 20, curses.A_UNDERLINE)
        self.CW_IP.lowercase(True)
        self.CW_IP.set_text(preference.get("CW_IP") if preference.get("CW_IP") else "")
        self.CW_port = EditTextField(self.screen, 20, 35, 5, curses.A_UNDERLINE)
        self.CW_port.set_text(
            str(preference.get("CW_port") if preference.get("CW_port") else "")
        )

        self.input_fields = [
            self.mycallsign,
            self.myclass,
            self.mysection,
            self.power,
            self.usehamdb,
            self.useqrz,
            self.usehamqth,
            self.lookupusername,
            self.lookuppassword,
            self.userigctld,
            self.useflrig,
            self.CAT_ip,
            self.CAT_port,
            self.cloudlog,
            self.cloudlogapi,
            self.cloudlogurl,
            self.cloudlogstationid,
            self.cwdaemon,
            self.pywinkeyer,
            self.CW_IP,
            self.CW_port,
            self.altpower,
            self.outdoors,
            self.notathome,
            self.satellite,
            self.antenna,
        ]

        self._display_menu()

    def _title(self):
        position = int((self.WIDTH / 2) - (len(self.TITLE) / 2))
        self.screen.addch(0, position - 1, curses.ACS_RTEE)
        self.screen.addstr(0, position, self.TITLE)
        self.screen.addch(curses.ACS_LTEE)

    def _display_menu(self):
        """Displays menu text and input fields"""
        for vert, line in enumerate(self.MENU):
            self.screen.addstr(vert + 1, 1, line)
        for item in self.input_fields:
            item.get_focus()
        self.mycallsign.get_focus()

    def show(self):
        """show screen"""
        self.mycallsign.get_focus()
        self.screen.refresh()
        while True:
            c = self.screen.getch()
            if c == self.TAB:
                self.input_field_focus += 1
                if self.input_field_focus > len(self.input_fields) - 1:
                    self.input_field_focus = 0
                self.input_fields[self.input_field_focus].get_focus()
                continue
            if c == self.SHIFT_TAB:
                self.input_field_focus -= 1
                if self.input_field_focus < 0:
                    self.input_field_focus = len(self.input_fields) - 1
                self.input_fields[self.input_field_focus].get_focus()
                continue
            if c == self.ESCAPE:
                self.screen.erase()
                return False
            if c == self.ENTERKEY:
                self.preference["mycallsign"] = self.mycallsign.text()
                self.preference["myclass"] = self.myclass.text()
                self.preference["mysection"] = self.mysection.text()
                self.preference["power"] = self.power.text()
                self.preference["usehamdb"] = self.usehamdb.get_state()
                self.preference["useqrz"] = self.useqrz.get_state()
                self.preference["usehamqth"] = self.usehamqth.get_state()
                self.preference["lookupusername"] = self.lookupusername.text()
                self.preference["lookuppassword"] = self.lookuppassword.text()
                self.preference["userigctld"] = self.userigctld.get_state()
                self.preference["useflrig"] = self.useflrig.get_state()
                self.preference["CAT_ip"] = self.CAT_ip.text()
                try:
                    self.preference["CAT_port"] = int(self.CAT_port.text())
                except ValueError:
                    self.preference["CAT_port"] = 0
                self.preference["cloudlog"] = self.cloudlog.get_state()
                self.preference["cloudlogapi"] = self.cloudlogapi.text()
                self.preference["cloudlogurl"] = self.cloudlogurl.text()
                self.preference["cloudlogstationid"] = self.cloudlogstationid.text()
                self.preference["altpower"] = self.altpower.get_state()
                self.preference["outdoors"] = self.outdoors.get_state()
                self.preference["notathome"] = self.notathome.get_state()
                self.preference["satellite"] = self.satellite.get_state()
                self.preference["antenna"] = self.antenna.get_state()
                self.preference["cwtype"] = 0
                if self.cwdaemon.get_state():
                    self.preference["cwtype"] = 1
                if self.pywinkeyer.get_state():
                    self.preference["cwtype"] = 2
                self.preference["CW_IP"] = self.CW_IP.text()
                try:
                    self.preference["CW_port"] = int(self.CW_port.text())
                except ValueError:
                    self.preference["CW_port"] = 0
                self.screen.erase()
                return self.preference
            self.input_fields[self.input_field_focus].getchar(c)
            time.sleep(0.01)

    def close(self):
        """not useful yet"""
        self.screen.endwin()


def main():
    """Just in case..."""
    print("I'm not a program.")


if __name__ == "__main__":
    main()
