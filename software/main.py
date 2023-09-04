from __future__ import division
import sys
import os
import face_recognition
import cv2
import numpy as np
import base64
import json
import mydata_classes as MyDataClasses
import MySQL_classes as MySQLClasses
import interface_securityCodeScreen as securityCodeScreen
import threading
import requests
import re
import pyaudio
import time
import multiprocessing
import logging
import fs
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path
from enum import Enum
from screeninfo import get_monitors
from tkinter import *
from time import sleep
from PIL import Image, ImageTk
from six.moves import queue
from xml.etree.ElementTree import fromstring, ElementTree
from datetime import datetime
from fs.osfs import OSFS
from fs.mirror import mirror
from queue import Queue
from jsonmerge import merge

DEBUG = True
DEFAULT_CONFIG_FILE = 'config/defaultConfig.json'
GLOBAL_CONFIG_FILE = 'config/globalConfig.json'
SPECIFIC_CONFIG_FILE = 'config/config.json'
SMB_GLOBAL_CONFIG_FILE = 'globalConfig.json'

ENABLE_SAMBA = False
ENABLE_REGISTRATION_FILES = False
FILE_UPDATE_INTERVAL = 10 #Minutos
TOLERANCE = 0.45 #Menor es más restrictivo
average_recog = 9000
out_of_scope = 300
resizeFrameFactor = 0.25 #[0.25 - 1.0]
minimumFaceHeight = 200
knownPeople = MyDataClasses.Known_people()
detectedPeople = MyDataClasses.Detected_people()

webcam = 0
videoCapture = cv2.VideoCapture(webcam)
videoQueue = Queue(maxsize=0)
processThisFrame = False
processGui = True
lastUser = -1
#Thread managers
eventManagerModeOpen   = threading.Event()
eventBlock_videoGet    = threading.Event()
eventBlock_videoShow   = threading.Event()
eventRelease_videoGet  = threading.Event()
eventRelease_videoShow = threading.Event()

