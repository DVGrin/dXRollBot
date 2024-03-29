import shuntingyard
import pytest

tested = shuntingyard.ExpressionEvaluation


class TestClass(object):
    '''Test class for Shunting Yard algorithm and dXRollBot'''
    def test_arithmetic(self):
        assert float(tested("(5 + 7.5 * (2**5 - 60/2))%2").result) == 0

    def test_arithmetic_2(self):
        result = tested("(2^3 + 2) % 4 / 3 + 7d13").result
        assert round(float(result), 3) == 0.667 + sum(result.rolls[0])

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
            tested("2d6 + round(roo)")

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
        with pytest.raises(shuntingyard.RollModifierMisuse):
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

    def test_roll_modifier_misuse(self):
        with pytest.raises(shuntingyard.RollModifierMisuse):
            tested("(3d6+2)k2")

    def test_reroll(self):
        result = tested("1000d6r5").result
        assert 5 not in result.rolls[0]

    def test_reroll_2(self):
        result = tested("1000d8r>5").result
        assert not [roll for roll in result.rolls[0] if roll > 5]

    def test_reroll_3(self):
        result = tested("1000d6r<3").result
        assert not [roll for roll in result.rolls[0] if roll < 3]

    def test_reroll_4(self):
        result = tested("1000dFr=-1").result
        assert -1 not in result.rolls[0]

    def test_exploding_dice(self):
        result = tested("1000d6!").result
        assert len(result.rolls[0]) == 1000 + len([x for x in result.rolls[0] if x == 6])

    def test_exploding_dice_2(self):
        result = tested("1000d6!=3").result
        assert len(result.rolls[0]) == 1000 + len([x for x in result.rolls[0] if x == 3])

    def test_exploding_dice_3(self):
        result = tested("1000d6!>4").result
        assert len(result.rolls[0]) == 1000 + len([x for x in result.rolls[0] if x > 4])

    def test_exploding_dice_4(self):
        result = tested("1000d6!< 3").result
        assert len(result.rolls[0]) == 1000 + len([x for x in result.rolls[0] if x < 3])

    def test_compounding_exploding_dice(self):
        result = tested("1000d6!!").result
        for x, y in zip([x for x in result.rolls[0]], [x for x in result.additional_rolls[0]]):
            if y > 0:
                assert x - y == 6

    def test_compounding_exploding_dice_2(self):
        result = tested("1000d6!!=3").result
        for x, y in zip([x for x in result.rolls[0]], [x for x in result.additional_rolls[0]]):
            if y > 0:
                assert x - y == 3

    def test_compounding_exploding_dice_3(self):
        result = tested("1000d6!!>4").result
        for x, y in zip([x for x in result.rolls[0]], [x for x in result.additional_rolls[0]]):
            if y > 0:
                assert x - y > 4

    def test_compounding_exploding_dice_4(self):
        result = tested("1000d6!!< 3").result
        for x, y in zip([x for x in result.rolls[0]], [x for x in result.additional_rolls[0]]):
            if y > 0:
                assert x - y < 3
