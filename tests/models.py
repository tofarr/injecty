class Foo:
    priority: int = 100


class Bar(Foo):
    pass


class Zap(Foo):
    priority: int = 90


class Bang(Foo):
    priority: int = 110
