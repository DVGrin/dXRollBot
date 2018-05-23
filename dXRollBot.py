import sys
import time
import telepot
import telepot.loop
import re

import shuntingyard

# telepot.api.set_proxy("http://proxy.url")


class dXRollBot:
    '''Telegram Bot that rolls dice. Meant to mimic Roll20 dice functionality'''
    def __init__(self, token):
        self.bot = telepot.Bot(token)
        self.sent_message = ''
        self.commands = {"help": self._help,
                         "roll": self._roll,
                         "r": self._roll}
        telepot.loop.MessageLoop(self.bot, {'chat': self.on_chat_message}).run_as_thread()
        print('Started listening...')
        while 1:
            time.sleep(10)

    def _help(self, chat_id, topic=''):
        with open("helpfile.txt", "r") as f:
            if not topic:
                for line in f:
                    if line[0] == "[":
                        break
                    print(line)
            else:
                print_flag = False
                for line in f:
                    if line == f"[{topic}]":
                        print_flag = True
                        continue
                    if print_flag:
                        if (line[0] == "["):
                            break
                    print(line)

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
        except shuntingyard.MismatchedBrackets as exc:
            error_message = "Error: There was a mismatched bracket in the expression"
        except shuntingyard.EmptyExpression:
            error_message = "Error: No expression was given"
        except ZeroDivisionError:
            error_message = "Error: There was an attempt to divide by zero"
        finally:
            if error_message:
                self.sent_message = self.bot.sendMessage(chat_id, error_message, parse_mode='Markdown')
                print(f"Sent exception message: \"{self.sent_message['text']}\"")
                return False
        new_text = f'```\n{query} = {result}```'
        if (len(new_text) >= 4095):
            if (len(str(result)) < 4088):
                new_text = f'```\n{result}```'
            else:
                new_text = "Error: The message is too long to display"
        self.sent_message = self.bot.sendMessage(chat_id, new_text, parse_mode='Markdown')
        print(f"Sent message: \"{self.sent_message['text']}\"")
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
            print(f"Sent message: \"{self.sent_message['text']}\"")
        return command[1]

    def on_chat_message(self, message):
        content_type, chat_type, chat_id = telepot.glance(message)
        if (content_type == 'text'):
            print(f'Received text message: \"{message["text"]}\" from {chat_type} chat, id {chat_id}')
            self._parse_command(message)
        else:
            print(f'Received non-text ({content_type}) message from {chat_type} chat, id {chat_id}')


dXRollBot(sys.argv[1])
