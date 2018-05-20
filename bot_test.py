import shuntingyard
import pytest

tested = shuntingyard.ExpressionEvaluation

class TestClass(object):
    '''Test class for Shunting Yard algorithm and dXRollBot'''
    def test_arithmetic(self):
        assert float(tested("(5 + 7.5 * (2**5 - 60/2))%2").result) == 0

    def test_arithmetic_2(self):
        result = tested("(2^3 + 2) % 4 / 3 + 7d13").result
        assert float(result) == 0.667 + sum(result.rolls[0])

    def test_arithmetic_3(self):
        assert float(tested("(5d1 + 3) / 2 ^ 2 + 0d0").result) == 2

    def test_arithmetic_4(self):
        result = tested("5d6 + 3d4 + 2d10 + 18d37").result
        roll_sum = 0
        for roll in result.rolls:
            roll_sum += sum(roll)
        assert float(result) == roll_sum

    def test_unary_minus(self):
        assert float(tested("-2 + 4d1").result) == 2

    def test_unary_minus_2(self):
        assert float(tested("4d1-(-2)").result) == 6

    def test_unary_minus_3(self):
        assert float(tested("4- -2").result) == 6

    def test_keep_rolls(self):
        assert float(tested("5d1k3").result) == 3

    def test_keep_high_rolls(self):
        assert float(tested("5d1kh3").result) == 3

    def test_keep_low_rolls(self):
        assert float(tested("5d1kl3").result) == 3

    def test_drop_high_rolls(self):
        assert float(tested("5d1dh3").result) == 2

    def test_drop_low_rolls(self):
        assert float(tested("5d1dl3").result) == 2

    def test_fate_dice(self):
        result = tested("(3d1 + 3 + 0d0) / 2 + 6dF").result
        assert float(result) == sum(result.rolls[2]) + 3

    def test_zero_division(self):
        with pytest.raises(ZeroDivisionError):
            tested("3/0d0")

    def test_unknown_symbol(self):
        with pytest.raises(shuntingyard.UnknownSymbol):
            tested("2d6 + abs(argh)")

    def test_empty_stack(self):
        with pytest.raises(shuntingyard.StackIsEmpty):
            tested("2d6+")
                
    def test_empty_stack_2(self):
        with pytest.raises(shuntingyard.StackIsEmpty):
            tested("-")

    def test_negative_roll_measurements(self):
        with pytest.raises(shuntingyard.NegativeRollMeasurements):
            tested("-2d6")

    def test_negative_roll_measurements_2(self):
        with pytest.raises(shuntingyard.NegativeRollMeasurements):
            tested("2d(2-3)")

    def test_keep_drop_error(self):
        with pytest.raises(shuntingyard.KeepValueError):
            tested("5kl2")

    def test_keep_drop_error_2(self):
        with pytest.raises(shuntingyard.KeepValueError):
            tested("2d6dl3")

    def test_keep_drop_error_3(self):
        with pytest.raises(shuntingyard.KeepValueError):
            tested("2d6k(2-3)")

    def test_mismatched_brackets(self):
        with pytest.raises(shuntingyard.MismatchedBrackets):
            tested("2d6+(3*(2-4)")

    def test_mismatched_brackets_2(self):
        with pytest.raises(shuntingyard.MismatchedBrackets):
            tested("2d6+(3*(2-4)))")

    def test_function_for_dice(self):
        result = tested("ceil(6dF + 0.5)").result
        assert float(result) == sum(result.rolls[0]) + 1

    def test_function_for_dice_2(self):
        result = tested("abs(8dF - 2)").result
        assert float(result) == abs(sum(result.rolls[0]) - 2)

    def test_function_for_dice_3(self):
        result = tested("round(6dF + 0.3)").result
        assert float(result) == sum(result.rolls[0])
