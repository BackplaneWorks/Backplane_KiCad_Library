# generators is free software: you can redistribute it and/or modify it under the terms
# of the GNU General Public License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.
#
# generators is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# generators. If not, see < http://www.gnu.org/licenses/ >.
#
# (C) 2024 by Armin Schoisswohl (@armin.sch), <armin.schoisswohl@myotis.at>
# (C) The KiCad Librarian Team


import re
import warnings

from typing import Any, Iterable, Optional, TypedDict, Set, SupportsFloat
from asteval import Interpreter, make_symbol_table

from generators.tools.footprint.declarative_def_tools.utils import DotDict


class ASTresult:
    def __init__(self, value: Any, final: bool=True) -> None:
        self._value = value
        self._final = final

    @property
    def value(self):
        return self._value

    @property
    def final(self):
        return self._final

    def __call__(self):
        return self._value

    def __repr__(self):
        return str(f"{self.__class__.__name__}(value={self.value}, final={self.final})")


class ASTevaluator(object):
    """
    The ASTevaluator is a wrapper around a Python ASTeval interpreter that evaluates
    expressions of the form $(...) which are contained in strings nested Python
    objects (e.g., dictionaries, lists, sets, tuples).

    The typical use case for this class is to evaluate expressions contained
    in the object read in from a YAML file, allowing to embed pieces of Python
    code inside the YAML expressions to be dynamically evaluated at run-time.

    Examples:
        >>> from generators.tools.footprint.declarative_def_tools.ast_evaluator import ASTevaluator
        >>> ast = ASTevaluator()
        >>> dct = {"value": "$(sqrt(2))", "text": "$('%.2f' % value)"}
        >>> processed = ast.eval(dct)
        >>> print(processed)
        {'value': 1.4142135623730951, 'text': '1.41'}
        >>>


    For examples look at the unit test of the ASTevaluator.

    For details of the ASTeval interpreter see: https://docs.python.org/3/library/ast
    """


    """
    
        Args:
        expr: the string containing the expressions to evaluate enclsoed in $(...)
        sym_name: the interpreter used for evaluation (defaults to a minimal ASTeval interpreter).

    Returns:
        the evaluated string, if possible as the native evaluated Python data type if possible, else as a string.

    The expressions are evaluated using the given ASTeval interpreter.
    To escape from evaluation if you want to get the literal string '$(', use '$!('.

    See Also:
        https://newville.github.io/asteval/index.html

    """

    __verify_cache__: bool = False  # if set to True, then each cache access is compared to the symbol table

    def __init__(self, *,
                 self_update: Optional[bool] = True,
                 protected: Optional[bool] = True,
                 max_depth: Optional[int] = -1,
                 symbols: Optional[TypedDict] = None,
                 restricted: Optional[bool] = True):
        """
        Contructs the ASTevaluator object.

        Args:
            self_update:
                if set to True (default), then any evaluation will also update the interpreters symbol table.

            protected:
                if set to True (default), then any symbols which are passed as the 'symbol' argument will
                be protected from being overwritten the interpreters symbol table.

            max_depth:
                specifies the maximum recursion depth for evaluation of nested structures (dicts, lists, sets).
                If set to a negative number (default: -1), then there is no limit.

            symbols:
                any members of the dictionary passed as the 'symbol' argument are available to the interpreters
                symbol table in all evaluations (even after calling 'reset()').

            restricted:
                if set to True (default), then the calls to open() and numpy's load() and loadtxt() methods will
                be removed from the interpreters symbol table.

        """
        object.__init__(self)
        self.max_depth = max_depth
        self.self_update = self_update
        self.protected = protected
        self._eval_errors = dict()
        self._evaluated_syms = dict()
        self._num_eval_calls = 0
        self._num_cache_hits = 0
        self._symbols = set()
        self._default_sym_names = set()
        self._warn = True
        # create the symbol table for the ASTeval interpreter
        self._base_symbols = DotDict()
        if (symbols):
            all_symbols = DotDict(symbols)
            self._base_symbols.update(all_symbols)
        self._user_symbols = DotDict()
        self._restricted_symbols = set()
        if (restricted):
            self._restricted_symbols.add("open")
            self._restricted_symbols.add("load")
            self._restricted_symbols.add("loadtxt")
        self._interpreter = None

    def __call__(self, *args, **kwargs):
        """Calling the object itself will invoke the eval method."""
        return self.eval(*args, **kwargs)

    def eval(self, element: Any,
             sym_name: Optional[str] = None, *,
             max_depth: Optional[int] = None,
             self_update: Optional[bool] = True,
             persistent: Optional[bool] = False,
             allow_self_ref: Optional[bool] = False,
             self_ref_prefix: Optional[str] = None,
             allow_nested: Optional[bool] = False,
             try_resolve: Optional[bool] = True,
             skip: Optional[Iterable[str]] = None,
             ignore_cache: Optional[bool] = False,
             raise_errors: Optional[bool] = True,
             show_errors: Optional[bool] = True,
             suppress_warnings: Optional[bool] = False,
             symbols: Optional[TypedDict] = None):
        """
        Evaluate a string by replacing all expressions enclosed in $(...) with the value of the expression itself.

        Args:
            element:
                the element to be evaluated; this can be a string, a dictionary, an iterable (e.g., list, tuple)
                or a scalar object (like int, float, bool). Any entries which are strings containing an expressions
                enclosed in '$(<expression>)' will be evaluated.

            sym_name:
                the (optional) symbol name of the element to be evaluated.

            max_depth:
                maximum evaluation depth; controls how deep to recurse into hierarchic structures like nested
                dictionaries or lists. Defaults to -1, which means no limit.

            self_update:
                if set to True (default), then any symbol which is evaluated is also updating the interpreters
                symbol table (not just the cache). I.e., it can be referenced in expressions to be evaluated.

            persistent:
                if set to False (default), then the interpreter's symbol table will be reset to it's initial
                state (i.e., it's state when starting the evaluation) and it's cache will be cleared at the
                end of the evaluation; otherwise, both, symbol table an cache, will persist and my be used in
                successive evaluations.

                To reset the interpreter to its default state (i.e., it's state at the time of construction),
                use reset().

            allow_self_ref:
                when set to True (default: False), then the element to be evaluated itself is accessible in
                the interpreter's symbol table:

                - if self_ref_prefix is specified, then it can be accessed as 'self_ref_prefix', else
                - if sym_name is specified, then it can be accessed as 'sym_name', else
                - if the element is a dictionary all its members can be accessed by their keys.

                Note: any symbols that get accessible through the settings of allow_self_ref, self_ref_prefix, and
                    sym_name are automatically invalidated in the interpreters cache.

            self_ref_prefix:
                the name under which the element is accessible (if allow_self_ref is True).

            allow_nested:
                this flag (default: False) is used to allow nested evaliations, i.e., in case an $(...) expression
                evaluates to a string, which itself contains a $(...) expression, it will be evaluated again until
                it resolves.

            try_resolve:
                this flag (default: True) controls if dictionary should be tried to be resolved by iterating, allowing
                not only backward but also forward references.

            skip:
                any string or regular expression contained in this list is considered as a symbol name which is
                not evaluated but just kept as is. This allows, e.g., to prevent parts of a dictionary from being
                evaluated.

                Note: Symbol names referencing into dictionaries allow dot-notation.

            ignore_cache:
                if this flag is set to True (default: False), then the interpreters cache is ignored and all
                expressions and symbols are re-evaluated; this may lead to unexpected behavior as, e.g., escaped
                expressions '$!(...)', which are evaluated to '$(...)' may be re-evaluated.

            raise_errors:
                if this flag is set to False (default: True), then errors will be raised.

            show_errors:
                if this flag is set to True (default: False), then errors of the ASTeval interpreter will be displayed.

            suppress_warnings:
                if this flag is set to True (default: False), then warnings will be suppressed.

            symbols:
                any dictionary passed as 'symbols' will be made available to the interpreter as read-only symbols
                allowing dot-notation evaluation.

        Returns:
            the evaluated element, where all appearances of $(<expr>) in any string contained in any leaf of the
            element's symbol tree are replaced by the result of <expr>.

        Note: To escape from evaluation if you want to get the literal string '$(', use '$!('.

        Dictionaries can also be accessed by dot-notation, e.g., dct.name is equivalent to dct["name"].

        Examples:
            >>> dct = {"value": "$(sqrt(2))", "text": "$('%.2f' % value)"}
            >>> ast_eval = ASTevaluator()
            >>> ast_eval.eval(dct)

        See Also:
            https://newville.github.io/asteval/index.html
        """

        self._suppress_warnings = suppress_warnings

        if (max_depth is None):
            max_depth = self.max_depth

        # convert entry to DotDict to allow both, dictionary and dot notation
        if (isinstance(element, DotDict)):
            element = element.copy()
        elif (isinstance(element, dict)):
            element = DotDict(element)

        # assemble additional symbols
        new_symbols = DotDict()
        if (symbols):
            new_symbols.update(DotDict(symbols))

        self_ref_roots = set()
        if (allow_self_ref):
            if (isinstance(element, DotDict)):
                if (self_ref_prefix):
                    new_symbols[self_ref_prefix] = element
                    self_ref_roots.add(self_ref_prefix)
                else:
                    new_symbols.update(element)
                    self_ref_roots = set(element.keys())
            if (sym_name):
                new_symbols[sym_name] = element
                self_ref_roots.add(sym_name)

        self.__create_interpreter__(symbols=new_symbols, dirty_symbols=self_ref_roots)

        for name, value in new_symbols.items():
            if (name in self._interpreter.readonly_symbols):
                raise NameError(f"Symbol '{name}' is a read-only symbol in the asteval symbol table")
            self._interpreter.symtable[name] = value

        # prepare the skip-list; entries staring with '^' and ending with '$' are considered regex expressions
        if (skip is not None):
            if (isinstance(skip, str)):
                skip = [skip]
            skip_dct = DotDict(names=set(), regex=set())
            for pat in skip:
                if (re.match(r"^\^.+\$$", pat)):
                    skip_dct.regex.add(re.compile(pat))
                else:
                    skip_dct.names.add(pat)
        else:
            skip_dct = None

        # prepare arguments to pass for recursive calls to eval
        eval_args = {
            'max_depth': max_depth,
            'self_update': self_update,
            'skip': skip_dct,
            'ignore_cache': ignore_cache,
            'allow_nested': allow_nested,
            'try_resolve': try_resolve,
        }

        # clear evaluation errors
        self._eval_errors.clear()

        # perform the actual evaluation
        result = self._eval(element, sym_name, **eval_args)

        assert(hasattr(result, 'final'))

        # restore saved symbol table
        self.__destroy_interpreter__(persistent=persistent)

        # raise an error in case there have been errors
        if (len(self._eval_errors) != 0):
            for key, (expr, excp) in self._eval_errors.items():
                self.warn(f"{excp.__class__.__name__} in definition of attribute '{key}': {expr}", Warning)
            msg = f"failed to resolve {len(self._eval_errors)} expression(s): {', '.join(self._eval_errors.keys())}"
            self.warn(msg, Warning)
            if (raise_errors):
                raise ValueError(msg)

        if (not result.final):
            self.warn(f"nested evaluation of '{sym_name}' is not completely resolved", Warning)

        self._suppress_warnings = False

        return result.value

    def _eval(self, element, /, sym_name: str = None, *, call_depth: int = 0, **eval_args):
        """Main evaluation routine, called by 'eval()'."""

        if (element is None):
            return ASTresult(None)

        self._num_eval_calls += 1

        allow_nested = eval_args.get('allow_nested', False)
        self_update = eval_args.get('self_update', True)
        # check if we have a cached result, if yes, then return it
        if (not eval_args.get('ignore_cache', False) and sym_name in self._evaluated_syms):
            self._num_cache_hits += 1
            result = self._evaluated_syms[sym_name]
            if (self.__verify_cache__ and self_update):
                eval_result = self._interpreter.eval(sym_name)
                if (result.value != eval_result):
                    raise LookupError(f"cached result for symbol '{sym_name}' is corrupted")
            if (not result.final):
                raise LookupError(f"cached result for symbol '{sym_name}' is not final")
            return result

        if (0 <= eval_args.get('max_depth', -1) < call_depth):
            return ASTresult(element, False)

        if (sym_name and (skip_dct := eval_args.get('skip', None))):
            if (sym_name in skip_dct.names):
                return ASTresult(element, False)
            else:
                for pat in skip_dct.regex:
                    if (pat.match(sym_name)):
                        return ASTresult(element, False)

        if (self_update and sym_name and not self.is_known_symname(sym_name)):
            self._set_symbol(sym_name, element, create=True, overwrite=False)

        try:
            if (isinstance(element, str)):
                result = self._eval_str(element, sym_name, allow_nested=allow_nested)
            elif (isinstance(element, dict)):
                result = self._eval_dict(element, sym_name, call_depth=call_depth + 1, **eval_args)
            elif (isinstance(element, Iterable)):
                result = self._eval_iterable(element, sym_name, call_depth=call_depth + 1, **eval_args)
            elif (isinstance(element, (bool, int, float))):
                result = ASTresult(element)
            else:
                raise TypeError(f"Unsupported entry '{sym_name}' of type {type(element)}")

            if (sym_name and result != element):
                if (result.final):
                    self._evaluated_syms[sym_name] = result
                if (self_update):
                    self._set_symbol(sym_name, result.value)

            if (sym_name in self._eval_errors):
                del self._eval_errors[sym_name]
        except KeyboardInterrupt:
            raise
        except Exception as e:
            self._eval_errors[sym_name] = (element, e)
            return ASTresult(element, final=False)

        return result

    def _eval_str(self, expr: str, sym_name: str = None, *, allow_nested: bool = False) -> Any:
        """Low-level evaluator for a string; eventually contained $(<expr>) are replaced by the value of <expr>."""

        if (expr is None):
            return ASTresult(None)

        if (not isinstance(expr, str)):
            raise TypeError(f'{expr} is not a string')

        # shortcut if there is no need for evaluation at all
        if ("$(" not in expr):
            return ASTresult(expr.replace("$!(", "$("))

        result = None

        # parse the given string into a structure for evaluation
        try:
            parsed = __parse_and_split_expr__(expr)
        except KeyboardInterrupt:
            raise
        except Exception as e:
            raise SyntaxError(f"Could not parse '{sym_name}' expression '{expr}'")

        final = True

        while (True):
            if (parsed.start):
                result = ("" if (result is None) else str(result)) + str(parsed.start)
            if (parsed.expr):
                value = self._interpreter(parsed.expr, raise_errors=True, show_errors=False)
                if (value is not None):
                    if (__may_need_eval__(value)):
                        match = re.match(r"^\((['\"])(?P<expr>.+)\1\)$", parsed.expr)
                        if (not match or match["expr"] != value):
                            if (allow_nested):
                                final = False
                    result = value if (result is None) else str(result) + str(value)
            if (isinstance(parsed.end, DotDict)):
                parsed = parsed.end
                continue
            if (parsed.end):
                result = parsed.end if (result is None) else str(result) + str(parsed.end)
            break

        return ASTresult(result, final=final)

    def _eval_dict(self, dictionary: dict, sym_name: str = "", *, try_resolve: Optional[bool] = True, **eval_args):
        """Low-level evaluator for a dictionary."""
        dict_copy = DotDict(dictionary)

        # process the dictionary
        changed = True
        final = False
        num_loops = 0
        while (not final and changed):
            changed = False
            final = True
            num_loops += 1

            for key, value in dict_copy.items():

                if (isinstance(key, str) and re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*", key)):
                    full_name = f"{sym_name}.{key}" if (sym_name) else key
                else:
                    full_name = f"{sym_name}[{key}]" if (sym_name) else None

                result = self._eval(value, full_name, **eval_args)
                final = final and result.final

                if (result.value != value):
                    dict_copy[key] = result.value
                    changed = True

            if (try_resolve and not final):
                continue

            if (not final and not try_resolve):
                self.warn(f"dictionary '{sym_name}' could not be resolved and 'try_resolve=False'", Warning)
                break

        return ASTresult(dict_copy, final=final)

    def _eval_iterable(self, iterable: Iterable, sym_name, **eval_args):
        """Low-level evaluator for iterable objects."""
        values = []
        final = True
        for n, v in enumerate(iterable):
            result = self._eval(v, f"{sym_name}[{n}]" if (sym_name) else None, **eval_args)
            values.append(result.value)
            final = final and result.final

        result = type(iterable)(values)

        return ASTresult(result, final=final)

    def _set_symbol(self, full_name, value, *, create: bool = True, overwrite: bool = True, raise_errors: bool = True):
        """Assign a symbol value in the interpreters symbol table. Eventually creates the required DotDict structure(s)."""

        try:
            DotDict.assign_in(self._interpreter.symtable, full_name, value, create=create, assign=overwrite)
        except KeyboardInterrupt:
            raise
        except (NameError, KeyError) as e:
            err_msg = f"failed to set symbol '{full_name}' in the interpreter's symbol table"
            self.warn(err_msg, Warning)
            if (raise_errors):
                raise NameError(err_msg)
        except Exception as e:
            raise e

    def __create_interpreter__(self, *, symbols: Optional[DotDict] = None, dirty_symbols: Optional[Set] = None):
        """Create the AST evaluator from the saved symbol and cache tables."""
        if (self._interpreter is not None):
            raise RuntimeError("Interpreter already exists; cannot create. You have to run __destroy_interpreter__ before")

        symtable = make_symbol_table(nested=True)
        if (self._restricted_symbols):
            for sym in self._restricted_symbols:
                if (sym in symtable):
                    symtable.pop(sym)
        self._default_sym_names = set(symtable.keys())

        for sym, val in self._base_symbols.items():
            if (self.protected and sym in symtable):
                raise NameError(f"Symbol '{sym}' is protected in the asteval symbol table")
            symtable[sym] = val
        base_sym_names = set(symtable.keys())

        # create interpreter object
        self._interpreter = Interpreter(symtable=symtable,
                                        readonly_symbols=base_sym_names if (self.protected) else None,
                                        builtins_readonly=True,
                                        nested_symtable=True,
                                        minimal=True,
                                        with_ifexp=True,
                                        with_listcomp=True,
                                        with_dictcomp=True,
                                        with_setcomp=True)

        for dct in [ self._user_symbols, symbols ]:
            if (dct):
                for name, value in dct.items():
                    if (name in self._interpreter.readonly_symbols):
                        raise NameError(f"Symbol '{name}' is a read-only symbol in the asteval symbol table")
                    if (self.protected and name in base_sym_names):
                        raise NameError(f"Symbol '{name}' is a protected symbol in the asteval basic symbol table")
                    if (isinstance(value, dict)):
                        self._interpreter.symtable[name] = DotDict(value)
                    elif (hasattr(value, 'copy')):
                        self._interpreter.symtable[name] = value.copy()
                    else:
                        self._interpreter.symtable[name] = value

        if (dirty_symbols):
            for key in set(self._evaluated_syms.keys()):
                if (key.split('.', maxsplit=1)[0] in dirty_symbols):
                    self._evaluated_syms.pop(key)

    def __destroy_interpreter__(self, persistent: bool = False):
        """Destroy the AST evaluator and update symbol and cache tables."""
        if (self._interpreter and persistent):
            for key in set(self._interpreter.symtable.keys()):
                if (key in self._base_symbols):
                    self._base_symbols[key] = self._interpreter.symtable[key]
                elif (key not in self._interpreter.readonly_symbols):
                    self._user_symbols[key] = self._interpreter.symtable[key]
                else:
                    self._interpreter.symtable.pop(key)
            # refresh the cache
            for name in set(self._evaluated_syms.keys()):
                if (not self.is_known_symname(name)):
                    self._evaluated_syms.pop(name)
        else:
            # clear cache
            self._evaluated_syms.clear()

        self._interpreter = None

    def reset(self):
        """Reset the interpreter to its initial state after construction."""
        self._user_symbols.clear()
        self.clear_cache()
        self.clear_stats()

    def is_known_symname(self, sym_name: str):
        """Check if sym_name is a valid name in the interpreter's symbol table"""
        var_name = sym_name.split('.', maxsplit=1)[0].split('[', maxsplit=1)[0]
        if var_name not in self._interpreter.symtable:
            return False
        else:
            try:
                self._interpreter.eval(sym_name, raise_errors=True, show_errors=False)
            except KeyboardInterrupt:
                raise
            except Exception as e:
                return False
        return True

    @property
    def cache_stats(self):
        """Show statistics about the cache hits."""
        return f"Evaluation calls: {self._num_eval_calls}, cache hits: {self._num_cache_hits} ({100 if (self._num_eval_calls == 0) else (100 * self._num_cache_hits / self._num_eval_calls):.2f}%)"

    def clear_stats(self):
        """Clear statistics about the cache hits."""
        self._num_cache_hits = 0
        self._num_eval_calls = 0

    def clear_cache(self):
        """Manually clear the interpreter's cache; use with caution!"""
        self._evaluated_syms.clear()

    def show_errors(self):
        """Show errors of the last evaluation"""
        print("\n".join(self._eval_errors))

    def parse_float(self, expr, *, symbols = None, **kwargs):
        if (isinstance(expr, SupportsFloat)):
            return float(expr)
        elif (not __may_need_eval__(expr)):
            return self.parse_float(f"$({expr})", symbols=symbols, **kwargs)
        else:
            return float(self.eval(expr, self_update=False, allow_self_ref=False, symbols=symbols))

    def warn(self, msg, warn_type=Warning):
        if (not self._suppress_warnings):
            warnings.warn(f"\n{msg}", warn_type, stacklevel=2)


class ASTexprEvaluator:
    """
    ASTexprEvaluator is a simple AST evaluator which evaluates strings as expressions and returns everything else.
    """
    def __init__(self, *, symbols: Optional[dict] = None, protected: Optional[bool] = True):
        """
        Args:
            symbols: A dictionary with symbol names and values which may be used in the expressions to evaluate.
            protected: If set to True, then all symbols from the default interpreter symbol table are protected
                and must not be overwritten by entries in 'symbols'.
        """
        symtable = make_symbol_table(nested=True)
        base_sym_names = symtable.keys()
        if (symbols is not None):
            symbols = DotDict(symbols)
            for key, val in symbols.items():
                if (protected and key in symtable):
                    raise NameError(f"Symbol '{key}' is protected in the evaluator's symbol table")
                symtable[key] = val

        self._interpreter = Interpreter(symtable=symtable,
                                        readonly_symbols=base_sym_names if (protected) else None,
                                        builtins_readonly=True,
                                        nested_symtable=True,
                                        minimal=True,
                                        with_ifexp=True,
                                        with_listcomp=True,
                                        with_dictcomp=True,
                                        with_setcomp=True)

    def eval(self, expr, *, show_errors=False, raise_errors=True):
        """Evaluate an 'expr' if it is a string, otherwise just return expr."""
        if (isinstance(expr, str)):
            return self._interpreter.eval(expr, show_errors=show_errors, raise_errors=raise_errors)
        else:
            return expr

    def __call__(self, *args, **kwargs):
        """Call invokes eval()"""
        return self.eval(*args, **kwargs)


def __parse_and_split_expr__(expr: str) -> DotDict:
    """
    Parse an expression and extract all appearances of $(...).

    Args:
        expr: the string to parse

    Returns:
        a DotDict object which contains
        - start: the text preceding the first appearance of $(...)
        - expr: the expression enclosed between '$(' and ')', where the parentheses are matched for valid pairs
        - end: the text (or Dotdict) following the first appearance of $(...)
    """
    start_re = re.compile(r"^(?P<start>.*?)(?P<dollar>\$)(?P<esc>\!?)(?P<paren>\(?)(?P<end>.*)$")
    close_re = re.compile(r"^(?P<expr>(.*?\)))(?P<end>.*)$")
    result = DotDict(start="", expr="", end=expr)
    num_paren = 0
    while (match := start_re.match(result.end)):
        result.start += match["start"]
        result.end = match["end"]
        if (match["esc"] or not match["paren"]):
            result.start += match["dollar"] + match["paren"]
            continue
        else:
            result.expr = match["paren"]
            num_paren = 1
            break
    while (num_paren):
        if (match := close_re.match(result.end)):
            result.expr += match["expr"]
            result.end = match["end"]
            num_paren += match["expr"].count('(') - match["expr"].count(')')
        else:
            raise LookupError(f"failed to locate closing ')' in '{expr}'")
    if (result.end and result.end != expr):
        result.end = __parse_and_split_expr__(result.end)
    return result

def __may_need_eval__(expr: Any) -> bool:
    """Checks if the expression may need to be evaluated."""
    return isinstance(expr, str) and "$(" in expr


if __name__ == "__main__":
    ast = ASTevaluator()
    dct = { "value": "$(sqrt(2))", "text": "$('%.2f' % value)" }
    processed = ast.eval(dct)
    print(processed)
