import json
import socket
import sys
import subprocess
from uuid import getnode
import time

def main():
	if(len(sys.argv) == 3):
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
			s.send(bytes(json.dumps({"hearthbeat": True}), "utf-8"))

		s.close()
		print("connection closed")
	else:
		print("Usage: client host port")

if __name__ == "__main__":
    main()
