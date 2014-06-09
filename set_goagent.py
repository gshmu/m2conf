#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'mhohai'
"""
For GoAgent choice fast ip
"""

import re
import threading
import subprocess

#compile regex
"""
I'm using Ubuntu, re.compile by ping and w3m stdout.
Other system should change it to compare your PC.
please: $sudo apt-get install w3m
"""
re_avg_time = re.compile(r'\d+/(\d+)', re.M)
re_loss_percent = re.compile(r'(\d+)%', re.M)
# Exact match host name. old:([^:]+)
re_find_dns_name = re.compile(r'dNSName=[^:]*?\b(google\.\w+\.?\w*)', re.M)

#ip_set = [('0.0.0', min, max), ]
#ip_set = [('203.208.46', 140, 145), ]
from GCC import ip_set  # setting ip set first.
#ip_str = "IP|IP" #Easy add yourself ip.
ip_str = None

ip_list = []
init_threading_count = threading.activeCount()


def find_host(ip):
    w3m_cmd_command = ('w3m', 'https://'+ip)
    w3m_https = subprocess.Popen(w3m_cmd_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    w3m_https.wait()
    w3m_message = w3m_https.stdout.read()
    host_name = re_find_dns_name.search(w3m_message)
    host_name = host_name and host_name.group(1) or None

    return host_name


class Ping(threading.Thread):
    def __init__(self, ip_address):
        threading.Thread.__init__(self)
        self.ip_address = ip_address

    def run(self):
        # ping IP Address, add 0% loss to ip_list
        ping_cmd_command = ('ping', '-c 4', self.ip_address)
        ping_cmd = subprocess.Popen(ping_cmd_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        ping_cmd.wait()

        ping_cmd_echo = ping_cmd.stdout.read()
        loss_percent = re_loss_percent.search(ping_cmd_echo)
        loss_percent = int(loss_percent.group(1)) if loss_percent is not None else 200
        avg_time = re_avg_time.search(ping_cmd_echo)
        avg_time = avg_time and int(avg_time.group(1)) or 0

        # Don't check high loss ip's host.
        host_name = find_host(self.ip_address) if loss_percent < 80 else None

        if host_name is not None:
            # wait mutex and add to list
            global lock
            try:
                lock.acquire()
                ip_list.append((loss_percent, avg_time, self.ip_address, host_name))
                #test enable. 测试用，我还是喜欢屏蔽掉，下边会输出排序好的。
                print '%-6s%-4s%-16s%s' % (loss_percent, avg_time, self.ip_address, host_name)
            except:
                pass
            finally:
                lock.release()


def list_ping(_set):
    if ip_str is None or ip_str == '':
        for _ in _set:
            for i in range(_[1], _[2] + 1):
                ping_thread = Ping('%s.%d' % (_[0], i))
                ping_thread.start()
    else:
        ip = ip_str.split("|")
        for _ in ip:
            ping_thread = Ping(_)
            ping_thread.start()

    # once run threading.activeCount()=2 !!!maybe itself
    print threading.activeCount() - init_threading_count, 'threading working...'
    while threading.activeCount() > init_threading_count:
        pass
    
    ip_list.sort()
    # I want print by fast!!!  this doesn't work.
    print '%-6s%-4s%-16s%s' % ('loss%', 'avg', 'IP Address', 'dNSName')
    for ip in ip_list:
        print '%-6s%-4s%-16s%s' % ip

    print "you may love this."
    _ip = []
    for _ in ip_list:
        if int(_[0]) == 0:
            _ip.append(_[2])
    print "|".join(_ip)


if __name__ == '__main__':
    global lock
    lock = threading.Lock()
    list_ping(ip_set)
