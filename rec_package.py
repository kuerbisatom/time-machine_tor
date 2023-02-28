import sys, socket, select
from Queue import *
import http_parser
import saving_without_deduplication
import saving_data

## max Number of queued Connections
BACKLOG = 10000
## Buffer Size
MAX_DATA_RECV = 4096

class Recv_Server:
    input_list = []
    conn_participants = {}
    ignore = []
    url_queue = {}
    def __init__(self, host, port):
        ## Open Proxy Server Socket
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.bind((host, port))
            self.server.listen(BACKLOG)
            self.saves = saving_data.Saving()
        except OSError as msg:
            self.server.close()
            print ("Runtime Error:", msg)
            sys.exit(1)

    def main_loop(self):
        self.input_list.append(self.server)
        while 1:
            inputready, outputready, exceptready = select.select(self.input_list, [], [])
            for self._input in inputready:
                if self._input == self.server:
                    client, client_addr = self.server.accept()
                    data = client.recv(256)

                    sess_type = data.split(",", 3)
                    sessionid = int(sess_type[0])
                    tcp_type = sess_type[1]
                    id = int(sess_type[2])
                    if tcp_type == "req":
                        self.url_queue[id] = Queue()
                    url = self.url_queue[id]
                    self.input_list.append(client)
                    print ("[*] Accepting a new Connection")
                    parser = http_parser.HTTP_Parser(sessionid, url, self.ignore, tcp_type, self.saves)
                    self.conn_participants[client] = parser
                    if len(sess_type) >= 4 :
                        parser.handle_tcppacket(sess_type[3])
                    break

                data = self._input.recv(MAX_DATA_RECV)

                if len(data) == 0:
                    ## Check if need to save File( Readtillfinished)
                    if self.conn_participants[self._input].read_finish:
                        url = self.conn_participants[self._input].actual_url
                        http_packet = self.conn_participants[self._input].http_mess_body
                        sessionid = self.conn_participants[self._input].sessionid
                        self.saves.save_file(url, http_packet, sessionid)
                    self.input_list.remove(self._input)

                    self._input.close()
                    print ("[*] Closing Connection")
                    break

                url = self.conn_participants[self._input].url
                self.conn_participants[self._input].handle_tcppacket(data)

if __name__ == "__main__":
    host = sys.argv[1]
    port = int(sys.argv[2])
    server = Recv_Server(host, port)
    print("[*] RecvServer Initialized")
    print("[*] Listening on Port:" + str(port))
    server.main_loop()
