"""Testing EditField class"""
# pylint: disable=invalid-name

import curses
from curses.ascii import isalnum
import logging


class EditTextField:
    """basic text field edit"""

    def __init__(self, screen, y=0, x=0, length=10, attribute=curses.A_NORMAL):
        self.screen = screen
        self.textfield = ""
        self.attribute = attribute
        self.max_length = length
        self.position_x = x
        self.position_y = y
        self.cursor_position = 0
        self.length = 0
        self.is_bool = False
        self.my_state = False
        self.allow_lowercase = False

    def getchar(self, character) -> None:
        """Process character"""
        if self.is_bool:
            if character == 32:  # space
                self.toggle_state()
                self.get_focus()
                return
            try:
                if chr(character) in "XxYy1":
                    self.set_state(True)
                    self.get_focus()
                    return
                if chr(character) in "0nN":
                    self.set_state(False)
                    self.get_focus()
                    return
            except ValueError:
                pass
        else:
            if character == curses.KEY_LEFT:
                self.cursor_position -= 1
                self.cursor_position = max(self.cursor_position, 0)
            if character == curses.KEY_RIGHT:
                self.cursor_position += 1
                if self.cursor_position > len(self.textfield):
                    self.cursor_position = len(self.textfield)
            if character == curses.KEY_BACKSPACE:
                if self.cursor_position > 0:
                    self.textfield = (
                        self.textfield[: self.cursor_position - 1]
                        + self.textfield[self.cursor_position :]
                    )
                    self.cursor_position -= 1
                    self.cursor_position = max(self.cursor_position, 0)
            if character == curses.KEY_DC:
                self.textfield = (
                    self.textfield[: self.cursor_position]
                    + self.textfield[self.cursor_position + 1 :]
                )
            if isalnum(character) or character == ord("."):
                if len(self.textfield) < self.max_length:
                    self.textfield = (
                        f"{self.textfield[:self.cursor_position]}"
                        f"{chr(character)}"
                        f"{self.textfield[self.cursor_position:]}"
                    )
                    if not self.allow_lowercase:
                        self.textfield = self.textfield.upper()
                    self.cursor_position += 1
            self.screen.addstr(
                self.position_y, self.position_x, " " * self.max_length, self.attribute
            )
            self.screen.addstr(
                self.position_y, self.position_x, self.textfield, self.attribute
            )
            self._movecursor()

    def _movecursor(self) -> None:
        """moves cursor to current position"""
        self.screen.move(self.position_y, self.position_x + self.cursor_position)

    def lowercase(self, allow):
        """Allows a field to have lowercase letters"""
        self.allow_lowercase = bool(allow)

    def set_bool(self, is_bool: bool) -> None:
        """Sets behaviour of input to boolian or text input"""
        self.is_bool = is_bool

    def get_state(self):
        """Return the boolean state"""
        return self.my_state

    def toggle_state(self):
        """Toggles the logical state if it's a bool"""
        self.set_state(not self.my_state)
        logging.debug("toggle state now: %s", self.my_state)

    def set_state(self, state):
        """Sets the boolean state"""
        self.my_state = bool(state)
        if self.my_state:
            self.set_text("X")
        else:
            self.set_text(" ")

    def text(self) -> str:
        """Returns contents of field"""
        return self.textfield

    def clearfield(self) -> None:
        """clear the field"""
        self.textfield = ""
        self.cursor_position = 0

    def set_text(self, input_string: str) -> None:
        """Set the contents of the edit field"""
        self.textfield = input_string
        self.cursor_position = len(self.textfield)

    def get_cursor_position(self):
        """return current cursor position"""
        return self.cursor_position

    def set_cursor_position(self, position: int) -> None:
        """set cursor position"""
        self.cursor_position = position

    def get_focus(self):
        """redisplay textfield, move cursor to end"""
        self.screen.addstr(
            self.position_y, self.position_x, " " * self.max_length, self.attribute
        )
        self.screen.addstr(
            self.position_y, self.position_x, self.textfield, self.attribute
        )
        self.set_cursor_position(len(self.textfield) * (not self.is_bool))
        self.screen.move(self.position_y, self.position_x + self.cursor_position)

def main():
    """Just in case..."""
    print("I'm not a program.")

if __name__ == "__main__":
    main()
    