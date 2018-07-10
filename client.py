import socket
import sys
from uuid import getnode

def main():
	if(len(sys.argv) == 4):
		host = sys.argv[1]
		port = int(sys.argv[2])

		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
		s.connect((host, port))
		print("connected to ")

		clientID = str(getnode())
		print(clientID)
		registerInfo = clientID;
		sentbytes = s.send(bytes(registerInfo, "utf-8"))
		print("send ")
	
		#b = s.recv(500)
		#b.decode("utf-8")
		#print(b)

		s.close()
		print("connection closed")
	else:
		print("Usage: client host port command")

if __name__ == "__main__":
    main()
