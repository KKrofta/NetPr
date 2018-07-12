import json
import socket
import subprocess
import sys
import time
from threading import Thread
from uuid import getnode

packages = [{"package": "1", "version": "1", "url": "1"}, {"package": "2", "version": "2", "url": "2"}]
consoleInput = []

def main():
	if(len(sys.argv) == 3):
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
				if command == "update":
					req = {"type": "update", "packages": []}
					for package in packages:
						req["packages"].append(package)
					print(req)
					s.send(bytes(json.dumps(req), "utf-8"))
				consoleInput.pop(0)
			
		s.close()
		print("connection closed")
	else:
		print("Usage: client host port")

def startListener():
	while 1:
		command = input("")
		consoleInput.append(command)

if __name__ == "__main__":
    main()
