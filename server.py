import hashlib
import json
import os.path
import re
import select
import socket
import sys
import _thread
import time
from threading import Thread, Timer
from time import gmtime, strftime

clients = []
packages = []
host = "localhost"
port = 5000
ready = False
connected = False
running = True
packsize = 500

def main():
	global host
	global port
	if len(sys.argv) == 3:
		host = sys.argv[1]
		port = int(sys.argv[2])
	else:
		print("Usage: python3 server.py [host] [port]")
	generateTestPackages()
	loadPackages()
	loadClients()
	t = Thread(target=startListener, args=())
	t.start()
	handleInput()


def handleInput():
	""" 
	Reads in console commands while running is True
	command : function
	client : shows a list of the clients
	client [id] : shows the client with given id
	packages : shows the installed packages
	install [packageName] [version] [path] : installs or updates the package at [path] under the name [packageName] and sets it's version to [version]
	"""
	global running
	while running:
		command = input("")
		command = command.split(" ")
		if (command[0] == "close" or command == "c" or command == "quit"):
			print("closing")
			running = False
			t.join()
		elif command[0] == "clients":
			if len(clients) == 0:
				print("No clients found!")
			else:
				print("ID : IP : Info : Connected : Last log in")
				for client in clients:
					print(client["clientID"] + " : " + client["ip"] + " : " + str(client["Info"]) + " : " + str(client["alive"]) + " : " + client["date"])
		elif command[0] == "client":
			if len(command) == 2:
				found = False
				for client in clients:
					if client["clientID"] == command[1]:
						print(client)
						found = True
				if not found:
					print("Client not found, might be a wrong ID")
			else:
				print("Usage: client [clientID]")
		elif command[0] == "packages":
			print("Package : Version : Path")
			for pack in packages:
				print(pack["package"] + " : " + pack["version"] + " : " + pack["url"])

		elif command[0] == "install":
			if len(command) != 4:
				print("Usage: install [packageName] [version] [path]")
			else:
				if not os.path.isfile(command[3]):
					print("No file found under given path! Move the package to the given path before calling install!")
				else:
					alreadyInstalled = False
					for package in packages:
						if package["package"] == command[1]:
							alreadyInstalled = True
							print("Package already installed! If you want to update it type 'yes'.")
							confirmation = input("")
							if confirmation == "yes":
								packages.append({"package": command[1], "version": command[2], "url": command[3]})
								print("Package successfully updated")
							break
						
					if not alreadyInstalled:		
						packages.append({"package": command[1], "version": command[2], "url": command[3]})
						print("Package successfully installed")

		else:
			print("command : function")
			print("client : shows a list of the clients")
			print("client [id] : shows the client with given id")
			print("packages : shows the installed packages")
			print("install [packageName] [version] [path] : installs or updates the package at [path] under the name [packageName] and sets it's version to [version]")

def loadPackages():
	global packages
	f = None
	try:
		f = open("packages.json", "r")
		packages = json.loads(f.read())
	except FileNotFoundError:
		f = open("packages.json", "w+")
		f.write("[]")
	f.close()
	print("packages loaded")

def savePackages():
	global packages
	try:
		f = open("packages.json", "w")
		f.write(json.dumps(packages))
		f.close()
	except Exception as e:
		print(e)
			
def loadClients():
	global clients
	f = None
	try:
		f = open("clients.json", "r")
		clients = json.loads(f.read())
	except FileNotFoundError:
		f = open("clients.json", "w+")
		f.write("[]")
	f.close()
	for client in clients:
		client["alive"] = False
	print("clients loaded")

def saveClients():
	global clients
	f = None
	try:
		f = open("clients.json", "w")
		f.write(json.dumps(clients))
	finally:
		f.close()

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
	global clients
	threads = []
	try:
		while running:
			s.settimeout(2) #Might cause strange behaviour later on
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
						if client["alive"]:
							#TODO
							print("ERROR: Client already connected!")
						else:
							client["Info"] = info["Info"]
							client["alive"] = True
							client["date"] = info["date"]
							client["ip"] = info["ip"]
							saveClients()
						break
				if(not alreadyRegistered):
					clients.append(info)
					saveClients()

				t = None
				while not connected:
					print("not connected")
					port += 1
					t = Thread(target=connect, args=(host, port, info,))
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

