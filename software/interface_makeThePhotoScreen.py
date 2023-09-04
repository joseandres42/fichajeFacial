
from tkinter import *
import threading
import interface_controlMenuScreen
import time
import cv2
from PIL import Image, ImageTk
from queue import Queue
import numpy as np
import sys
import os, re
import logging

logger = logging.getLogger(__file__)
video_Queue = Queue(maxsize=0)
foto_Queue  = Queue(maxsize=0)
eventPause_videoShow = threading.Event()
eventResume_videoShow= threading.Event()
localPeoplePath = os.path.dirname(__file__) + R"/localPeople/"
def startSelectUserScreen(__terminalNumber, __getPeople, __LOCAL_PEOPLE_PATH,__version, __window,__mainFrame,__videoCapture, __eventRelease_videoShow,  __eventRelease_videoGet ,__eventBlock_videoShow, __eventBlock_videoGet,__eventManagerModeOpen, __previousWindows, __mainDB, __videoQueue):
    global terminalNumber, getPeople,state_DeletePictures,buttonDelete,  LOCAL_PEOPLE_PATH,eventRelease_videoGet,window,mainFrame ,videoCapture, version, eventBlock_videoShow,  eventBlock_videoGet, eventRelease_videoShow, eventManagerModeOpen, selectUserWindows, mainDB, videoQueue, videoWidget, eventExit_videoShow
    #Global variables declaration and set
    terminalNumber      = __terminalNumber
    getPeople           = __getPeople
    LOCAL_PEOPLE_PATH   = __LOCAL_PEOPLE_PATH
    version             = __version
    window              = __window
    mainFrame           = __mainFrame
    videoCapture        = __videoCapture
    videoQueue          = __videoQueue
    mainDB              = __mainDB
    eventRelease_videoGet  = __eventRelease_videoGet
    eventBlock_videoShow   = __eventBlock_videoShow
    eventBlock_videoGet    = __eventBlock_videoGet
    eventRelease_videoShow = __eventRelease_videoShow
    eventManagerModeOpen   = __eventManagerModeOpen
    selectUserWindows      = Frame(__window)
    selectUserWindows.pack(anchor=W, fill=Y)#, expand=True, side=LEFT)
    
    state_DeletePictures = False
    #spacer to grid the rest
    addSelectBoxToWindow()
    addButtonsToWindow()
    if(__previousWindows != None):
        __previousWindows.destroy()

    eventExit_videoShow= threading.Event()

    #Graphics window
    imageFrame = Frame(selectUserWindows, width=50, height=50)
    imageFrame.grid(row=0, column=0, padx = 5, pady=2, columnspan = 1, rowspan = 1, sticky="WENS")
    videoWidget = Label(imageFrame, width=260, height=340)
    videoWidget.grid(row=0,column=0, sticky="WENS")

    getVideo = controlThread(eventExit_videoShow)
    vt = videoShow(eventExit_videoShow) #Start video showing thread

def addButtonsToWindow():
    global selectUserWindows, button_acceptPhoto, button_rejectPhoto, buttonAccept, back_Button, button_managePictures, buttonDelete
    buttonAccept       = Button(selectUserWindows, text="Hacer\nfotografía",       command = makePhoto, height = 4, bg="gray",font = ("Piboto Regular", 18),activebackground ="gray", width=15, state = "disabled")
    buttonAccept.grid(row=2,column=0,columnspan = 1, sticky="WENS" )
    buttonDelete       = Button(selectUserWindows, text="Borrar\nfotografía",       command = removeSelectedPicture,bg="tomato",font = ("Piboto Regular", 18),activebackground="tomato", height = 4,  width=15)

    back_Button         = Button(selectUserWindows, text="Atrás",                  command = exit,        bg="gray",   height = 4,  width=15, font = ("Piboto Regular", 18), activebackground="gray")
    back_Button.grid(row=2,column=3,columnspan = 3, sticky="WENS" )
    button_managePictures= Button(selectUserWindows, text="Gestionar\nfotografías",command = manageUserPictures, bg="gray",font = ("Piboto Regular", 18),activebackground ="gray", height = 4, width=15,state = "disabled")
    button_managePictures.grid(row=2,column=1,columnspan = 2,sticky="WENS" )
    
    button_acceptPhoto   = Button(selectUserWindows, text="Aceptar",               command = acceptPhoto, bg="khaki",font = ("Piboto Regular", 18),activebackground ="khaki",   height = 4)#.grid(row=4,column=3,sticky="WENS" )
    button_rejectPhoto   = Button(selectUserWindows, text="Rechazar",              command = rejectPhoto, bg="tomato",font = ("Piboto Regular", 18),activebackground="tomato", height = 4)#.grid(row=4,column=2,sticky="WENS" )

