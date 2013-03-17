# -*- coding: utf-8 -*-
#!/usr/bin/env python

import os
import sys

spaces = ["5G", "10G", "20G", "40G", "80G", "160G", "320G"]
size = ["512B", "1KB", "2KB", "4KB", "8KB", "16KB", "32KB", "64KB", "128KB", \
        "256KB", "512KB", "1MB", "2MB", "4MB", "8MB", "16MB", "32MB", "64MB"]
interval = 3

specs = ["4K", "8K", "16K", "32K", "64K", "128K", "256K", "512K", "1MB", "2MB", "4MB", "8MB", "16MB", "32MB", "64MB"]
managers = ["vm1", "vm2"]

class EndOfTestException(Exception):
    def __init__(self):
        Exception.__init__(self)

class ParseException(Exception):
    def __init__(self, detail):
        Exception.__init__(self)
        self.detail = detail

class Spec():
    def __init__(self):
        self.name = ""
        self.values = []

    def handler(self, f):
        line = f.readline()
        self.values = line.split(",")
        self.name = self.values[0]

        return f

class TestSpec():
    
    def __init__(self):
        self.name       = ""
        self.spec_name  = ["size", "case_rate", "read_rate", "random_rate", "delay", "burst", "align", "replay"]
        self.specs      = []
        self.spec_num   = 0

    def get_spec(self, f):
        line = f.readline()
        if not line.startswith("'Access specification name"):
            raise ParseException("Expect Spec Name but get %s" % line)
        
        self.spec_num += 1
        while True:
            spec = Spec()
            f = spec.handler(f)
            self.specs.append(spec)
            
            line = f.readline()
            if line.lstrip("'").startswith("End access specifications"):
                break
            else:
                self.spec_num += 1

        return f

class Manager():

    def __init__(self):
        self.name = ""
        self.values = []
        self.worker_num = 1
        self.disk_num = 1

    def handler(self, f):
        line = f.readline()
        if not line.startswith("MANAGER"):
            raise ParseException("Except start of manager but get %s" % line)
        self.values = line.split(",")
        self.worker_num = int(self.values[4].rstrip("\r\n"))
        self.disk_num = int(self.values[5].rstrip("\r\n"))
        
        #pass the processor info
        while True:
            if not f.readline().startswith("PROCESSOR"):
                break

        #pass the worker and disk info
        for i in range(0, self.worker_num + self.disk_num - 1):
            line = f.readline()

        return f


class TestResult():
    def __init__(self):
        self.attr_name = ["Target Type", "Target Name", "Access Specification Name",\
                "Managers", "Workers", "Disks", "IOps", "Read IOps", "Write IOps", \
                "MBps (Binary)", "Read MBps (Binary)", "Write MBps (Binary)", \
                "MBps (Decimal)", "Read MBps (Decimal)", "Write MBps (Decimal)", \
                "Transactions per Second", "Connections per Second", \
                "Average Response Time", "Average Read Response Time", \
                "Average Write Response Time", "Average Transaction Time", \
                "Average Connection Time", "Maximum Response Time", \
                "Maximum Read Response Time", "Maximum Write Response Time", \
                "Maximum Transaction Time", "Maximum Connection Time", "Errors", \
                "Read Errors", "Write Errors", "Bytes Read", "Bytes Written", \
                "Read I/Os", "Write I/Os", "Connections", "Transactions per Connection", \
                "Total Raw Read Response Time", "Total Raw Write Response Time", \
                "Total Raw Transaction Time", "Total Raw Connection Time", \
                "Maximum Raw Read Response Time", "Maximum Raw Write Response Time", \
                "Maximum Raw Transaction Time", "Maximum Raw Connection Time", \
                "Total Raw Run Time", "Starting Sector", "Maximum Size", "Queue Depth", \
                "% CPU Utilization", "% User Time", "% Privileged Time", "% DPC Time", \
                "% Interrupt Time", "Processor Speed", "Interrupts per Second", \
                "CPU Effectiveness", "Packets/Second", "Packet Errors", \
                "Segments Retransmitted/Second"]
        self.attrs = {}
        self.mgr_num = 1
        self.managers = []

    def get_overview(self, f):
        line = f.readline()
        if not line.startswith("'Results"):
            raise ParseException("Expect start of result but get %s" % line)
        f.readline() #read the attr name
        line = f.readline()
        values = line.split(",")
        self.attrs = dict(zip(self.attr_name, values))
        
        return f

    def get_result(self, f):
        f = self.get_overview(f)
        self.mgr_num = int(self.attrs["Managers"].rstrip("\r\n"))
        for i in range(0, self.mgr_num):
            mgr = Manager()
            f = mgr.handler(f)
            self.managers.append(mgr)

        return f

    def get_manager(self, idx):
        if len(self.managers) < (idx + 1):
            return None

        return dict(zip(self.attr_name, self.managers[idx].values))


