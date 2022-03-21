"""Testing EditField class"""
# pylint: disable=invalid-name

import curses
from curses.ascii import isalnum


class EditTextField:
    """basic text field edit"""

    def __init__(self, screen, y=0, x=0, length=10, placeholder="edit me"):
        self.screen = screen
        self.textfield = ""
        self.placeholder = placeholder
        self.max_length = length
        self.position_x = x
        self.position_y = y
        self.cursor_position = 0
        self.length = 0

    def getchar(self, character) -> None:
        """Process character"""
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
                    f"{chr(character).upper()}"
                    f"{self.textfield[self.cursor_position:]}"
                )
                self.cursor_position += 1
        self.screen.addstr(self.position_y, self.position_x, " " * self.max_length)
        self.screen.addstr(self.position_y, self.position_x, self.textfield)
        self._movecursor()

    def _movecursor(self) -> None:
        """moves cursor to current position"""
        self.screen.move(self.position_y, self.position_x + self.cursor_position)

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
        self.screen.addstr(self.position_y, self.position_x, " " * self.max_length)
        self.screen.addstr(self.position_y, self.position_x, self.textfield)
        self.set_cursor_position(len(self.textfield))
        self.screen.move(self.position_y, self.position_x + self.cursor_position)
