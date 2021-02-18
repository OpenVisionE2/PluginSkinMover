#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function
#######################################################################
# maintainer: <schomi@vuplus-support.org> 
# This plugin is free software, you are allowed to
# modify it (if you keep the license),
# but you are not allowed to distribute/publish
# it without source code (this version and your modifications).
# This means you also have to distribute
# source code of your modifications.
#######################################################################
'''The code written by Schomi
extended by mfaraj57
-settings added to select target device,/media/usb is available in original plugin
-more info about free and total space of flash and target device
-update size info after moving any plugin
-removed bytes2human modules and replaced by local functions
'''
from Components.ActionMap import ActionMap
from Components.config import config, getConfigListEntry, ConfigSubsection, ConfigText, ConfigSelection, ConfigYesNo, NoSave, ConfigNothing, ConfigNumber
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
from Plugins.Plugin import PluginDescriptor
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.Standby import TryQuitMainloop
from Tools.Directories import *
from Tools.LoadPixmap import LoadPixmap
from enigma  import eTimer
from Tools import Notifications
from os import listdir, remove, rename, system, path, symlink, chdir, statvfs
from os import path as os_path
from os import walk as os_walk
from os.path import join, getsize
import shutil

from __init__ import _

pname = _("PluginSkinMover")
pdesc = _("Move plugins between flash memory and pen drive")
pversion = "0.6" ## extended by mfaraj57
pdate = "201406013"

# PluginSkinMover
config.PluginSkinMover = ConfigSubsection()
config.PluginSkinMover.targetdevice=ConfigText(default="/media/usb", fixed_size=False)
def foldersize(size):
         try:
            fspace=round(float((size) / (1024.0*1024.0)), 2)        
	    #tspace=round(float((capacity) / (1024.0 * 1024.0)),1)
            spacestr=str(fspace)+'MB'
            return spacestr
         except:
            return ""

def freespace(folder='/'):
         try:  
            diskSpace = os.statvfs(folder)
            capacity = float(diskSpace.f_bsize * diskSpace.f_blocks)
            available = float(diskSpace.f_bsize * diskSpace.f_bavail)
            fspace=round(float((available) / (1024.0*1024.0)), 2)        
	    tspace=round(float((capacity) / (1024.0 * 1024.0)), 1)
            spacestr='Free space(' +str(fspace)+'MB) Total space(' + str(tspace)+'MB)'
            return spacestr
         except:
            return "location is unavaiable or not mounted"

def Plugins(**kwargs):
	return [PluginDescriptor(name=_("PluginSkinMover"), description=_("Move your Plugins and skins"), where=PluginDescriptor.WHERE_PLUGINMENU, icon="plugin.png", fnc=main),
		PluginDescriptor(name="PluginSkinMover", description=_("Move your Plugins and skins"), where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=main)]

def main(session, **kwargs):
	print("[PluginSkinMover]: Started ...")
	session.open(PluginSkinMoverScreen)

