"""Unit tests for MathEvaluator service."""

import pytest
from src.services.math_evaluator import MathEvaluator


@pytest.fixture
def evaluator():
    return MathEvaluator()


def test_basic_arithmetic(evaluator):
    assert evaluator.evaluate_expr("125 + 45") == 170
    assert evaluator.evaluate_expr("10 * 5 / 2") == 25
    assert evaluator.evaluate_expr("2 ^ 8") == 256
    assert evaluator.evaluate_expr("sqrt(16)") == 4


def test_variable_evaluation(evaluator):
    vars_dict = {"precio": 50, "cantidad": 3}
    assert evaluator.evaluate_expr("precio * cantidad", vars_dict) == 150


def test_process_note_text(evaluator):
    text = "precio = 50\ncantidad = 4\ntotal = precio * cantidad ="
    updated, modified = evaluator.process_note_text(text)
    assert modified is True
    assert "total = precio * cantidad = 200" in updated


def test_process_note_text_simple_equation(evaluator):
    text = "120 + 35 ="
    updated, modified = evaluator.process_note_text(text)
    assert modified is True
    assert "120 + 35 = 155" in updated
