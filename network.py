__author__ = 'Adelola'
import subprocess as sp
from random import random
import os
from backend import *
import re

win = 0x08000000

class Network:
    def Create(self,ssid,key):
        com = sp.check_output(['netsh','wlan','set','hostednetwork','mode=allow',
                               'ssid='+str(ssid),'key='+str(key)], creationflags=win)

        com = sp.check_output(['netsh','wlan','start','hostednetwork'],creationflags=win)
        start = "started"
        if start in com:
            return 1
        else:
            return 0
    def Stop(self):
        com = sp.check_output(['netsh','wlan','stop','hostednetwork'],creationflags=win)
        com1 = sp.check_output("netsh wlan disconnect",creationflags=win)

    def findChr(self,text):
        n = 70; m = 70
        lis = []
        state = True
        while state:
            strt = text.find("SSID",n)
            if strt == -1:
                break
            end = text.find("Encryption",m)
            ins = text[strt:end]
            h = ins.find(":")
            sd = ins[h+2:]
            done = sd.split("\r")[0]
            lis.append(done)
            n = end; m = text.find("Encryption",n+1)
        return lis

    def Search(self):
        proc = sp.check_output("netsh wlan show networks",creationflags=win)
        new = "\n".join(re.findall(r"(?<=SSID \d : )(\S+)",proc)).split("\n")
        return new

    def Connect(self,ssid,key):
        f = open('settings/connect.xml','r')
        tree = f.read()
        f.close()
        hexer = ssid.encode('hex')
        hexer = hexer.upper()
        j = tree.replace("<name></name>","<name>%s</name>"%ssid)
        j = j.replace("<name>%s</name>"%ssid,"<name>wifi-name</name>",1)
        j = j.replace("<hex></hex>",'<hex>%s</hex>'%hexer)
        j = j.replace("<keyMaterial></keyMaterial>",'<keyMaterial>%s</keyMaterial>'%key)
        n = open('mics/wifi.xml','w')
        n.write(j)
        n.close()
        path = os.path.join(os.getcwdu(),'mics','wifi.xml')
        cmd = sp.check_output(['netsh','wlan','add','profile',
                               'filename='+path,], creationflags=win)
        state = 0
        os.remove(path)
        if 'added' in cmd:
            cmd = sp.check_output(['netsh','wlan','connect','name=wifi-name'],creationflags=win)
            j = sp.check_output("netsh wlan show interface",creationflags=win)
            pi = "".join(re.findall(r"(?<=State                  : )(\S+)",j))
            if 'connected' in pi:
                state = 1
            else:
                state = 0
        return state

    def Disconnect(self):
        sp.check_output('netsh wlan disconnect',creationflags=win)
        sp.check_output(['netsh','wlan','delete','profile','name=wifi-name'],creationflags=win)

    def GetCreateIP(self):
        proc = sp.check_output("ipconfig" ,creationflags=win)
        ip = "".join(re.findall(r"(?<=IPv4 Address. . . . . . . . . . . : )(\d+\.\d+\.\d+\.\d+)",proc))
        return ip

    def GetJoinIP(self):
        proc = sp.check_output("ipconfig",creationflags=win)
        ip = "".join(re.findall(r"(?<=Default Gateway . . . . . . . . . : )(\d+\.\d+\.\d+\.\d+)",proc))
        return ip

    def GetStatus(self):
        ho = sp.check_output("netsh wlan show driver",creationflags=win)
        new = "\n".join(re.findall(r"(?<=Hosted network supported  : )(\S+)",ho)).split("\n")
        return new[0]


class Random:
    def Generate(self):
        rand = str(random())
        rand = rand[2:10]
        return rand

