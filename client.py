import hashlib
import json
import socket
import subprocess
import sys
import time
from threading import Thread
from uuid import getnode

packages = []
consoleInput = []
tarencoding = "latin-1"

def main():
	if(len(sys.argv) == 3):
		loadPackages()

		t = Thread(target=startListener, args=())
		t.start()

		host = sys.argv[1]
		port = int(sys.argv[2])

		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
		s.connect((host, port))
		print("connected to ")

		info = {}
		cpu = subprocess.Popen(["lscpu | grep -E \"Model name\""], stdout=subprocess.PIPE, shell=True)
		cpu = str(cpu.communicate()[0]).replace("\\n", "")
		cpu = cpu[2: len(cpu)-2]
		print(cpu)
		info["cpu"] = cpu
		info["gpu"] = ""
		info["ram"] = ""
		#TODO

		clientID = str(getnode())
		clientInfo = {"clientID": clientID, "Info":info}
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
					print(packages)

				elif command[0] == "upgrade":
					if len(command) == 2:
						packageFound = False
						for package in packages:
							if package["package"] == command[1]:
								req = {"type": "upgrade", "package": package}
								s.send(bytes(json.dumps(req), "utf-8"))
								pack = s.recv(5000)
								pack = json.loads(pack.decode("utf-8"))
								if pack["info"] == None:
									f = open("bob.tar.gz", "wb")
									f.write(bytes(pack["file"], tarencoding))
									f.close()
								else:
									print(pack["info"])
								
								packageFound = True
						if not packageFound:
							print("No such package installed")
					else:
						print("Usage: upgrade [packagename]")
				
				consoleInput.pop(0)
			
		s.close()
		print("connection closed")
	else:
		print("Usage: client host port")

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

def startListener():
	while 1:
		command = input("")
		command = command.split(" ")
		consoleInput.append(command)

if __name__ == "__main__":
    main()
