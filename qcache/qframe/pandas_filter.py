from __future__ import unicode_literals

from qcache.qframe import COMPARISON_OPERATORS, JOINING_OPERATORS
from qcache.qframe.common import assert_list, raise_malformed, is_quoted, unquote, assert_len


def _leaf_node(df, q):
    if isinstance(q, basestring):
        if is_quoted(q):
            return q[1:-1].encode('utf-8')

        try:
            return df[q]
        except KeyError:
            raise_malformed("Unknown column", q)

    return q


def _bitwise_filter(df, q):
    assert_len(q, 3)
    op, column, arg = q
    if not isinstance(arg, (int, long)):
        raise_malformed('Invalid argument type, must be an integer:'.format(t=type(arg)), q)

    try:
        series = df[column] & arg
        if op == "any_bits":
            return series > 0
        return series == arg
    except TypeError:
        raise_malformed("Invalid column type, must be an integer", q)


def _not_filter(df, q):
    assert_len(q, 2, "! is a single arity operator, invalid number of arguments")
    return ~_do_pandas_filter(df, q[1])


def _isnull_filter(df, q):
    assert_len(q, 2, "isnull is a single arity operator, invalid number of arguments")

    # Slightly hacky but the only way I've come up with so far.
    return df[q[1]] != df[q[1]]


def _comparison_filter(df, q):
    assert_len(q, 3)
    op, col_name, arg = q
    return COMPARISON_OPERATORS[op](df[col_name], _do_pandas_filter(df, arg))


def _join_filter(df, q):
    result = None
    if len(q) < 2:
        raise_malformed("Invalid number of arguments", q)
    elif len(q) == 2:
        # Conjunctions and disjunctions with only one clause are OK
        result = _do_pandas_filter(df, q[1])
    else:
        result = reduce(lambda l, r: JOINING_OPERATORS[q[0]](l, _do_pandas_filter(df, r)),
                        q[2:], _do_pandas_filter(df, q[1]))

    return result


def _in_filter(df, q):
    assert_len(q, 3)
    _, col_name, args = q

    if not isinstance(args, list):
        raise_malformed("Second argument must be a list", q)

    return df[col_name].isin(args)


def _like_filter(df, q):
    assert_len(q, 3)
    op, column, raw_expr = q

    if not is_quoted(raw_expr):
        raise_malformed("like expects a quoted string as second argument", q)

    regexp = unquote(raw_expr)

    if not regexp.startswith('%'):
        regexp = '^' + regexp
    else:
        regexp = regexp[1:]

    if not regexp.endswith('%'):
        regexp += '$'
    else:
        regexp = regexp[:-1]

    # 'like' is case sensitive, 'ilike' is case insensitive
    case = op == 'like'

    try:
        return df[column].str.contains(regexp, case=case)
    except AttributeError:
        raise_malformed("Invalid column type for (i)like", q)


def _do_pandas_filter(df, q):
    if not isinstance(q, list):
        return _leaf_node(df, q)

    if not q:
        raise_malformed("Empty expression not allowed", q)

    result = None
    op = q[0]
    try:
        if op in ('any_bits', 'all_bits'):
            result = _bitwise_filter(df, q)
        elif op == "!":
            result = _not_filter(df, q)
        elif op == "isnull":
            result = _isnull_filter(df, q)
        elif op in COMPARISON_OPERATORS:
            result = _comparison_filter(df, q)
        elif op in JOINING_OPERATORS:
            result = _join_filter(df, q)
        elif op == 'in':
            result = _in_filter(df, q)
        elif op in ('like', 'ilike'):
            result = _like_filter(df, q)
        else:
            raise_malformed("Unknown operator", q)
    except KeyError:
        raise_malformed("Column is not defined", q)
    except TypeError:
        raise_malformed("Invalid type in argument", q)

    return result


def pandas_filter(df, filter_q):
    if filter_q:
        assert_list('where', filter_q)
        return df[_do_pandas_filter(df, filter_q)]

    return df
