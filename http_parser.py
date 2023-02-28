import re
import sys
import datetime
from Queue import *
import saving_data

import os


class HTTP_Parser:
    def __init__(self, sessionid, url, ignore, tcptype, saves):
        #self.tcp_type = tcp_type  # request or response
        self.request_nr = 0  # request
        self.response_nr = 0 # response
        self.inmessagebody = 0  # if its in message body
        self.mb_chars_to_read = 0  # chars of message body to read
        self.http_header = ""  # actual http header
        self.http_mess_body = ""  # actual http message body
        self.ignore = ignore  # which response-contentlength to ignore because of HEAD request
        self.url = url  #Queue
        self.chunkedmessage = 0  # shows if message-body has chunked encoding
        self.chunkedheader = ""  # chunked header
        self.chunkedbody = ""  # Chunked Body
        self.read_finish = 0  # when no content length is specified
        self.sessionid = sessionid
        self.tcptype = tcptype
        self.saves = saves   # Saving Object
        self.actual_url = ("","")
        self.encoding = ""

    def handle_tcppacket(self, tcppacket):
        # No Info about Length
        if self.read_finish:
            self.readrest(tcppacket)
        # Chunked Message Body
        elif self.chunkedmessage:
            self.handle_chunked_message(tcppacket)
        # Message Body with content Length
        elif self.inmessagebody:
            self.handle_message(tcppacket)
        # Header handling
        else:
            if self.tcptype == "req":
                self.handle_req(tcppacket)
            elif self.tcptype == "res":
                self.handle_res(tcppacket)

    def handle_chunked_message(self, tcppacket):
        tcppacket = self.chunkedheader + tcppacket
        # Check if in chunked message
        if self.inmessagebody:
            self.handle_ch_body(tcppacket)
        else:
            searchObj = re.search(r"0\r\n\r\n", tcppacket, re.I)
            if searchObj:
                ## Chunked message reading finished
                url = self.actual_url
                self.saves.save_file(url, self.http_mess_body, self.sessionid, self.encoding)

                self.http_mess_body = ""
                self.chunkedmessage = 0
                self.chunkedheader = ""
                mess = re.split("0\r\n\r\n", tcppacket, 1)
                # Exist because found eralier
                self.handle_tcppacket(mess[1])
            else:
                ### Get other expression
                searchObj = re.search(r"[0-9a-f]+\r\n", tcppacket, re.I | re.M)
                if searchObj:
                    ## Dont Need Header anymore
                    self.chunkedheader = ""
                    self.inmessagebody = 1
                    self.mb_chars_to_read = int(searchObj.group(), 16)
                    mess = re.split("[0-9a-f]+\r\n", tcppacket, re.I)
                    self.handle_ch_body(mess[1])
                else:
                    self.chunkedheader += tcppacket

    def handle_ch_body(self, tcppacket):
        if len(map(ord, tcppacket)) <= self.mb_chars_to_read:
            self.mb_chars_to_read -= len(map(ord, tcppacket))
            self.chunkedbody += tcppacket
            if self.mb_chars_to_read == 0:
                self.http_mess_body += self.chunkedbody
                self.chunkedbody = ""
        else:
            array = map(ord, tcppacket)
            message_data = array[:self.mb_chars_to_read]
            rest_of_package = array[self.mb_chars_to_read:]
            self.mb_chars_to_read -= len(message_data)
            array = map(chr, message_data)
            mess = ""
            rest = ""
            for m in array:
                mess += m
            message_data = mess
            array = map(chr, rest_of_package)
            for r in array:
                rest += r
            rest_of_package = rest
            self.inmessagebody = 0
            self.chunkedbody += message_data
            self.http_mess_body += self.chunkedbody
            self.chunkedbody = ""
            self.handle_chunked_message(rest_of_package)

    def handle_message(self, tcppacket):
        # Maybe detecting new Header
        if len(map(ord, tcppacket)) <= self.mb_chars_to_read:
            # Read whole Packet as Message Data
            self.mb_chars_to_read -= len(map(ord, tcppacket))
            self.http_mess_body += tcppacket
            # finished message body
            if self.mb_chars_to_read == 0:
                self.inmessagebody = 0
                # Writing the Packet to a file for saving

                url = self.actual_url

                self.saves.save_file(url, self.http_mess_body, self.sessionid, self.encoding)
                self.http_mess_body = ""
        else:
            # Message Body contains new HTTP-Packet
            array = map(ord, tcppacket)
            message_data = array[:self.mb_chars_to_read]
            rest_of_package = array[self.mb_chars_to_read:]
            array = map(chr, message_data)
            mess = ""
            rest = ""
            for m in array:
                mess += m
            message_data = mess
            array = map(chr, rest_of_package)
            for r in array:
                rest += r
            rest_of_package = rest
            # Saving the http packet
            self.inmessagebody = 0
            self.mb_chars_to_read = 0
            self.http_mess_body += message_data
            self.http_mess_body += message_data
            ## Finished Reading Packet

            url = self.actual_url

            self.saves.save_file(url, self.http_mess_body, self.sessionid, self.encoding)
            self.http_mess_body = ""
            # handling the rest of the package
            self.handle_tcppacket(rest_of_package)

    def handle_req(self, tcppacket):
        found = tcppacket.find("\x0d\x0a\x0d\x0a")
        # whole http header is there
        if found >= 0:

            searchObj = re.search(r"(GET|HEAD|POST|PUT|DELETE|CONNECT|OPTIONS|TRACE) .+ HTTP/\d.\d",
                                      self.http_header + tcppacket, re.I)
            if searchObj:
                # Ignore Content Length of HEAD request
                searchObj = re.search(r"HEAD", self.http_header + tcppacket, re.I)
                if searchObj:
                    self.ignore.append(self.request_nr)
                searchObj = re.search(r"\r\nHost: .*", self.http_header + tcppacket, re.M | re.I)
                if searchObj:
                    host = re.sub(r'Host: ', "", searchObj.group())
                    host = re.sub(r'\r\n', "", host)
                    host = re.sub(r'\r', "", host)
                    searchObj = re.search(r"(GET|HEAD|POST|PUT|DELETE|CONNECT|OPTIONS|TRACE) .* HTTP",
                                              self.http_header + tcppacket, re.I)
                    if searchObj:
                        uri = re.sub(r'(GET|HEAD|POST|PUT|DELETE|CONNECT|OPTIONS|TRACE) ', "", searchObj.group())
                        uri = re.sub(r' HTTP', "", uri)
                        if uri == "/":
                            uri = "/index.html"

                        _uri = uri.rsplit("/", 1)
                        host += _uri[0]
                        uri = _uri[1]
                    else:
                        uri = "U_notfound"
                else:
                    host = "H_notfound"
                self.url.put((host, uri))
                self.actual_url = (host,uri)
                self.request_nr += 1
                self.handle_header(tcppacket)
        else:
            # Need to wait for rest of Header
            self.http_header += tcppacket

    def handle_res(self, tcppacket):
        self.encoding = ""
        found = tcppacket.find("\x0d\x0a\x0d\x0a")
        # whole http header is there
        if found >= 0:
            searchObj = re.search(r"HTTP/\d.\d \d\d\d .+", self.http_header + tcppacket, re.I)
            if searchObj:
                self.actual_url = self.url.get()
                self.response_nr += 1
                searchObj = re.search(r"\r\ncontent-encoding: .+", self.http_header + tcppacket, re.M | re.I)
                if searchObj:
                    self.encoding = re.sub(r'\r\ncontent-encoding: ', "", searchObj.group())
                self.handle_header(tcppacket)
        else:
            # Need to wait for rest of Header
            self.http_header += tcppacket


    def handle_header(self, tcppacket):
        l_header = re.split("\x0d\x0a\x0d\x0a", tcppacket, 1)
        self.http_header += l_header[0]
        # Get Content Length
        searchObj = re.search(r"\r\nContent-Length: \d+", self.http_header, re.M | re.I)
        if searchObj:
            # Extract the Content Length Value
            self.mb_chars_to_read = int(re.sub(r'\D', "", searchObj.group()))
            self.inmessagebody = 1
            # Check if I schould ignore Content-Length
            if self.tcptype == "res" and (self.response_nr - 1) in self.ignore:
                self.inmessagebody == 0

        else:
            searchObj = re.search(r"\r\nTransfer-Encoding: chunked", self.http_header, re.M | re.I)
            if searchObj:
                # Go to chunked message
                self.chunkedmessage = 1
            else:
                if self.tcptype == "res":
                    searchObj = re.search(r"1\d\d |204 | 304", self.http_header, re.M | re.I)
                    if searchObj:
                        searchObj = re.search(r"1\d\d |204 ", self.http_header, re.M | re.I)
                        if searchObj:
                            self.url.put(self.actual_url)

                        self.read_finish = 0
                    else:
                        # Read till finished
                        self.read_finish = 1
        self.http_header = ""
        self.handle_tcppacket(l_header[1])

    def readrest(self, tcppacket):
        self.http_mess_body += tcppacket
