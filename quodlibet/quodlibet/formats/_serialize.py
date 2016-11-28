# -*- coding: utf-8 -*-
# Copyright 2016 Christoph Reiter
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation

"""Code for serializing AudioFile instances"""

import pickle

from quodlibet.util.picklehelper import pickle_loads, pickle_dumps
from ._audio import AudioFile


class SerializationError(Exception):
    pass


def load_audio_files(data):
    """unpickles the item list and if some class isn't found unpickle
    as a dict and filter them out afterwards.

    In case everything gets filtered out will raise SerializationError
    (because then likely something larger went wrong)

    Returns:
        List[AudioFile]
    Raises:
        SerializationError
    """

    dummy = type("dummy", (dict,), {})
    error_occured = []
    temp_type_cache = {}

    def lookup_func(base, module, name):
        try:
            real_type = base(module, name)
        except (ImportError, AttributeError):
            error_occured.append(True)
            return dummy

        if module.split(".")[0] not in ("quodlibet", "tests"):
            return real_type

        # return a straight dict subclass so that unpickle doesn't call
        # our __setitem__. Further down we simply change the __class__
        # to our real type.
        if not real_type in temp_type_cache:
            new_type = type(name, (dict,), {"real_type": real_type})
            temp_type_cache[real_type] = new_type

        return temp_type_cache[real_type]

    try:
        items = pickle_loads(data, lookup_func)
    except pickle.UnpicklingError as e:
        raise SerializationError(e)

    if error_occured:
        items = [i for i in items if not isinstance(i, dummy)]

        if not items:
            raise SerializationError(
                "all class lookups failed. something is wrong")

    try:
        for i in items:
            i.__class__ = i.real_type
    except AttributeError as e:
        raise SerializationError(e)

    return items


def dump_audio_files(item_list):
    """Pickles a list of AudioFiles

    Returns:
        bytes
    Raises:
        SerializationError
    """

    assert isinstance(item_list, list)
    assert not item_list or isinstance(item_list[0], AudioFile)

    try:
        return pickle_dumps(item_list, 2)
    except pickle.PicklingError as e:
        raise SerializationError(e)