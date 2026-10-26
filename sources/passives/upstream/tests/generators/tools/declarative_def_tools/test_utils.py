from generators.tools.footprint.declarative_def_tools.utils import DotDict


def test_as_list():
    from generators.tools.footprint.declarative_def_tools.utils import as_list

    assert ["foo"] == as_list("foo")
    assert ["foo"] == as_list(["foo"])
    assert [42] == as_list(42)
    assert [] == as_list([])
    assert [42] == as_list([42])
    assert [42] == as_list((42,))
    assert [42] == as_list({42})
    assert [None] == as_list(None)


def test_dotdict():
    original = dict(
        {
            "a0": 1,
            "b0": [1, 2],
            "c0": 3,
            "d0": {
                "a1": 11,
                "b1": [11, 12],
                "c1": 13,
                "d1": {
                    "a2": 21,
                    "b2": [21, 22],
                    "c2": 23,
                },
            },
        }
    )
    dotdict = DotDict(original)
    dotdict_sybling = dotdict
    dict_copy = DotDict(original.copy())
    dotdict_copy = dotdict.copy()
    assert original == dotdict
    dotdict.a0 = "changed"
    assert 1 == original["a0"]
    assert dotdict == dotdict_sybling
    assert original == dict_copy
    assert original == dotdict_copy
    dotdict.d0.a1 = "changed"
    assert 11 == original["d0"]["a1"]
    assert dotdict == dotdict_sybling
    assert original == dict_copy
    assert original == dotdict_copy
    dotdict_sybling.d0.d1 = DotDict({"changed": True})
    assert True == dotdict_sybling.d0.d1.changed
    assert dotdict == dotdict_sybling
    assert original == dict_copy
    assert original == dotdict_copy

    # modify the list
    dotdict.b0[0] = "changed"
    assert 1 == original["b0"][0]
    assert dotdict == dotdict_sybling
    assert original == dict_copy
    assert original == dotdict_copy


def test_dotdict_assign():
    dotdict = DotDict()
    expct = DotDict()

    dotdict.assign("a0", 1)
    expct.a0 = 1
    assert expct == dotdict

    dotdict.assign("b0[0]", 1)
    expct.b0 = [1]
    assert expct == dotdict

    dotdict.assign("b0[3]", 3)
    expct.b0 += [None, None, 3]
    assert expct == dotdict

    dotdict.assign("c0.c1[0]['hallo']", "hallo")
    expct.c0 = DotDict(c1=[DotDict(hallo="hallo")])
    assert expct == dotdict

    dotdict.assign("c0.c1[0][0].c2", 3)
    expct.c0.c1[0][0] = DotDict(c2=3)
    assert expct == dotdict

    dotdict.assign("c0['c1'][0][0]['d2']", "d2")
    expct.c0.c1[0][0].d2 = "d2"
    assert expct == dotdict
