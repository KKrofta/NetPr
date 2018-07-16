import hashlib
import json
import platform
import select
import socket
import subprocess
import sys
import time
from psutil import virtual_memory
from threading import Thread
from uuid import getnode

packages = []
consoleInput = []
tarEncoding = "latin-1"
running = True

def main():
	"""
	Creates a thread to listen to console commands and then starts a socket on the given host and port.
	To start communication a message containing "clientID", "ip" and "info" which contains "cpu", "gpu" and "ram" is send via the socket.
	When the server sends a port as answer the connection is closed and the connection to a new socket is started with the given port.
	Then a while loop is started doing two things on each loop:
		First a message containing a dictionary with one attribute "type" wich contains the string "hearthbeat" is send.
		Second the commands stored in consoleInput are worked off.
		If the command is "packages" the packages installed are printed out
		If the command is "update" a message is send to the server which contains a dictionary with "type" "update" and the packages list as "packages". The server then replies with a list of packages in the same format which contain those packages that have a different version on the server compared to the ones installed on the client. This list gets printed out.
		If the command is "aviable" the procedure is similar to update with the difference that the packages send by the sever are the ones which are not installed on the client.
		If the command is "upgrade" a message gets send to the server that contains the "type" upgrade and the package that shall be updated. The server then sends the file and new version number. The file is then installed und der the path given under "url" in the corresponding element in packages.
		If the command is "install" the procedure is similar to upgrade with the difference that the given path is used and the package is added to packages.
	"""
	if(len(sys.argv) == 3):
		generateTestPackages()
		loadPackages()

		t = Thread(target=startListener, args=())
		t.start()

		host = sys.argv[1]
		port = int(sys.argv[2])

		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
		s.connect((host, port))
		print("connected to ")

		info = {}
		gpu = subprocess.Popen(["lshw -c video | grep -E Prod\|prod"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
		gpu = gpu.communicate()[0].decode("utf-8").replace("\\n", "")[16:]
		cpu = platform.processor()
		mem = virtual_memory()
		mem = mem.total
		info["cpu"] = cpu
		info["gpu"] = gpu
		info["ram"] = mem
		#TODO

		clientID = str(getnode())
		clientInfo = {"clientID": clientID, "Info": info, "ip": socket.gethostbyname(socket.gethostname())}
		clientInfo = json.dumps(clientInfo)
		print(clientInfo)
		sentbytes = s.send(bytes(clientInfo, "utf-8"))
		print("send ")
	
		port = s.recv(500)
		port = int(port.decode("utf-8"))
		print("connecting to port: " + str(port))

		s.close()
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
		s.connect((host, port))
		print("connected")
		
		while 1:
			time.sleep(1)
			s.send(bytes(json.dumps({"type": "hearthbeat"}), "utf-8"))
			for command in consoleInput:
				if command[0] == "update":
					req = {"type": "update", "packages": []}
					for package in packages:
						req["packages"].append(package)
					s.send(bytes(json.dumps(req), "utf-8"))
					updates = s.recv(500)
					updates = json.loads(updates.decode("utf-8"))
					if len(updates) == 0:
						print("There are no new updates aviable")
					else:
						print("There are updates for the following packages:")
						for update in updates:
							u = update["package"] + ": Version " + update["updateVersion"] + " aviable, current Version is " + update["version"]
							print(u)

				elif command[0] == "packages":
					print("Package : Version : Path")
					for pack in packages:
						print(pack["package"] + " : " + pack["version"] + " : " + pack["url"])

				elif command[0] == "aviable":
					req = {"type": "aviable", "packages": []}
					for package in packages:
						req["packages"].append(package)
					s.send(bytes(json.dumps(req), "utf-8"))
					packs = s.recv(500)
					packs = json.loads(packs.decode("utf-8"))
					if len(packs) == 0:
						print("There are no packages aviable to install")
					else:
						print("The following packages can be installed:")
						for pack in packs:
							u = pack["package"] + ": Version " + pack["version"]
							print(u)

				elif command[0] == "upgrade":
					if len(command) == 2:
						packageFound = False
						for package in packages:
							if package["package"] == command[1]:
								req = {"type": "upgrade", "package": package}
								s.send(bytes(json.dumps(req), "utf-8"))
								pack = s.recv(8000)
								complete = False
								while not complete:
									rdy = select.select([s], [], [], 0.1)
									if rdy[0]:
										pack += s.recv(8000)
									else:
										complete = True
								pack = pack.decode("utf-8")
								pack = json.loads(pack)
								if pack["info"] == None:
									try:
										f = open(package["url"], "wb")
										f.write(bytes(pack["file"], tarEncoding))
										f.close()
										package["version"] = pack["version"]
										savePackages()
										print("Package " + package["package"] + " successfully upgraded to version " + package["version"])
									except Exception as e:
										print(e)
								else:
									print(pack["info"])
								
								packageFound = True
						if not packageFound:
							print("No such package installed")
					else:
						print("Usage: upgrade [packagename]")

				elif command[0] == "install":
					if len(command) == 3:
						path = command[2]
						if path[7:] != ".tar.gz":
							path = path + (".tar.gz")
						package = {"package": command[1], "version": "", "url": path}
						req = {"type": "upgrade", "package": package}
						s.send(bytes(json.dumps(req), "utf-8"))
						pack = s.recv(8000)
						complete = False
						while not complete:
							rdy = select.select([s], [], [], 0.1)
							if rdy[0]:
								pack += s.recv(8000)
							else:
								complete = True
						pack = pack.decode("utf-8")
						pack = json.loads(pack)
						if pack["info"] == None:
							try:
								f = open(package["url"], "wb")
								f.write(bytes(pack["file"], tarEncoding))
								f.close()
								package["version"] = pack["version"]
								packages.append(package)
								savePackages()
								print("Package " + package["package"] + " successfully installed")
							except Exception as e:
								print(e)
						else:
							print(pack["info"])
								
						packageFound = True
					else:
						print("Usage: install [packagename] [path]")
				
				else:
					print("command : function")
					print("update : shows a list of the packages that require updates")
					print("packages : shows the installed packages")
					print("aviable : shows the packages that could be installed")
					print("upgrade [packageName] : upgrades the package [packageName] to the newest version]")
					print("install [packageName] [path] : installs the package [packageName] at the given [path]")

				consoleInput.pop(0)
			
		s.close()
		print("connection closed")
	else:
		print("Usage: client host port")

def generateTestPackages():
	"""
	Generates dummy package data for testing.
	"""
	global packages
	packages = [{"package": "upToDate", "version": "1.0", "url": "ClientPackages/upToDate.tar.gz"}, {"package": "needsUpgrade", "version": "1.0", "url": "ClientPackages/needsUpgrade.tar.gz"}, {"package": "brokenUrlServerside", "version": "2.0", "url": "ClientPackages/brokenUrlServerside.tar.gz"}, {"package": "brokenUrlClientside", "version": "3.0", "url": ""}, {"package": "notOnServer", "version": "1.0", "url": "ClientPackages/notOnServer.tar.gz"}]
	savePackages()

def loadPackages():
	"""
	Loads the installed packages from a json file called localPackages.json. If the file is not fould it gets created.
	"""
	global packages
	f = None
	try:
		f = open("localPackages.json", "r")
		packages = json.loads(f.read())
	except FileNotFoundError:
		f = open("localPackages.json", "w+")
		f.write("[]")
	f.close()
	print("packages loaded")

def savePackages():
	"""
	Saves the installed packages to a json file called localPackages.json
	"""
	global packages
	f = None
	try:
		f = open("localPackages.json", "w")
		f.write(json.dumps(packages))
		f.close()
	except Exception as e:
		print(e)

def startListener():
	"""
	Listens for console input and adds it to the consoleInput list so that it can be handled.
	"""
	while running:
		command = input("")
		command = command.split(" ")
		consoleInput.append(command)

if __name__ == "__main__":
    main()
