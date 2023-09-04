from tkinter import *
import threading
import time
import os 
import socket 
import cv2
from subprocess import PIPE, run
import interface_selectUserOption
import interface_makeThePhotoScreen
import logging

logger = logging.getLogger(__file__)
menuWindow = False
def out(command):
    result = run(command, stdout=PIPE, stderr=PIPE, universal_newlines=True, shell=True)
    return result.stdout

def startControlScreen(__terminalNumber, __getPeople, __LOCAL_PEOPLE_PATH,__version, __window,__mainFrame,__videoCapture, __eventRelease_videoShow,  __eventRelease_videoGet ,__eventBlock_videoShow, __eventBlock_videoGet, __eventManagerModeOpen, __mainDB, __videoQueue, __previousWindows = None ):
    """Starts the control menu screen with a couple of options. This function also close the previous windows passed as argument.
    This managers has stopped other threads of the main code so a call to them must be done to resume these threads

    Args:
        __eventBlock (threading.event): This event was setted before to stop the threads untill an eventRelease will be sent. Must be cleared after eventRelease is setted up
        __eventRelease (threading.event): The main threads are waiting until this event will be set
        __eventManagerModeOpen ([type]): [description]
        __previousWindows ([type]): [description]
    """
    global terminalNumber, getPeople, LOCAL_PEOPLE_PATH,eventManagerModeOpen, menuWindow, mainDB,mainFrame, eventRelease_videoGet ,eventBlock_videoShow, version,  eventBlock_videoGet, eventRelease_videoShow, videoQueue, videoCapture, window,mainFrame
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

    menuWindow = Frame(window)
    menuWindow.pack(anchor=W, fill=Y, expand=True, side=LEFT)

    host_ip = ""
    host_ip = out("ip -4 -o addr show eth0 |awk '{print $4}' |cut -d '/' -f 1")
    if host_ip == "":
        host_ip = out("ip -4 -o addr show wlan0 |awk '{print $4}' |cut -d '/' -f 1")

    btn = Button(menuWindow, text="Gestionar\nusuarios", height = 5,bg="khaki",  width=20,  font = ("Piboto Regular", 18), command = startSelectUserWindow).grid(row=0,rowspan = 4, sticky="WENS")
    btnRestart = Button(menuWindow, text="Reiniciar", command = restart, height = 5,bg="deepskyblue", font = ("Piboto Regular", 18),width=20).grid(row=4,rowspan = 3, sticky="WENS")
    btn = Button(menuWindow, text="Apagar",   command = shutdown, height = 5,bg="tomato",font = ("Piboto Regular", 18), width=20).grid(row=7,rowspan = 3, sticky="WENS")
    Label(menuWindow, text = " ", width = 27).grid(row=6,column=3)
    Label(menuWindow, text = " ", width = 2).grid(row=0,column=4)
    btn = Button(menuWindow, text="Atrás", command = exit, activebackground="gray",font = ("Piboto Regular", 18),height = 5,width=14,bg="gray").grid(row=7,rowspan = 5,columnspan=2, column=4, sticky="WENS" )
    if not host_ip.endswith("\n"):
        host_ip = host_ip + "\n"
    labelText = "Versión del código  :\t" + version + "\n"+\
           "IP del dispositivo  :\t\t" + host_ip     +\
           "Número de terminal  :\t" + str(terminalNumber)
           #The host_ip had a \n at the end

    label_Info =Label(menuWindow, text = labelText ,font = ("Piboto Regular", 12), justify=LEFT, width = 35).grid(row=1,column=1,padx = 2, columnspan=4, sticky="W" )
    if(__previousWindows != None):
        __previousWindows.destroy()

def confirmationWindow(commandInput):
    global window, menuWindow
    confirmationWindow = Frame(window)
    confirmationWindow.pack(anchor=W, fill=Y, expand=True, side=LEFT)

    label_spacer0=Label(confirmationWindow, text = " ",height=2, width=4 ).grid(padx = 5, pady = 5, row=0,column=0)
    btnConfirm = Button(confirmationWindow, text="Confirmar", font=('Piboto Regular', 20),activebackground="salmon",  height = 12, width=18, bg="salmon",command = lambda :os.system(commandInput)).grid(column=1,row = 1,padx = 10, pady = 5, sticky="WENS")

    label_spacer1=Label(confirmationWindow, text = " ",height=2, width=2 ).grid(row=0,column=2)
    btnReject = Button(confirmationWindow, text="Atrás", font=('Piboto Regular', 20), height = 12,bg="gray", activebackground="gray", width=18, command = lambda :rejectConfirmationWindow(confirmationWindow)).grid(column=3,row = 1, sticky="WENS")

def rejectConfirmationWindow(confirmationWindow):
    confirmationWindow.destroy()
    menuWindow.pack(anchor=W, fill=Y, expand=True, side=LEFT)

def shutdown():
    global menuWindow
    menuWindow.pack_forget()
    confirmationWindow("sudo shutdown now")

def restart():
    global menuWindow
    menuWindow.pack_forget()
    confirmationWindow("sudo shutdown -r now")

def startSelectUserWindow():
    global eventRelease_videoGet ,eventBlock_videoShow,  eventBlock_videoGet, eventRelease_videoShow, eventManagerModeOpen, menuWindow
    menuWindow.pack_forget()
    menuWindow.destroy()
    interface_makeThePhotoScreen.startSelectUserScreen(terminalNumber, getPeople, LOCAL_PEOPLE_PATH,version, window,mainFrame,videoCapture, eventRelease_videoShow,  eventRelease_videoGet ,eventBlock_videoShow,  eventBlock_videoGet, eventManagerModeOpen , menuWindow, mainDB, videoQueue)

def exit():
    global eventRelease_videoGet, eventRelease_videoShow, eventBlock_videoShow,  eventBlock_videoGet, eventManagerModeOpen, mainFrame
    eventBlock_videoShow.clear()
    eventBlock_videoGet.clear()
    eventRelease_videoGet.set()
    eventRelease_videoShow.set()
    time.sleep(0.2)
    eventRelease_videoGet.clear()
    eventRelease_videoShow.clear()
    eventManagerModeOpen.clear()
    global menuWindow
    menuWindow.destroy()
    mainFrame.pack(anchor=W, fill=Y, expand=True, side=LEFT)
