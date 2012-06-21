from logging import Handler
import logging
import sys
import config
import curses

screen = curses.initscr()
curses.noecho()
curses.curs_set(1)
screen.keypad(1)
screen_size_y, screen_size_x = screen.getmaxyx()

mainpad = curses.newpad(120, 1000)
logpad = curses.newpad(120, 1000)
#mypad.border()

mainpad_pos = 0
logpad_pos = 0
from pydev import pydevd
pydevd.settrace('localhost', port=51234, stdoutToServer=False, stderrToServer=False)

def refresh():
    global mainpad_pos
    global logpad_pos
    middle = screen_size_x / 2
    (y, x) = mainpad.getyx()
    if mainpad_pos - y > screen_size_y:
        mainpad_pos = y - screen_size_y

    (y, x) = logpad.getyx()
    if logpad_pos - y > screen_size_y:
        logpad_pos = y - screen_size_y

    mainpad.refresh(mainpad_pos, 0, 0, 0, screen_size_y - 1, middle)
    logpad.refresh(logpad_pos, 0, 0, middle + 1, screen_size_y - 1, screen_size_x - 1)


class CursesHandler(Handler):
    def emit(self, record):
        try:
            logpad.addstr("%s\n" % self.format(record))
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

#hack back the logging so it is redirected to curses
logger = logging.getLogger('')
hdlr = CursesHandler()
hdlr.setFormatter(logging.Formatter('%(levelname)s %(message)s'))

# zap them all to avoid noise on the console
for h in logger.handlers:
    logger.removeHandler(h)

logger.addHandler(hdlr)

class JIDMock():
    domain = 'meuh'
    resource = 'bidon'

    def __init__(self, node):
        self.node = node

    def getNode(self):
        return self.node

    def bareMatch(self, whatever):
        return False

    def getStripped(self):
        return self.node


class MessageMock():
    def __init__(self, body):
        self.body = body

    def getType(self):
        return 'chat'

    def getFrom(self):
        return JIDMock(config.BOT_ADMINS[0])

    def getProperties(self):
        return {}

    def getBody(self):
        return self.body

    def getThread(self):
        return None


class ConnectionMock():
    def send(self, mess):
        if hasattr(mess, 'getBody'):
            mainpad.addstr(mess.getBody())

ENCODING_INPUT = sys.stdin.encoding

def prompt():
    mainpad.addstr('\nTalk to me >>')


def patch_jabberbot():
    from errbot import jabberbot

    conn = ConnectionMock()

    def fake_serve_forever(self):
        self.jid = JIDMock('blah') # whatever
        self.connect() # be sure we are "connected" before the first command
        try:
            buffer = ""
            prompt()
            mainpad_pos = mainpad.getyx()[0] - 40
            refresh()
            while True:
                event = screen.getch()
                if event == ord('\n'):
                    mainpad.addstr('\n')
                    self.callback_message(conn, MessageMock(buffer))
                    buffer = ""
                    prompt()
                elif event == curses.KEY_PPAGE:
                    mainpad_pos -= 5
                elif event == curses.KEY_NPAGE:
                    mainpad_pos += 5
                elif event == curses.KEY_BACKSPACE or event == 127:
                    if buffer:
                        buffer = buffer[:-1]
                        (y, x) = mainpad.getyx()
                        mainpad.move(y, x - 1)
                        mainpad.delch()
                elif event == curses.KEY_RESIZE:
                    screen_size_x, screen_size_y = screen.getmaxyx()
                elif event > 256:
                    mainpad.addstr('MUMBO JUMBO')
                else:
                    c = str(chr(event))
                    mainpad.addstr(c)
                    buffer += c

                refresh()

        except EOFError as eof:
            pass
        except KeyboardInterrupt as ki:
            pass
        finally:
            curses.endwin()
            mainpad.addstr("\nExiting...")

    def fake_connect(self):
        if not self.conn:
            self.conn = ConnectionMock()
            self.activate_non_started_plugins()
            logging.info('Notifying connection to all the plugins...')
            self.signal_connect_to_all_plugins()
            logging.info('Plugin activation done.')
        return self.conn

    jabberbot.JabberBot.serve_forever = fake_serve_forever
    jabberbot.JabberBot.connect = fake_connect