def setupConfig():
    global mainDB, BASE_PATH, PEOPLE_PATH, LOGS_PATH, IMAGES_PATH, REBOOT_TIME, TERMINAL
    global logger, urlZaguan, sambaPeopleURL, sambaLogsURL, sambaBaseURL, VERSION
    global reintentosZaguan, pictureCount, ADMIN_PASSWORD, zaguanLogger, LOCAL_PEOPLE_PATH
    try:
        dcf = open(DEFAULT_CONFIG_FILE, 'rt')
    except:
        print('[ERROR] al abrir el fichero {}'.format(DEFAULT_CONFIG_FILE))
        sys.exit(-1)
    try:
        defaultConfig = json.load(dcf)
    except:
        print('[ERROR] al cargar la información del fichero {}'.format(DEFAULT_CONFIG_FILE))
        sys.exit(-1)
    try:
        dcf.close()
    except:
        print('[ERROR] al cerrar {}'.format(DEFAULT_CONFIG_FILE))
        
    loadGlobal = False
    if os.path.isfile(GLOBAL_CONFIG_FILE):
        try:
            gcf = open(GLOBAL_CONFIG_FILE, 'rt')
        except:
            print('Fallo al abrir fichero')
        try:
            globalConfig = json.load(gcf)
            loadGlobal = True
        except:
            print('Fallo al parsear fichero json')
        try:
            gcf.close()
        except:
            print('Fallo al cerrar fichero')
    if loadGlobal == True:
        config = merge(defaultConfig, globalConfig)
    else:
        config = defaultConfig
    
    loadSpecific = False
    if os.path.isfile(SPECIFIC_CONFIG_FILE):
        try:
            scf = open(SPECIFIC_CONFIG_FILE, 'rt')
        except:
            print('Fallo al abrir fichero')
        try:
            specificlConfig = json.load(scf)
            loadSpecific = True
        except:
            print('Fallo al parsear fichero json')
    if loadSpecific == True:
        config = merge(config, specificConfig)

    VERSION = defaultConfig["version"]
    BASE_PATH = config["path"]["basepath"]
    PEOPLE = config["path"]["people"]
    LOCAL_PEOPLE = config["path"]["localPeople"]
    LOGS = config["path"]["logs"]
    PEOPLE_PATH = Path(BASE_PATH + PEOPLE)
    if not os.path.exists(PEOPLE_PATH):
        os.makedirs(PEOPLE_PATH)
    LOCAL_PEOPLE_PATH = Path(BASE_PATH + LOCAL_PEOPLE)
    LOGS_PATH = Path(BASE_PATH + LOGS)
    IMAGES_PATH = Path(BASE_PATH + config["path"]["images"])
    TERMINAL = config["Terminal"]
    fileSize = config["logging"]["logfile_size"]
    fileCount = config["logging"]["logfile_count"]
    pictureCount = config["logging"]["picture_count"]
    rotatingFileHandler = RotatingFileHandler(
        filename  = LOGS_PATH / Path('log.txt'),
        mode = 'a',
        maxBytes = fileSize * 1024 * 1024,
        backupCount = fileCount,
        encoding = None,
        delay = 0)
    if DEBUG:
        loggingLevel = logging.DEBUG
    else:
        loggingLevel = logging.INFO
    logging.basicConfig(
        level = loggingLevel,
        format = "%(asctime)s - %(levelname)s - %(message)s",
        datefmt = "%d-%m-%y %H:%M:%S",
        handlers = [rotatingFileHandler])
    logger = logging.getLogger(__name__)
    logger.addHandler(logging.StreamHandler())
    host = config["DB"]["host"]
    port = config["DB"]["port"]
    database = config["DB"]["database"]
    user = config["DB"]["user"]
    password = config["DB"]["password"]
    mainDB = MySQLClasses.database(host, port, database, user, password, logger)
    REBOOT_TIME = config["rebootTime"]
    ADMIN_PASSWORD = config["adminPassword"]

    if ENABLE_SAMBA:
        smbConf = config["samba"]
        sambaBaseURL = ('smb://' + smbConf["user"] + ':' + smbConf["password"]
                        + '@' + smbConf["ip"] + ':' + smbConf["port"] + '/'
                        + smbConf["path"] + '/')
        sambaURL = sambaBaseURL + 'Terminal_' + str(TERMINAL)
        sambaPeopleURL = sambaURL + PEOPLE
        sambaLogsURL = sambaURL + LOGS

def nextLabelPage():
    global actualPage, logger
    actualPage = actualPage+1
    maxPages = 1
    try:
        maxPages = int(len(incidencias) / 8) +1 #Empieza en 1
    except:
        logger.info("No hay incidencias en base de datos.")
    if actualPage > maxPages:
        actualPage = 1
    logger.info("Incremento la página a {}".format(actualPage))
    labelOptions.config(text = incidenciasTexts[actualPage-1], justify=LEFT)
    

def fileOrder(file):
    try: 
        value = file.split('_')[1]
    except:
        value = ''
    return value