def connect(host, port, client):
	#TODO catch client disconnecting
	print("hello")
	global ready
	global connected
	global running
	global packsize
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

	while running:
		if not tim.is_alive():
			for cl in clients:
				if cl["clientID"] == client["clientID"]:
					cl["alive"] = False
					break
			break

		rdy = select.select([inSocket], [], [], 2)
		if rdy[0]:
			msg = inSocket.recv(5000)
			msg = msg.decode("utf-8")
			if msg == "":
				print("client " + client["clientID"] + " disconnected")
				for cl in clients:
					if cl["clientID"] == client["clientID"]:
						cl["alive"] = False
						break
				break
			msg = msg.split("}{")
			#TODO: catch halve complete messages
			i = 0
			for m in msg:
				if i != 0:
					m = "{" + m
				if i != len(msg)-1:
					m = m + "}"
				m = json.loads(m)
				i += 1

				if(m["type"] == "hearthbeat"):
					tim.cancel()
					tim = Timer(10, timeout)
					tim.start()

				elif m["type"] == "update":
					updates = []
					for clPackage in m["packages"]:
						for sePackage in packages:
							if clPackage["package"] == sePackage["package"]:
								if clPackage["version"] != sePackage["version"]:
									clPackage["updateVersion"] = sePackage["version"]
									updates.append(clPackage)
									break
					inSocket.send(bytes(json.dumps(updates), "utf-8"))

				elif m["type"] == "aviable":
					packs = packages
					for clPackage in m["packages"]:
						for sePackage in packages:
							if clPackage["package"] == sePackage["package"]:
								packs.remove(sePackage)
					inSocket.send(bytes(json.dumps(packs), "utf-8"))
				
				elif m["type"] == "upgrade":
						msg = {}
						packageFound = False
						for package in packages:
							if package["package"] == m["package"]["package"]:
								packageFound = True
								if package["version"] == m["package"]["version"]:
									msg["info"] = "Already up to Date!"
								else:
									f = None
									try:	
										f = open(package["url"], "rb")
										pack = f.read()
										f.close()
										try: 
											pack = pack.decode("utf-8")
										except UnicodeDecodeError:
											pack = pack.decode("latin-1")
										msg = {"info": None, "version": package["version"], "file": pack}
									except FileNotFoundError:
										print("Error: couldn't find File of package " + package["package"])
										msg["info"] = "File couldn't be found on the server!"
									break
						if not packageFound:
							print("Package " + m["package"] + " was requested but not found")
							msg = {"info": "Package couldn't be found on the server!"}
						if msg != {}:
							inSocket.send(bytes(json.dumps(msg), "utf-8"))
	tim.cancel()
	for cl in clients:
		if cl["clientID"] == client["clientID"]:
			cl["alive"] = False
			break
	print("Thread for client " + client["clientID"] + " finished")

def timeout():
	print("Ich heiße Tim!")	

def generateTestPackages():
	global packages
	packages = [{"package": "upToDate", "version": "1.0", "url": "Packages/upToDate.tar.gz"}, {"package": "needsUpgrade", "version": "2.0", "url": "Packages/needsUpgrade.tar.gz"}, {"package": "brokenUrlServerside", "version": "3.0", "url": "1"}, {"package": "brokenUrlClientside", "version": "4.0", "url": "Packages/brokenUrlClientside.tar.gz"}, {"package": "notOnClient", "version": "1.0", "url": "Packages/notOnClient.tar.gz"}]
	savePackages()

if __name__ == "__main__":
    main()

#json.dump(data, write_file)    writes to json converted data in write_file
#json.dumps(data)   returns data as json-string
#json.loads(json_string)   returns data as in python format (dict for json objects) depending on json_string
#json.load(read_file)   see loads
