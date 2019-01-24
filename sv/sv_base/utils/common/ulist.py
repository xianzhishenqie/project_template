

def convert_item(stype, item):
    return stype(item)


def typefilter(slist, stype, strict=False):
    rlist = []
    for item in slist:
        if item is not None:
            try:
                rlist.append(convert_item(stype, item))
            except Exception as e:
                if strict:
                    raise e
                else:
                    continue
    return rlist


def areafilter(slist, sarea, strict=False):
    stype = type(sarea[0])
    rlist = typefilter(slist, stype, strict)
    return list(set(sarea) & set(rlist))


def listfilter(slist, param, strict=False):
    if isinstance(param, (tuple, list, set)):
        return areafilter(slist, param, strict)

    return typefilter(slist, param, strict)


def valuefilter(value, param, strict=False):
    ret = listfilter([value], param, strict)
    if ret:
        return ret[0]
    return None