def getPeople(filesPath): #Process user photos; create encodings and add them to the DB:
    global knownPeople
    try:
        allFiles = os.listdir(filesPath)
    except: 
        logger.error('Path not found: {}'.format(filesPath))
        return -1
    encodedPhotos = mainDB.ID_ENCODINGS.getPhotoList()
    if encodedPhotos == -1:
        encodedPhotos = []
    userFiles = []
    for i, filename in enumerate(allFiles):
        if DEBUG == True:
            logger.info('Procesando archivo: {}'.format(filename))
        if (filename not in encodedPhotos) and (filename.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif'))):
            try:
                name=filename.split("_")[1]
                uuid =filename.split("_")[0]
            except:
                logger.error('Nombre de archivo incorrecto: {}'.format(filename))
                continue
            #1) check if user is in database and get its id
            user = mainDB.USUARIOS.loadByUuid(uuid)
            if user == -1:
                logger.error('El usuario de la fotografía {} no existe en la base de datos'.format(filename))
            else:
                try:
                    face = face_recognition.load_image_file(os.path.join(filesPath, filename))
                except:
                    logger.error('Error al cargar el fichero {}'.format(filename))
                    continue
                encodings = face_recognition.face_encodings(face)
                if encodings:
                    face_encoding = encodings[0]
                else:
                    logger.error('No se pudo realizar encoding al archivo {}'.format(filename)) 
                    continue
            #2) register the encoding 
                idUsuario = user.transaccion
                mainDB.ID_ENCODINGS.create(None, idUsuario, uuid, filename, face_encoding)
                logger.info('Añadido encoding de {}'.format(filename))
        elif filename.startswith('altas') or filename.startswith('bajas'):
            userFiles.append(filename)
    
    if ENABLE_REGISTRATION_FILES:
        #Process user registration files
        userFiles.sort(key = fileOrder)
        try:
            with open('logs/procesados.txt', 'r') as f:
                processedFiles = [line[:-1] for line in f]
        except:
            logger.error('Fallo al abrir el fichero logs/procesados.txt')
            processedFiles = []
        try:
            listFile = open('logs/procesados.txt', 'a')
        except:
            logger.error('Fallo al abrir el fichero logs/procesados.txt')
        for userFile in userFiles:
            if userFile not in processedFiles: 
                if userFile.startswith('bajas'):
                    result = mainDB.procesarBajas(PEOPLE_PATH/userFile)
                    if result == 0:
                        try:
                            listFile.write(userFile+'\n')
                        except:
                            logger.error('Fallo al registar {} en la lista de archivos procesados'.format(userFile))
                elif userFile.startswith('altas'):
                    result = mainDB.procesarAltas(PEOPLE_PATH/userFile)
                    if result == 0:
                        try:
                            listFile.write(userFile+'\n')
                        except:
                            logger.error('Fallo al registar {} en la lista de archivos procesados'.format(userFile))
    loadEncodings()
    
def loadEncodings():   #Load encodings from DB:
    results = mainDB.getEncodings()
    if results != -1:
        for result in results:
            picture = result[3]
            if picture not in knownPeople.picture:
                uuid = result[0]
                name = result[1]
                encoding = np.fromiter(result[2][1:-1].split(), dtype=np.float32)
                knownPeople.add(uuid, name, encoding, picture)

def clear_GUI():
    global processGui
    labelId.config(text = "")
    labelOptions.config(text = "")
    videoBorder.config(bg="grey")
    iconStatus.config(image="")
    iconStatus.image=""
    labelSpacer.grid(row = 3, column = 3)
    processGui = True

def detectedUser(id, rgbFrame, pictureName):
    global window, processGui, option, lastZaguanUser, lastUser, actualPage
    if(processGui == True):
        name = knownPeople.get_name_byid(id)
        logger.info('Detectado usuario con UUID {}'.format(id))

        labelId.config(text = "\n" + name + f"\n\n Fichaje realizado\na las " + datetime.now().strftime('%H:%M'))
        videoBorder.config(bg="green")
        iconStatus.config(image=imgOk)
        iconStatus.image = imgOk
        option = -10
        proceed = -10
        mainDB.MARCAJES.create(id, '0000', TERMINAL, 0)
        saveFrame(id, rgbFrame, pictureName)
        
        if id != lastUser:
            mainDB.MARCAJES.create(id, '0000', TERMINAL, 0)
            lastUser = id
                
        window.after(5000, clear_GUI)
        processGui = False

def unknown_user():
    global window
    global processGui
    if(processGui == True):
        labelId.config(text = "\nUsuario desconocido")
        videoBorder.config(bg="red")
        iconStatus.config(image=imgStop)
        iconStatus.image = imgStop
        window.after(1500, clear_GUI) #4000
        processGui = False

def saveFrame(id, rgbFrame, pictureName):
    fecha = datetime.now().strftime('%Y%m%d%H%M%S')
    imagePath = 'logs/pictures/'+fecha+'_'+pictureName
    try:
        res = cv2.imwrite(imagePath, cv2.cvtColor(rgbFrame, cv2.COLOR_RGB2BGR))
        if res == False:
            logger.error('Fallo al guardar la captura')
        else:
            logger.info('Captura guardada')
    except:
        logger.error('Fallo al guardar la captura')

def processFrame(rgbFrame):
    global knownPeople
    global detectedPeople
    if knownPeople.face_encoding: # If there is any encoded face in memory
        # Resize frame of video to 1/4 size for faster face recognition processing
        rgbSmallFrame = cv2.resize(rgbFrame, (0, 0), fx=resizeFrameFactor, fy=resizeFrameFactor)
        # Find all the faces and face encodings in the current frame of video
        face_locations = face_recognition.face_locations(rgbSmallFrame)
        face_encodings = []
        if face_locations:
            top, right, bottom, left = face_locations[0]
            faceHeight = bottom - top
            if faceHeight > minimumFaceHeight * resizeFrameFactor:
                face_encodings = face_recognition.face_encodings(rgbSmallFrame, face_locations)
        remove = detectedPeople.decr_prec()
        for index, face_encoding in enumerate(face_encodings):
            # See if the face is a match for the known face(s)
            matches = face_recognition.compare_faces(knownPeople.face_encoding, face_encoding, tolerance = TOLERANCE)
            name = "Unknown"

            face_distances = face_recognition.face_distance(knownPeople.face_encoding, face_encoding)
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                id = knownPeople.id[best_match_index]
                name = knownPeople.get_name_byid(id)
                
                detectedUser(id, rgbFrame, knownPeople.picture[best_match_index])
                
                if id in detectedPeople.id:
                    detectedPeople.update(id,face_locations[index],average_recog,out_of_scope)
                else:
                    detectedPeople.add(id, face_locations[index])
            
            if DEBUG == True:
                print("Detectado usuario: {}".format(name))
            if(name == "Unknown"):
                unknown_user()

        for pos in remove:
            detectedPeople.remove(pos)

def logginPeople():
    global knownPeople
    global detectedPeople

    for confirmed in detectedPeople.confirmed:
        index=detectedPeople.confirmed.index(confirmed)
        if confirmed and not detectedPeople.logged[index]:
            name = knownPeople.get_name_byid(detectedPeople.id[index])
            id = detectedPeople.id[index]
            detectedPeople.logged[index] = True
            logging.append(MyDataClasses.Logging(id, name, dir))

class videoThread(threading.Thread):
    def __init__(self, eventBlock, eventRelease):
        threading.Thread.__init__(self)
        self.eventBlock_videoShow   = eventBlock
        self.eventRelease_videoShow = eventRelease  
        self.start()
    def run(self):
        while True:
            if self.eventBlock_videoShow.is_set():
                self.eventRelease_videoShow.wait()
            else:
                rgbFrame = videoQueue.get()
                while(videoQueue.qsize() > 5):
                    rgbFrame = videoQueue.get()
                rgbSmall = cv2.resize(rgbFrame, (0,0), fx = 0.7, fy = 0.7)
                y, x, c = rgbSmall.shape
                vcrop = 95
                rgbSmall = rgbSmall[vcrop:y-vcrop, 0:x] #crop image vertically
                imgTk = ImageTk.PhotoImage(image = Image.fromarray(rgbSmall))
                videoWidget.config(image = imgTk)
                videoWidget.image = imgTk

class fileThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.start()
    
    def syncPeople(self):
        try:
            smbPeopleFS = fs.open_fs(sambaPeopleURL, writeable=False, create=True) 
        except:
            logger.error('Fallo al abrir la carpeta en red')
            return -1
        try:
            homePeopleFS = OSFS(PEOPLE_PATH)
        except:
            logger.error('Fallo al abrir la carpeta local para sincronizar los archivos')
            smbPeopleFS.close()
            return -1
        try:
            mirror(smbPeopleFS, homePeopleFS, walker = None, copy_if_newer=True, workers = 0)
            logger.info('Archivos de red sincronizados')
        except:
            logger.error('Fallo al sincronizar los archivos')
            smbPeopleFS.close()
            homePeopleFS.close()
            return -1
        smbPeopleFS.close()
        homePeopleFS.close()
        return 0
        
    def syncLogs(self):
        try:
            smbLogsFS = fs.open_fs(sambaLogsURL, writeable=True, create=True)
        except:
            logger.error('Fallo al abrir la carpeta en red')
            return -1
        try:
            homeLogsFS = OSFS(LOGS_PATH)
        except:
            logger.error('Fallo al abrir la carpeta local para sincronizar los archivos: /n{}'.format(LOGS_PATH))
            smbLogsFS.close()
            return -1
        try:
            mirror(homeLogsFS, smbLogsFS, walker = None, copy_if_newer=True, workers = 0)
            logger.info('Archivos de red sincronizados')
        except:
            logger.error('Fallo al sincronizar los archivos de log')
            smbPeopleFS.close()
            homePeopleFS.close()
            return -1
        smbLogsFS.close()
        homeLogsFS.close()
        return 0

    def deleteOldPictures(self):
        try:
            fileList = os.listdir('logs/pictures')
            fileNumber = len(fileList)
            if fileNumber > pictureCount:
                fileList.sort()
                for i in range(fileNumber - pictureCount):
                    os.remove('logs/pictures/'+fileList[i])
        except:
            logger.error('Fallo borrando capturas antiguas')
            return -1
        return 0
        
    def getGlobalConfigFile(self):
        try:
            smbBase = fs.open_fs(sambaBaseURL, writeable=False, create=False) 
        except:
            logger.error('Fallo al abrir la carpeta en red: /n{}'.format(sambaBaseURL))
            return -1
        directory = smbBase.listdir('/')
        if GLOBAL_CONFIG_FILE in directory:
            try:
                homeFS = OSFS(BASE_PATH)
            except:
                logger.error('Fallo al abrir la carpeta local para sincronizar los archivos')
                smbBase.close()
                return -1
            copied = fs.copy.copy_file_if_newer(smbBase, SMB_GLOBAL_CONFIG_FILE, homeFS, GLOBAL_CONFIG_FILE)
            if copied:
                logger.info('Copiado archivo de configuracion global')
                os.system('sudo shutdown -r {}'.format(REBOOT_TIME))
            try: 
                homeFS.close()
            except:
                logger.error('Fallo al cerrar sistema de ficheros local')
        try:
            smbBase.close()
        except:
            logger.error('Fallo al cerrar el sistema de ficheros remoto')
        return 0

    def run(self):
        if ENABLE_SAMBA:
            while True:
                self.getGlobalConfigFile()
                self.syncPeople()
                getPeople(PEOPLE_PATH)
                self.syncLogs()
                self.deleteOldPictures()
                time.sleep(FILE_UPDATE_INTERVAL * 3600)
        else:
            while True:
                getPeople(PEOPLE_PATH)
                self.deleteOldPictures()
                time.sleep(FILE_UPDATE_INTERVAL * 3600)

class controlThread(threading.Thread):
    def __init__(self, eventBlock, eventRelease):
        threading.Thread.__init__(self)
        self.eventBlock_videoGet   = eventBlock
        self.eventRelease_videoGet = eventRelease
        self.start()

    def run(self):
        #organize UI (6x4 grid):
        labelSpacer.grid(row = 3, column = 3)
        videoBorder.grid(row=0, column=0, columnspan=3, rowspan=6, padx=40, pady=50)
        labelId.grid(row=1, column=3, rowspan=1, columnspan=1)
        labelOptions.grid(row=2, column=3,padx = 3, rowspan=4, columnspan=6, sticky = NW) 
        iconStatus.grid(row=1, column=4, padx = 5, rowspan=1)
        while True:
            if self.eventBlock_videoGet.is_set():
                print("Bloqueado")
                self.eventRelease_videoGet.wait()
                print("Saliendo del wait")
                for x in range(20):
                    (ret, frameInv) = videoCapture.read()
            else:
                (ret, frameInv) = videoCapture.read()
                if ret:
                    frame = cv2.flip(frameInv, 1)
                    frameRotated = cv2.rotate(frame,cv2.ROTATE_90_COUNTERCLOCKWISE)
                    rgbFrame = cv2.cvtColor(frameRotated, cv2.COLOR_BGR2RGB)
                    videoQueue.put(rgbFrame)
                    # Only process every other frame of video to save time
                    global processThisFrame
                    if processThisFrame:
                        # Grab a single frame of video
                        if DEBUG == True:
                            processFrame(rgbFrame)
                        else:
                            try:
                                processFrame(rgbFrame)
                            except:
                                print('[ERROR] en processFrame')
                        logginPeople()
                    processThisFrame = not processThisFrame

                else:
                    print("Video error")
                    time.sleep(1)

def startControlInterface(event):
    """Start a new window that require a code to enter into the admin mode
    Args:
        event ([type]): Unused variable, is a string blinded to the image that needs to be passed as arg
    """
    global eventManagerModeOpen, eventBlock_videoShow,  eventBlock_videoGet, eventRelease_videoShow,  eventRelease_videoGet, videoQueue, videoCapture
    if not eventManagerModeOpen.is_set():
        eventManagerModeOpen.set()
        eventBlock_videoGet.set()
        eventBlock_videoShow.set()
        mainFrame.pack_forget()
        securityCodeScreen.startSecurityCodeWindow(TERMINAL, getPeople, LOCAL_PEOPLE_PATH, VERSION, window,mainFrame,  videoCapture, eventRelease_videoShow,  eventRelease_videoGet ,eventBlock_videoShow,  eventBlock_videoGet, eventManagerModeOpen, ADMIN_PASSWORD, mainDB, videoQueue)

def getserial():
    # Extract serial from cpuinfo file
    cpuserial = "0000000000000000"
    try:
        f = open('/proc/cpuinfo','r')
        for line in f:
            if line[0:6]=='Serial':
                cpuserial = line[10:26]
        f.close()
    except:
        cpuserial = "ERROR000000000"
    return cpuserial

def getLocalCode():
    f = open("/usr/user", "r")
    file = f.read()
    file = file.replace("\n", "")
    file = file.replace("", "")
    return file

def securityCheck():
    hwCode = getserial()
    securityCode = getLocalCode()
    if hwCode == securityCode:
        return True
    else:
        logger.error("SECURITY ERROR")
        #os.system("sudo shutdown now")
        sys.exit(-1)
        return False

if __name__ == '__main__':
    global incidencias
    setupConfig()
    logging =[]
    securityCheck()
    loadEncodings()
    #GUI Setup:
    screenW=800
    screenY=480
    labelFont = ('Piboto Regular', 12)
    videoCapture.set(cv2.CAP_PROP_FRAME_WIDTH, screenW)
    videoCapture.set(cv2.CAP_PROP_FRAME_HEIGHT, screenY)
    window = Tk()
    window.protocol("WM_DELETE_WINDOW", window.quit())
    window.config(cursor="none")
    window.attributes('-fullscreen', True)
    window.pack_propagate(0) #So widgets cannot resize window
    mainFrame = Frame(window)
    mainFrame.pack(anchor=W, fill=Y, expand=True, side=LEFT)
    videoBorder = Frame(mainFrame, bg="grey", bd=6)
    videoWidget = Label(videoBorder)
    videoWidget.bind('<Button-1>', startControlInterface)
    videoWidget.grid()
    imgStop = ImageTk.PhotoImage(Image.open(IMAGES_PATH/"Dialog-stop-hand.gif"))
    imgOk = ImageTk.PhotoImage(Image.open(IMAGES_PATH/"Dialog-ok-hand.gif"))
    labelId = Label(mainFrame, font=('Piboto Regular', 20))
    labelId.config(text = "")
    labelOptions = Label(mainFrame, font=labelFont)
    labelOptions.config(text="")
    iconStatus = Label(mainFrame)
    labelSpacer = Label(mainFrame, height = 1, width = 27, text = " ")

    incidencias = mainDB.getIncidencias()
    incidenciasTexts = []
    incidenciasOptions = []
    numPages = 1
    stillNotProcessed = 0
    try:
        stillNotProcessed = len(incidencias)
        numPages = int(len(incidencias) / 8) +1 #Empieza en 1
    except:
        logger.info("No hay incidencias en base de datos.")
    pageCount = 0
    while(stillNotProcessed > 0):
        incidenciasOptions.append([0])
        startText ="Seleccione una de las opciones"
        if numPages > 1:
            startText = startText + " ("+ str(pageCount+1) + "/" + str(numPages) +"):\n"
        else:
            startText = startText + "\n"
        incidenciasTexts.append(startText)
        incidenciasTexts[pageCount] =  incidenciasTexts[pageCount] + "0 - SALIR\n"   
        if(stillNotProcessed >= 8):
            for x in range(8):
                incidenciasOptions[pageCount].append(x+1)
                incidenciaPosition = len(incidencias)-stillNotProcessed+x
                incidenciaActualOption = incidencias[incidenciaPosition][1]
                if(len(incidenciaActualOption)>28):
                    incidenciaActualOption = incidenciaActualOption[0:26:]+"..." 
                incidenciasTexts[pageCount] = incidenciasTexts[pageCount] + str(x+1) + " - " + incidenciaActualOption+ "\n"
            stillNotProcessed = stillNotProcessed -8
        else:
            for x in range(stillNotProcessed):
                incidenciasOptions[pageCount].append(x+1)
                incidenciaPosition = len(incidencias)-stillNotProcessed+x
                incidenciaActualOption = incidencias[incidenciaPosition][1]
                if(len(incidenciaActualOption)>28):
                    incidenciaActualOption = incidenciaActualOption[0:26:]+"..." 
                incidenciasTexts[pageCount] =  incidenciasTexts[pageCount] + str(x+1) + " - " + incidenciaActualOption+ "\n"
            stillNotProcessed = 0
        if len(incidencias) >=8:
            incidenciasOptions[pageCount].append(9)
            incidenciasTexts[pageCount] =  incidenciasTexts[pageCount] + "9 - SIGUIENTE PÁGINA"
            pageCount = pageCount+1
    
    if DEBUG:
        logger.debug("Textos a mostrar")
        for element in incidenciasTexts:
            logger.debug(element)
        logger.debug("Numeros permitidos por pg")
        logger.debug(incidenciasOptions)
        logger.debug("Incidencias")
        logger.debug(incidencias)

    
    eventBlock_videoShow.clear()
    eventBlock_videoGet.clear()
    
    ft = fileThread() #Start file updating thread
    vt = videoThread(eventBlock_videoShow, eventRelease_videoShow) #Start video showing thread
    app = controlThread(eventBlock_videoGet, eventRelease_videoGet) #Start control thread
    window.mainloop() #GUI endless loop 

    # Release handle to the webcam
    videoCapture.release()
    cv2.destroyAllWindows()
    