def backFromDeletePictures():
    global buttonAccept, listNodeUsers, scrollbarUsers, listNodePictures, scrollbarPictures, buttonDelete
    buttonAccept['state']="disabled"
    button_managePictures['state']="disabled"
    button_managePictures.grid(row=2,column=1,columnspan = 2,sticky="WENS" )
    buttonAccept.grid(row=2,column=0,columnspan = 1, sticky="WENS" )
    buttonDelete.grid_remove()
    listNodePictures.grid_remove()
    listNodeUsers.grid(column=1,columnspan = 3,row=0,padx = 5, pady = 5,sticky="WENS")
    scrollbarPictures.grid_remove()
    scrollbarUsers.grid(column=4,row=0,sticky="WENS")
    eventPause_videoShow.clear()
    eventResume_videoShow.set()

def manageUserPictures(preSelectedUser = None):
    global listNodeUsers, buttonAccept, button_managePictures,scrollbarUsers, scrollbarPictures, listNodePictures, state_DeletePictures, buttonDelete, currentSelectedUser

    buttonDelete.grid(row=2,column=2, sticky="WENS" )
    buttonAccept.grid_remove()
    eventResume_videoShow.clear()
    eventPause_videoShow.set()
    state_DeletePictures = True
    buttonAccept.config(state="disabled")
    button_managePictures.grid_remove()
    logger.info("Usuario seleccionado")
    mainDBList = mainDB.USUARIOS.getList()
    mainDBList.sort(key=lambda x: x[1], reverse=False)#ORDENADO POR APELLIDO
    exit = False
    if preSelectedUser == None:
        try:
            posSelected = listNodeUsers.curselection()[0]
            currentSelectedUser = posSelected
        except:
            backFromDeletePictures()
            exit = True
    else:
        posSelected = preSelectedUser
    if not exit:
        filename = mainDBList[posSelected][0] + "_" + mainDBList[posSelected][2] + "_local_" #+ str(number) + ".jpg"
        logger.info("Buscando archivos que empiecen por " + filename)
        if not os.path.exists(localPeoplePath):
                os.makedirs(localPeoplePath)
        listOfPictures = os.listdir(localPeoplePath)
        count = 0
        listOfPictures.sort()#ORDENADO ALFABETICAMENTE
        logger.info(str(listOfPictures)+"\n")
        userLocalPics = []
        listNodePictures.delete(0, END)
        for file in listOfPictures:
            if(file.startswith(filename) == True):#.startwith(filename)):
                logger.info("Coincidencia")
                count = count +1
                userLocalPics.append(file)
                listNodePictures.insert(END, file)
        logger.info("Encontrados {} archivos".format(count))
        if(count >0):
            imgTk = ImageTk.PhotoImage(Image.open(localPeoplePath + userLocalPics[0]))
            videoWidget.config(image = imgTk)
            videoWidget.imgtk = imgTk
            
            listNodeUsers.grid_remove()
            listNodePictures.grid(column=1,columnspan = 3,row=0,padx = 5, pady = 5,sticky="WENS")
            scrollbarUsers.grid_remove()
            scrollbarPictures.grid(column=5,row=0,sticky="WENS")
        else:
            backFromDeletePictures()

def onPictureSelect(evt):
    global videoWidget, eventResume_videoShow, eventPause_videoShow
    w = evt.widget    
    index = int(w.curselection()[0])
    fileName = w.get(index)
    logger.info ('You selected item {}: {}'.format(index, fileName))
    size = 260, 340
    img = Image.open(localPeoplePath + fileName)
    img.thumbnail(size)#, Image.ANTIALIAS)
    #img_resized = resize_and_crop(localPeoplePath + fileName,size )
    imgTk = ImageTk.PhotoImage(img)
    videoWidget.config(image = imgTk)
    videoWidget.imgtk = imgTk        

