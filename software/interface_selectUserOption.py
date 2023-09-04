import interface_makeThePhotoScreen
import interface_controlMenuScreen
from tkinter import *
import logging

logger = logging.getLogger(__file__)

def startSelectUserOption(__terminalNumber, __getPeople, __LOCAL_PEOPLE_PATH,__version, __window,__mainFrame,__videoCapture, __eventRelease_videoShow,  __eventRelease_videoGet ,__eventBlock_videoShow, __eventBlock_videoGet, __eventManagerModeOpen, __securityCode, __mainDB, __videoQueue, __previousWindows=None):
    global terminalNumber, getPeople, LOCAL_PEOPLE_PATH,eventManagerModeOpen, selectUser, mainDB,mainFrame, eventRelease_videoGet ,eventBlock_videoShow, version,  eventBlock_videoGet, eventRelease_videoShow, videoQueue, videoCapture, window,mainFrame
    terminalNumber = __terminalNumber
    getPeople = __getPeople
    LOCAL_PEOPLE_PATH = __LOCAL_PEOPLE_PATH
    version = __version
    window = __window
    mainFrame = __mainFrame
    videoCapture = __videoCapture
    videoQueue = __videoQueue
    mainDB     = __mainDB
    eventRelease_videoGet  = __eventRelease_videoGet
    eventBlock_videoShow   = __eventBlock_videoShow
    eventBlock_videoGet    = __eventBlock_videoGet
    eventRelease_videoShow = __eventRelease_videoShow
    eventManagerModeOpen = __eventManagerModeOpen

    selectUser = Frame(window)
    selectUser.pack(anchor=W, fill=Y, expand=True, side=LEFT)
    if(__previousWindows != None):
        __previousWindows.destroy()
 
    button_makeThePhoto = Button(selectUser, text="Gestionar fotografías", width=20, height = 8, bg="khaki",activebackground="khaki", font=("Piboto Regular", 18),command = startMakeThePhoto).grid(column=0,rowspan=4, row=0, padx=2, pady=2, sticky="WENS")
    button_manageUsers =Label(selectUser, text=" ", width = 20, height = 8,font=("Piboto Regular", 18)).grid(column=0,rowspan=4, row=4, padx=2, pady=2, sticky="WENS")

    label_spacer = Label(selectUser, text=" ", width = 18, font=("Piboto Regular", 18)).grid(row=4,column=2, sticky="WENS" )
    button_back         = Button(selectUser, text="Atrás",          width=10, height = 3, bg="gray",  font =("Piboto Regular", 18),command = exit,    activebackground="gray").grid(row=5,column=3,rowspan = 3, sticky="WENS" )

def startMakeThePhoto():
    global eventRelease_videoGet ,eventBlock_videoShow,  eventBlock_videoGet, eventRelease_videoShow, eventManagerModeOpen, selectUser
    selectUser.pack_forget()
    selectUser.destroy()
    interface_makeThePhotoScreen.startSelectUserScreen(getPeople, LOCAL_PEOPLE_PATH,version, window,mainFrame,videoCapture, eventRelease_videoShow,  eventRelease_videoGet ,eventBlock_videoShow,  eventBlock_videoGet, eventManagerModeOpen , selectUser, mainDB, videoQueue)

def exit():
    global eventRelease_videoGet ,eventBlock_videoShow,  eventBlock_videoGet, eventRelease_videoShow, eventManagerModeOpen, selectUser

    selectUser.pack_forget()
    selectUser.destroy()
    interface_controlMenuScreen.startControlScreen(terminalNumber, getPeople, LOCAL_PEOPLE_PATH,version, window,mainFrame,videoCapture, eventRelease_videoShow,  eventRelease_videoGet ,eventBlock_videoShow,  eventBlock_videoGet, eventManagerModeOpen,mainDB,videoQueue, selectUser)
