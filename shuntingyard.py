from numbers import Real
from collections import deque
import operator
import random
import math
import re
import logging

import timeout

'''
TODO: Legality checks, line ~310
'''

logging.basicConfig(format="%(levelname)-8s (%(asctime)s) %(message)s", level=logging.DEBUG, datefmt="%d.%m.%y, %H:%M:%S")
logger = logging.getLogger(__name__)


class UnknownSymbol(Exception):
    '''There was a symbol or function in the expression that the algorithm doesn't support'''


class StackIsEmpty(Exception):
    '''There was an attempt to pop from empty stack'''


class NegativeRollMeasurements(Exception):
    '''The user tried to roll a die with negative side count or negative number of dice'''


class KeepValueError(Exception):
    '''The user either tried to keep something that is not a roll or the number of dice to keep was wrong'''


class MismatchedBrackets(Exception):
    '''There was a mismatched bracket'''


class RolledDice:
    '''Class that simulates a dice roll and holds all the information about it to allow arithmetics'''
    def __init__(self, number, sides, rolls=None, dropped_rolls=None, additional_rolls=None, sum=None):
        logger.debug("Created RolledDice(number=%s, sides=%s, rolls=%s, dropped_rolls=%s, additional_rolls=%s, sum=%s) instance", number, sides, rolls, dropped_rolls, additional_rolls, sum)
        if (isinstance(number, RolledDice)):
            rolls = number.rolls
            dropped_rolls = number.dropped_rolls
            additional_rolls = number.additional_rolls
        self.number = int(number)
        if (isinstance(sides, RolledDice)):
            rolls = sides.rolls
            dropped_rolls = sides.dropped_rolls
            additional_rolls = sides.additional_rolls
        self.sides = sides
        if self.sides != "F":
            self.sides = int(sides)
        if (self.sides != "F" and self.sides < 0):
            logger.debug("Raised NegativeRollMeasurements exception, sides = %s", self.sides)
            raise NegativeRollMeasurements(f"Cannot roll dice with negative number of sides: {self.sides}")
        if (self.number < 0):
            logger.debug("Raised NegativeRollMeasurements exception, number of dice = %s", self.number)
            raise NegativeRollMeasurements(f"Cannot roll negative number of dice: {self.number}")
        self.rolls = self.__default_argument(rolls, [])
        self.dropped_rolls = self.__default_argument(dropped_rolls, [])
        self.additional_rolls = self.__default_argument(additional_rolls, [])
        self.sum = self.__default_argument(sum, self.__roll_dice())
        logger.debug("Initialized RolledDice(number=%s, sides=%s, rolls=%s, dropped_rolls=%s, additional_rolls=%s, sum=%s) instance", self.number, self.sides, self.rolls, self.dropped_rolls, self.additional_rolls, self.sum)

    def __repr__(self):
        return f"RolledDice({self.number}, " + repr(self.sides) + f", {self.rolls}, {self.dropped_rolls}, {self.additional_rolls}, {self.sum})"

    def __str__(self):
        return f"{self.number}d{self.sides}({self.sum})"

    def __roll_dice(self):
        self.rolls.append([])
        self.dropped_rolls.append([])
        self.additional_rolls.append([])
        sum = 0
        for i in range(0, self.number):
            if self.sides == "F":
                roll = random.randint(-1, 1)
            else:
                roll = random.randint(1, self.sides)
            self.rolls[-1].append(roll)
        for roll in self.rolls[-1]:
            sum += roll
        return sum

    def __default_argument(self, arg, default):
        if arg:
            return arg
        else:
            return default

    def __operators(operator):
        def _add_lists(me, other):
            if(isinstance(other, RolledDice)):
                me.rolls += other.rolls
                me.dropped_rolls += other.dropped_rolls
                me.additional_rolls += other.additional_rolls

        def forward(me, other):
            if(isinstance(other, Real)):
                me.sum = operator(me.sum, other)
                return me
            elif(isinstance(other, RolledDice)):
                me.sum = operator(me.sum, other.sum)
                _add_lists(me, other)
                return me
            else:
                return NotImplemented
        forward.__name__ = '__' + operator.__name__ + '__'
        forward.__doc__ = f"Implementation of operator {operator} for RolledDice class"

        def reverse(me, other):
            if(isinstance(other, Real)):
                me.sum = operator(other, me.sum)
                return me
            else:
                return NotImplemented
        reverse.__name__ = '__' + operator.__name__ + '__'
        reverse.__doc__ = f"Implementation of reverse operator {operator} for RolledDice class"
        return forward, reverse

    def __int__(self):
        return int(self.sum)

    def __float__(self):
        return float(self.sum)

    def __round__(self, ndigits=0):
        self.sum = round(self.sum, ndigits)
        return self

    def __abs__(self, ndigits=0):
        self.sum = abs(self.sum)
        return self

    def __floor__(self):
        self.sum = math.floor(self.sum)
        return self

    def __ceil__(self):
        self.sum = math.ceil(self.sum)
        return self

    __add__, __radd__ = __operators(operator.add)
    __sub__, __rsub__ = __operators(operator.sub)
    __mul__, __rmul__ = __operators(operator.mul)
    __truediv__, __rtruediv__ = __operators(operator.truediv)
    __mod__, __rmod__ = __operators(operator.mod)
    __pow__, __rpow__ = __operators(operator.pow)


