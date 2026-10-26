import math
import os
import re

import pytest

from generators.tools.footprint.declarative_def_tools.ast_evaluator import (
    ASTevaluator,
    ASTexprEvaluator,
)
from generators.tools.footprint.declarative_def_tools.utils import DotDict
from tests.generators.callstack import __caller_frame__


class CustomException(AssertionError):
    pass


class TestASTevaluator:

    __num_pos__ = 17
    failureException = CustomException

    @pytest.fixture(autouse=True)
    def setup_fixtures(self, request):
        """Automatically injects `ast` into the class."""

        request.cls.ast = ASTevaluator(symbols=dict(num_pos=self.__num_pos__))

    def test_unallowed(self):
        import pathlib
        import tempfile

        filename = pathlib.Path(tempfile.mktemp()).as_posix()

        r_stmt = f"$(1 if open('{filename}') else 0)"
        w_stmt = f"$(1 if open('{filename}', 'w') else 0)"
        a_stmt = f"$(1 if open('{filename}', 'a') else 0)"

        ast = self.ast
        weak_ast = ASTevaluator(restricted=False)

        open(filename, "w")
        assert 1 == weak_ast.eval(r_stmt)
        pytest.raises(Exception, ast.eval, r_stmt, suppress_warnings=True)
        pytest.raises(Exception, weak_ast.eval, w_stmt, suppress_warnings=True)
        pytest.raises(Exception, ast.eval, w_stmt, suppress_warnings=True)
        pytest.raises(Exception, weak_ast.eval, a_stmt, suppress_warnings=True)
        pytest.raises(Exception, ast.eval, a_stmt, suppress_warnings=True)
        # make sure opening a file without read permissions fails
        os.chmod(filename, 0)
        if not os.access(filename, os.R_OK):
            pytest.raises(Exception, weak_ast.eval, r_stmt, suppress_warnings=True)
        pytest.raises(Exception, ast.eval, r_stmt, suppress_warnings=True)
        os.chmod(filename, 0o600)
        os.remove(filename)

        pytest.raises(Exception, weak_ast.eval, r_stmt, suppress_warnings=True)
        pytest.raises(Exception, ast.eval, r_stmt, suppress_warnings=True)
        pytest.raises(Exception, weak_ast.eval, w_stmt, suppress_warnings=True)
        pytest.raises(Exception, ast.eval, w_stmt, suppress_warnings=True)
        pytest.raises(Exception, weak_ast.eval, a_stmt, suppress_warnings=True)
        pytest.raises(Exception, ast.eval, a_stmt, suppress_warnings=True)

    def test_eval_str(self):
        from math import cos, radians, sin

        ast = self.ast
        assert (
            ast.eval(
                "hallo $(1 - (2 - 3) - (2 - 1) + (0)), das ist der zweite $('string')"
            )
            == "hallo 1, das ist der zweite string"
        )
        assert ast.eval("$(1 - (2 - 3) - (1 - 2) + (17))") == 20
        assert ast.eval("das ist ein $('string')") == "das ist ein string"
        assert ast.eval("hallo $(1 - (2 - 3) - (1 - 2))") == "hallo 3"
        assert ast.eval("hallo ((as") == "hallo ((as"
        assert ast.eval("$(sin(radians(30)))") == sin(radians(30))
        assert ast.eval("$( [sin(radians(30)), cos(radians(30))] )") == [
            sin(radians(30)),
            cos(radians(30)),
        ]
        assert ast.eval("$(1+1) +") == "2 +"
        assert ast.eval("$(1+1) $!") == "2 $"
        assert ast.eval("$(1+1)$") == "2$"
        assert ast.eval("$(1+1))") == "2)"
        assert ast.eval("($(1+1)(") == "(2("
        assert ast.eval("$(1+1)$!(a$!$(2+2)") == "2$(a$4"
        assert ast.eval("$( ())") == ()
        assert ast.eval("$") == "$"

    def __check_dict(self, expected_dct: DotDict, dct: dict, *, location) -> int:
        num_checked = 0
        for key, value in dct.items():
            if isinstance(value, dict):
                num_checked += self.__check_dict(expected_dct, value, location=location)
            elif expct := expected_dct[key]:
                num_checked += 1
                msg = f"{location}: YAML line {expct.line}: {key}: {expct.expr}"
                assert expct.value == value, msg

        return num_checked

    def __compare_dict_to_yaml(self, dct: DotDict, yaml: str, *, overrides: dict = {}):
        expected_dct = DotDict()
        regex = re.compile(
            r"\s*(?P<key>\w+)\s*:\s*(?P<expr>.*?)\s*(#\s*(?P<expct>.+?))?\s*$"
        )
        num_checks = 0
        for num, txt in enumerate(yaml.splitlines()):
            if match := regex.match(txt):
                key = match.group("key")
                expr = match.group("expr")
                expct = match.group("expct")
                expct = (
                    overrides[key]
                    if (key in overrides)
                    else eval(expct) if (expct) else None
                )
                if expct:
                    expected_dct[key] = DotDict(
                        {"expr": expr, "value": expct, "line": num + 1}
                    )
                    num_checks += 1
                else:
                    expected_dct[key] = None

        num_checked = self.__check_dict(expected_dct, dct, location=__caller_frame__())
        assert (
            num_checks == num_checked
        ), f"{__caller_frame__()}: {num_checks} checks expected, only {num_checked} done"

    def test_asteval_dict(self):

        yaml_spec = """
            defaults:
              v01_string: 'test'  # str("test")
              v02_bool:   True    # bool(True)
              v03_float:  0.075   # float(0.075)
              v04_int:    17      # int(17)
              v05_dict:
                v06_selfref: $(v04_int)                 # int(17)
                v07_int_div: $(v04_int // 10)           # int(1)
                v08_escape:  $!(blabla % 10)$           # str("$(blabla % 10)$")
                v09_string:  $("a=%.5f" % v03_float)    # str("a=0.07500")
                v10_forwref: $(v05_dict.v11_math)       # str("$(sqrt(4))")
                v11_math:    $(sqrt(4))                 # float(2.0)
                v12_backref: $(v05_dict.v11_math)       # float(2.0)
                v13_string:  $(str("10"))               # str("10")
                v14_list:    [ $(1+2), $(17+4) ]        # [ int(3), int(21) ]
                v15_list:    $([ 1+2, 17+4 ])           # [ int(3), int(21) ]
                v16_tuple:   $(( 1, 2 ))                # ( int(1), int(2) )
                v17_tuple:   $(( 1+2, "17+4" ))         # ( int(3), str("17+4") )
                v18_string:  $("$(1+2)")                # str("$(1+2)")
                v19_string:  $!($(1+2)                  # str("$(3")
                v20_float:   $(pi)                      # float(3.141592653589793)
            """
        import yaml

        spec = yaml.safe_load(yaml_spec)

        self.ast.clear_stats()
        params1 = self.ast.eval(spec["defaults"], allow_self_ref=True)
        stats1 = self.ast.cache_stats
        self.__compare_dict_to_yaml(params1, yaml_spec)

        self.ast.clear_stats()
        params2 = self.ast.eval(spec["defaults"], allow_self_ref=True, persistent=True)
        stats2 = self.ast.cache_stats
        self.__compare_dict_to_yaml(params2, yaml_spec)

        self.ast.clear_stats()
        params3 = self.ast.eval(spec["defaults"], allow_self_ref=True, persistent=True)
        stats3 = self.ast.cache_stats
        self.__compare_dict_to_yaml(params3, yaml_spec)

        self.ast.clear_stats()
        params4 = self.ast.eval(spec["defaults"], persistent=True)
        stats4 = self.ast.cache_stats
        self.__compare_dict_to_yaml(params4, yaml_spec)

        self.ast.clear_stats()
        params5 = self.ast.eval(spec["defaults"])
        stats5 = self.ast.cache_stats
        self.__compare_dict_to_yaml(params5, yaml_spec)

        self.ast.clear_stats()
        self.ast.clear_cache()
        params6 = self.ast.eval(spec["defaults"])
        stats6 = self.ast.cache_stats
        self.__compare_dict_to_yaml(params6, yaml_spec, overrides={"v10_forwref": 2.0})

        self.ast.clear_stats()
        self.ast.reset()
        params7 = self.ast.eval(spec["defaults"], allow_self_ref=True)
        stats7 = self.ast.cache_stats
        self.__compare_dict_to_yaml(params7, yaml_spec)

        self.ast.reset()
        params8 = self.ast.eval(
            spec["defaults"], allow_self_ref=True, allow_nested=True
        )
        stats8 = self.ast.cache_stats
        self.__compare_dict_to_yaml(params8, yaml_spec, overrides={"v10_forwref": 2.0})

    def test_ast_evaluator_skip(self):
        self.ast.reset()
        dct = DotDict(
            {
                "a": "$(pi)",
                "aa": "$(pi)",
                "aaa": "$(pi)",
                "d": {"a": "$(pi)", "aa": "$(pi)", "aaa": "$(pi)"},
            }
        )
        expected = DotDict(
            {
                "a": math.pi,
                "aa": math.pi,
                "aaa": math.pi,
                "d": {"a": math.pi, "aa": math.pi, "aaa": math.pi},
            }
        )

        result = self.ast.eval(dct, allow_self_ref=True)
        assert expected == result

        result = self.ast.eval(
            dct, allow_self_ref=True, skip=["a"], suppress_warnings=True
        )
        expct = expected.copy()
        expct.a = dct.a
        assert expct == result

        result = self.ast.eval(
            dct, allow_self_ref=True, skip=["d.a"], suppress_warnings=True
        )
        expct = expected.copy()
        expct.d.a = dct.d.a
        assert expct == result

        result = self.ast.eval(
            dct, allow_self_ref=True, skip=[r"^(.+\.)?a$"], suppress_warnings=True
        )
        expct = expected.copy()
        expct.a = dct.a
        expct.d.a = dct.d.a
        assert expct == result

        result = self.ast.eval(
            dct, allow_self_ref=True, skip=["d"], suppress_warnings=True
        )
        expct = expected.copy()
        expct.d = dct.d.copy()
        assert expct == result

    def test_ast_evaluator_resolve(self):
        dct = {
            "a3": "$(b2 + 1)",
            "b2": "$(d1 + 1)",
            "c0": "$(1 - 1)",
            "d1": "$(c0 + 1)",
        }
        expct = {
            "a3": 3,
            "b2": 2,
            "c0": 0,
            "d1": 1,
        }
        result = self.ast.eval(dct, allow_self_ref=True, try_resolve=True)
        assert expct == result

        expct = dct.copy()
        expct.update(
            {
                "c0": 0,
                "d1": 1,
            }
        )
        result = self.ast.eval(
            dct,
            allow_self_ref=True,
            try_resolve=False,
            raise_errors=False,
            suppress_warnings=True,
        )
        assert expct == result

    def test_eval(self):
        # some tests which are assumed to call eval
        assert "test" == self.ast.eval("test")
        assert "1+1" == self.ast.eval("1+1")
        assert 2 == self.ast.eval("$(1+1)")
        # tests which just return the argument
        assert self.ast.eval(None) is None
        assert 2.2 == self.ast.eval(1.2 + 1)
        # tests containing containers
        assert [1, "1+1", 3] == self.ast.eval([1, "1+1", "$(1+2)"])
        assert (1, "1+1", 3) == self.ast.eval((1, "1+1", "$(1+2)"))
        assert {1, "1+1", 3} == self.ast.eval({1, "1+1", "$(1+2)"})
        assert [1, "1+1", 3, (10, "10+1", 12)] == self.ast.eval(
            [1, "1+1", "$(1+2)", (10, "10+1", "$(10+2)")]
        )
        assert {"a1": 1, "b1": {"a2": 2, "b2": {"a3": 3}}} == self.ast.eval(
            {"a1": "$(1)", "b1": {"a2": "$(a1 + 1)", "b2": {"a3": "$(a1 + b1.a2)"}}},
            allow_self_ref=True,
        )

    def test_eval_max_depth(self):
        # test that recursion depth can be controlled in containers
        input = ["$(1)", ["$(2)", ["$(3)", ["$(4)"]]]]
        expected = input.copy()
        assert expected == self.ast.eval(input, max_depth=0, suppress_warnings=True)
        expected[0] = 1
        assert expected == self.ast.eval(input, max_depth=1, suppress_warnings=True)
        expected[1][0] = 2
        assert expected == self.ast.eval(input, max_depth=2, suppress_warnings=True)
        expected[1][1][0] = 3
        assert expected == self.ast.eval(input, max_depth=3, suppress_warnings=True)
        expected[1][1][1][0] = 4
        assert expected == self.ast.eval(input, max_depth=4)
        # test that recursion depth can be controlled in containers
        input = DotDict(
            a="$(1)", b=DotDict(a="$(2)", b=DotDict(a="$(3)", b=DotDict(a="$(4)")))
        )
        expected = DotDict(input)
        assert expected == self.ast.eval(input, max_depth=0, suppress_warnings=True)
        expected.a = 1
        assert expected == self.ast.eval(input, max_depth=1, suppress_warnings=True)
        expected.b.a = 2
        assert expected == self.ast.eval(input, max_depth=2, suppress_warnings=True)
        expected.b.b.a = 3
        assert expected == self.ast.eval(input, max_depth=3, suppress_warnings=True)
        expected.b.b.b.a = 4
        assert expected == self.ast.eval(input, max_depth=4)

    def test_expr_evaluator(self):
        evaluate_expr = ASTexprEvaluator(symbols={"a": 1, "b": 2})

        assert 1 == evaluate_expr("a")
        assert 2 == evaluate_expr("b")
        assert "a" == evaluate_expr("'a'")
        assert 1 == evaluate_expr(1)
        assert math.sqrt(2) == evaluate_expr("sqrt(2)")
        assert 1 == evaluate_expr("1 if (sqrt(2) < 2) else 2")
        assert 2 == evaluate_expr("1 if (sqrt(2) > 2) else 2")
        assert [0, 1] == evaluate_expr("[n for n in range(2)]")
