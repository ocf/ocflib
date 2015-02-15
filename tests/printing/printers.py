#!/usr/bin/env python3
import ocflib.printing.printers as printers

if __name__ == '__main__':
    for printer in printers.PRINTERS:
        print(printer)
        print("\ttoner: {}".format(printers.get_toner(printer)))
        print("\tmaint kit: {}".format(printers.get_maintkit(printer)))