def keep(roll, number, highest=True):
    logger.debug("Trying to keep %s highest (%s) rolls for %s", int(number), highest, roll)
    if (type(roll) != RolledDice):
        logger.debug("Raised KeepValueError for value '%s', not a roll", roll)
        raise KeepValueError(f"Cannot keep/drop something that is not a roll: {roll}")
    else:
        number = int(number)
        if ((0 > number) or (number > len(roll.rolls[-1]))):
            logger.debug("Raised KeepValueError for trying to keep (%s) rolls out of (%s)", number, len(roll.rolls[0]))
            raise KeepValueError(f"Number of dice to keep/drop ({number}) has to be positive and less than number of rolls ({len(roll.rolls[0])})")
        else:
            logger.debug("Rolls before dropping: %s", roll.rolls)
            to_remove = roll.rolls[-1]
            print(f"number = {number}, len = {len(roll.rolls[-1])}")
            to_remove.sort()
            if highest:
                to_remove = to_remove[:len(roll.rolls[-1]) - number]
            else:
                to_remove = to_remove[number:]
            for element in to_remove:
                roll.dropped_rolls[-1].append(element)
                roll.rolls[-1].remove(element)
                roll.sum -= element
            logger.debug("Rolls after dropping: %s", roll.rolls)
        logger.debug("Result of keeping: %s", roll)
        return roll


def keep_highest(roll, number):
    return keep(roll, number, highest=True)


def keep_lowest(roll, number):
    return keep(roll, number, highest=False)


def drop_highest(roll, number):
    return keep(roll, len(roll.rolls[0]) - number, highest=False)


def drop_lowest(roll, number):
    return keep(roll, len(roll.rolls[0]) - number, highest=True)


class Operator:
    def __init__(self, function, priority=0, operands=2):
        assert((operands == 1) or (operands == 2))
        self.operands = operands
        self.priority = priority
        self.function = function
        if (operands == 1):
            self.operation = self.__unary
        else:
            self.operation = self.__binary

    def __unary(self, arg):
        if ((self.function) == str(self.function)):
            return eval(self.function)
        else:
            return self.function(arg)

    def __binary(self, left, right):
        if ((self.function) == str(self.function)):
            return eval(self.function)
        else:
            return self.function(left, right)


