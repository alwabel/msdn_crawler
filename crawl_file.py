#!/usr/bin/env python
import sys
from parser import *
import os

def main():
    if len(sys.argv) < 2:
        print >> sys.stderr, "Please provide the right arguments"
        sys.exit(1)
    src = sys.argv[1]
    for r,d,f in os.walk(src):
        for file in f:
            parser = ParseMSDN("https://www.microsoft.com")
            handler = open(os.path.join(r,file),"r")
            parser.feed( handler.read() )
            if parser.isCode:
                module = parser.dll.lower()
                if module.find(".dll") != -1:
                    module=module[:module.find(".dll")]
                else: module = "None"
                msg = ""
                msg += "{} {} {}.{}".format(parser.ret,parser.conv,module,parser.name)
                msg += "("
                for i,a in enumerate(parser.arguments):
                    if i>0:
                        msg += ","
                    msg += "{}".format(a)
                msg +=")\n"

                for v in parser.var:
                    msg += "{} {} {}.{}".format(parser.ret,parser.conv,module,v)
                    msg += "("
                    for i,a in enumerate(parser.arguments):
                        if i>0:
                            msg += ","
                        msg += "{}".format(a)
                    msg += ")\n"
                    
                sys.stdout.write(msg)
            parser.close()
                 

if __name__ == "__main__":
    main()

