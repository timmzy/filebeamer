__author__ = 'Adelola'

import wx
import sys
from wx import aui
import wx.gizmos as gz
from wx.lib.pubsub import pub
from wx.lib.wordwrap import wordwrap
import  wx.lib.scrolledpanel as scrolled
from twisted.internet import wxreactor
wxreactor.install()
from twisted.internet import reactor, protocol
from twisted.protocols.basic import LineReceiver, FileSender
import json as js
import os, time, shutil
import subprocess as sp
from datetime import datetime as lovetime, timedelta
from preference import PrefDialog
from network import Random, Network
from backend import *
from database import *



TBFLAGS = (wx.TB_HORIZONTAL| wx.NO_BORDER| wx.TB_FLAT| wx.TB_TEXT)
#Settings
with open("settings.json") as f:
    getit = f.read()
gdata = js.loads(getit)
del getit

if gdata['start']=="0":
    username = os.environ.get("USERNAME")
    gdata['network'] = username+"-Net"
    gdata['name'] = username
    gdata['start'] = "1"
    with open("settings.json",'w') as f:
        f.write(js.dumps(gdata))

name = {"name":gdata['name']}

datasize = Mics()
history_check = 0

class CreateDialog(wx.Dialog):
    def __init__(self, parent, id, title, size):
        wx.Dialog.__init__(self,parent,id,title,size=(300,230))

        self.CenterOnParent(True)

        with open("settings.json") as f:
            getit = f.read()
        self.jdata = js.loads(getit)

        vbox = wx.BoxSizer(wx.VERTICAL)

        hbox = wx.BoxSizer(wx.HORIZONTAL)

        Lssid = wx.StaticText(self,-1,"Network Name: ")
        self.ssid = wx.TextCtrl(self,-1,)
        enter = wx.Button(self,6,"Create",size=((60,-1)))
        hbox.Add(Lssid,0,wx.ALIGN_CENTER);hbox.Add(self.ssid,0,wx.ALIGN_CENTER)
        hbox.Add(enter,0,wx.ALIGN_CENTER|wx.LEFT,3)

        self.ssid.SetValue(self.jdata['network'])

        vbox.Add(hbox,0,wx.ALIGN_CENTER|wx.TOP|wx.BOTTOM,8)

        self.display = wx.TextCtrl(self,3,"Create Network...",size=(500,124), style=wx.TE_READONLY|wx.TE_MULTILINE)
        self.display.SetBackgroundColour('#FFFACD')

        vbox.Add(self.display,2,wx.ALL,3)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        done = wx.Button(self,wx.ID_OK,"Done")
        cancel = wx.Button(self,wx.ID_CANCEL,"Close")
        close = wx.Button(self,5,"Stop Network")

        hbox.Add(done); hbox.Add(cancel); hbox.Add(close)

        vbox.Add(hbox,3,wx.ALIGN_CENTER)

        self.SetSizer(vbox)

        self.Bind(wx.EVT_BUTTON,self.OnCreate,id=6)
        self.Bind(wx.EVT_BUTTON, self.CancelNet, id=5)

        pub.subscribe(self.OnPeer, 'createDialog')
        pub.subscribe(self.windowListener, "close")

    def windowListener(self, msg):
        try:self.Destroy()
        except:pass

    def OnCreate(self, evt):
        ran = Random()
        ran = ran.Generate()
        if self.jdata['password']!="":ran=self.jdata['password']
        network = Network()
        network.Stop()
        ssid = self.ssid.GetValue()
        if ssid == "":
            dlg = wx.MessageDialog(self, 'Please enter a value!','Alert!',
                               wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
        else:
            try:
                network.Create(ssid,ran)
                self.display.SetLabel('Network Password is: %s'%(ran))
                self.display.AppendText('\nWaiting for peers to join...')
                get = Network()
                time.sleep(3)
                ip = get.GetCreateIP()
                reactor.listenTCP(8000, ServerFactory(), interface=str(ip))
            except:
                dlg = wx.MessageDialog(self, 'Sorry an error was found. Make sure you are running this application with administrative priviledge. '
                                             'This could also be caused by network driver issues. Click on the about Info-button to get help',
                               'Error Detected',
                               wx.OK | wx.ICON_ERROR)
                dlg.ShowModal()
                dlg.Destroy()
                self.Destroy()

    def OnPeer(self, message):
        self.display.AppendText("\n%s Joined"%(message))

    def CancelNet(self, evt):
        network = Network()
        network.Stop()
        self.display.SetLabelText("Network stopped.")

class JoinDialog(wx.Dialog):
    def __init__(self, parent, id, title):
        wx.Dialog.__init__(self,parent,id,title,size=(300,250))

        vbox = wx.BoxSizer(wx.VERTICAL)
        self.scanBtn = wx.Button(self,11,"Scan ((!))")
        vbox.Add(self.scanBtn,0,wx.EXPAND|wx.ALIGN_CENTER|wx.TOP,2)
        self.net = Network(); lis = self.net.Search()
        self.list = wx.ListBox(self,-1,size=((-1,142)), choices=lis)
        if self.list.GetCount():
            self.list.Select(0)
        vbox.Add(self.list,0,wx.EXPAND|wx.ALL,2)
        connect = wx.Button(self,12,"Connect")
        cancel = wx.Button(self,wx.ID_CANCEL,"Close")
        disconnect = wx.Button(self,13,"Disconnect")
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(connect); hbox.Add(cancel); hbox.Add(disconnect)
        vbox.Add(hbox,0,wx.ALIGN_CENTER|wx.BOTTOM,2)
        self.g1 = wx.Gauge(self, -1, 50, (110, 40), (250, 25))
        vbox.Add(self.g1,0,wx.EXPAND)

        self.Bind(wx.EVT_BUTTON,self.OnScan,id=11)
        self.Bind(wx.EVT_BUTTON,self.OnConnect,id=12)
        self.Bind(wx.EVT_BUTTON, self.OnDisconnect,id=13)

        self.SetSizer(vbox)

        self.CenterOnParent()

        pub.subscribe(self.windowListener,"close")

    def windowListener(self, msg):
        self.Destroy()

    def OnScan(self, evt):
        self.scanBtn.SetLabelText("Searching...")
        lis = self.net.Search()
        self.list.Clear()
        self.list.SetItems(lis)
        if self.list.GetCount():
            self.list.Select(0)
        self.scanBtn.SetLabelText("Scan ((!)))")

    def OnConnect(self, evt):
        if self.list.GetCount()>0:
            dlg = wx.TextEntryDialog(self, 'Enter WI-FI Password?','Connect',style=wx.TE_PASSWORD|wx.OK|wx.CANCEL)
            dlg.CenterOnParent()
            if dlg.ShowModal() == wx.ID_OK:
                self.g1.Pulse()
                var = dlg.GetValue()
                if len(var)<8:
                    new = wx.MessageDialog(self, 'Password must be 8 or more characters! Please reconnect','Alert!',
                                   wx.OK | wx.ICON_INFORMATION)
                    new.ShowModal()
                else:
                    self.g1.Pulse()
                    new = Network()
                    new.Stop()
                    ssid = self.list.GetStringSelection()
                    key = dlg.GetValue()
                    state = new.Connect(ssid,key)
                    if state == 0:
                        new = wx.MessageDialog(self, 'Password not correct or network not found again!','Error Connecting!',
                                   wx.OK | wx.ICON_INFORMATION)
                        new.ShowModal()
                    else:
                        self.g1.Pulse()
                        time.sleep(3)
                        new = Network()
                        ip = new.GetJoinIP()
                        reactor.connectTCP(str(ip) , 8000, ClientFactory())

    def OnDisconnect(self, evt):
        dis = Network()
        dis.Disconnect()

class MyApp(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self,parent,id,title, size=(800,600),style=wx.MINIMIZE_BOX|
                          wx.CAPTION|wx.CLOSE_BOX)
        self.Maximize(False)
        appimg = wx.Bitmap('img/app.ico',wx.BITMAP_TYPE_ICO)
        icon = wx.EmptyIcon()
        icon.CopyFromBitmap(appimg)
        self.SetIcon(icon)

        self.process = 0

        self.update = 0

        self.users = {}

        self.speed = 0
        self.speedCheck = 0
        self.tim = 0

        self.mgr = aui.AuiManager()
        self.mgr.SetManagedWindow(self)

        self.tb = wx.ToolBar(self,style=TBFLAGS)

        self.tb.SetToolBitmapSize(wx.Size(48,48))
        self.status = self.CreateStatusBar()
        self.status.SetFieldsCount(3)
        make = self.status.GetField(1)
        self.status.SetStatusWidths([250,-2,-1])
        rect2 = self.status.GetFieldRect(2)
        rect1 = self.status.GetFieldRect(1)
        self.sendtext = wx.StaticText(self.status,-1,"")
        self.sendtext.SetPosition((rect1.x+2,rect1.y+2))
        self.sendtext.SetSize((rect1.width-4,rect1.height-4))
        self.g1 = wx.Gauge(self.status, -1, 50, (110, 95), (250, 25))
        self.g1.SetPosition((rect2.x+2,rect2.y+2))
        self.g1.SetSize((rect2.width-4,rect2.height-4))

        tsize = (50,50)
        create_bmp = wx.Bitmap('img/create_small.png')
        join_bmp = wx.Bitmap('img/join_small.png')
        send_bmp = wx.Bitmap('img/send_small.png')
        stop_bmp = wx.Bitmap('img/cancel_small.png')
        profile_bmp = wx.Bitmap('img/settings_small.png')
        disc_bmp = wx.Bitmap('img/discon_small.png')
        recon_bmp = wx.Bitmap('img/recon_small.png')
        info_bmp = wx.Bitmap('img/info_small.png')
        self.tbox = wx.BoxSizer(wx.HORIZONTAL)
        Lpeers = wx.StaticText(self.tb,-1,'Peers:\t')
        self.peers = wx.CheckListBox(self.tb,-1,size=((-1,68)))

        self.tbox.Add(Lpeers)
        self.tbox.Add(self.peers)

        self.tb.SetToolBitmapSize(tsize)

        #Toolbars
        self.tb.AddLabelTool(11, "Create Network", create_bmp, shortHelp="Create Network", longHelp="Create Network")
        self.tb.AddLabelTool(12, "Join Network", join_bmp, shortHelp="Join Network", longHelp="Join a created Network")
        self.tb.AddLabelTool(16, "Reconnect", recon_bmp, shortHelp="Reconnect", longHelp="Reconnect to same Network")
        self.tb.AddLabelTool(17, "Disconnect", disc_bmp, shortHelp="Disconnect", longHelp="Disconnect Network")
        self.tb.AddLabelTool(13, "Send", send_bmp, shortHelp="Send", longHelp="Send Files/Folders")
        self.tb.AddLabelTool(14, "Cancel", stop_bmp, shortHelp="Cancel", longHelp="Cancel File(s)")
        self.tb.AddLabelTool(15, "Preference ", profile_bmp, shortHelp="Preference", longHelp="Preference")
        self.tb.AddLabelTool(18, "Info ", info_bmp, shortHelp="About", longHelp="About")
        self.tb.AddSeparator()
        self.tb.AddSeparator()
        self.tb.AddControl(Lpeers)
        self.tb.AddControl(self.peers)
        self.tb.AddStretchableSpace()
        self.tb.Realize()


        self.tb.EnableTool(13,False)
        self.tb.EnableTool(14,False)

        #ToolBar Bindings
        self.Bind(wx.EVT_TOOL, self.CreateNet, id=11)
        self.Bind(wx.EVT_TOOL, self.JoinNet, id=12)
        self.Bind(wx.EVT_TOOL, self.OnSend, id=13)
        self.Bind(wx.EVT_TOOL, self.OnPreference, id=15)
        self.Bind(wx.EVT_TOOL, self.OnCancel, id=14)
        self.Bind(wx.EVT_TOOL, self.OnReconnect, id=16)
        self.Bind(wx.EVT_TOOL, self.OnDisconncet,id=17)
        self.Bind(wx.EVT_TOOL, self.aboutDialog,id=18)

        self.dir = wx.GenericDirCtrl(self, -1)

        tree = self.dir.GetTreeCtrl()

        #self.Bind(wx.EVT_TREE_SEL_CHANGED,self.tellMe,tree)

        self.nb = aui.AuiNotebook(self, style=aui.AUI_NB_TOP)
        self.panel1 = wx.Panel(self)
        self.panel1.SetBackgroundColour("WHITE")
        self.panel2 = scrolled.ScrolledPanel(self, -1, size=(140, 300),style = wx.TAB_TRAVERSAL|wx.SUNKEN_BORDER, name="panel1")

        self.panel2.SetupScrolling()

        self.queues = wx.ListBox(self,-1)

        self.probox = wx.BoxSizer(wx.VERTICAL)
        self.hisbox = wx.BoxSizer(wx.VERTICAL)

        self.listhis = wx.ListCtrl(self.panel2,-1,style=wx.LC_REPORT)
        self.listhis.InsertColumn(0,"Filename")
        self.listhis.InsertColumn(1,"Size")
        self.listhis.InsertColumn(2,"Date Created")

        self.listhis.SetColumnWidth(0,300)
        self.listhis.SetColumnWidth(1,90)
        self.listhis.SetColumnWidth(2,180)

        self.real = wx.Menu()
        openfile = self.real.Append(-1,"Open File")
        openfolder = self.real.Append(-1,"Open Folder")
        delete = self.real.Append(-1,"Delete File history")

        self.realqueue = wx.Menu()
        deletequeue = self.realqueue.Append(-1,"Delete Queue")

        self.Bind(wx.EVT_MENU, self.deleteQueue, deletequeue)

        self.Bind(wx.EVT_MENU, self.openFile, openfile)
        self.Bind(wx.EVT_MENU, self.openFolder, openfolder)
        self.Bind(wx.EVT_MENU, self.deleteFile, delete)

        self.listhis.Bind(wx.EVT_CONTEXT_MENU, self.listMenu)

        self.queues.Bind(wx.EVT_CONTEXT_MENU,self.queueMenu)

        self.panel1.SetSizer(self.probox)
        self.panel2.SetSizer(self.hisbox)

        self.hisbox.Add(self.listhis,0,wx.GROW)

        self.perc = wx.BoxSizer(wx.HORIZONTAL)
        self.detail1 = wx.BoxSizer(wx.HORIZONTAL)
        self.detail2 = wx.BoxSizer(wx.HORIZONTAL)
        self.probox.Clear()
        self.g1 = wx.Gauge(self.panel1, -1, 50, (110, 40), (250, 25))
        self.filename = wx.StaticText(self.panel1,-1,"Filename: ")
        self.filenamereal = wx.StaticText(self.panel1,-1)
        self.start = gz.LEDNumberCtrl(self.panel1,-1,size=(75,30))
        self.start.SetValue("--")
        self.end = gz.LEDNumberCtrl(self.panel1,-1,size=(75,30))
        self.end.SetValue("--")
        self.filesize = wx.StaticText(self.panel1,-1,"Filesize: ")
        self.size = wx.StaticText(self.panel1,-1)
        self.make = wx.StaticText(self.panel1,-1)

        #self.start.Hide()
        #self.end.Hide()

        self.perc.Add(self.start)
        self.perc.Add(self.end)
        self.detail1.Add(self.filename); self.detail1.Add(self.filenamereal)
        self.detail2.Add(self.filesize); self.detail2.Add(self.size)
        self.probox.Add(self.perc,0,wx.ALIGN_CENTER|wx.TOP|wx.BOTTOM,2)
        self.probox.Add(self.g1,0,wx.GROW|wx.ALL,5)
        self.probox.Add(self.detail1,0,wx.LEFT|wx.RIGHT,5)
        self.probox.Add(self.detail2,0,wx.LEFT|wx.RIGHT,5)
        self.probox.Add(self.make,0,wx.LEFT|wx.RIGHT,5)
        self.probox.Layout()
        self.probox.RecalcSizes()
        self.panel1.Layout()

        self.populateHistory()


        self.nb.AddPage(self.panel1, "Downloading")
        self.nb.AddPage(self.panel2, "History")

        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)

        self.nb.SetSelection(1)

        self.mgr.AddPane(self.tb,aui.AuiPaneInfo().ToolbarPane().Top().Dockable(False))
        self.mgr.AddPane(self.dir, aui.AuiPaneInfo().Name('main').CenterPane())
        self.mgr.AddPane(self.queues, aui.AuiPaneInfo().Name('side').Right().Caption("Process Queue").CloseButton(False).BestSize((150,-1)))
        self.mgr.AddPane(self.nb,aui.AuiPaneInfo().Caption("Thread").Bottom().CloseButton(False).BestSize((-1,500)))

        self.mgr.Update()

        self.Center()

        pub.subscribe(self.peerListener, "peers")
        pub.subscribe(self.lostListener, "lost")
        pub.subscribe(self.processListener, "process")
        pub.subscribe(self.updateListener, "update")
        pub.subscribe(self.clearListener, "done")
        pub.subscribe(self.sendingListener, "analysing")
        pub.subscribe(self.stopListener, "stopanalysing")
        pub.subscribe(self.sentListener, "donereceived")
        pub.subscribe(self.fileQueue,"filequeue")
        pub.subscribe(self.deleteFileQueue,"deletefile")
        pub.subscribe(self.folderQueue,"folderqueue")
        pub.subscribe(self.deleteFileQueue,"deletefolder")
        pub.subscribe(self.folderFile,"updatefolder")

    def folderFile(self,msg):
        self.update = int(msg)

    def folderQueue(self,msg):
        path = msg.split('\\')[-1]
        self.queues.Append("(FLD) "+path)

    def fileQueue(self, msg):
        self.queues.Append("(FLS) "+msg)

    def deleteFileQueue(self,msg):
        try:
            self.queues.Delete(0)
        except:
            pass

    def tellMe(self, evt):
        misc = Mics()
        try:
            path = self.dir.GetPath()
            real = os.path.abspath(path)
            size = misc.getFolderSize(real)
        except:
            path = self.dir.GetFilePath()
            real = os.path.abspath(path)
            size = os.path.getsize(real)
            size = misc.coverbyte(int(size))
        self.status.SetStatusText("Size: %s"%size)

    def openFile(self, evt):
        ind = self.listhis.GetFocusedItem()
        get = self.history[ind]
        os.startfile(os.path.abspath(get.path), "open")

    def openFolder(self, evt):
        ind = self.listhis.GetFocusedItem()
        get = self.history[ind]
        local = get.path.split("\\")[:-1]
        path = ""
        for i in local:
            path = path+i+"\\"
        sp.call(["explorer", path])

    def deleteFile(self, evt):
        lst = ["Delete History","Delete History and File"]
        dlg = wx.SingleChoiceDialog( self,"Select Option","Info", lst)
        if dlg.ShowModal() == wx.ID_OK:
            choice = dlg.GetSelection()
            if choice==0:
                ind = self.listhis.GetFocusedItem()
                get = self.history[ind]
                id = get.id
                his = History.get(id=int(id))
                his.delete_instance()
                self.populateHistory()
            elif choice==1:
                ind = self.listhis.GetFocusedItem()
                get = self.history[ind]
                id = get.id
                shutil.rmtree(os.path.abspath(get.path))
                his = History.get(id=int(id))
                his.delete_instance()
                self.populateHistory()
        dlg.Destroy()

    def dele(self,ind):
        self.queues.Refresh()
        self.queues.Delete(0)

    def deleteQueue(self, evt):
        pp = []; kk = []
        ind = self.queues.GetSelection()
        test = self.queues.GetString(ind)
        total = self.queues.GetStrings()
        self.sendQueue(total,ind,test)
        self.queues.Delete(ind)

    def sendQueue(self,total,ind,test):
        hy = 0; ty = 0
        slt = ["(FLD)","(FLS)"]
        pp=[];kk=[]
        k=0
        for i in total:
            if slt[0] in i[0:5]:
                pp.append([k,i])
            else:
                kk.append([k,i])
            k+=1
        if slt[0] in test[0:5]:
            k = 0
            for i in pp:
                if ind==i[0]:
                    hy = k
                    ty = "1"
                k+=1
        else:
            k = 0
            for i in kk:
                if ind==i[0]:
                    hy = k
                    ty = "2"
                k+=1
        pub.sendMessage("deletequeues",msg=str(hy),msg2=ty)

    def listMenu(self, evt):
        self.listhis.PopupMenu(self.real)

    def queueMenu(self, evt):
        if self.queues.GetSelection()!=-1:
            self.listhis.PopupMenu(self.realqueue)

    def populateHistory(self):
        self.listhis.DeleteAllItems()
        self.history = History.select().order_by(History.time_stamp.desc())
        for items in self.history:
            ind = self.listhis.InsertStringItem(self.listhis.GetItemCount(), items.filename)
            self.listhis.SetStringItem(ind,1,items.size)
            self.listhis.SetStringItem(ind,2,items.time_stamp)

    def sentListener(self, msg):
        self.sendtext.SetLabelText("File/Folder Recieved")

    def sendingListener(self, msg):
        self.sendtext.SetLabelText("Please Hold while compilining Files")
        self.status.SetBackgroundColour("WHITE")
        self.g1.Pulse()

    def stopListener(self, msg):
        self.g1.SetValue(0)
        self.sendtext.SetLabelText("You can Continue while still Sending...")

    def lostListener(self, name):
        if name=="lost":
            self.peers.Clear()
            self.users.clear()
            self.tb.EnableTool(13,False)
            self.tb.EnableTool(14,False)
            self.status.SetBackgroundColour("RED")
            self.SetStatusText("Connection Disconnected")
        else:
            ind = self.users[name]
            del self.users[name]
            self.peers.Delete(int(ind))
            self.status.SetBackgroundColour("RED")
            self.status.SetStatusText("Connection Disconnected!")
            if self.users.__len__()==0:
                self.SetStatusText("Connection Disconnected")
                self.tb.EnableTool(13,False)
                self.tb.EnableTool(14,False)
            else:
                self.SetStatusText("One Peer Lost")

    def clearListener(self, msg):
        self.process+=1
        self.sendtext.SetLabelText("File/Folder recieved")

    def peerListener(self, name, port):
        self.status.SetBackgroundColour("WHITE")
        self.status.SetStatusText("Connected to a Network")
        count = self.peers.GetCount()
        self.peers.Append(name)
        self.tb.EnableTool(13,True)
        self.tb.EnableTool(14,True)
        self.peers.Check(count)
        self.peers.Disable()
        pub.sendMessage("close", msg="")
        self.users[port] = count

    def processListener(self, name, size, num):
        self.remain = size
        self.speedCheck = 0
        self.nb.SetSelection(0)
        if self.process != 0:
            self.filename.SetLabelText("")
            self.size.SetLabelText("")
            self.start.SetValue("--")
            self.make.SetLabelText("")
        self.probox.Clear()
        self.g1.SetRange(int(size))
        if len(name)>100:
            name = name[:70]+"..."+name.split(".")[-1]
        self.filenamereal.SetLabelText(name)
        self.filename.SetLabelText("Filename: ")
        self.start.Show()
        self.end.Show()
        self.end.SetValue("100")
        self.filesize.SetLabelText("Filesize:  ")
        self.download = size
        self.size.SetLabelText(datasize.coverbyte(int(size)))
        if self.update:
            self.update-=1
        else:
            self.update = 0
        self.make.SetLabelText("File(s): Remining %d"%(self.update))

    def updateListener(self, current,speed):
        if self.speedCheck == 0:
            self.tim = time.ctime()[17:19]
            self.speedCheck = 1
        if self.tim == time.ctime()[17:19]:
            self.speed +=speed
        else:
            self.remain -= self.speed
            sec = self.remain/self.speed
            self.sendtext.SetLabelText(self.timeReamining(sec))
            n = Mics()
            self.nb.SetPageText(0,"Downloading... Speed: %s /Sec"%n.coverbyte(self.speed)); self.tim = time.ctime()[17:19]; self.speed = 0
        current = float(current)
        if current>self.download:
            current = self.download
        total = int(self.download)
        perc = (current/total)*100
        self.g1.SetValue(int(current))
        self.start.SetValue(str(int(perc)))

    def timeReamining(self,get):
        try:
            sec = timedelta(seconds=get)
            d = lovetime(1,1,1)+sec
        except:
            sec = timedelta(seconds=1)
            d = lovetime(1,1,1)+sec
        return "%dhour: %dmins: %dsec left"%(d.hour,d.minute,d.second)

    def CreateNet(self, evt):
        get = Network()
        get = get.GetStatus()
        if get=="Yes":
            dlg = CreateDialog(self,-1,"Create Network",((10,50)))
            var = dlg.ShowModal()
        else:
            dlg = wx.MessageDialog(self, 'Your computer does not support creating a network. You can try and create a network on the other computer '
                                         'and join from this computer.',
                               'Alert',
                               wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()

    def JoinNet(self, evt):
        dlg = JoinDialog(self,-1,"Join Network")
        var = dlg.ShowModal()

    def addingHistory(self, path, size, send):
        misc = Mics()
        tyme = time.strftime("%d/%m/%Y %H:%M %p")
        filename = path.split("\\")[-1]
        if filename=="":filename=path
        types = filename.split(".")[-1]
        database = History(filename=filename,size=str((size)),time_stamp=str(tyme),type="M",sender=send,path=path)
        database.save()
        self.populateHistory()

    def OnSend(self, evt):
        self.nb.SetSelection(1)
        mics = Mics()
        try:
            path = self.dir.FilePath
            size = os.path.getsize(path)
            if size>=150000000:
                dlg = wx.MessageDialog(self, 'You are not allowed to send more than the limit size (150Mb) for this version',
                "Not Allowed",wx.OK | wx.ICON_WARNING)
                dlg.ShowModal()
            else:
                self.addingHistory(path,size=mics.coverbyte(size),send=1)
                pub.sendMessage("file", real=path, path=path.split("\\")[-1], size=size)
        except:
            path = self.dir.GetPath()
            size = os.path.getsize(path)
            if size>=150000000:
                dlg = wx.MessageDialog(self, 'You are not allowed to send more than the limit size (150Mb) for this version',
                                       "Not Allowed",wx.OK | wx.ICON_WARNING)
                dlg.ShowModal()
            else:
                if len(path.split("\\"))==2:
                    dlg = wx.MessageDialog(self, 'You are trying to send from a location that might cause the application to crash. '
                                                 'If you are sure you know what you are doing, click Yes','Note!',
                                   wx.YES_NO | wx.ICON_WARNING)
                    if dlg.ShowModal()==wx.ID_YES:
                        self.addingHistory(path,size=mics.coverbyte(size),send=1)
                        pub.sendMessage("folder", path=path)
                    else:
                        pass
                else:
                    self.addingHistory(path,size=mics.coverbyte(size),send=1)
                    pub.sendMessage("folder", path=path)

    def OnCancel(self, evt):
        pub.sendMessage("stop",msg="")

    def OnPreference(self, evt):
        dlg = PrefDialog(self,-1,"Preference")
        var = dlg.ShowModal()
        if var == 5101:
            if dlg.his_id==1:
                self.populateHistory()

    def OnDisconncet(self, evt):
        pub.sendMessage("closewindow",msg="")
        #sp.check_output("netsh wlan stop hostednetwork")
        #sp.check_output("netsh wlan disconnect")
        self.status.SetStatusText("Disconnected!")

    def OnReconnect(self, evt):
        j = self.peers.GetCount()
        if j<1:
            new = Network()
            ip = new.GetJoinIP()
            reactor.connectTCP(str(ip) , 8000, ClientFactory())
        else:
            pass

    def aboutDialog(self, evt):
        info = wx.AboutDialogInfo()
        info.SetIcon(wx.Icon("img\icon.png",wx.BITMAP_TYPE_PNG))
        info.SetName("File Beamer")
        info.SetVersion("1.0.0")
        info.Description = wordwrap("Now you can send files from one computer to another without looking for mass storage devices. " \
                           "Files are sent wirelessly",250,wx.ClientDC(self))
        info.SetCopyright("(C) 2016 CreativeWorks Studio")
        info.WebSite = ("http://www.creativestart.tk","CreativeWorks")
        info.SetLicence("Hold On")
        info.AddDeveloper("Adelola Adedapo")

        wx.AboutBox(info)

    def OnCloseWindow(self, evt):
        pub.sendMessage("closewindow",msg="")
        new = Network()
        new.Stop()
        self.Destroy()

class EchoClient(LineReceiver):
    def __init__(self):
        pub.subscribe(self.filenameListener,"file")
        pub.subscribe(self.folderListener, "folder")
        pub.subscribe(self.cancelData,"stop")
        pub.subscribe(self.deleteQueue,"deletequeues")
        pub.subscribe(self.closed,"closewindow")
        self.filestate = 1
        self.folderstate = 1
        self.folderpath = ""
        self.filequeue = []
        self.folderqueue = []
        self.total = 0
        self.done = 0
        self.which = 0
        self.filecount = 0
        self.num = 0
        self.cancel = 0
        self.foldertab = 0
        self.count = 0
        self.overal = 0

    def connectionMade(self):
        pass

    def closed(self,msg):
        self.transport.loseConnection()

    def cancelData(self,msg):
        if not self.filestate:self.cancelOtherData()
        self.sendLine('{"canceldone":"1"}')

    def deleteQueue(self,msg,msg2):
        if msg2 == "1":
            try:
                del self.folderqueue[int(msg)]
            except:pass
        elif msg2 == "2":
            try:
                del self.filequeue[int(msg)]
            except:pass

    def deleteFolderQueue(self,msg):
        ind = int(msg)
        del self.folderqueue[ind]

    def cancelOtherData(self):
        self.transport.unregisterProducer()
        self.sendLine("cancel")
        if self.filequeue:
            pub.sendMessage("deletefile",msg="0")
            del self.filequeue[0:self.count]

    def filenameListener(self, real, path, size):
        if self.filestate == 1 and self.folderstate == 1:
            self.filestate = 0
            if self.count:
                self.count-=1
            data = {"filename":path,"size":size}
            jdata = js.dumps(data)
            self.sendLine(jdata)
            self.f = open(os.path.abspath(real), 'rb')
            self.sender = FileSender()
            self.sender.beginFileTransfer(self.f,self.transport).addCallback(self.otan)
        else:
            if path.find("\\")==-1:
                pub.sendMessage("filequeue",msg=path)
            self.filequeue.append([real,path,size])

    def monitor(self,data):
        pass

    def otan(self, lastsent):
        self.f.close()
        self.sendLine("done")

    def folderListener(self, path):
        if self.filestate == 1 and self.folderstate == 1:
            self.folderstate = 0
            self.folderpath = path
            get = folderHandle(path)
            buff = get.folderDetails()
            data = {"folder": buff[0],"files":buff[1],"filesize":buff[2]}
            self.count = buff[1]; self.overal=buff[1]
            jdata = js.dumps(data)
            self.sendLine(jdata)
            data = get.searchFolder()
            self.transport.write(data)
            self.sendLine("folderDone")
        else:
            pub.sendMessage("folderqueue",msg=path)
            self.folderqueue.append(path)

    def lineReceived(self, line):
        jdata = js.loads(line)
        self.decideData(jdata)

    def decideData(self, data):
        if "name" in data.keys():
            p = self.transport.getPeer()
            jdata = js.dumps(name)
            self.sendLine(jdata)
            pub.sendMessage("peers", name=data['name'],port=p.port)

        elif "canceldone" in data.keys():
            self.cancelOtherData()

        elif "disconnect" in data.keys():
            pub.sendMessage("close",msg="")

        elif "filename" in data.keys():
            self.which = 0
            self.proc = HandleFiles(data['filename'])
            self.proc.openFile()
            if self.num:
                self.filecount+=1
                self.num-=1
            else:
                self.filecount = 0
            pub.sendMessage("process", name=data['filename'],size=data['size'],num=str(self.filecount))
            self.setRawMode()

        elif "folder" in data.keys():
            self.which = 1
            self.num = int(data['files'])
            pub.sendMessage("updatefolder",msg=str(data['files']))
            self.proc = HandleFiles("None")
            self.proc.openFolder()
            self.setRawMode()

        elif "done" in data.keys():
            pub.sendMessage("donereceived",msg="")
            self.filestate = 1
            if self.filequeue:
                self.continueFileQueue()
            else:
                if self.folderqueue:
                    self.continueFolderQueue()
                else:
                    pass
        elif "doneFolder" in data.keys():
            self.folderstate = 1
            self.processFiles()

        elif "kepp" in data.keys():
            self.cancel = 0

    def createFolder(self):
        pro = folderHandle("None")
        pro.createFolder()

    def processFiles(self):
        path = self.folderpath+r"\\"
        get = folderHandle(path)
        files = get.getFiles()
        for i in files:
            self.filenameListener(i[1],i[0],i[2])

    def continueFolderQueue(self):
        if self.folderqueue:
            self.folderListener(self.folderqueue[0])
            del self.folderqueue[0]
        elif self.folderstate==1:
            self.continueFileQueue()

    def continueFileQueue(self):
        if self.filequeue:
            self.filenameListener(self.filequeue[0][0],self.filequeue[0][1],self.filequeue[0][2])
            del self.filequeue[0]
            pub.sendMessage("deletefile",msg="0")
        elif self.filestate==1:
            self.continueFolderQueue()

    def rawDataReceived(self, data):
        if "cancel\r\n" in data:
            self.sendLine('{"done":"1"}')
            self.setLineMode()
        if self.which == 1:
            get = self.proc.writeFolder(data)
            if get == 1:
                self.total = 0
                self.createFolder()
                self.sendLine('{"doneFolder":"1"}')
                self.setLineMode()
        elif self.which == 0:
            get = self.proc.writeFile(data)
            self.total+=len(data)
            pub.sendMessage("update",current=str(self.total),speed=len(data))
            if get == 1:
                self.total = 0
                pub.sendMessage("done",msg="")
                self.sendLine('{"done":"1"}')
                self.setLineMode()
            else:
                pass
        elif self.which == 3:
            pass

    def sendFileName(self, name):
        data = {"filename":name}
        jdata = js.dumps(data)
        self.sendLine(jdata)

class EchoServer(LineReceiver):
    def __init__(self,user):
        pub.subscribe(self.filenameListener,"file")
        pub.subscribe(self.folderListener, "folder")
        pub.subscribe(self.cancelData,"stop")
        pub.subscribe(self.deleteQueue,"deletequeues")
        pub.subscribe(self.closed,"closewindow")
        self.filestate = 1
        self.folderstate = 1
        self.folderpath = ""
        self.filequeue = []
        self.folderqueue = []
        self.total = 0
        self.done = 0
        self.which = 0
        self.filecount = 0
        self.num = 0
        self.cancel = 0
        self.foldertab = 0
        self.count = 0
        self.overal = 0
        self.user = user
        self.speed = 0

    def closed(self,msg):
        self.transport.loseConnection()

    def cancelData(self,msg):
        if not self.filestate:self.cancelOtherData()
        self.sendLine('{"canceldone":"1"}')

    def deleteQueue(self,msg,msg2):
        if msg2 == "1":
            try:
                del self.folderqueue[int(msg)]
            except:pass
        elif msg2 == "2":
            try:
                del self.filequeue[int(msg)]
            except:pass

    def deleteFolderQueue(self,msg):
        ind = int(msg)
        del self.folderqueue[ind]

    def cancelOtherData(self):
        self.transport.unregisterProducer()
        self.sendLine("cancel")
        if self.filequeue:
            pub.sendMessage("deletefile",msg="0")
            del self.filequeue[0:self.count]

    def filenameListener(self, real, path, size):
        if self.filestate == 1 and self.folderstate == 1:
            self.filestate = 0
            if self.count:
                self.count-=1
            data = {"filename":path,"size":size}
            jdata = js.dumps(data)
            self.sendLine(jdata)
            self.f = open(os.path.abspath(real), 'rb')
            self.sender = FileSender()
            self.sender.beginFileTransfer(self.f,self.transport).addCallback(self.otan)
        else:
            if path.find("\\")==-1:
                pub.sendMessage("filequeue",msg=path)
            self.filequeue.append([real,path,size])

    def monitor(self,data):
        pass

    def otan(self, lastsent):
        self.f.close()
        self.sendLine("done")

    def folderListener(self, path):
        if self.filestate == 1 and self.folderstate == 1:
            self.folderstate = 0
            self.folderpath = path
            get = folderHandle(path)
            buff = get.folderDetails()
            data = {"folder": buff[0],"files":buff[1],"filesize":buff[2]}
            self.count = buff[1]; self.overal=buff[1]
            jdata = js.dumps(data)
            self.sendLine(jdata)
            data = get.searchFolder()
            self.transport.write(data)
            self.sendLine("folderDone")
        else:
            pub.sendMessage("folderqueue",msg=path)
            self.folderqueue.append(path)

    def lineReceived(self, line):
        jdata = js.loads(line)
        self.decideData(jdata)

    def decideData(self, data):
        if "name" in data.keys():
            p = self.transport.getPeer()
            self.user[p.port] = self
            pub.sendMessage("peers", name=data['name'],port=p.port)

        elif "canceldone" in data.keys():
            self.cancelOtherData()

        elif "filename" in data.keys():
            self.which = 0
            self.proc = HandleFiles(data['filename'])
            self.proc.openFile()
            if self.num:
                self.filecount+=1
                self.num-=1
            else:
                self.filecount = 0
            pub.sendMessage("process", name=data['filename'],size=data['size'],num=str(self.filecount))
            self.setRawMode()

        elif "folder" in data.keys():
            self.which = 1
            self.num = int(data['files'])
            pub.sendMessage("updatefolder",msg=str(data['files']))
            self.proc = HandleFiles("None")
            self.proc.openFolder()
            self.setRawMode()

        elif "done" in data.keys():
            pub.sendMessage("donereceived",msg="")
            self.filestate = 1
            if self.filequeue:
                self.continueFileQueue()
            else:
                if self.folderqueue:
                    self.continueFolderQueue()
                else:
                    pass
        elif "doneFolder" in data.keys():
            self.folderstate = 1
            self.processFiles()

        elif "kepp" in data.keys():
            self.cancel = 0

    def createFolder(self):
        pro = folderHandle("None")
        pro.createFolder()

    def processFiles(self):
        path = self.folderpath+r"\\"
        get = folderHandle(path)
        files = get.getFiles()
        for i in files:
            self.filenameListener(i[1],i[0],i[2])

    def continueFolderQueue(self):
        if self.folderqueue:
            self.folderListener(self.folderqueue[0])
            del self.folderqueue[0]
        elif self.folderstate==1:
            self.continueFileQueue()

    def continueFileQueue(self):
        if self.filequeue:
            self.filenameListener(self.filequeue[0][0],self.filequeue[0][1],self.filequeue[0][2])
            del self.filequeue[0]
            pub.sendMessage("deletefile",msg="0")
        elif self.filestate==1:
            self.continueFolderQueue()

    def rawDataReceived(self, data):
        if "cancel\r\n" in data:
            self.sendLine('{"done":"1"}')
            self.setLineMode()
        if self.which == 1:
            get = self.proc.writeFolder(data)
            if get == 1:
                self.total = 0
                self.createFolder()
                self.sendLine('{"doneFolder":"1"}')
                self.setLineMode()
        elif self.which == 0:
            get = self.proc.writeFile(data)
            self.total+=len(data)
            pub.sendMessage("update",current=str(self.total),speed=len(data))
            if get == 1:
                self.total = 0
                pub.sendMessage("done",msg="")
                self.sendLine('{"done":"1"}')
                self.setLineMode()
            else:
                pass
        elif self.which == 3:
            pass

    def sendFileName(self, name):
        data = {"filename":name}
        jdata = js.dumps(data)
        self.sendLine(jdata)

    def connectionMade(self):
        jdata = js.dumps(name)
        self.sendLine(jdata)

    def connectionLost(self, reason):
        p = self.transport.getPeer()
        for key,value in self.user.iteritems():
            if key == p.port:
                pub.sendMessage("lost",name=p.port)
                del self.user[key]
                break

class ClientFactory(protocol.ClientFactory):
    def buildProtocol(self, addr):
        return EchoClient()

    def clientConnectionFailed(self, connector, reason):
        pass

    def clientConnectionLost(self, connector, reason):
        pub.sendMessage("lost", name="lost")

class ServerFactory(protocol.Factory):
    def __init__(self):
        self.users = {}

    def buildProtocol(self, addr):
        return EchoServer(self.users)

if __name__ == '__main__':
    app = wx.App()
    frame = MyApp(None,-1,'File Beamer Test Version (Beta)')
    frame.Show()
    frame.CenterOnScreen(True)
    reactor.registerWxApp(app)
    reactor.run()

