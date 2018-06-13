from numbers import Real
from collections import deque
import operator
import random
import math
import re
import logging
import functools

# import timeout

logging.basicConfig(format="%(levelname)-8s (%(asctime)s) %(message)s", level=logging.INFO, datefmt="%d.%m.%y, %H:%M:%S")
logger = logging.getLogger(__name__)


class UnknownSymbol(Exception):
    '''There was a symbol or function in the expression that the algorithm doesn't support'''


class StackIsEmpty(Exception):
    '''There was an attempt to pop from empty stack'''


class NegativeRollMeasurements(Exception):
    '''The user tried to roll a die with negative side count or negative number of dice'''


class KeepValueError(Exception):
    '''The number of dice to keep was wrong'''


class RerollValueError(Exception):
    '''The target number for reroll was wrong'''


class ExplodeValueError(Exception):
    '''The target number for exploding dice was wrong'''


class MismatchedBrackets(Exception):
    '''There was a mismatched bracket'''


class EmptyExpression(Exception):
    '''The expression given was empty'''


class RollModifierMisuse(Exception):
    '''The user tried to apply roll modifier to something that is not a roll'''


class IncorrectArgumentCount(Exception):
    '''Wrong number of arguments passed to the operator'''


class RolledDice:
    '''Class that simulates a dice roll and holds all the information about it to allow arithmetics'''
    def __init__(self, number, sides):
        logger.debug("Created %s(number=%s, sides=%s) instance", type(self).__name__, number, sides)
        self.rolls, self.dropped_rolls, self.additional_rolls = [], [], []
        if (isinstance(number, RolledDice)):
            self.rolls += number.rolls
            self.dropped_rolls += number.dropped_rolls
            self.additional_rolls += number.additional_rolls
        self.__number = round(number)
        if (isinstance(sides, RolledDice)):
            self.rolls += sides.rolls
            self.dropped_rolls += sides.dropped_rolls
            self.additional_rolls += sides.additional_rolls
        self.__sides = sides
        if self.sides != "F":
            self.__sides = round(sides)
        if (self.sides != "F" and self.sides < 0):
            logger.debug("Raised NegativeRollMeasurements exception, sides = %s", self.sides)
            raise NegativeRollMeasurements(f"Cannot roll dice with negative number of sides: {self.sides}")
        if (self.number < 0):
            logger.debug("Raised NegativeRollMeasurements exception, number of dice = %s", self.number)
            raise NegativeRollMeasurements(f"Cannot roll negative number of dice: {self.number}")
        self.sum = self._roll_dice()
        self.finished = False
        logger.debug("Initialized %s(number=%s, sides=%s, rolls=%s, sum=%s) instance", type(self).__name__, self.number, self.sides, self.rolls, self.sum)

    @property
    def number(self):
        return self.__number

    @property
    def sides(self):
        return self.__sides

