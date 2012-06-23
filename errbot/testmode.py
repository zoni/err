import logging
import sys
import config

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
            print mess.getBody()

ENCODING_INPUT = sys.stdin.encoding
import sys, tty, termios
fd = sys.stdin.fileno()
old_settings = termios.tcgetattr(fd)

def setup_getch():
    tty.setraw(sys.stdin.fileno())

def getch():
    return sys.stdin.read(1)

def restore_getch():
    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def patch_jabberbot():
    from errbot import jabberbot

    conn = ConnectionMock()

    def fake_serve_forever(self):
        self.jid = JIDMock('blah') # whatever
        self.connect() # be sure we are "connected" before the first command
        try:

            while True:
                buffer = ''
                c = None
                sys.stdout.write('>>')
                setup_getch()
                while c != '\r':
                    c = getch()
                    buffer+=c
                    sys.stdout.write(c)
                    if ord(c) == 3: # ctrl c
                        raise EOFError()
                restore_getch()
                sys.stdout.write('\n')
                self.callback_message(conn, MessageMock(buffer))
        except EOFError as eof:
            pass
        except KeyboardInterrupt as ki:
            pass
        finally:
            restore_getch()
            print "\nExiting..."


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