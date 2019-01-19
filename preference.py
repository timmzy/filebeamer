__author__ = 'Adelola'
import wx
from database import History
import json as js
import os

class PrefDialog(wx.Dialog):
    his_id = 0
    def __init__(self, parent, id, title):
        wx.Dialog.__init__(self,parent,id,title,size=(420,330))

        vbox = wx.BoxSizer(wx.VERTICAL)
        pbox = wx.BoxSizer(wx.HORIZONTAL)
        nbox = wx.BoxSizer(wx.HORIZONTAL)

        ppbox = wx.StaticBox(self, -1, "User Profile name")

        profile = wx.StaticText(self,-1,"This name would be displayed to whichever user is connected "
                                        "to you.\nUsers can identify you by this")

        ppbsizer = wx.StaticBoxSizer(ppbox, wx.VERTICAL)
        ppbsizer.Add(profile,0,wx.BOTTOM,10)

        prof = wx.StaticText(self,-1,"Profile Name:")
        self.prof = wx.TextCtrl(self,-1,)

        pbox.Add(prof,0,wx.ALIGN_CENTER_VERTICAL|wx.RIGHT,5); pbox.Add(self.prof)

        ppbsizer.Add(pbox,0,wx.ALIGN_CENTER_HORIZONTAL|wx.BOTTOM,5)

        nnbox = wx.StaticBox(self, -1, "Network Options")

        network = wx.StaticText(self,-1,"This will serve as a default Hotspot name and password "
                                        "If this is\nselected, there will be no need to generate Hotspot name and \nrandom"
                                        " password each time you create a network")
        nnsizer = wx.StaticBoxSizer(nnbox,wx.VERTICAL)
        nnsizer.Add(network,0,wx.BOTTOM,10)

        net = wx.StaticText(self,-1,"Network Name:")
        self.net = wx.TextCtrl(self,-1,)


        pas = wx.StaticText(self,-1,"Password:")
        self.pas = wx.TextCtrl(self,-1,)

        self.populateField()

        nbox.Add(net,0,wx.ALIGN_CENTER_VERTICAL|wx.RIGHT,5)
        nbox.Add(self.net); nbox.Add(pas,0,wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.LEFT,5); nbox.Add(self.pas)

        nnsizer.Add(nbox)

        self.clear = wx.Button(self,-1,"Clear History")
        self.open = wx.Button(self,-1,"Open folder with files")
        self.save = wx.Button(self,-1,"Save")
        self.close = wx.Button(self,wx.ID_CANCEL,"Close")

        self.Bind(wx.EVT_BUTTON,self.OnClearHistory,self.clear)
        self.Bind(wx.EVT_BUTTON,self.OnSave,self.save)
        self.Bind(wx.EVT_BUTTON,self.OnOpen,self.open)
        bbox = wx.BoxSizer(wx.HORIZONTAL)
        bbox.Add(self.clear); bbox.Add(self.open)

        lbox = wx.BoxSizer(wx.HORIZONTAL)
        lbox.Add(self.save); lbox.Add(self.close)



        vbox.Add(ppbsizer,0,wx.TOP|wx.LEFT,15); vbox.Add(nnsizer,0,wx.TOP|wx.LEFT,15)
        vbox.Add(bbox,0,wx.ALIGN_CENTER_HORIZONTAL|wx.TOP,10); vbox.Add(lbox,0,wx.ALIGN_CENTER_HORIZONTAL|wx.TOP,5)

        self.SetSizer(vbox)
        self.CenterOnParent(True)

    def OnClearHistory(self, evt):
        dlg = wx.MessageDialog(self, 'Are you sure',
                               'Alert', wx.YES_NO | wx.ICON_WARNING)
        if dlg.ShowModal() == 5104:
            pass
        else:
            print "LOve"
            his = History.delete()
            his.execute()
            self.his_id = 1

    def OnSave(self, evt):
        with open("settings.json") as f:
            data = js.loads(f.read())
        profile = self.prof.GetValue()
        netwrk = self.net.GetValue()
        key = self.pas.GetValue()
        if profile == "":
            dlg = wx.MessageDialog(self, 'You have no profile name',
                               'Alert!', wx.OK | wx.ICON_WARNING)
            dlg.ShowModal()
        elif not netwrk == "" and key == "":
            dlg = wx.MessageDialog(self, 'Password missing',
                               'Alert!', wx.OK | wx.ICON_WARNING)
            dlg.ShowModal()
        elif netwrk == "" and not key == "":
            dlg = wx.MessageDialog(self, 'Network name missing',
                               'Alert!', wx.OK | wx.ICON_WARNING)
            dlg.ShowModal()
        data['name'] = str(profile); data['network'] = str(netwrk); data['password'] = key
        with open('settings.json','w') as f:
            f.write(js.dumps(data))
        self.Destroy()

    def OnOpen(self, evt):
        with open('settings.json') as f:
            data = f.read()
        jdata = js.loads(data)
        path = jdata['local']
        path = path.replace("\\",r"\\")
        os.startfile(os.path.abspath(path))

    def populateField(self):
        with open("settings.json") as f:
            data = f.read()
        jdata = js.loads(data)
        self.prof.SetValue(jdata['name'])
        self.net.SetValue(jdata['network'])
        self.pas.SetValue(jdata['password'])