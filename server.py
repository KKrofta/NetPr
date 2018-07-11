import socket
import json
import time
from time import gmtime, strftime
from threading import Thread

clients = []
host = "localhost"
port = 5000
ready = False
connected = False

def main():
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
	try:
		while 1:
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

			while not connected:
				port += 1
				t = Thread(target=connect, args=(host, port,))
				t.start()
				while not ready:
					time.sleep(0.0001)
			sentbytes = inSocket.send(bytes(str(port), "utf-8"))				
			ready = False
			connected = False
			inSocket.close()
			print(clients)
				
	finally:
		s.close()

def connect(host, port):
	global ready
	global connected
	try:
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
		s.bind((host, port))
		s.listen(socket.SOMAXCONN)
		insocket, addr = s.accept()
		ready = True
		connected = True
		print("thread setup complete on port:")
		print(port)
	except OSError:
		ready = True
		print("thread setup failed")
		

if __name__ == "__main__":
    main()

#json.dump(data, write_file)    writes to json converted data in write_file
#json.dumps(data)   returns data as json-string
#json.loads(json_string)   returns data as in python format (dict for json objects) depending on json_string
#json.load(read_file)   see loads