def onPersonSelect(evt):
    global button_managePictures, listNodeUsers, mainDB
    w = evt.widget    
    index = int(w.curselection()[0])
    posSelected = listNodeUsers.curselection()[0]
    mainDBList = mainDB.USUARIOS.getList()
    mainDBList.sort(key=lambda x: x[1], reverse=False)#ORDENADO POR APELLIDO
    filename = mainDBList[posSelected][0] + "_" + mainDBList[posSelected][2] + "_local_" #+ str(number) + ".jpg"
    buttonAccept.config(state=NORMAL)
    buttonAccept.config(bg="khaki")
    buttonAccept.config(activebackground="khaki")
    
    thereIsAnyPicture = False
    for f in os.listdir(localPeoplePath):
        if re.match(filename, f):
            thereIsAnyPicture = True
    if(thereIsAnyPicture):
        #pongoBotonDeBorrarHabilitado
        button_managePictures.config(state=NORMAL)
        button_managePictures.config(bg="tomato")
        button_managePictures.config(activebackground ="tomato")
    else:
        #Deshabilito el botón
        button_managePictures.config(state="disabled")
        button_managePictures.config(bg="gray")
        button_managePictures.config(activebackground ="gray")

def acceptPhoto():
    global button_acceptPhoto, button_rejectPhoto, foto_Queue, listNodeUsers, button_managePictures
    logger.info("Foto aceptada, añadiendo...")
    if (not foto_Queue.empty()):
        actualPicture = foto_Queue.get()
        actualPicture = cv2.cvtColor(actualPicture, cv2.COLOR_RGB2BGR)
        if not os.path.exists(localPeoplePath):
            os.makedirs(localPeoplePath)
        posSelected = listNodeUsers.curselection()[0]
        
        mainDBList = mainDB.USUARIOS.getList()
        mainDBList.sort(key=lambda x: x[1], reverse=False)#ORDENADO POR APELLIDO
        number = 1
        logger.info(mainDBList[posSelected])
        filename = mainDBList[posSelected][0] + "_" + mainDBList[posSelected][2] + "_local_" #+ str(number) + ".jpg"
        exit = False
        while(not exit):
            if(os.path.isfile(localPeoplePath +filename+ str(number) + ".jpg")):
                number = number+1
            else:
                exit = True
        filename = filename+ str(number) + ".jpg"
        cv2.imwrite(localPeoplePath+filename, actualPicture) 
    eventPause_videoShow.clear()
    eventResume_videoShow.set()
    button_acceptPhoto.grid_remove()
    button_rejectPhoto.grid_remove()
    button_managePictures.grid(row=2,column=1,columnspan = 2,sticky="WENS" )
    listNodeUsers.configure(state=NORMAL)

def rejectPhoto():
    global button_acceptPhoto, button_rejectPhoto, listNodeUsers, back_Button, button_managePictures
    logger.info("Foto Rechazada")
    eventPause_videoShow.clear()
    eventResume_videoShow.set()
    button_acceptPhoto.grid_remove()
    button_rejectPhoto.grid_remove()
    button_managePictures.grid(row=2, column=1,columnspan = 2,sticky="WENS" )

    listNodeUsers.configure(state=NORMAL)
    if (not foto_Queue.empty()):
        foto_Queue.get()
        logger.info("Descarto la foto")

def makePhoto():
    global listNodeUsers, button_acceptPhoto, button_rejectPhoto, buttonAccept, back_Button, button_managePictures
    try:
        if "No se han encontrado usuarios" == listNodeUsers.get(listNodeUsers.curselection()):
            logger.info("No hay ningún usuario seleccionado")
        else:
            logger.info("Seleccionado usuario ->" + listNodeUsers.get(listNodeUsers.curselection()))
            listNodeUsers.configure(state=DISABLED)
            
            eventResume_videoShow.clear()
            eventPause_videoShow.set()
            button_managePictures.grid_remove()
            button_acceptPhoto.grid(row=2,column=0, columnspan = 1,sticky="WENS" )
            button_rejectPhoto.grid(row=2, column=1,columnspan = 2,sticky="WENS" )
    except:
        logger.warning("No hay ningún usuario seleccionado")

def addSelectBoxToWindow():
    global selectUserWindows, mainDB, listNodeUsers,scrollbarUsers, scrollbarPictures, listNodePictures
    choices     = mainDB.USUARIOS.getList()
    scrollbarUsers   = Scrollbar(selectUserWindows, width=60)
    scrollbarUsers.grid(column=4,row=0,sticky="WENS")
    listNodeUsers    = Listbox(selectUserWindows, yscrollcommand=scrollbarUsers.set,font=('System', 12), height = 17, width=45)
    listNodeUsers.grid(column=1,columnspan = 3,row=0,padx = 5, pady = 5,sticky="WENS")

    choices     = mainDB.USUARIOS.getList()
    try:
        choices.sort(key=lambda x: x[1], reverse=False)#ORDENADO POR APELLIDO
    except:
        logger.warning("No hay usuarios en la base de datos.")
    if choices != -1:
        for code, secondName, firstName in choices:
            listNodeUsers.insert(END, secondName + ", " + firstName)
    else:
        listNodeUsers.insert(END, "No se han encontrado usuarios")
    scrollbarUsers.config(command=listNodeUsers.yview)

    scrollbarPictures   = Scrollbar(selectUserWindows, width=60)
    listNodePictures    = Listbox(selectUserWindows, yscrollcommand=scrollbarUsers.set,font=('System', 12),height = 17, width=45)
    listNodePictures.bind('<<ListboxSelect>>', onPictureSelect)
    listNodeUsers.bind('<<ListboxSelect>>', onPersonSelect)
    scrollbarPictures.config(command=listNodePictures.yview)
    
