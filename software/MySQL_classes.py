import mysql.connector
from mysql.connector import Error
from datetime import datetime
from datetime import timedelta
import numpy as np
import json
import os
import sys
import time

global host, port, database, user, password
global myconn, mycursor
global logger

def connect(host, port, database, user, password):
    conn = None 
    try:
        conn = mysql.connector.connect(host=host, port=port, database=database,
                                       user=user, password=password)
        if conn.is_connected():
            print('Connected to MySQL database')
    except Error as e:
        print(e)
    return conn

def isConnectionOk():
    try:
        mycursor.execute("SELECT 1")
        result = mycursor.fetchall()
        if result[0][0] == 1:
            return True
    except:
        logger.error('Error al conectar con DB')
        return False
    return False

def checkConnection():
    global host, port, database, user, password, myconn, mycursor, logger
    if isConnectionOk():
        return True
    try:
        cursor.close()
    except:
        logger.error('Error cerrando cursor a DB')
    try:
        conector.close()
    except:
        logger.error('Error closing connection to DB')
    success = False
    for x in range(3):
        try:
            myconn = connect(host, port, database, user, password)
            mycursor = myconn.cursor()
            success = True
            logger.error('Conexion con DB restablecida')
            logger.info('Conexion con DB restablecida')
        except:
            logger.error('Error estableciendo conexion con DB')
            time.sleep(5)
    if success == False:
        logger.error('No es posible establecer conexion con DB')
        sys.exit(-1)
        

class employee():
    def __init__(self, transaccion, tarjeta, apellidos, nombre, control):
        self.transaccion = transaccion
        self.tarjeta = tarjeta
        self.apellidos = apellidos
        self.nombre = nombre
        self.control = control
    
