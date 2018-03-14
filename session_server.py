#!/usr/bin/python
import random

import threading,time
import sys,errno,traceback,os,re
import socket
import http.server
import http.server
import json
from xml.sax.handler import ContentHandler;
import xml.sax;
from socketserver import ThreadingMixIn

import logging,locallog

logger = locallog.Logger("session_server").logger

PORT = 22002
FILE="index.html"

############## EXCEPTIONS ####################

class InvalidDictionaryTypeException(Exception):
  pass;

class InvalidRequestException (Exception):
   def __init__(self, value):
      self.value = value
   def __str__(self):
      return repr(self.value)

################################################

def reply_type(path) : 
   #Check the file extension required and
   #set the right mime type

   print ("reply_type - path="+str(path))
   if path == "/": 
     retpath = FILE
   else :
     retpath = path

   logger.debug("path = " +retpath)

   sendReply = False
   mimetype = None

   if retpath.endswith(".html"):
    mimetype='text/html'
    sendReply = True
   if retpath.endswith(".jpg"):
    mimetype='image/jpg'
    sendReply = True
   if retpath.endswith(".gif"):
    mimetype='image/gif'
    sendReply = True
   if retpath.endswith(".js"):
    mimetype='application/javascript'
    sendReply = True
   if retpath.endswith(".css"):
    mimetype='text/css'
    sendReply = True

   return [sendReply,mimetype,retpath]


def stringify(input) : # removed unicode or other coding
  parsed = [];
  for entry in input:
    if isinstance(entry,dict):
       parsedentry = dict()
       for key in list(entry.keys()) :
           # known types retained, others stringified
           if isinstance(entry[key],int) or isinstance(entry[key],float) or isinstance(entry[key],bool) : 
              parsedentry[str(key)]=entry[key]
           else : 
              parsedentry[str(key)]=str(entry[key])
       parsed.append(parsedentry)
    else :
       raise InvalidDictionaryTypeException()
  return parsed


def get_random_data():
  ''' generates random data for demo '''
  return [random.uniform(0,1) for x in range(0,20)]


'''
   Request Type = 1 means a Sync Request
'''
def sync_refresh(request_data,fs,sess) :  
   print(("type(request_data)="+str(type(request_data))+ " request_data: "+str(request_data)))
   parsed_request_data =  stringify(request_data)
   logger.debug("sync_refresh:"+str(parsed_request_data))
   ret=dict()
   ret['response_type']=1;
   ret['response_data']=[];
   return ret;


'''
   Request Type = 2 means an Async Request
'''
def async_refresh(request_data,fs,sess) :
   parsed_request_data =  stringify(request_data)
   logger.debug("async_refresh:"+str(parsed_request_data))
   ret=dict()
   ret['response_type']=1;
   ret['response_data']=get_random_data();
   return ret;



def handleRequest(req,fs,sess):
   request_type_key='request_type' 
   data_key='request_data'
   print ("handleRequest:"+str(req))
   handlers_map = { 1 : sync_refresh , 2 : async_refresh }
   if data_key in req and request_type_key in req : 
        if req[request_type_key] in handlers_map :
             return json.dumps(handlers_map[req[request_type_key]](req[data_key],fs,sess))
        else : 
           raise UnknownRequestTypeException()
   else : 
       raise InvalidRequestException(req)
   

class MTServer (ThreadingMixIn, http.server.HTTPServer):
    allow_reuse_address = True
    acceptable_errors = (errno.EPIPE, errno.ECONNABORTED)

    def handle_error(self, request, client_address):
        error = sys.exc_info()[1]
        if ((isinstance(error, socket.error) and
             isinstance(error.args, tuple) and
             error.args[0] in self.acceptable_errors)
            or
            (isinstance(error, IOError) and
             error.errno in self.acceptable_errors)):
            pass  # remote hang up before the result is sent
        else:
            logger.error(error)


class HTTPHandler(http.server.SimpleHTTPRequestHandler):
    """Handling all HTTP Requests here."""

    filestore = None
    sessions = {}

    def do_GET(self):
        logger.debug("Processing DEBUG");
        pattern ="(.*)\?(.*)"
        params_dict=dict()
        res=re.search(pattern,self.path);
        if res :
              main_path=res.group(1)
              params=res.group(2)
              ppattern="([^=]+)=([^=\&]*)[\&]*(.*)"
              pres = re.search(ppattern,params);
              while pres :
                   #logger.debug("param(\""+pres.group(1)+"\")=\""+pres.group(2)+"\"")
                   params_dict[pres.group(1).strip()]=pres.group(2).strip();
                   pres = re.search(ppattern,pres.group(3));
        else :
              main_path=self.path

        if len(list(params_dict.keys()))>0 :
              logger.debug("ParamsDict="+str(params_dict));

        (sendReply,mimetype,path)=reply_type(main_path)

        if sendReply : 
          resp=open(os.path.abspath(os.path.dirname(sys.argv[0]))+"/"+path).read().encode()
          self.send_response(200)
          self.send_header("Content-type",mimetype)
          self.send_header("Content-length", len(resp))
          self.end_headers()
          self.wfile.write(resp)



    def do_POST(self):
        length = int(self.headers.get_all('content-length')[0])        
        
        json_request_data = self.rfile.read(length).decode()
        logger.debug("Request Arrived: \""+str(json_request_data)+"\"")
        try:
            #logger.debug("Parsed json:"+str(json.loads(json_request_data)))
            result = handleRequest(json.loads(json_request_data),self.filestore,self.sessions)
            self.send_response(200)
            self.send_header("Content-type","application/json")
            self.send_header("Content-length", len(result))
            self.end_headers()
        except:
            traceback.print_exc(file=sys.stdout)
            result = 'error'
        self.wfile.write(result.encode())


def run_server(server):
       server.serve_forever()

def start_server(HOSTNAME):
    """Start the server."""
    server_address = (HOSTNAME, PORT)
    httpHandler = HTTPHandler 
    server = MTServer(server_address,httpHandler)
    st=threading.Thread(None,run_server,"HTTPServerThread",[server]);
    st.start()
    logger.info("Started Server on Port:"+str(PORT))
    st.join()


if __name__ == "__main__":
    HOSTNAME="localhost"
    start_server(HOSTNAME)