def processLocalPeople():
    getPeople(LOCAL_PEOPLE_PATH)
    return

def removeSelectedPicture():
    global currentSelectedUserm ,mainDB
    logger.info("Eliminando archivo " + listNodePictures.get(listNodePictures.curselection()))
    os.remove(str(LOCAL_PEOPLE_PATH) + "/" + listNodePictures.get(listNodePictures.curselection()))
    mainDB.ID_ENCODINGS.deleteByPhotoname(listNodePictures.get(listNodePictures.curselection()))
    backFromDeletePictures()
    manageUserPictures(currentSelectedUser)

def exit():
    global state_DeletePictures
    if(state_DeletePictures):
        state_DeletePictures = False
        backFromDeletePictures()
    else:
        global eventRelease_videoGet ,eventBlock_videoShow,  eventBlock_videoGet, eventRelease_videoShow, eventManagerModeOpen, selectUserWindows, eventExit_videoShow
        rejectPhoto()
        eventResume_videoShow.set()
        eventExit_videoShow.set()
        selectUserWindows.pack_forget()
        selectUserWindows.destroy()
        t =threading.Thread(target=processLocalPeople)#Lo inicio en una hebra para que no ralentice el interfaz
        t.start()
        interface_controlMenuScreen.startControlScreen(terminalNumber, getPeople, LOCAL_PEOPLE_PATH,version, window,mainFrame,videoCapture, eventRelease_videoShow,  eventRelease_videoGet ,eventBlock_videoShow,  eventBlock_videoGet, eventManagerModeOpen,mainDB,videoQueue, selectUserWindows)

class videoShow(threading.Thread):
    def __init__(self,__eventExit_videoShow):
        threading.Thread.__init__(self)
        self.eventExit_videoShow   = __eventExit_videoShow
        self.start()
    def run(self):
        global videoWidget, foto_Queue
        rgbFrame = False
        exit = False
        while not exit:
            if self.eventExit_videoShow.is_set():
                break
                exit = True
            elif eventPause_videoShow.isSet():
                foto_Queue.put(rgbFrame)
                eventResume_videoShow.wait()
            else:
                try:
                    rgbFrame = video_Queue.get(timeout = 100)
                    rgbSmall = cv2.resize(rgbFrame, (0,0), fx = 0.7, fy = 0.7)
                    y, x, c = rgbSmall.shape
                    vcrop = 95
                    rgbSmall = rgbSmall[vcrop:y-vcrop, 0:x] #crop image vertically
                    imPre = Image.fromarray(rgbSmall)
                    size = (260, 340)
                    imPre.thumbnail(size)#, Image.ANTIALIAS)

                    imgTk = ImageTk.PhotoImage(image = imPre)
                    videoWidget.config(image = imgTk)
                    videoWidget.imgtk = imgTk
                except:
                    logger.warning("Queue timeout")

class controlThread(threading.Thread):
    def __init__(self, __eventExit_videoShow):
        threading.Thread.__init__(self)
        self.eventExit_videoShow = __eventExit_videoShow
        self.start()

    def run(self):
        #organize UI (6x4 grid):
        global video_Queue, foto_Queue
        exit = False
        while not exit:
            if self.eventExit_videoShow.is_set():
                while not video_Queue.empty():
                    video_Queue.get_nowait() 
                break
                exit = True
            elif eventPause_videoShow.isSet():
                eventResume_videoShow.wait()
                for x in range(20):
                    (ret, frameInv) = videoCapture.read()
            else:
                (ret, frameInv) = videoCapture.read()
                
                if ret:
                    frame = cv2.flip(frameInv, 1)
                    frameRotated = cv2.rotate(frame,cv2.ROTATE_90_COUNTERCLOCKWISE)
                    rgbFrame = cv2.cvtColor(frameRotated, cv2.COLOR_BGR2RGB)
                    video_Queue.put(rgbFrame)                    

                else:
                    logger.error("Video error")
                    time.sleep(1000)