#    def __repr__(self):
#        return f"{type(self).__name__}({self.number}, " + repr(self.sides) + f", {self.rolls}, {self.dropped_rolls}, {self.additional_rolls}, {self.sum})"

    def __str__(self):
        return f"{self.number}d{self.sides}({self.sum})"

    def _roll_dice(self):
        self.rolls.append([])
        self.dropped_rolls.append([])
        self.additional_rolls.append([])
        if self.sides == "F":
            self.rolls[-1] = [random.randint(-1, 1) for i in range(self.number)]
        else:
            self.rolls[-1] = [random.randint(1, self.sides) for i in range(self.number)]
        result = sum(self.rolls[-1])
        return result

    def _operators(oper):
        def _add_lists(me, other):
            if(isinstance(other, RolledDice)):
                me.rolls += other.rolls
                me.dropped_rolls += other.dropped_rolls
                me.additional_rolls += other.additional_rolls

        def forward(me, other):
            if(isinstance(other, Real)):
                me.sum = oper(me.sum, other)
                return me
            elif(isinstance(other, RolledDice)):
                me.sum = oper(me.sum, other.sum)
                _add_lists(me, other)
                return me
            else:
                return NotImplemented
        forward.__name__ = '__' + oper.__name__ + '__'
        forward.__doc__ = f"Implementation of operator {oper} for RolledDice class"

        def reverse(me, other):
            if(isinstance(other, Real)):
                me.sum = oper(other, me.sum)
                return me
            else:
                return NotImplemented
        reverse.__name__ = '__' + oper.__name__ + '__'
        reverse.__doc__ = f"Implementation of reverse operator {oper} for RolledDice class"
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

    __add__, __radd__ = _operators(operator.add)
    __sub__, __rsub__ = _operators(operator.sub)
    __mul__, __rmul__ = _operators(operator.mul)
    __truediv__, __rtruediv__ = _operators(operator.truediv)
    __mod__, __rmod__ = _operators(operator.mod)
    __pow__, __rpow__ = _operators(operator.pow)

    @staticmethod
    def keep(roll, number, *, highest=True):
        logger.debug("Trying to keep %s highest (%s) rolls for %s", int(number), highest, roll)
        try:
            number = int(number)
        except ValueError:
            logger.debug("Raised KeepValueError: couldn't convert %s to int", number)
            raise KeepValueError(f"Number of dice to keep/drop ({number}) has to be a number")
        if ((0 > number) or (number > len(roll.rolls[-1]))):
            logger.debug("Raised KeepValueError for trying to keep (%s) rolls out of (%s)", number, len(roll.rolls[0]))
            raise KeepValueError(f"Number of dice to keep/drop ({number}) has to be positive and less than number of rolls ({len(roll.rolls[0])})")
        else:
            logger.debug("Rolls before dropping: %s", roll.rolls)
            to_remove = roll.rolls[-1]
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

    @staticmethod
    def reroll(roll, target, *, relation, once=False):
        def reroll_die(sides):
            if sides == "F":
                return random.randint(-1, 1)
            else:
                return random.randint(1, sides)

        logger.debug("Rerolling all dice in %s that are %s%s, once (%s)", roll, relation, target, once)
        try:
            target = int(target)
        except ValueError:
            logger.debug("Raised RerollValueError: couldn't convert %s to int", target)
            raise RerollValueError(f"Number of dice to reroll ({str(target)}) has to be a number")
        logger.debug("Rolls before rerolling: %s", roll.rolls)
        relations = {">": operator.gt, "<": operator.lt, "=": operator.eq}
        new_rolls = []
        for value in roll.rolls[-1]:
            while relations[relation](value, target):
                value = reroll_die(roll.sides)
                if once is True:
                    break
            new_rolls.append(value)
        roll.rolls[-1] = new_rolls
        logger.debug("Rolls after rerolling: %s\nResult of reroll: %s", roll.rolls[-1], roll)
        return roll

    @staticmethod
    def explode(roll, target, *, relation, special=None):
        def roll_die(sides):
            if sides == "F":
                return random.randint(-1, 1)
            else:
                return random.randint(1, sides)

        logger.debug("Exploding dice for %s, target is %s%s, special modifier is %s", roll, relation, target, special)
        try:
            if target != "F":
                target = int(target)
        except ValueError:
            logger.debug("Raised ExplodeValueError: couldn't convert %s to int", target)
            raise ExplodeValueError(f"Target number for exploding dice ({str(target)}) has to be a number (or 'F' for Fate dice)")
        logger.debug("Rolls before exploding: %s", roll.rolls)
        relations = {">": operator.gt, "<": operator.lt, "=": operator.eq}
        for value in roll.rolls[-1]:
            if relations[relation](value, target):
                roll.rolls[-1].append(roll_die(roll.sides))
        logger.debug("Rolls after exploding: %s\nResult of exploding: %s", roll.rolls[-1], roll)
        return roll


keep_highest = functools.partial(RolledDice.keep, highest=True)
keep_lowest = functools.partial(RolledDice.keep, highest=False)

