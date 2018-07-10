import socket
import json

clients = []

def main():
	host = "localhost"
	port = 5000
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
	s.bind((host, port))
	s.listen(socket.SOMAXCONN)
	try:
		while 1:
			inSocket, addr = s.accept()
			info = inSocket.recv(500)
			info.decode("utf-8")
			print(info)
			inSocket.close()
	finally:
		s.close()

def registerClient():
	try:
		while 1:
			inSocket, addr = s.accept()
			info = s.recv(500)
			info.decode("utf-8")
			
	finally:
		s.close()

if __name__ == "__main__":
    main()

#json.dump(data, write_file)    writes to json converted data in write_file
#json.dumps(data)   returns data as json-string
#json.loads(json_string)   returns data as in python format (dict for json objects) depending on json_string
#json.load(read_file)   see loads
