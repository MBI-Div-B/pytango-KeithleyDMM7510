from .KeithleyDMM7510 import KeithleyDMM7510


def main():
    import sys
    import tango.server

    args = ["KeithleyDMM7510"] + sys.argv[1:]
    tango.server.run((KeithleyDMM7510,), args=args)