class PluginSkinMoverScreen(Screen):
	skin = """
		<screen position="center,center" size="1000,520" title="">
		<widget name="info" position="10,10" size="830,60" font="Regular;24" foregroundColor="#00fff000"/>
		<widget source="menu" render="Listbox" position="10,80" size="630,360" zPosition="5" scrollbarMode="showOnDemand" transparent="1">
			<convert type="TemplatedMultiContent">
				{"template":
					[
						MultiContentEntryPixmapAlphaTest(pos = (2, 2), size = (54, 54), png = 1),
						MultiContentEntryText(pos = (60, 13), size = (100, 30), font=0, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER, text = 2),
						MultiContentEntryText(pos = (170, 13), size = (450, 30), font=0, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER, text = 0),
					],
					"fonts": [gFont("Regular", 22),gFont("Regular", 16)],
					"itemHeight": 60
				}
			</convert>
		</widget>
		<widget name="Picture" position="780,240" size="100,40" alphatest="on" />
		<ePixmap position="10,455" size="25,25" zPosition="0" pixmap="~/pic/button_red.png" transparent="1" alphatest="on"/>
		<ePixmap position="215,455" size="185,25" zPosition="0" pixmap="~/pic/button_green.png" transparent="1" alphatest="on"/>
		<ePixmap position="500,455" size="185,25" zPosition="0" pixmap="~/pic/button_yellow.png" transparent="1" alphatest="on"/>
		<ePixmap position="785,455" size="185,25" zPosition="0" pixmap="~/pic/button_blue.png" transparent="1" alphatest="on"/>
                <widget source="key_red" render="Label" position="40,455" size="185,25" zPosition="1" font="Regular;20" halign="left" transparent="1" />
		<widget source="key_green" render="Label" position="245,455" size="185,25" zPosition="1" font="Regular;20" halign="left" transparent="1" />
		<widget source="key_yellow" render="Label" position="530,455" size="185,25" zPosition="1" font="Regular;20" halign="left" transparent="1" />
		<widget source="key_blue" render="Label" position="815,455" size="185,25" zPosition="1" font="Regular;20" halign="left" transparent="1" />
        </screen>"""
	
	def __init__(self, session):
		Screen.__init__(self, session)
		self.skin_path = resolveFilename(SCOPE_PLUGINS, "Extensions/PluginSkinMover")
		self.session = session
		
		self.title = pname + " (" + pversion + ")"
		try:
			self["title"]=StaticText(self.title)
		except:
			print('self["title"] was not found in skin')
		self["info"] = Label("Please wait..")				
		self["Picture"] = Pixmap()
		self["key_red"] = StaticText(_("Exit"))
		self["key_green"] = StaticText(_("in Flash"))
		self["key_yellow"] = StaticText(_("Settings"))
		self["key_blue"] = StaticText(_("SkinMover"))
		menu_list = []
		self["menu"] = List(menu_list)
		self["shortcuts"] = ActionMap(["SetupActions", "ColorActions", "DirectionActions"],
		{
			"ok": self.startmoving,
			"cancel": self.keyCancel,
			"red": self.keyCancel,
			"green": self.startmoving,
			'blue': self.skinmover,
			"yellow": self.showsettings,
		}, -2)
		
		self.plugin_base_dir = resolveFilename(SCOPE_PLUGINS, "Extensions")
		try:
		         targetlocation=config.PluginSkinMover.targetdevice.value
		except:
		         targetlocation="/media/usb"
		self.mount_dir = targetlocation
		self.ext_dir = targetlocation+"/Extensions"
		self.enabled_pic = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, "Extensions/PluginSkinMover/pic/loc_flash.png"))
		self.disabled_pic = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, "Extensions/PluginSkinMover/pic/loc_media.png"))
		if not self.selectionChanged in self["menu"].onSelectionChanged:
			self["menu"].onSelectionChanged.append(self.selectionChanged)
		
		#self.onLayoutFinish.append(self.createMenuList)
		self.timer = eTimer()
                self.timer.callback.append(self.createMenuList)
                self.timer.start(50, 1)
	
        def startmoving(self):
                self["info"].setText("Moving plugin,please wait...")
		self.timer = eTimer()
                self.timer.callback.append(self.runMenuEntry)
                self.timer.start(50, 1)        
        
        def skinmover(self):
            from skinmover import SkinMoverScreen 
            self.session.open(SkinMoverScreen)
        
        def showsettings(self):
                     from settings import storagedevicescreen
                     self.session.openWithCallback(self.selectionChanged, storagedevicescreen)	    
        
        def selectionChanged(self,result=None):
                if result==True:
                   self.createMenuList()
		try:
		         sel = self["menu"].getCurrent()
		except:
		         return
		try:
                  self.setPicture(sel[0])
		  if sel[1] == self.enabled_pic:
			self["key_green"].setText(_("in Flash"))
		  elif sel[1] == self.disabled_pic:
			self["key_green"].setText(_("Exported"))
		except:
                  pass
		self.getdevices_sizes()	
		# Flash size
        def getdevices_sizes(self):
		freeflash='Unable to read flash size'
		try:
                   stat = statvfs("/")
                   freeflash = freespace("/")#bytes2human(freeflash, 1)
		except:
                   pass
		# Device size
		freedev="The device is unavailable or not mounted"
		try:
			#stat = statvfs(self.mount_dir)
			devicelocation=config.PluginSkinMover.targetdevice.value
			self.mount_dir=devicelocation
			freedev =devicelocation+" "+ freespace(devicelocation)
		except:
			try:
			         devicelocation=config.PluginSkinMover.targetdevice.value
			except:
			         devicelocation='unknown'
			freedev =devicelocation+" "+ freedev
                        pass
		#freedev = (stat.f_bavail or stat.f_bfree) * stat.f_bsize
		self["info"].setText(_("Flash: %s \n Device: %s") % (freeflash, freedev))

	def createMenuList(self):
		self["info"].setText(_("read ..."))
		chdir(self.plugin_base_dir)
		f_list = []
		list_dir = sorted(listdir(self.plugin_base_dir))
