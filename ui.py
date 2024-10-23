from blessed import Terminal
from generators import Color
import typing
import sys
from collections.abc import Callable

class Gui:
    colors: typing.List[Color] = []
    _term = Terminal()
    _frame_time = 0.0
    _prompt = ""
    _console: typing.List[str] = []
    _max_height = 5
    _commands: dict[str, Callable[..., str | None]] = {}
    _lines = 1


    def __init__(self):
        assert self._term.hpa(1) != u'', ("Terminal does not support hpa")
        self.register_command(
            "help",
            lambda *_: self.log(
                "Available commands: " + " ".join(self._commands.keys())
            )
        )
        self.register_command("exit", lambda *_: exit(0))
        print()


    def set_frame_time(self, frame_time: float):
        NEW_VAL_WEIGHT = 1/10
        self._frame_time = self._frame_time * (1-NEW_VAL_WEIGHT) + frame_time * NEW_VAL_WEIGHT


    def register_command(self, command: str, callback: Callable[..., str | None]):
        self._commands[command] = callback


    def _truncate_log(self):
        while len(self._console) > self._max_height:
            self._console.pop(0)


    def _process_prompt(self) -> None:
        self._console.append("> " + self._prompt)

        split = self._prompt.split(" ")
        command = split[0]
        arguments: typing.List[str] = []
        if len(split) > 1:
            arguments = split[1:]

        try:
            match self._commands.get(command, lambda *_: "")(*arguments):
                case "" | None: pass
                case s: self.log(s)
        except TypeError:
            self.log_error(f"bad arguments for {command}")
        self._prompt = ""
        sys.stdout.write(self._term.move_x(0) + self._term.ljust(" "))
        self._truncate_log()


    def log(self, message: str):
        self._console.append(message)


    def log_error(self, err_str: str):
        self._console.append(
            f"{self._term.color_rgb(255, 100, 100)}{err_str}{self._term.normal}")


    def render(self):
        lines = 1
        display = ""

        l = ""
        for color in self.colors:
            l += self._term.on_color_rgb(*color) + " "
        l += self._term.normal + "\n"
        display += l
        self.colors = []

        display += self._term.ljust(f"frame time: {self._frame_time * 1000:.1f}ms")
        display += "\n"
        lines += 1

        for line in self._console:
            display += self._term.ljust(line) + "\n"
            lines += 1

        display += "> " + self._prompt

        #if self._prompt == "":
        #    display += "\n"
        #    lines += 1

        display = self._term.move_x(0) + self._term.move_up * self._lines + display
        self._lines = lines
        sys.stdout.write(display)
        sys.stdout.flush()

    
    def poll(self, poll_for: float):
        with self._term.raw(), self._term.keypad():
                inp = self._term.inkey(poll_for)
                if inp == chr(3):
                    # ^c exits
                    raise KeyboardInterrupt
                elif inp.is_sequence:
                    match inp.code:
                        case 263: # Backspace
                            self._prompt = self._prompt[0:-1]
                        case 343: # Return
                            self._process_prompt()
                        case _:
                            pass
                            #print(inp.code)
                            #exit(0)
                else:
                    self._prompt += inp
                #display += self.console