reroll_equal = functools.partial(RolledDice.reroll, relation="=", once=False)
reroll_more = functools.partial(RolledDice.reroll, relation=">", once=False)
reroll_less = functools.partial(RolledDice.reroll, relation="<", once=False)
reroll_once_equal = functools.partial(RolledDice.reroll, relation="=", once=True)
reroll_once_more = functools.partial(RolledDice.reroll, relation=">", once=True)
reroll_once_less = functools.partial(RolledDice.reroll, relation="<", once=True)
explode_equal = functools.partial(RolledDice.explode, relation="=")
explode_more = functools.partial(RolledDice.explode, relation=">")
explode_less = functools.partial(RolledDice.explode, relation="<")


def drop_highest(roll, number):
    return keep_lowest(roll, len(roll.rolls[0]) - number)


def drop_lowest(roll, number):
    return keep_highest(roll, len(roll.rolls[0]) - number)


def explode(roll):
    return RolledDice.explode(roll, roll.sides, relation="=")


class Operator:
    def __init__(self, function, priority=0, operands=2):
        self.operands = operands
        self.priority = priority
        self.function = function

    def operation(self, args):
        if len(tuple(args)) != self.operands:
            logger.error("Incorrect argument count for operator '%s': %s", self.function, tuple(args))
            raise IncorrectArgumentCount(f"Operation: {self.operation}, arguments: {tuple(args)}")
        return self.function(*args)


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

        self.roll_modifiers = {"k": Operator(keep_highest, priority=4, operands=2),
                               "kh": Operator(keep_highest, priority=4, operands=2),
                               "kl": Operator(keep_lowest, priority=4, operands=2),
                               "dh": Operator(drop_highest, priority=4, operands=2),
                               "dl": Operator(drop_lowest, priority=4, operands=2),
                               "r": Operator(reroll_equal, priority=4, operands=2),
                               "r=": Operator(reroll_equal, priority=4, operands=2),
                               "r>": Operator(reroll_more, priority=4, operands=2),
                               "r<": Operator(reroll_less, priority=4, operands=2),
                               "ro": Operator(reroll_once_equal, priority=4, operands=2),
                               "ro=": Operator(reroll_once_equal, priority=4, operands=2),
                               "ro>": Operator(reroll_once_more, priority=4, operands=2),
                               "ro<": Operator(reroll_once_less, priority=4, operands=2),
                               "!": Operator(explode, priority=4, operands=1),
                               "!=": Operator(explode_equal, priority=4, operands=2),
                               "!>": Operator(explode_more, priority=4, operands=2),
                               "!<": Operator(explode_less, priority=4, operands=2), }

        for oper in self.roll_modifiers:
            self.operators[oper] = self.roll_modifiers[oper]
        self.result = None
        # seconds_to_timeout = 1
        try:
            # self.result = timeout.evaluate(seconds_to_timeout, self._evaluate, expression)
            self.result = self._evaluate(expression)
            logger.info("The result of evaluation: %s", self.result)
            if isinstance(self.result, RolledDice):
                logger.info("Rolls made: %s", self.result.rolls)
                if self.result.dropped_rolls != [[]]:
                    logger.info("Rolls dropped: %s", self.result.dropped_rolls)
                if self.result.additional_rolls != [[]]:
                    logger.info("Additional rolls made: %s", self.result.additional_rolls)
        except Exception as e:
            logger.info("Raised exception %r for expression '%s'", e, expression)
            raise e

    def _is_operand(self, token):
        if token == "F":
            return True
        try:
            float(token)
            return True
        except ValueError:
            return False

    def _peek(self, stack):
        return stack[-1] if stack else None

    def _roll_modifier_legality(self, oper, value):
        if oper in self.roll_modifiers:
            if not isinstance(value, RolledDice) or value.finished is True:
                logger.debug("Raised RollModifierMisuse exception while applying roll modifier '%s' to non-roll value '%s'", oper, value)
                raise RollModifierMisuse(f"Tried to apply roll modifier to something that is not a roll: {value}")
        elif isinstance(value, RolledDice):
            value.finished = True
            logger.debug("Changed 'finished' attribute of %s to %s", value, value.finished)

    def _apply_operator(self, operators, values):
        oper = operators.pop()
        if oper not in self.operators:
            logger.error("Trying to apply unknown operator '%s'", oper)
            raise ValueError(f"Unknown operator: {oper}")
        args = []
        for i in range(self.operators[oper].operands):
            if (self._peek(values) is None):
                logger.debug("Raised StackIsEmpty exception for values while applying operator '%s', stack: %s", oper, values)
                raise StackIsEmpty(oper)
            args.append(values.pop())
        self._roll_modifier_legality(oper, args[-1])
        args.reverse()
        logger.debug("Applying operator '%s' to values %s", oper, args)
        values.append(self.operators[oper].operation(args))

    def _apply_function(self, operators, values):
        function = operators.pop()
        arg = values.pop()
        logger.debug("Applying function '%s' to argument %s", function, arg)
        values.append(self.functions[function](arg))

    def _greater_precedence(self, op1, op2):
        return self.operators[op1].priority >= self.operators[op2].priority

    def _preprocess_expression(self, expression):
        expression = re.compile("\s").sub("", expression)
        expression = re.compile("\*\*").sub("^", expression)
        expression = re.compile("d%").sub("d100", expression)
        expression = re.compile("((?=[^)0-9F]).|\A)\-").sub(r"\1_", expression)  # Change unary minus to _
        logger.debug("Preprocessed expression: %s", expression)
        return expression

    def _divide_expression(self, expression):
        func_tokens, op_tokens, tokens = '(', '(', []
        for function in self.functions:
            func_tokens += function + '|'
        func_tokens = func_tokens[:-1] + ')'
        func_tokens = re.split(func_tokens, expression)
        for oper in self.operators:
            if oper in '.^$*+?{}[]|-\\':
                oper = '\\' + str(oper)
            elif oper == "d":
                oper = "d(?=[0-9(F])"
            elif oper == "!":
                oper = "!(?![!><=p])"
            else:
                for oper2 in self.operators:
                    if oper in oper2 and oper != oper2 and self.operators[oper].operands > 1:
                        oper = oper + "(?=[0-9(])"
            op_tokens += oper + "|"
        op_tokens = op_tokens[:-1] + "|\(|\))"
        for token in func_tokens:
            if token not in self.functions:
                token = re.split(op_tokens, token)
            if (isinstance(token, list)):
                tokens += [tok for tok in token if tok]
            else:
                tokens.append(token)
        logger.debug("Divided expression: %s", tokens)
        return tokens

    def _evaluate(self, expression):
        expression = self._preprocess_expression(expression)
        tokens = self._divide_expression(expression)
        values, operators = deque(), deque()
        if not tokens:
            raise EmptyExpression
        for token in tokens:
            if self._is_operand(token):
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
                top = self._peek(operators)
                while top is not None and top != '(':
                    self._apply_operator(operators, values)
                    top = self._peek(operators)
                if top is None:
                    logger.debug("There was a mismatched closing bracket. Raised MismatchedBrackets exception")
                    raise MismatchedBrackets
                else:
                    operators.pop()  # Discard the '('
                    logger.debug("Discarded opening bracket")
                    if self._peek(operators) in self.functions:
                        self._apply_function(operators, values)
                logger.debug("Finished closing bracket handling. Values: %s, Operators: %s", values, operators)
            elif token in self.operators:
                logger.debug("Met an operator: '%s'", token)
                top = self._peek(operators)
                while top is not None and top not in "()" and self._greater_precedence(top, token):
                    self._apply_operator(operators, values)
                    top = self._peek(operators)
                operators.append(token)
                logger.debug("Added operator '%s' to operator stack: %s", token, operators)
            else:
                logger.debug("Raised UnknownSymbol('%s') exception", token)
                raise UnknownSymbol(token)
        while self._peek(operators) is not None:
            if self._peek(operators) == '(':
                logger.debug("There was a mismatched opening bracket. Raised MismatchedBrackets exception")
                raise MismatchedBrackets
            else:
                self._apply_operator(operators, values)
        return values[0]


def main():
    expression = input("Enter expression:\n")
    print(f"Answer: {ExpressionEvaluation(expression).result}")


if (__name__ == "__main__"):
    main()
