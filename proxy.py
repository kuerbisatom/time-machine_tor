import sys, socket, select
import http_parser

## TC Port
C_PORT = 9150
## Saving Machine
S_HOST = "127.0.0.1"
S_PORT = 12346
## max Number of queued Connections
BACKLOG = 10000
## Buffer Size
MAX_DATA_RECV = 4096

## Create a Proxy Server
class ProxyServer:
    input_list = []
    conn_participants = {}
    sessionid = 0

    def __init__(self, host, port, sessionid):
        ## Open Proxy Server Socket
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.bind((host, port))
            self.server.listen(BACKLOG)
            self.sessionid = sessionid
        except OSError as msg:
            self.server.close()
            print ("Runtime Error:", msg)
            sys.exit(1)

    def main_loop(self, host, port):
        id = 0
        self.input_list.append(self.server)
        while (1):
            ## Selecting from input_list readable file-descriptor
            inputready, outputready, exceptready = select.select(self.input_list, [], [])
            ## Handling the fd where somethin can be read
            for self._input in inputready:
                ## For Server accepting new Connections
                if self._input == self.server:
                    id += 1
                    print ("[*] Accepting a new Connection")
                    connection = Connection(self)
                    connection.socks_conn(host, port)

                    ## Adding for select.select
                    self.input_list.append(connection.client)
                    self.input_list.append(connection.forward)

                    ## For getting the right Forwarding of the msg.
                    sessionid = self.sessionid
                    safe_server_req = Server(sessionid, "req", id)
                    safe_server_res = Server(sessionid, "res", id)

                    #parser = http_parser.HTTP_Parser(sessionid)
                    self.conn_participants[connection.forward] = (connection.client, safe_server_res)
                    self.conn_participants[connection.client] = (connection.forward, safe_server_req)
                    break

                self.data = self._input.recv(MAX_DATA_RECV)

                if len(self.data) == 0:
                    self.my_close()
                    print ("[*] Closing Connection")
                    break
                else:
                    ## Forward Message
                    self.handle_data()

    def handle_data(self):
        ## Send to HTTP_Parser
        self.conn_participants[self._input][1].rec_server.sendall(self.data)
        ## Sending to Tor-Client
        self.conn_participants[self._input][0].sendall(self.data)

    def my_close(self):
        ## Removing Connection from input List
        self.input_list.remove(self._input)
        self.input_list.remove(self.conn_participants[self._input][0])

        ## Clossing Connections
        self._input.close()
        self.conn_participants[self._input][0].close()

        ## Deleting from Dict
        del self.conn_participants[self.conn_participants[self._input][0]]
        del self.conn_participants[self._input]

## Create Connection from TB to Proxy to TC
class Connection:
    def __init__(self, proxy):
        self.forward = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ## Accept Connection from TB
        self.client, self.client_addr = proxy.server.accept()

    def socks_conn(self, host, port):
        try:
            self.forward.connect((host, port))
            ## Establish SOCKS connection
            socks_request = self.client.recv(MAX_DATA_RECV)
            self.forward.sendall(socks_request)
            socks_answer = self.forward.recv(MAX_DATA_RECV)
            self.client.sendall(socks_answer)
            print ("[*] SOCKS Connection established")

        except OSError as msg:
            ## TC Connection Fails
            print ("[*] Connection Failed:", msg)
            self.client.close()

class Server:
    ## Connection to the other server
    def __init__(self, sessionid, tcptype, id):
        try:
            self.rec_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.rec_server.connect((S_HOST, S_PORT))
            string = str(sessionid) + "," + tcptype + "," + str(id) + ","
            self.rec_server.sendall(string)
        except OSError as msg:
            self.server.close()
            print ("[*] Runtime Error:", msg)
            sys.exit(1)

if __name__ == "__main__":
    host = sys.argv[1]
    port = int(sys.argv[2])
    sessionid = int(sys.argv[3])
    proxy = ProxyServer(host, port, sessionid)
    print("[*] Proxy Initialized")
    print("[*] Listening on Port:" + str(port))
    proxy.main_loop(S_HOST, C_PORT)
