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
		print("connecting to port:")
		print(port)

		s.close()
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
		s.connect((host, port))
		print("connected to ")
		
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
	global packages
	packages = [{"package": "upToDate", "version": "1.0", "url": "ClientPackages/upToDate.tar.gz"}, {"package": "needsUpgrade", "version": "1.0", "url": "ClientPackages/needsUpgrade.tar.gz"}, {"package": "brokenUrlServerside", "version": "2.0", "url": "ClientPackages/brokenUrlServerside.tar.gz"}, {"package": "brokenUrlClientside", "version": "3.0", "url": ""}, {"package": "notOnServer", "version": "1.0", "url": "ClientPackages/notOnServer.tar.gz"}]
	savePackages()

def loadPackages():
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
	global packages
	f = None
	try:
		f = open("localPackages.json", "w")
		f.write(json.dumps(packages))
		f.close()
	except Exception as e:
		print(e)

def startListener():
	while running:
		command = input("")
		command = command.split(" ")
		consoleInput.append(command)

if __name__ == "__main__":
    main()
