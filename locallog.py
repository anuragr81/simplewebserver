
import logging;

loglevel=logging.DEBUG

loglevelmap = { 'megabook':logging.DEBUG,
                'server':logging.DEBUG} ;

class Logger :
  def __init__(self,LOGGER_NAME):
      FORMAT='%(asctime)-15s %(message)s'
      logging.basicConfig(format=FORMAT);
      self.logger = logging.getLogger(LOGGER_NAME);
      global loglevel
      if LOGGER_NAME in loglevelmap :
          self.logger.setLevel(loglevelmap[LOGGER_NAME])
          #self.attachFile("/home/fxdev/lq2mlog",logging.INFO)
      else:
          self.logger.setLevel(loglevel)

  def attachFile(self,fname,loglevel):
      fh = logging.FileHandler(fname)
      fh.setLevel(loglevel)
      self.logger.addHandler(fh)

