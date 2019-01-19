__author__ = 'Adelola'
import os, re
import json as js
import win32com.client as com
from win32com.shell import shell, shellcon

class Settings:
    def setSsid(self,data):
        f = open('settings.json')
        get = js.loads(f.read())
        f.close()
        get['ssid'] = data
        get = js.dumps(get)
        f = open('settings.json', 'w')
        f.write(get)
        f.close()
        del f

    def getSsid(self):
        f = open('settings.json')
        get = js.loads(f.read()); f.close()
        return get['ssid']

    def trying(self):
        local = self.getLocal()
        os.makedirs(local)
        os.makedirs(local+"apps")
        os.makedirs(local+"audios")
        os.makedirs(local+"compressed")
        os.makedirs(local+"docs")
        os.makedirs(local+"videos")
        os.makedirs(local+"images")
        os.makedirs(local+"others")
        os.makedirs(local+"folders")

    def getLocal(self):
        local = shell.SHGetFolderPath(0,shellcon.CSIDL_PERSONAL,None,0)
        neq = local+"\\File Beamer\\"
        data = neq.replace("\\","\\\\")
        return data

    def fileTypes(self, path):
        f = open("filetypes.json")
        get = f.read()
        jdata = js.loads(get)
        f.close()
        try:
            self.trying()
        except:
            pass
        local = self.getLocal()
        if path.find("\\")==-1:
            real = path.split(".")[-1]
            if real in jdata['app']:
                realpath = os.path.abspath(local+"apps\\"+path)
            elif real in jdata['audio']:
                realpath = os.path.abspath(local+"audios\\"+path)
            elif real in jdata['com']:
                realpath = os.path.abspath(local+"compressed\\"+path)
            elif real in jdata['docs']:
                realpath = os.path.abspath(local+"docs\\"+path)
            elif real in jdata['video']:
                realpath = os.path.abspath(local+"videos\\"+path)
            elif real in jdata['image']:
                realpath = os.path.abspath(local+"images\\"+path)
            else:
                realpath = os.path.abspath(local+"others\\"+path)
        else:
            realpath = os.path.abspath(local+"folders\\"+path)
        return realpath

class HandleFiles:
    def __init__(self, path):
        self.path = path

    def readFile(self):
        f = open(self.path, 'rb')
        size = os.path.getsize(self.path)
        data = f.read()[:size]
        f.close()
        return data

    def readLargeFile(self):
        f = open(self.path, 'rb')
        while True:
            data = f.read(1048576)
            if not data:
                break
            self.Send(data)
        f.close()

    def Send(self, data):
        return len(data)

    def getSize(self):
        size = os.path.getsize(self.path)
        return size

    def openFile(self):
        get = Settings()
        realpath = get.fileTypes(self.path)
        self.f = open(realpath, 'wb')
        return self.f

    def writeFile(self, data):
        if re.search('done\r\n',data):
            self.f.write(data[:-6])
            self.f.close()
            state = 1
        else:
            self.f.write(data)
            state = 0
        return state

    def openFolder(self):
        self.f = open("mics/folder.txt", "wb")
        return self.f

    def writeFolder(self, data):
        if re.search('folderDone\r\n',data):
            self.f.write(data[:-12])
            self.f.close()
            state = 1
        else:
            self.f.write(data)
            state = 0
        return state

class folderHandle:
    def __init__(self, path):
        self.path = os.path.join(path)
        self.list = []
        self.start = path.split("\\")[-1]
        self.n = len(path)
        self.send = ""
    def searchFolder(self):
        for dirpath, subdir, files in os.walk(os.path.join(self.path)):
            self.send = self.send+"\n"+(self.start+dirpath[self.n:])
        self.send = self.send+"\n"
        self.send = self.send[1:]
        return str(self.send)

    def folderDetails(self):
        filecount = 0
        folders = 0
        for dir, sub, files in os.walk(self.path):
            for subs in sub:
                folders+=1
        for dir, sub, files in os.walk(self.path):
            for file in files:
                filecount+=1
        filesize = os.path.getsize(self.path)

        return ([folders,filecount,filesize])

    def getFiles(self):
        #start = self.path.split("\\")[-3]
        pls = self.path[:-2]
        h = len(pls)
        p = pls.split("\\")[-1]
        j = len(p)
        for dir, sub, files in os.walk(self.path):
            if files:
                for file in files:
                    po = dir[h-j:]+"\\"+file
                    po = po.replace("\\\\","\\")
                    l = dir+"\\"+file
                    self.list.append([po,os.path.abspath(l),os.path.getsize(os.path.abspath(l))])
        return self.list

    def createFolder(self):
        set = Settings()
        local = set.getLocal()
        with open("mics/folder.txt") as f:
            for lines in f:
                try:
                    os.makedirs(local+"folders\\"+lines[:-1])
                except:
                    pass

class Mics:
    def coverbyte(self,bytes):
        b = float(bytes)
        kb = float(1024)
        mb = float(kb**2)
        gb = float(kb**3)
        tb = float(kb**4)

        if b<kb:
            return "%d %s"%(b,"Bytes" if 0==b > 1 else "Byte")
        elif kb <= b < mb:
            return "%0.2f Kb"%(b/kb)
        elif mb <= b< gb:
            return "%0.2f Mb"%(b/mb)
        elif gb <= b < tb:
            return "%0.2f Gb"%(b/gb)
        elif tb <= b:
            return "%0.2f Tb"%(b/tb)

    def getFolderSize(self, path):
        fso = com.Dispatch("Scripting.FileSystemObject")
        folder = fso.GetFolder(path)
        size = self.coverbyte(folder.size)
        return size
