class Enum:
    def __init__(self, **source):
        self.__dict__ = source

    @property
    def source(self):
        return self.__dict__

    @property
    def reverse_source(self):
        reverse_dict = {}
        try:
            for k, v in self.source.items():
                reverse_dict[v] = k
        except:
            pass
        return reverse_dict

    def keys(self):
        return self.source.keys()

    def values(self):
        return self.source.values()

    def update(self, **source):
        self.__dict__.update(source)


class SVEnum:
    se = Enum()

    def __new__(cls, **kwargs):
        cls.se.update(**kwargs)
        return Enum(**kwargs)

se = SVEnum.se
