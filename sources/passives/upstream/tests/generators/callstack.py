import inspect


def __get_frame__(lvl: int = 0) -> inspect.Traceback:
    # inspired by https://stackoverflow.com/questions/6810999/how-to-determine-file-function-and-line-number
    callerframerecord = inspect.stack()[
        1 + lvl
    ]  # 0 represents this line, 1 represents line at caller
    frame = callerframerecord[0]
    info = inspect.getframeinfo(frame)
    return info


def __format_frame__(frame: inspect.Traceback):
    return f"{frame.filename}:{frame.lineno} func<{frame.function}>"


class __frame_meta__(type):

    def __repr__(self):
        return self.__call__(1)

    def __str__(self):
        return self.__call__(1)

    def __call__(self, lvl: int = 0):
        return __format_frame__(__get_frame__(lvl + self.__frame_offset__ + 1))


class __frame__(metaclass=__frame_meta__):
    """
    Returns the current call location when called as:
    >>> __frame__()

    If you want to return the call location down the call-stack, use
    >>> __frame__(offset)
    """

    __frame_offset__ = 0


class __caller_frame__(metaclass=__frame_meta__):
    """
    Returns the location of the parent call-stack when called as:
    >>> __caller_frame__()
    """

    __frame_offset__ = 1


__current_frame__ = __frame__
