from collections import deque
import hashlib
import datetime
import os
import libnacl.public
import libnacl.utils
import re
import base64

class Saving():
    def __init__(self):
        self.linked_list = deque()
        ## Initialize Linked List with existing values
        try:
            with open("test/url_list", 'r') as f:
                for line in f:
                    self.linked_list.append(line)
                f.close()
        except:
            print("[*] URL File don't exist yet")

    def save_file(self, uri, http_message, sessionid, encoding):
        ##  Hash the http_message
        hash = hashlib.sha256(http_message).hexdigest()
        if (hash +"\n") in self.linked_list:
            print "[*] Linked List contains Element"
            # Write which URL belongs to which Data
            f = open("test/data_and_uri", 'ab')
            f.write("(" + hash + "," + uri[0] + "/" + uri[1] + "," + encoding + ")\n")
            f.close()
        else:
            ## Save Hash to file to use later
            f = open("test/url_list", 'ab')
            f.write(hash + "\n")
            f.close()
            # Write which URL belongs to which Data
            f = open("test/data_and_uri", 'ab')
            encoding = re.sub("\r\n","",encoding)
            encoding = re.sub("\n","",encoding)
            f.write("(" + hash + "," + uri[0] + "/" + uri[1] + "," + encoding + ")\n")
            f.close()

            ## Getting Key
            bob = libnacl.utils.load_key('bob.key')
            alice = libnacl.utils.load_key('alice_public.key')
            ##Encrypt Content
            bob_box = libnacl.public.Box(bob.sk, alice.pk)
            bob_ctxt = bob_box.encrypt(http_message)

            # Save encrypted content
            timestamp = 'Timestamp:{:%Y-%m-%d}'.format(datetime.datetime.now())
            timestamp = "test/" + timestamp + "/" + str(sessionid)

            # Base64 encoding filepath
            hosts = uri[0].split("/")
            path = ""
            for i in range(1,len(hosts)):
                base64.b64encode('data to be encoded')
                temp = "/" + base64.urlsafe_b64encode(hosts[i])
                path += temp

            if not os.path.exists(timestamp + "/" + hosts[0] + path):
                os.makedirs(timestamp + "/" + hosts[0] + path)

            ## Saving Hash of filename
            filename = hashlib.sha256(uri[1]).hexdigest()
            f = open("test/saved_files","ab")
            f. write("(" + filename + "," + uri[1] + ")\n")
            f.close()

            ## Save to File
            file_out = open(timestamp + "/" + hosts[0] + path + "/" + filename, 'ab')
            file_out.write(bob_ctxt)
            file_out.close()
