#!/usr/bin/env python
import HTMLParser
import urllib
import sys
import re
import urlparse

class Argument:
    def __init__(self,access=None,type=None,name=None):
        self.type = type
        self.access = access
        self.name = name
    def __str__(self):
        return "{} {} {}".format(self.access,self.type,self.name)


class ParseMSDN(HTMLParser.HTMLParser):
    def __init__(self,base):
        self.base = base
        HTMLParser.HTMLParser.__init__(self)
        self.links = set()
        self.tag = ""
        self.isCode=False
        self.expect = -1 #what do expect next tag!

        self.HEADER = 0
        self.LIBRARY = 1
        self.DLL = 2
        self.VARIATION = 3

        self.header = ""
        self.library = ""
        self.dll =""
        self.var = []
        self.ret = self.conv = self.name = self.arguments= None
        self.record_pre = False
        self.pre_data = ""
    def parse_function(self,func):
        regex = "[\s\t]*([a-zA-Z]+[a-zA-Z_0-9]*)"#([\s\t]*\*)?)" #return type
        regex += "(([\s\t]+)([A-Za-z_0-9]+))?" #call convention
        regex += "[\s\t]+([a-zA-Z_]+[a-zA-Z_0-9_]*)" #function name
        regex += "[\s\t]*"
        regex += "\(([^\)\(]+)\)" #parmeter

        m = re.match(regex,func)
        ret = conv = name = param = None
        arguments = []
        if m:
            groups = m.groups()
            ret = groups[0]
            conv = groups[3]
            name = groups[4]
            param =groups[5]
            param = param.split(',')
            for p in param:
                p = p.strip()
                a=Argument(*p.split(' '))
                arguments.append(str(a))
        return ret,conv,name,arguments
    def handle_data(self,data):
        
        '''
        if self.tag == "pre" and not self.isCode:
            print "============================",self.tag
            print data
            print "============================"
            data = data.replace("\n","")
            data = data.replace("\xc2\xa0"," ")
            data = re.sub(r'\s+',' ',data)
            self.ret,self.conv,self.name,self.arguments=self.parse_function(data)
            if self.name:
                self.isCode=True
        '''                
        if self.record_pre :
            self.pre_data += data
        elif self.isCode: 
            if self.tag == "p":
                if data == "Unicode and ANSI names":
                    self.expect = self.VARIATION
                elif data == "DLL":
                    self.expect = self.DLL
                elif data == "Library":
                    self.expect = self.LIBRARY
                elif data == "Header":
                    self.expect = self.HEADER
            elif self.expect != -1 and self.tag == "dt":
                if self.expect == self.HEADER:
                    m=re.match("^([^\s]+\.h).*",data)
                    self.header = m.groups()[0]
                    self.expect = -1
                elif self.expect == self.DLL:
                    self.dll = data
                    self.expect = -1
                elif self.expect == self.LIBRARY:
                    self.library = data
                    self.expect = -1
                #elif self.expect == self.VARIATION:
                #    self.var.add(data)
                #    self.expect = -1
            elif self.expect == self.VARIATION and self.tag == "strong":
                #if data.beginswith(self.api_name):
                 #print "---",data
                 self.var.append(data)
    def handle_starttag(self,tag,attr):
        self.tag = tag
        if tag == 'a':
            for (key,value) in attr:
                if key == "href":
                    url =urlparse.urljoin(self.base,value)
                    self.links.add(url)
        elif tag == 'pre' and not self.isCode:
          self.pre_data = ""
          self.record_pre = True
    def handle_endtag(self,tag):
        if tag == "table":
          self.expect=-1
        elif tag == 'pre':
          self.record_pre= False  
          data = self.pre_data
          data = data.replace("\n","")
          data = data.replace("\xc2\xa0"," ")
          data = re.sub(r'\s+',' ',data)
          self.ret,self.conv,self.name,self.arguments=self.parse_function(data)
          if self.name:
            self.isCode=True

        self.tag = ""

def main():
    url = sys.argv[1]
    parser=ParseMSDN("http://msdn.microsoft.com/")
    #data = urllib.urlopen(url).read()
    #f = open("web.html","r")
    #parser.feed( f.read() )
    parser.feed( urllib.urlopen(url).read() )
    if parser.name:
        module = parser.dll.lower()
        if module.find(".dll") != -1:
            module=module[:module.find(".dll")]
        sys.stdout.write("{} {}.{}".format(parser.ret,module,parser.name))
        sys.stdout.write("(")
        for a in parser.arguments:
            sys.stdout.write("{}".format(a))
        sys.stdout.write(")")
        sys.stdout.write(":{}\n".format(parser.ret))
        for v in parser.var:
            print  "{}.{}:{}".format(module,v,parser.ret)
    parser.close()

if __name__ == "__main__":
    main()
