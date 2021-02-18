#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.InputBox import InputBox
from Screens.HelpMenu import HelpableScreen
from Components.Sources.StaticText import StaticText
from Tools.Directories import *
from Components.config import ConfigSubsection, ConfigText, ConfigLocations, getConfigListEntry, configfile
from Components.config import config
import os
from Components.ActionMap import NumberActionMap, HelpableActionMap
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.Button import Button
from Components.FileList import FileList
from Components.MenuList import MenuList
from enigma import getDesktop
from os import environ
import gettext
from Components.Language import language
from Components.Harddisk import harddiskmanager
import os

###########################################################################

mountedDevs = []
for p in harddiskmanager.getMountedPartitions(True):
        mountedDevs.append((p.mountpoint, (_(p.description) if p.description else "")))

###########################################################################

PLUGIN_PATH = resolveFilename(SCOPE_PLUGINS, 'Extensions/PluginSkinMover')
mounted_string = "Nothing mounted at "


class storagedevicescreen(Screen, HelpableScreen):
    skin = '''
        <screen name="storagedevicescreen" position="center,center" title=" " size="1280,720" flags="wfNoBorder">
        <widget source="Title" render="Label" position="80,80" size="750,30" zPosition="3" font="Regular;26" transparent="1"/>
        <widget source="session.VideoPicture" render="Pig"  position="80,120" size="380,215" zPosition="3" backgroundColor="#ff000000"/>
        <widget source="text" render="Label" position="80,470" size="260,25" font="Regular;22" transparent="1" zPosition="1" foregroundColor="#ffffff" />
        <widget source="oktext" render="Label" position="540,596" size="660,25" font="Regular;22" transparent="1" zPosition="1" halign="left" valign="center" />
        <widget name="target" position="80,500" size="540,22" valign="left" font="Regular;22" transparent="1" />
        <widget name="filelist" position="550,120" size="610,503" zPosition="1" scrollbarMode="showOnDemand" selectionDisabled="1" transparent="1" />
	<ePixmap position="210,635" size="25,25" zPosition="0" pixmap="~/pic/button_red.png" transparent="1" alphatest="on"/>
	<ePixmap position="495,635" size="260,25" zPosition="0" pixmap="~/pic/button_green.png" transparent="1" alphatest="on"/>
        <widget source="key_red" render="Label" position="240,635" size="260,25" zPosition="1" font="Regular;20" halign="left" transparent="1" />
	<widget source="key_green" render="Label" position="525,635" size="260,25" zPosition="1" font="Regular;20" halign="left" transparent="1" />
        </screen>'''

    def __init__(self, session, text="", filename="", currDir=None, location=None, userMode=False, windowTitle=_("Choose backup location"), minFree=None, autoAdd=False, editDir=False, inhibitDirs=[], inhibitMounts=[]):
        Screen.__init__(self, session)
	self.skin_path = resolveFilename(SCOPE_PLUGINS, "Extensions/PluginSkinMover")
        HelpableScreen.__init__(self)
        self.skinName = 'storagedevicescreen'
        self["text"] = StaticText(_("Selected device location:"))
        self["oktext"] = StaticText(_(" "))
        self.text = text
        self.filename = filename
        self.minFree = minFree
        self.reallocation = location
        self.location = location and location.value[:] or []
        self.userMode = userMode
        self.autoAdd = autoAdd
        self.editDir = editDir
        self.inhibitDirs = inhibitDirs
        self.inhibitMounts = inhibitMounts
        inhibitDirs = ["/bin", "/boot", "/dev", "/lib", "/proc", "/sbin", "/sys", "/mnt", "/var", "/home", "/tmp", "/srv", "/etc", "/share", "/usr", "/ba", "/MB_Images"]
        inhibitMounts = ["/mnt", "/ba", "/MB_Images"]
        self["filelist"] = FileList(currDir, showDirectories=True, showFiles=False, inhibitMounts=inhibitMounts, inhibitDirs=inhibitDirs)
        self["mountlist"] = MenuList(mountedDevs)
	self["key_red"] = StaticText(_("Cancel"))
	self["key_green"] = StaticText(_("Save"))
        self["green"] = Pixmap()
        self["red"] = Pixmap()
        self["target"] = Label()
        if self.userMode:
            self.usermodeOn()

        class BackupLocationActionMap(HelpableActionMap):
            def __init__(self, parent, context, actions={}, prio=0):
                HelpableActionMap.__init__(self, parent, context, actions, prio)

        self["WizardActions"] = BackupLocationActionMap(self, "WizardActions",
            {
                "left": self.left,
                "right": self.right,
                "up": self.up,
                "down": self.down,
                "ok": (self.ok, _("Select")),
                "back": (self.cancel, _("Cancel")),
            }, -2)

        self["ColorActions"] = BackupLocationActionMap(self, "ColorActions",
            {
                "red": self.cancel,
                "green": self.select,
            }, -2)
        self.setWindowTitle()
        self.onLayoutFinish.append(self.switchToFileListOnStart)

    def setWindowTitle(self):
        self.setTitle(_("Choose target device location"))

    def switchToFileListOnStart(self):
        if self.reallocation and self.reallocation.value:
            self.currList = "filelist"
            currDir = self["filelist"].current_directory
            if currDir in self.location:
                self["filelist"].moveToIndex(self.location.index(currDir))
        else:
            self.switchToFileList()

    def switchToFileList(self):
        if not self.userMode:
            self.currList = "filelist"
            self["filelist"].selectionEnabled(1)
            self.updateTarget()

    def up(self):
        self[self.currList].up()
        self.updateTarget()

    def down(self):
        self[self.currList].down()
        self.updateTarget()

    def left(self):
        self[self.currList].pageUp()
        self.updateTarget()

    def right(self):
        self[self.currList].pageDown()
        self.updateTarget()

    def ok(self):
        if self.currList == "filelist":
            if self["filelist"].canDescent():
                self["filelist"].descent()
                self.updateTarget()

    def updateTarget(self):
        currFolder = self.getPreferredFolder()
        if currFolder is not None:
            self["target"].setText(''.join((currFolder, self.filename)))
        else:
            self["target"].setText(_("Invalid Location"))

    def cancel(self):
        self.close(False)

    def getPreferredFolder(self):
        if self.currList == "filelist":
            return self["filelist"].getSelection()[0]

    def saveSelection(self, ret):
        if ret:
            ret = ''.join((self.getPreferredFolder(), self.filename))
            config.PluginSkinMover.targetdevice.value = ret
            config.PluginSkinMover.targetdevice.save()
            print("175", config.PluginSkinMover.targetdevice.value)
            config.save()
            self.close(True)
        else:
            self.close(False)

    def checkmountBackupPath(self, path):
           	if path is None:
              		self.session.open(MessageBox, _("nothing entered"), MessageBox.TYPE_ERROR)
                        return False
           	else:
			sp = []
			sp = path.split("/")
			print(sp)
			if len(sp) > 1:
				if sp[1] != "media":
 	             			self.session.open(MessageBox, mounted_string + path, MessageBox.TYPE_ERROR)
					return False
			mounted = False
			self.swappable = False
			sp2 = []
                	f = open("/proc/mounts", "r")
       		 	m = f.readline()
        		while (m) and not mounted:
				if m.find("/%s/%s" % (sp[1], sp[2])) is not -1:
					mounted = True
					print(m)
					sp2 = m.split(" ")
					print(sp2)
					if sp2[2].startswith("ext") or sp2[2].endswith("fat"):
						print("[stFlash] swappable")
						self.swappable = True
           			m = f.readline()
			f.close()
			if not mounted:
 	             		self.session.open(MessageBox, mounted_string + str(path), MessageBox.TYPE_ERROR)
                                return False
		        if os.path.exists(config.PluginSkinMover.targetdevice.value):
		             try:
		 		os.chmod(config.PluginSkinMover.targetdevice.value, 0777)
                             except:
                                pass
                        return True

    def select(self):
        currentFolder = self.getPreferredFolder()
        foldermounted = self.checkmountBackupPath(currentFolder)
        if foldermounted == True:
           pass
        else:
           return
        if currentFolder is not None:
            if self.minFree is not None:
                try:
                    s = os.statvfs(currentFolder)
                    if (s.f_bavail * s.f_bsize) / 314572800 > self.minFree:
                        return self.saveSelection(True)
                except OSError:
                    pass
                self.session.openWithCallback(self.saveSelection, MessageBox, _("There might not be enough Space on the selected Partition.\nDo you really want to continue?"), type=MessageBox.TYPE_YESNO)
            else:
                self.saveSelection(True)
