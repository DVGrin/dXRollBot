import sys
import time
import telepot
import telepot.loop
import re
import logging

import shuntingyard

# telepot.api.set_proxy("http://proxy.url")

logging.basicConfig(format="%(levelname)-8s (%(asctime)s) %(message)s", level=logging.DEBUG, datefmt="%d.%m.%y, %H:%M:%S")
logger = logging.getLogger(__name__)


class dXRollBot:
    '''Telegram Bot that rolls dice. Meant to mimic Roll20 dice functionality'''
    def __init__(self, token):
        self.bot = telepot.Bot(token)
        self.sent_message = ''
        self.commands = {"help": self._help,
                         "roll": self._roll,
                         "r": self._roll}
        telepot.loop.MessageLoop(self.bot, {'chat': self.on_chat_message}).run_as_thread()
        logger.info('Started listening...')
        while 1:
            time.sleep(10)

    def _help(self, chat_id, topic=''):
        with open("helpfile.txt", "r") as f:
            print_flag = not topic
            help_message = ""
            for line in f:
                if line == f"[{topic}]\n":
                    print_flag = True
                    continue
                if print_flag:
                    if (line[0] == "["):
                        break
                    help_message += line
        self.sent_message = self.bot.sendMessage(chat_id, help_message, parse_mode='Markdown')
        logger.info('Sent help message: "%s"', self.sent_message['text'])

    def _roll(self, chat_id, query):
        error_message = ""
        try:
            result = round(float(shuntingyard.ExpressionEvaluation(query)), 4)
            if result == int(result):
                result = int(result)
        except shuntingyard.UnknownSymbol as exc:
            error_message = f"Error: There was an unknown symbol or function in the expression: {exc}"
        except shuntingyard.StackIsEmpty as exc:
            error_message = f"Error: There was not enough values for one of the operators: {exc}"
        except shuntingyard.NegativeRollMeasurements as exc:
            error_message = "Error: " + exc
        except shuntingyard.KeepValueError as exc:
            error_message = "Error: " + exc
        except shuntingyard.RerollValueError as exc:
            error_message = "Error: " + exc
        except shuntingyard.MismatchedBrackets as exc:
            error_message = "Error: There was a mismatched bracket in the expression"
        except shuntingyard.EmptyExpression:
            error_message = "Error: No expression was given"
        except shuntingyard.RollModifierMisuse as exc:
            error_message = "Error: " + exc
        except ZeroDivisionError:
            error_message = "Error: There was an attempt to divide by zero"
        finally:
            if error_message:
                self.sent_message = self.bot.sendMessage(chat_id, error_message, parse_mode='Markdown')
                logger.info('Sent exception message: "%s"', self.sent_message['text'])
                return False
        new_text = f'```\n{query} = {result}```'
        if (len(new_text) >= 4095):
            if (len(str(result)) < 4088):
                new_text = f'```\n{result}```'
            else:
                new_text = "Error: The message is too long to display"
        self.sent_message = self.bot.sendMessage(chat_id, new_text, parse_mode='Markdown')
        logger.info('Sent message: "%s"', self.sent_message['text'])
        return True

    def _parse_command(self, message):
        _, _, chat_id = telepot.glance(message)
        if (message["text"][0] != '/'):
            return None
        command = re.compile("(\w+)(?:\s+|$)").match(message["text"][1:])
        if not command:
            return None
        if (command[1] in self.commands):
            self.commands[command[1]](chat_id, message["text"][command.span()[1]:])
        else:
            error_message = f"Unrecognized command: \"{command[1]}\""
            self.sent_message = self.bot.sendMessage(chat_id, error_message, parse_mode='Markdown')
            logger.info('Sent error message: "%s"', self.sent_message['text'])
        return command[1]

    def on_chat_message(self, message):
        content_type, chat_type, chat_id = telepot.glance(message)
        if (content_type == 'text'):
            logger.info('Received text message: "%s" from %s chat, id %s', message["text"], chat_type, chat_id)
            self._parse_command(message)
        else:
            logger.info('Received non-text (%s) message from %s chat, id %s', content_type, chat_type, chat_id)


dXRollBot(sys.argv[1])
