import socket
import selectors
import types
import os
import struct
import hashlib
import time as t
from time import time


class GLOBALES:
    clientes = []
    HOST = '127.0.0.1'
    PORT = 65432
    sel = selectors.DefaultSelector()
    f = open('./archivos/Datos.txt', "rb")
    cantidadClientes = 0
    tamannoArchivo = 0
    nombreArchivo = ""
    clientesListos = 0


def iniciar_server():
    GLOBALES.HOST = '127.0.0.1'
    GLOBALES.PORT = 65432
    GLOBALES.clientes = []

    GLOBALES.sel = selectors.DefaultSelector()
    lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    lsock.bind((GLOBALES.HOST, GLOBALES.PORT))
    lsock.listen()
    print('listening on', (GLOBALES.HOST, GLOBALES.PORT))
    lsock.setblocking(False)
    GLOBALES.sel.register(lsock, selectors.EVENT_READ, data=None)
    eligio = False
    while eligio is not True:
        print("Ingrese el número del archivo que desea enviar: ")
        print("1. Datos.txt")
        print("2. Fondos One Piece.zip")
        archivo = int(input(""))
        if archivo == 1:
            GLOBALES.f = open('./archivos/Datos.txt', "rb")
            GLOBALES.tamannoArchivo = (os.path.getsize('./archivos/Datos.txt'))/1024
            GLOBALES.nombreArchivo = "Datos.txt"
            eligio = True
        elif archivo == 2:
            GLOBALES.f = open('./archivos/Fondos One Piece.zip', "rb")
            GLOBALES.tamannoArchivo = (os.path.getsize('./archivos/Fondos One Piece.zip'))/1024
            GLOBALES.nombreArchivo = "Fondos One Piece.zip"
            eligio = True
        else:
            print("No existe ese archivo")
    GLOBALES.cantidadClientes = int(input("Ingrese a cuantos clientes en simultaneo desea enviar el archivo \n"))


def accept_wrapper(sock):
    conn, addr = sock.accept()  # Should be ready to read
    print('accepted connection from', addr)
    conn.setblocking(False)
    data = types.SimpleNamespace(addr=addr, inb=b'', outb=b'')
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    GLOBALES.sel.register(conn, events, data=data)
    GLOBALES.clientes.insert(0, {"id": int(str(addr).split(",")[1].split(")")[0]), "handShakeSend": False, "handShakeReceived": False, "received": False})


def service_connection(key, mask, cliente):
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024)  # Should be ready to read
        if recv_data == b'HandShake' and cliente['handShakeSend'] is not True:
            print('received', repr(recv_data), 'from connection', data.addr)
            data.outb += recv_data
            cliente['handShakeSend'] = True
        elif recv_data == b'HandShakeReceived':
            cliente['handShakeReceived'] = True
            GLOBALES.clientesListos += 1
        elif recv_data == b'End':
            print('received', repr(recv_data), 'from connection', data.addr)
            tiempo_final = time()
            tiempo_ejecucion = tiempo_final - tiempo_inicial
            print(tiempo_ejecucion)
            GLOBALES.clientesListos -= 1
            data.outb = b'hash:' + hashlib.sha1(GLOBALES.f.read()).digest()
            GLOBALES.f.seek(0)
        elif recv_data == b'Hashed':
            print('received', repr(recv_data), 'from connection', data.addr)
            print('closing connection to', data.addr)
            GLOBALES.sel.unregister(sock)
            sock.close()
    if mask & selectors.EVENT_WRITE:
        if data.outb:
            print('sending... ',  'to', data.addr)
            sent = sock.send(data.outb)  # Should be ready to write
            data.outb = data.outb[sent:]


iniciar_server()
while True:
    events = GLOBALES.sel.select(timeout=None)
    for key, mask in events:
        if key.data is None:
            print("New Connection")
            accept_wrapper(key.fileobj)
        elif GLOBALES.cantidadClientes == GLOBALES.clientesListos:
            id = int(str(key.data.addr).split(",")[1].split(")")[0])
            cliente = {}
            for i in range(len(GLOBALES.clientes)):
                if GLOBALES.clientes[i]['id'] == id:
                    cliente = GLOBALES.clientes[i]
                    break
            if cliente['received'] is not True and cliente['handShakeReceived']:
                key.data.outb = b'nombre:'+GLOBALES.nombreArchivo.encode('utf-8')+b',tamanno:'+bytearray(struct.pack("f",GLOBALES.tamannoArchivo))
                service_connection(key, mask, cliente)
                t.sleep(0.2)

                tiempo_inicial = time()
                key.data.outb = GLOBALES.f.read()
                service_connection(key, mask, cliente)
                """while dataSend:
                    hash = hashlib.sha1(dataSend)
                    key.data.outb = dataSend
                    service_connection(key, mask, cliente)
                    dataSend = GLOBALES.f.readline()"""
                cliente['received'] = True
                key.data.outb = b''
                GLOBALES.f.seek(0)
            service_connection(key, mask, cliente)
        else:
            id = int(str(key.data.addr).split(",")[1].split(")")[0])
            cliente = {}
            for i in range(len(GLOBALES.clientes)):
                if GLOBALES.clientes[i]['id'] == id:
                    cliente = GLOBALES.clientes[i]
                    break
            service_connection(key, mask, cliente)