class ExpressionEvaluation:
    '''Shunting Yard algorithm'''
    def __init__(self, expression):
        logger.info("Initializing evaluation of expression '%s'", expression)
        self.functions = {"floor": math.floor,
                          "ceil": math.ceil,
                          "abs": abs,
                          "round": round }

        self.operators = {"+": Operator(operator.add, priority=1, operands=2),
                          "-": Operator(operator.sub, priority=1, operands=2),
                          "*": Operator(operator.mul, priority=2, operands=2),
                          "/": Operator(operator.truediv, priority=2, operands=2),
                          "%": Operator(operator.mod, priority=2, operands=2),
                          "^": Operator(operator.pow, priority=3, operands=2),
                          "d": Operator(RolledDice, priority=5, operands=2),
                          "_": Operator(operator.neg, priority=10, operands=1) }

        self.roll_modifiers = {"kh": Operator(keep_highest, priority=4, operands=2),
                               "kl": Operator(keep_lowest, priority=4, operands=2),
                               "dh": Operator(drop_highest, priority=4, operands=2),
                               "dl": Operator(drop_lowest, priority=4, operands=2) }

        for oper in self.roll_modifiers:
            self.operators[oper] = self.roll_modifiers[oper]
        self.result = None
        seconds_to_timeout = 1
        try:
            self.result = round(timeout.evaluate(seconds_to_timeout, self.__evaluate, expression), 3)
            logger.info("The result of evaluation: %s", self.result)
            # self.result = round(self.__evaluate(expression), 3)
            if isinstance(self.result, RolledDice):
                logger.info("Rolls made: %s", self.result.rolls)
                logger.info("Rolls dropped: %s", self.result.dropped_rolls)
                logger.info("Additional rolls made: %s", self.result.additional_rolls)
            # self.result = float(self.result)
            # if self.result == int(self.result):
            #     self.result = int(self.result)
        except Exception as e:
            logger.warning("Raised exception %r for expression '%s'", e, expression)
            raise e

    def __is_operand(self, token):
        try:
            if token == "F":
                return True
            float(token)
            return True
        except ValueError:
            return False

    def __peek(self, stack):
        return stack[-1] if stack else None

    def __apply_operator(self, operators, values):
        oper = operators.pop()
        if (self.__peek(values) is None):
            logger.debug(f"Raised StackIsEmpty exception for values while applying operator '{oper}', stack: {values}")
            raise StackIsEmpty(oper)
        right = values.pop()
        if oper not in self.operators:
            logger.critical("Trying to apply unknown operator '%s'", oper)
            raise ValueError(f"Unknown operator: {oper}")
        if self.operators[oper].operands == 2:
            if (self.__peek(values) is None):
                logger.debug(f"Raised StackIsEmpty exception for values while applying operator '{oper}', stack: {values}")
                raise StackIsEmpty(oper)
            left = values.pop()
            logger.debug("Applying operator '%s' to values (%s, %s)", oper, left, right)
            values.append(self.operators[oper].operation(left, right))
        elif self.operators[oper].operands == 1:
            logger.debug("Applying operator '%s' to value %s", oper, right)
            values.append(self.operators[oper].operation(right))
        else:
            logger.critical("Raised ValueError exception for operator %s with %s operands", oper, oper.operands)
            raise ValueError(f"The operator {oper} had {oper.operands} operands")

    def __apply_function(self, operators, values):
        function = operators.pop()
        arg = values.pop()
        logger.debug("Applying function '%s' to argument %s", function, arg)
        values.append(self.functions[function](arg))

    def __greater_precedence(self, op1, op2):
        return self.operators[op1].priority > self.operators[op2].priority

    def __preprocess_expression(self, expression):
        expression = re.compile("\s").sub("", expression)
        expression = re.compile("\*\*").sub("^", expression)
        expression = re.compile("(?![a-zA-Z])(.)k(?=[0-9(])").sub(r"\1kh", expression)
        expression = re.compile("d%").sub("d100", expression)
        expression = re.compile("((?=[^)0-9F]).|\A)\-").sub(r"\1_", expression)
        # TODO: Legality checks!
        logger.debug("Preprocessed expression: %s", expression)
        return expression

    def __divide_expression(self, expression):
        func_tokens, op_tokens, tokens = '(', '', []
        for function in self.functions:
            func_tokens += function + '|'
        func_tokens = func_tokens[:-1] + ')'
        func_tokens = re.split(func_tokens, expression)
        for oper in self.operators:
            if oper in '.^$*+?{}[]|-\\':
                oper = '\\' + str(oper)
            if oper == "d":
                oper = "d(?![hl])"
            op_tokens += oper + "|"
        op_tokens = op_tokens[:-1]
        for token in func_tokens:
            if token not in self.functions:
                token = re.split("(" + op_tokens + "|\(|\))", token)
            if (isinstance(token, list)):
                tokens += token
            else:
                tokens.append(token)
        for token in tokens:
            if not token:
                tokens.remove(token)
        logger.debug("Divided expression: %s", tokens)
        return tokens

    def __evaluate(self, expression):
        expression = self.__preprocess_expression(expression)
        tokens = self.__divide_expression(expression)
        values, operators = deque(), deque()
        for token in tokens:
            if self.__is_operand(token):
                try:
                    values.append(float(token))
                except ValueError:
                    values.append(token)
                logger.debug("Added token '%s' to value stack: %s", token, values)
            elif token in self.functions:
                operators.append(token)
                logger.debug("Added function '%s' to operator stack: %s", token, operators)
            elif token == '(':
                operators.append(token)
                logger.debug("Added '%s' to stack: %s", token, operators)
            elif token == ')':
                logger.debug("Found the closing bracket. Operator stack is %s", operators)
                top = self.__peek(operators)
                while top is not None and top != '(':
                    self.__apply_operator(operators, values)
                    top = self.__peek(operators)
                if top is None:
                    logger.debug("There was a mismatched closing bracket. Raised MismatchedBrackets exception")
                    raise MismatchedBrackets
                else:
                    operators.pop()  # Discard the '('
                    logger.debug("Discarded opening bracket")
                    if self.__peek(operators) in self.functions:
                        self.__apply_function(operators, values)
                logger.debug("Finished closing bracket handling. Values: %s, Operators: %s", values, operators)
            elif token in self.operators:  # Operator or roll modifier
                logger.debug("Met an operator: '%s'", token)
                top = self.__peek(operators)
                while top is not None and top not in "()" and self.__greater_precedence(top, token):
                    self.__apply_operator(operators, values)
                    top = self.__peek(operators)
                operators.append(token)
                logger.debug("Added operator '%s' to operator stack: %s", token, operators)
            else:
                logger.debug("Raised UnknownSymbol('%s') exception", token)
                raise UnknownSymbol(token)
        while self.__peek(operators) is not None:
            if self.__peek(operators) == '(':
                logger.debug("There was a mismatched opening bracket. Raised MismatchedBrackets exception")
                raise MismatchedBrackets
            else:
                self.__apply_operator(operators, values)
        return values[0]


def main():
    expression = input("Enter expression:\n")
    print(f"Answer: {ExpressionEvaluation(expression).result}")


if (__name__ == "__main__"):
    main()