class database():
    def __init__(self, _host, _port, _database, _user, _password, _logger):
        global host, port, database, user, password, myconn, mycursor, logger
        host = _host
        port = _port
        database = _database
        user = _user
        password = _password
        myconn = connect(host, port, database, user, password)
        mycursor = myconn.cursor()
        logger = _logger
        self.USUARIOS = self.employeesTable()
        self.ID_ENCODINGS = self.encodingsTable(self)
        self.MARCAJES = self.markingsTable()
    
    class employeesTable():
            
        def getLength(self):
            checkConnection()
            try:
                mycursor.execute("SELECT COUNT(*) FROM EMPLEADOS")
                result = mycursor.fetchall()
                length = result[0][0]
            except:
                logger.error('Error accediendo a DB')
                return -1
            return length

        def isNewUserValid(self, employee):
            checkConnection()
            sql = "SELECT * FROM EMPLEADOS WHERE TARJETA = %s"
            val = (employee.tarjeta, )
            mycursor.execute(sql, val)
            result = mycursor.fetchall()
            if result:
                logger.error('{} ya está en uso'.format(employee.tarjeta))
                return False
            return True
                
        def create(self, employee):
            checkConnection()
            if self.isNewUserValid(employee):
                sql = "INSERT INTO EMPLEADOS (TARJETA, APELLIDOS, NOMBRE, CONTROL) VALUES (%s, %s, %s, %s)"
                val = (employee.tarjeta, employee.apellidos, employee.nombre, employee.control)
                mycursor.execute(sql, val)
                myconn.commit()
            else:
                logger.error('No se pudo añadir el usuario con tarjeta {} a la base de datos'.format(employee.tarjeta))
                return -1

        def loadById(self, transaccion):
            checkConnection()
            sql = "SELECT * FROM EMPLEADOS WHERE TRANSACCION = %s"
            val = (transaccion, )
            mycursor.execute(sql, val)
            result = mycursor.fetchall()
            if not result:
                logger.debug('Usuario no encontrado')
                user = -1
            else: 
                user = employee(result[0][0], result[0][1], result[0][2], 
                                result[0][3], result[0][4])
            return user

        def loadByUuid(self, tarjeta):
            checkConnection()
            sql = "SELECT * FROM EMPLEADOS WHERE TARJETA = %s"
            val = (tarjeta, )
            mycursor.execute(sql, val)
            result = mycursor.fetchall()
            if not result:
                logger.debug('Usuario no encontrado')
                user = -1
            else:
                user = employee(result[0][0], result[0][1], result[0][2], 
                                result[0][3], result[0][4])
            return user
            
        def deleteUserByUuid(self, tarjeta):
            checkConnection()
            user = self.loadByUuid(tarjeta)
            if user == -1:
                logger.error('No se pudo eliminar al usuario con tarjeta {} de la base de datos'.format(tarjeta))
                return -1 
            sql = "DELETE FROM EMPLEADOS WHERE TARJETA = %s"
            val = (tarjeta, )
            mycursor.execute(sql, val)
            myconn.commit()
            
        def getList(self):
            checkConnection()
            mycursor.execute("SELECT TARJETA, APELLIDOS, NOMBRE FROM EMPLEADOS")
            result = mycursor.fetchall()
            if not result:
                result = -1
            return result
    
    class encodingsTable():
        def __init__(self, database):
            self.USUARIOS = database.USUARIOS
            
        def create(self, idEncoding, idUsuario, uuid, fichero, encoding):
            checkConnection()
            user = self.USUARIOS.loadByUuid(uuid)
            if user == -1:
                logger.debug('No se pudo añadir el encoding a la DB')
                return -1
            sql = "INSERT INTO ENCODINGS (ID_ENCODING, ID_EMPLEADO, UUID, FICHERO_ORIGEN, ENCODING) VALUES (%s, %s, %s, %s, %s)"
            val = (idEncoding, idUsuario, uuid, fichero, np.array2string(encoding))
            mycursor.execute(sql, val)
            myconn.commit()
            
        def loadById(self, idEncoding):
            checkConnection()
            sql = "SELECT * FROM ENCODINGS WHERE ID_ENCODING = %s"
            val = (idEncoding, )
            mycursor.execute(sql, val)
            result = mycursor.fetchall()
            if not result:
                logger.debug('No se pudo cargar el encoding de la DB')
                encoding = -1
            else:
                encoding = np.fromiter(result[0][2][1:-1].split(), dtype=np.float32)
            return encoding
            
        def deleteByPhotoname(self, photoname):
            checkConnection()
            sql = "DELETE FROM ENCODINGS WHERE FICHERO_ORIGEN = %s"
            val = (photoname, )
            mycursor.execute(sql, val)
            myconn.commit()
            
        def getPhotoList(self):
            checkConnection()
            mycursor.execute("SELECT FICHERO_ORIGEN FROM ENCODINGS")
            result = mycursor.fetchall()
            if not result:
                logger.debug('No hay fotografías codificadas')
                photoList = -1
            else:
                photoList = list(sum(result, ()))
            return photoList
            
    class markingsTable():
        def mark(self, tarjeta, fecha, hora, incidencia, terminal, itipo):
            checkConnection()
            sql = "INSERT INTO MARCAJES (TARJETA, FECHA, HORA, INCIDENCIA, TERMINAL, ITIPO) VALUES (%s, %s, %s, %s, %s, %s)"
            val = (tarjeta, fecha, hora, incidencia, terminal, itipo)
            mycursor.execute(sql, val)
            myconn.commit()
        
        def getLastId(self):
            checkConnection()
            mycursor.execute("SELECT MAX(TRANSACCION) FROM MARCAJES")
            result = mycursor.fetchall()
            if not result:
                logger.error('Fallo al obtener el ID de marcaje')
                return -1
            else:
                return result[0][0]
                
        def getLastMarking(self):
            checkConnection()
            mycursor.execute("SELECT TARJETA, FECHA, HORA, INCIDENCIA FROM MARCAJES ORDER BY TRANSACCION DESC LIMIT 1")
            result = mycursor.fetchall()
            if not result:
                logger.error('Fallo al obtener marcaje de la DB')
                return -1
            else:
                return result[0]
        
        def deleteLastMarking(self):
            checkConnection()
            mycursor.execute("DELETE FROM MARCAJES ORDER BY TRANSACCION DESC LIMIT 1")
            myconn.commit()
        
        def create(self, tarjeta, incidencia, terminal, itipo):
            now = datetime.now()
            fecha = now.strftime('%Y-%m-%d')
            hora = now.strftime('%H:%M:%S') 
            lastMarking = self.getLastMarking()
            if lastMarking == -1:
                try:
                    self.mark(tarjeta, fecha, hora, incidencia, terminal, itipo)
                except:
                    logger.error('Fallo al realizar marcaje')
                    return -1
                return 0
            lastTarjeta = lastMarking[0]
            lastFecha = lastMarking[1]
            lastTime = lastMarking[2]
            lastIncidencia = lastMarking[3]
            
            if lastTarjeta != tarjeta: #Different user from last time
                self.mark(tarjeta, fecha, hora, incidencia, terminal, itipo)
                return 0
            
            lastDay = str(lastFecha).split()[0]
            newDay = str(fecha).split()[0]
            lastHour = str(lastTime).split()[0]
            newHour = str(hora).split()[0]
            
            if lastDay != newDay: #different day 
                self.mark(tarjeta, fecha, hora, incidencia, terminal, itipo)
                return 0
            else: #Same user and same day
                lastHourT = datetime.strptime(lastHour, '%H:%M:%S')
                newHourT = datetime.strptime(newHour, '%H:%M:%S')
                print('Hora: {}'.format(newHourT))
                print('lastTime: {}'.format(lastHourT))
                if newHourT >= (lastHourT + timedelta(minutes = 5)):
                    self.mark(tarjeta, fecha, hora, incidencia, terminal, itipo)
                else: #Within 5 minutes
                    if incidencia != '0000':
                        self.deleteLastMarking()
                        self.mark(tarjeta, fecha, hora, incidencia, terminal, itipo)
                return 0
            logger.debug('Unexpected condition')


    def getEncodings(self):
        checkConnection()
        mycursor.execute("SELECT USRS.TARJETA, USRS.NOMBRE, ENCS.ENCODING, ENCS.FICHERO_ORIGEN FROM ENCODINGS AS ENCS INNER JOIN EMPLEADOS AS USRS ON ENCS.UUID = USRS.TARJETA")
        result = mycursor.fetchall()
        if not result:
            logger.debug('No hay encodings en la DB')
            encodings = -1
        else:
            encodings = result
        return encodings
       
    def getIncidencias(self):
        checkConnection()
        mycursor.execute("SELECT INCIDENCIA, DESCRIPCION FROM INCIDENCIAS")
        result = mycursor.fetchall()
        if not result:
            result = -1
        return result
        
    def procesarAltas(self, jsonFile):
        try:
            f = open(jsonFile, 'rt')
        except:
            logger.error('No se pudo abrir el fichero {}'.format(jsonFile))
            return -1
        try:
            data = json.load(f)
        except:
            logger.error('Fallo al obtener la información de {}'.format(jsonFile))
            return -1
        for register in data:
            user = employee(register['uuid'], '_', register['name'], '_')
            self.USUARIOS.create(user)
        try:
            f.close()
        except:
            logger.error('No se pudo cerrar el fichero {}'.format(jsonFile))
        return 0
        
    def procesarBajas(self, jsonFile):
        try:
            f = open(jsonFile, 'rt')
        except:
            logger.error('No se pudo abrir el fichero {}'.format(jsonFile))
            return -1
        try:
            data = json.load(f)
        except:
            logger.error('Fallo al obtener la información de {}'.format(jsonFile))
            return -1
        for register in data:
            self.USUARIOS.deleteUserByUuid(register['uuid'])
        try:
            f.close()
        except:
            logger.error('No se pudo cerrar el fichero {}'.format(jsonFile))
        return 0

