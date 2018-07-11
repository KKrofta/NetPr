import json
import socket
import sys
from uuid import getnode
import time

def main():
	if(len(sys.argv) == 3):
		host = sys.argv[1]
		port = int(sys.argv[2])

		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
		s.connect((host, port))
		print("connected to ")

		clientID = str(getnode())
		clientInfo = {"clientID": clientID, "Info":{}}
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

		s.close()
		print("connection closed")
	else:
		print("Usage: client host port")

if __name__ == "__main__":
    main()