class TestCase():

    def __init__(self):
        #self.path       = path
        self.spec       = TestSpec()
        self.result     = TestResult()

    def get_start(self, f):

        while True:
            line = f.readline()
            if line.startswith("'"):
                line = line.lstrip("'")
            if line.startswith("Access specifications"):
                break;
            elif line.startswith("End Test"):
                raise EndOfTestException()

        return f

    def get_spec(self, f):
        
        return self.spec.get_spec(f)

    def get_result(self, f):

        return self.result.get_result(f)

    def print_case(self, f):
        print >> f, self.spec.name
        print >> f, self.spec.specs
        print >> f, self.result.attrs


class TestFile():
    """
    Container of TestCase.
    """
    def __init__(self, path):
        self.path       = path
        self.name       = os.path.basename(path)
        self.fhandler   = None
        self.testcases  = []
    
    def init(self):
        self.fhandler = open(self.path, "r")

    def parse(self, f=sys.stdout):

        try:
            while True:
                test = TestCase()
                self.fhandler = test.get_start(self.fhandler)
                self.fhandler = test.get_spec(self.fhandler)
                self.fhandler = test.get_result(self.fhandler)
                self.testcases.append(test)
                #test.print_case(f)
        except EndOfTestException:
            pass
        except EOFError:
            pass
        finally:
            self.fhandler.close()


def get_testcase_list(base_dir):
    """
    Get the file list of test results in the path base_dir.
    """
    entry_list = []
    for entry in os.listdir(base_dir):
        path = os.path.join(base_dir, entry)
        ext = os.path.splitext(path)[1].lower()
        if os.path.isfile(path) and ext == r'.csv':
            entry_list.append(path)

    return entry_list

def print_title1():
    
    print "\t",
    for item in spaces:
        print item + "\t",
    print ""

def print_benchmark1(files, attr):
    
    print_title1()
    k = 0
    for s in size:
        print s + "\t",
        
        for sp in spaces:
            p = 0
            for f in files:
                if f.name.startswith(sp):
                    break
                else:
                    p = p + 1
        
            val = 0
            for i in range(0, interval):
                val += float(files[p+i].testcases[k].result.attrs[attr].rstrip("\r\n"))

            print "%.3f\t" % (val/interval),
        print ""#print \n
        k += 1

def print_title2():
    
    print "\t",
    for item in managers:
        print item + "\t",
    print ""

def print_benchmark2(files, attr):
    
    print_title2()
    for sidx, sp in enumerate(specs):
        print sp + "\t",

        for midx, mgr in enumerate(managers):

            val = .0
            for fidx, f in enumerate(files):
                val += float(f.testcases[sidx].result.get_manager(midx)[attr].rstrip("\r\n"))
            print "%.2f\t" % (val/len(files)),
        print ""

def main():

    plist = get_testcase_list('/home/kangda/Documents/Lab/Test2')
    plist.sort()
    files = []
    for path in plist:
        test = TestFile(path)
        test.init()
        try:
            test.parse()
        except ParseException, e:
            print e.detail

        files.append(test)

    print "************IOPS************"
    #print_benchmark1(files, "IOps")
    print_benchmark2(files, "IOps")
    print "**********BANDWIDTH*********"
    #print_benchmark1(files, "MBps (Binary)")
    print_benchmark2(files, "MBps (Binary)")
    print "***********LATENCY**********"
    #print_benchmark1(files, "Average Response Time")
    print_benchmark2(files, "Average Response Time")

if __name__ == '__main__':
    main()
