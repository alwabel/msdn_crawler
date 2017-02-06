#!/usr/bin/env python
import HTMLParser
import urllib
import sys
from parser import *
import threading

class writer_wrapper(object):
    def __init__(self,dest=sys.stdout):
        self.lock = threading.Lock()
        if type(dest) == type(''):
            self.dest = open(dest,'w')
        else: self.dest = dest
    def write(self,msg):
        with self.lock:
            print >> self.dest,msg

    def close(self):
        with self.lock:
            self.dest.close()
class UrlPool(object):
    def __init__(self):
        self.lock =threading.Loc()
        self.urlpool = []
        self.urldone = {}
        self.urlworking = {}
    def next(self):
        with self.lock:
            if len(urlpool) ==0 and len(self.urlworking) == 0:
                raise StopIteration
            url = self.urlpool()
            self.urlworing[url] = 0
            return url
    def __iter__(self):
        return self
    def done(self,url):
        with self.lock:
            if url in self.urlworking:
                del self.urlworking[url]
                self.urldone[url]
    def add_url(self,url):
        with self.lock:
            if url not in self.urlworking and\
                url not in self.urldone:
                    self.urlpool.add(url)
class crawler:
    def __init__(self,seed,accepted_pattern):
        self.accepted=accepted_pattern
        self.fresh_links = set()
        self.visited_links = {}
        self.fresh_links.add(seed)
    def start(self,writer):
        while len(self.fresh_links) > 0:
            parser = ParseMSDN()
            url = self.fresh_links.pop()
            writer.write("visiting "+ url+"\n")
            parser.feed( urllib.urlopen(url).read())
            if parser.isCode:
                module = parser.dll.lower()
                if module.find(".dll") != -1:
                    module=module[:module.find(".dll")]
                    writer.write("{} {}.{}".format(parser.conv,module,parser.name))
                    writer.write("(")
                    for a in parser.arguments:
                       writer.write("{}".format(a))
                       writer.write(")")
                       writer.write(":{}\n".format(parser.ret))
                for v in parser.var:
                    writer.write("{}.{}:{}\n".format(module,v,parser.ret))

            parser.close()
            self.visited_links[url]=0

            for item in parser.links:
                if re.match(self.accepted,item) and \
                    item not in self.visited_links:
                    self.fresh_links.add(item)

import ConfigParser
def main():
    Config = ConfigParser.ConfigParser()
    Config.read("config")
    options = Config.options("parameters")
    for o in options:
        if o.upper() == "MAX_THREADS":
            MAX_THREADS = int(Config.get("parameters",o))
    '''
    parser = ParseMSDN()
    url="https://msdn.microsoft.com/en-us/library/windows/desktop/bg126469(v=vs.85).aspx"
    #url="https://msdn.microsoft.com/en-us/library/windows/desktop/dd239108(v=vs.85).aspx"
    parser.feed( urllib.urlopen(url).read())
    parser.close()
    #for item in parser.links:
    #    if re.match(".*en-us/library/windows/desktop.*",item):
    #        print item
    url="https://msdn.microsoft.com/en-us/library/windows/desktop/bg126469(v=vs.85).aspx"
    '''
    url="https://msdn.microsoft.com/en-us/library/windows/desktop/bg126469(v=vs.85).aspx"
    url="https://msdn.microsoft.com/en-us/library/windows/desktop/dd239108(v=vs.85).aspx"
    url = "https://msdn.microsoft.com/en-us/library/windows/desktop/aa363851(v=vs.85).aspx"
    c = crawler(url,".*en-us/library/windows/desktop.*")
    writer = writer_wrapper()
    c.start(writer)

if __name__ == "__main__":
    main()
