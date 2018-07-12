import json
import re
import select
import socket
import sys
import _thread
import time
from threading import Thread, Timer
from time import gmtime, strftime

clients = []
packages = [{"package": "1", "version": "1", "url": "1"}, {"package": "2", "version": "2", "url": "2"}]
host = "localhost"
port = 5000
ready = False
connected = False
running = True

def main():
	global running
	t = Thread(target=startListener, args=())
	t.start()
	while running:
		command = input("")
		command = command.split(" ")
		if (command[0] == "close" or command == "c" or command == "quit"):
			print("closing")
			running = False
			t.join()
		elif command[0] == "clients":
			for client in clients:
				print(client)
		elif command[0] == "client":
			found = False
			for client in clients:
				if client["clientID"] == command[1]:
					print(client)
					found = True
			if not found:
				print("Client not found, might be a wrong ID")
			
		

def startListener():
	global host
	global port
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
	connected = False
	while not connected:
		try: 
			s.bind((host, port))
			connected = True
		except OSError:
			port += 1
	print(port)
		
	s.listen(socket.SOMAXCONN)
	registerClients(s)

def registerClients(s):
	global port
	global ready
	global connected
	global running
	threads = []
	try:
		while running:
			s.settimeout(2)
			try:
				inSocket, addr = s.accept()
				info = inSocket.recv(500)
				info = info.decode("utf-8")
				info = json.loads(info)
				info["alive"] = True
				info["date"] = strftime("%Y-%m-%d", gmtime())
				alreadyRegistered = False
				clientInfo = {}
				for client in clients:
					if client["clientID"] == info["clientID"]:
						alreadyRegistered = True
						clientInfo = client
				if(not alreadyRegistered):
					clients.append(info)
				elif clientInfo["alive"]:
					#TODO
					print("ERROR: Client already connected!")
				else:
					clientInfo = info

				t = None
				while not connected:
					print("not connected")
					port += 1
					t = Thread(target=connect, args=(host, port,))
					t.start()
					while not ready:
						#print("not ready")
						time.sleep(0.0001)
				sentbytes = inSocket.send(bytes(str(port), "utf-8"))				
				ready = False
				connected = False
				threads.append(t)
				inSocket.close()
			except socket.timeout:
				pass
			#print(clients)
				
	finally:
		print("closing childs")
		for t in threads:
			t.join()
			print("one less")
		print("all childs closed")
		s.close()
		print("child finished")

def connect(host, port):
	print("hello")
	global ready
	global connected
	global running
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
	try:
		s.bind((host, port))
		s.listen(socket.SOMAXCONN)
		ready = True
		connected = True
		print("thread setup complete on port:")
		print(port)
	except OSError as e:
		#TODO
		ready = True
		print("thread setup failed")
		print(e)
		sys.exit()
	
	inSocket, addr = s.accept()

	tim = Timer(10, timeout)
	tim.start()
	print("Tim lives")

	run = True
	while run and running:
		if not tim.is_alive():
			run = False
		#print("still running")

		rdy = select.select([inSocket], [], [], 2)
		if rdy[0]:
			msg = inSocket.recv(5000)
			msg = msg.decode("utf-8")
			msg = json.loads(msg)
			print(msg)

			if(msg["type"] == "hearthbeat"):
				tim.cancel()
				tim = Timer(10, timeout)
				tim.start()
	tim.cancel()
	print("child child finished")

def timeout():
	print("Ich heiße Tim!")	

if __name__ == "__main__":
    main()

#json.dump(data, write_file)    writes to json converted data in write_file
#json.dumps(data)   returns data as json-string
#json.loads(json_string)   returns data as in python format (dict for json objects) depending on json_string
#json.load(read_file)   see loads
