#Admin screen control

from tkinter import *
import threading
import time
import interface_controlMenuScreen
import cv2
import logging

logger = logging.getLogger(__file__)

label_SecutiryCode = None
stringSecutiryCode = ""
stringMask = ""

eventRelease_videoGet  = False
eventBlock_videoShow   = False
eventBlock_videoGet    = False
eventRelease_videoShow = False
secutiryCheckWindow    = False

securityCode = ""

def loadSecutiryScreen(secutiryCheckWindow):
    """This function starts a new window that ask for a password that must be configured on any of the config.json files of the proyect.

    Args:
        secutiryCheckWindow (tk): The windows tkinter manager for this windows
    """

    global label_SecutiryCode
    label_SecutiryCode = Label(secutiryCheckWindow, text = "", bg = "white", fg="black", font="System 25 bold", width=21)
    label_SecutiryCode.grid(column=1, row=1, columnspan=3, pady = 5, padx = 25, rowspan=2, sticky="WENS")# , columnspan=9)
    #label_SecutiryCode.focus()
    #Num pad
    addNumPad(secutiryCheckWindow, 1, 3)
    Button(secutiryCheckWindow, text="Atrás", height = 3,font = ("Piboto Regular", 18), bg="gray",width=12,activebackground="gray", command = exit).grid(rowspan = 4, row=12,column=12, sticky="WENS", padx=50)

def addNumPad(secutiryCheckWindow, c, r):
    cBase = c
    count = 0
    while count < 12:
        count = count +1
        if count < 10 :
            btn = Button(secutiryCheckWindow, text=count, width=2, height = 2, font="System 26 bold",  activebackground = "lightgrey", command = lambda arg = count:inputSecurityNumber(arg))
        elif count == 11:
            btn = Button(secutiryCheckWindow, text="0", width=2, height = 2, font="System 26 bold", activebackground = "lightgrey", command = lambda arg = 0 :inputSecurityNumber(0))

        elif count == 10:
            btn = Button(secutiryCheckWindow, text="Borrar", width=2, height = 1, bg="tomato", activebackground = "tomato",font=("Piboto Regular", 18),  command = clearSecurityNumber)
        elif count == 12:
            btn = Button(secutiryCheckWindow, text="Aceptar", width=2, height = 1, bg="khaki",  activebackground = "khaki", font=("Piboto Regular", 18),command = confirmSecurityCode)

        btn.grid(row=r,column=c, sticky="WENS", rowspan=2 )
        c = c+1
        if c>cBase+2:
            c = cBase
            r = r+3

def confirmSecurityCode():
    if(securityCode == stringSecutiryCode):
        logger.info("security code access success")
        clearSecurityNumber()
        startControlWindow()
    else:
        logger.warning("security code access FAIL")
        clearSecurityNumber()

def startControlWindow():
    global eventRelease_videoGet ,eventBlock_videoShow,  eventBlock_videoGet, eventRelease_videoShow, eventManagerModeOpen, secutiryCheckWindow, window
    interface_controlMenuScreen.startControlScreen(terminalNumber, getPeople, LOCAL_PEOPLE_PATH,version, window,mainFrame,videoCapture, eventRelease_videoShow,  eventRelease_videoGet ,eventBlock_videoShow,  eventBlock_videoGet, eventManagerModeOpen, mainDB, videoQueue, secutiryCheckWindow )

def inputSecurityNumber(arg):
    global stringSecutiryCode, stringMask, label_SecutiryCode
    stringSecutiryCode =  stringSecutiryCode+str(arg)
    logger.info("Input code #" + stringSecutiryCode)
    stringMask = stringMask + "*"
    label_SecutiryCode.configure(text = stringMask)

def clearSecurityNumber():
    global stringSecutiryCode, stringMask, label_SecutiryCode   
    stringSecutiryCode = ""
    stringMask = ""
    label_SecutiryCode.configure(text = stringMask)

def exit():
    global eventRelease_videoGet ,eventBlock_videoShow,  eventBlock_videoGet, eventRelease_videoShow, eventManagerModeOpen
    clearSecurityNumber()
    eventBlock_videoShow.clear()
    eventBlock_videoGet.clear()
    eventRelease_videoGet.set()
    eventRelease_videoShow.set()
    time.sleep(0.2)
    eventRelease_videoGet.clear()
    eventRelease_videoShow.clear()
    eventManagerModeOpen.clear()
    global secutiryCheckWindow
    secutiryCheckWindow.pack_forget()
    secutiryCheckWindow.destroy()
    mainFrame.pack(anchor=W, fill=Y, expand=True, side=LEFT)

def startSecurityCodeWindow(__terminalNumber, __getPeople, __LOCAL_PEOPLE_PATH,__version, __window,__mainFrame,__videoCapture, __eventRelease_videoShow,  __eventRelease_videoGet ,__eventBlock_videoShow, __eventBlock_videoGet, __eventManagerModeOpen, __securityCode, __mainDB, __videoQueue):
    """This code starts a new window and hold multiple event managers. 
    This managers has stopped other threads of the main code so a call to them must be done to resume these threads

    Args:
        __eventBlock (threading.event): This event was setted before to stop the threads untill an eventRelease will be sent. Must be cleared after eventRelease is setted up
        __eventRelease (threading.event): The main threads are waiting until this event will be set
        __eventManagerModeOpen (threading.event): [description]
        __securityCode (threading.event): [description]
    """
    global terminalNumber,  getPeople, LOCAL_PEOPLE_PATH,eventRelease_videoGet ,window, eventBlock_videoShow, mainFrame, eventBlock_videoGet, eventRelease_videoShow, secutiryCheckWindow, eventManagerModeOpen, version, securityCode,mainDB, videoQueue, videoCapture
    terminalNumber = __terminalNumber
    getPeople = __getPeople
    LOCAL_PEOPLE_PATH = __LOCAL_PEOPLE_PATH
    version = __version
    window = __window
    mainFrame    = __mainFrame
    videoCapture = __videoCapture
    videoQueue = __videoQueue
    mainDB          = __mainDB
    eventRelease_videoGet  = __eventRelease_videoGet
    eventBlock_videoShow   = __eventBlock_videoShow
    eventBlock_videoGet    = __eventBlock_videoGet
    eventRelease_videoShow = __eventRelease_videoShow

    eventManagerModeOpen = __eventManagerModeOpen
    securityCode         = __securityCode
    secutiryCheckWindow  = Frame(__window)
    secutiryCheckWindow.pack(anchor=W, fill=Y, expand=True, side=LEFT)

    loadSecutiryScreen(secutiryCheckWindow)