#		print(list_dir)
		for f in list_dir:
			linked_dir = self.plugin_base_dir + "/" + f
			if os_path.isdir(linked_dir):
				# Flash size
				try:
					stat = statvfs(linked_dir)
				except OSError:
					return -1
				free = self.GetFolderSize(linked_dir)
				size = str(foldersize(free))
				#pic
				pic = self.enabled_pic
				if path.exists(linked_dir):
					if path.islink(linked_dir):
						pic = self.disabled_pic
					else:
						pic = self.enabled_pic
					f_list.append((f, pic, size))
			
		menu_list = []
		for entry in f_list:
		        print("166", entry)
			menu_list.append((entry[0], entry[1], str(entry[2])))
		self["menu"].updateList(menu_list)
		self.selectionChanged(False)

	def setPicture(self, f):
		preview = self.plugin_base_dir + "/" + f + "/" + "plugin.png"
		if not path.exists(preview):
			preview = self.plugin_base_dir + "/" + f + "/" + f.lower() + ".png"
		if path.exists(preview):
			self["Picture"].instance.setPixmapFromFile(preview)
			self["Picture"].show()
		else:
			self["Picture"].hide()
	
	def keyCancel(self):
		self.close()

	def runMenuEntry(self):
		try:
                   devicelocation=config.PluginSkinMover.targetdevice.value
		   self.mount_dir=devicelocation
		   print("242", self.mount_dir)
                except:
                   pass
		if os_path.ismount(self.mount_dir):
			self["info"].setText(_("Moving, please wait ..."))
			sel = self["menu"].getCurrent()
			inflash = self.plugin_base_dir + "/" + sel[0]
                        self.ext_dir = self.mount_dir+"/Extensions" 
			notinflash = self.ext_dir + "/" + sel[0]
			print("[PluginSkinMover] " + inflash)
			print("[PluginSkinMover] " + notinflash)
			print("[PluginSkinMover] Start movement!")
			error = False
			if sel[1] == self.enabled_pic:
				if path.exists(notinflash):
					shutil.rmtree(notinflash)
				debug=True
                                try:
					shutil.copytree(inflash, notinflash)
					error = False
				except:
					error = True
					print("[PluginSkinMover] Error during movement!")
				if error == False:
				        try:
					  shutil.rmtree(inflash)
					  symlink(notinflash, inflash)
				        except:
				          pass
			elif sel[1] == self.disabled_pic:
				if path.islink(inflash):
					remove(inflash)
					debug=True
					try:
						shutil.copytree(notinflash, inflash)
						error = False
					except:
						error = True
						print("[PluginSkinMover] Error during movement!")
					if error == False:
						try:
						         shutil.rmtree(notinflash)
						except:
						         pass
			if error:
				self.session.open(MessageBox, _("Plugin movement was not successful, please check devices!"), type=MessageBox.TYPE_ERROR, timeout=10)
				error = False
			self.createMenuList()
		else:
			self.session.open(MessageBox, _("No device to %s mounted. Plugin movement is not possible!") % self.mount_dir, type=MessageBox.TYPE_ERROR, timeout=10)
                self.selectionChanged()
	def GetFolderSize(self, path):
		TotalSize = 0
		for item in os_walk(path):
			for file in item[2]:
				try:
					TotalSize = TotalSize + getsize(join(item[0], file))
				except:
					print("error with file:  " + join(item[0], file))
		return TotalSize
