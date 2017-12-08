#!/usr/bin/env python
import HTMLParser
import urllib
import sys
from parser import *
import threading
import time
class writer_wrapper(object):
  def __init__(self,dest=sys.stdout):
    self.lock = threading.Lock()
    if type(dest) == type(''):
      self.dest = open(dest,'w')
    else: self.dest = dest
  def write(self,msg):
    with self.lock:
      self.dest.write(msg)

  def close(self):
    with self.lock:
      self.dest.close()
class UrlPool(object):

  def __init__(self):
    self.lock =threading.Lock()
    self.urlpool = []
    self.urldone = {}
    self.urlworking = {}

  def next(self):
    while True:
      with self.lock:
        if len(self.urlpool) ==0 and len(self.urlworking) == 0:
          raise StopIteration
        if len(self.urlpool) > 0:
          url = self.urlpool.pop()
          self.urlworking[url] = 0
          return url
      time.sleep(1)          

  def __iter__(self):
    return self

  def done(self,url):
    with self.lock:
      if url in self.urlworking:
        del self.urlworking[url]
        self.urldone[url]=0

  def addUrl(self,url):
    with self.lock:
      if url not in self.urlworking and\
        url not in self.urldone:
          self.urlpool.append(url)

  def reStack(self,url):
    with self.lock:
       self.urlpool.append(url)
       del self.urlworking[url]

  def checkpoint(self):
    with self.lock:
      print "Writing CHECKPOINT"
      with open("checkpoint","w") as f:
        print >> f , "#DONE"
        for done in self.urldone:
          print >> f, done
        print >> f,"#POOL"
        for p in self.urlpool:
          print >> f, p
        print >> f,"#WORKING"
        for w in self.urlworking:
          print >>f, w
      print "CHECKPOINT written"
     
  def readcheckpoint(self):
    with open("checkpoint","r") as f:
      print "Reading CHECKPOINT"
      u = None
      for line in f:
        line = line.strip()
        if line.startswith("#DONE"):
          u = self.urldone
        elif line.startswith("#POOL"):
          u = self.urlpool
        elif line.startswith("#WORKING"):
          u = self.urlpool
        else:
          if u:
           if type(u) == type([]):
            u.append(line)
           else:
            u[line] = 0
class crawler:

  def __init__(self,seed,accepted_pattern,MAX_THREADS=1,checkpoint = False,checkpoint_freq=60):
    self.accepted=accepted_pattern
    self.seed = seed
    self.pool = UrlPool()
    self.pool.addUrl(self.seed)
    self.MAX_THREADS = MAX_THREADS
    self.checkpoint_freq = checkpoint_freq
    if checkpoint:
      self.pool.readcheckpoint()

  def run(self,writer):
    for url in self.pool:
      try:        
        parser = ParseMSDN("https://msdn.microsoft.com")
        #writer.write("visiting "+ url+"\n")
        parser.feed( urllib.urlopen(url).read())
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
          writer.write(msg)
        parser.close()
        self.pool.done(url)
        for item in parser.links:
          if re.match(self.accepted,item) and item.find("newlocale=") == -1:
            self.pool.addUrl( item )
      except IOError as e:
        print >>sys.stderr, "Error1 {} {}".format(e,url)
        self.pool.reStack(url)
      except TypeError as e:
        print >> sys.stderr, "Error {}".format(e)
        print >> sys.stderr, url
        self.pool.done(url)
      except UnicodeDecodeError as e:
        print >> sys.stderr, "Error {}".format(e)
        print >> sys.stderr, url
        self.pool.done(url)
      except Exception as e:
        print >> sys.stderr, "Error {} {}".format(e,type(e))

  def pool_write(self):
    time.sleep(60)
    while len(self.pool.urlpool) > 0:
      self.pool.checkpoint()
      time.sleep(self.checkpoint_freq)
  def start(self,writer):
    t = []
    for i in range(0,self.MAX_THREADS):
      d = threading.Thread(target=self.run,args=(writer,) )     
      t.append( d )
      d.start()
    w = threading.Thread(target=self.pool_write,args=())
    w.start()
    for i in t:
      i.join()

import ConfigParser

def main():
  Config = ConfigParser.ConfigParser()
  Config.read("config")
  options = Config.options("parameters")
  checkpoint_freq = 60 #Save checkpoint every 60 seconds
  for o in options:
    if o.upper() == "MAX_THREADS":
      MAX_THREADS = int(Config.get("parameters",o))
    elif o.upper() == "CHECKPOINT_FREQ":
      checkpoint_freq = int(Config.get("parameters",o))
  '''
  parser = ParseMSDN()
  url="https://msdn.microsoft.com/en-us/library/windows/desktop/bg126469(v=vs.85).aspx"
  #url="https://msdn.microsoft.com/en-us/library/windows/desktop/dd239108(v=vs.85).aspx"
  parser.feed( urllib.urlopen(url).read())
  parser.close()
  #for item in parser.links:
  #  if re.match(".*en-us/library/windows/desktop.*",item):
  #    print item
  url="https://msdn.microsoft.com/en-us/library/windows/desktop/bg126469(v=vs.85).aspx"
  '''
  url="https://msdn.microsoft.com/en-us/library/windows/desktop/bg126469(v=vs.85).aspx"
  url="https://msdn.microsoft.com/en-us/library/windows/desktop/dd239108(v=vs.85).aspx"
  url = "https://msdn.microsoft.com/en-us/library/windows/desktop/aa363851(v=vs.85).aspx"
  checkpoint = False
  if len(sys.argv) > 1  :
    checkpoint = True
  c = crawler(url,".*msdn.*en-us/library/windows/desktop.*",MAX_THREADS,checkpoint,checkpoint_freq)
  writer = writer_wrapper("names.txt")
  c.start(writer)

if __name__ == "__main__":
  main()
