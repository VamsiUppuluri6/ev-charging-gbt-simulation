import can
import logging
import time as tm
import datetime as dt
from can import Message
from threading import Thread
import os.path
from scipy.integrate import quad
import json
import tornado.web
import tornado.websocket
import tornado.httpserver
import numpy as np
import asyncio
#from pymodbus.client.sync import ModbusSerialClient
'''
client = ModbusSerialClient(
    method='rtu',
    port='/dev/ttyUSB0',
    baudrate=9600,
    timeout=3,
    parity='N',
    stopbits=1,
    bytesize=8
)


def smps(jj,cur,onoff):
 for dev in  range(1,4):   
  if client.connect():  # Trying for connect to Modbus Server/Slave
  #  Reading from a holding register with the below content.
    re=client.write_register(2,onoff,unit=dev)
    re=client.write_register(0,jj,unit=dev)
    re=client.write_register(1,cur*1000,unit=dev)
    res = client.read_holding_registers(address=0, count=1, unit=dev)

   # Reading from a discrete register with the below content.
    # res = client.read_discrete_inputs(address=1, count=1, unit=1)

    if not res.isError():
        print(res.registers)
    else:
        print(res)

  else:
    print('Cannot connect to the Modbus Server/Slave')

'''






tornado_connections ={"wsconnect":""}
class extendcan(Thread):
      def __init__(self):

            self.startf=False
            self.setcur=0
            self.cumeng=0
            self.cumoeng=0
            self.lenbrm=0
            self.numbrm=0
            self.terbrm=0
            self.pgnbrm=0
            self.voltout=80
            self.curout=30
            self.cumtmp=1
            self.cummin=0
            self.inittm=dt.datetime.utcnow()
            self.maxvolt=100
            self.minvolt=0
            self.maxcur=30
            self.mincur=0
            self.npmesvolt=np.array([])
            self.npmescur=np.array([])
            self.npvoltout=np.array([])
            self.npcurout=np.array([])
            self.mesvolt=0.0
            self.mescur=0.0
            self.soc=0
            self.estrem=0
            self.curdem=0
            self.voltdem=0
            self.mode=0
            self.recmsg="CHM"
            self.iddecchr={0x1826F456:"CHM",0x1801F456:"CRM",0x1CECF456:{0X02:"CRB",0X06:"CCP",0X11:"CCB"},
                           0X1807F456:"CTS",0X1808F456:"CML",0X100AF456:"CRO",
                           0X1812F456:"CCS",0X101AF456:"CST",0X181DF456:"CSD",0x081ff456:"CEM"}
            self.iddecbms={0x182756F4:"BHM",0X1CEC56F4:{0X02:"BRM",0X06:"BCP",0X11:"BCS"},
                           0X100956F4:"BRO",0X181056F4:"BCL",0X1CEB56F4:"BMD",
                           0X181356F4:"BSM",0X101956F4:"BST",0X181C56F4:"BSD",0x081e56f4:"BEM"}        
            self.idencchr={"CHM":0X1826F456,"CRM":0x1801F456,"CRB":0x1CECF456,"CCP":0x1CECF456,"CCB":0x1CECF456,
                           "CTS":0X1807F456,"CML":0X1808F456,"CRO":0X100AF456,
                           "CCS":0X1812F456,"CST":0X101AF456,"CSD":0X181DF456,"CEM":0x081ff456}
            self.idencbms={"BHM":0x182756F4,"BRM":0X1CEC56F4,"BCP":0X1CEC56F4,"BCS":0X1CEC56F4,
                           "BRO":0X100956F4,"BCL":0X181056F4,"BMD":0X1CEB56F4,
                           "BSM":0X181356F4,"BST":0X101956F4,"BSD":0X181C56F4,"BEM":0x081e56f4}
            self.bus = can.interface.Bus(channel='vcan0', bustype='socketcan_native')
            Thread.__init__(self)
      def setwrsoc(self,wrsoc):
            
            self.wrsoc=wrsoc
#            self.writetoUI("soc",50)
      def startins(self):
            self.startf=True
      def stopins(self):
        #    smps(0,0,0)
            self.startf=False
            self.sendCST()
            self.recmsg="CHM"
      def resetnparr(self):
            self.npmesvolt=np.array([])
            self.npmescur=np.array([])
            self.npvoltout=np.array([])
            self.npcurout=np.array([])
      def setnpmes(self,volt,cur):
            self.npmesvolt=np.append(self.npmesvolt,[volt])
            self.npmescur=np.append(self.npmescur,[cur])
            self.npvoltout=np.append(self.npvoltout,[self.voltout])
            self.npcurout=np.append(self.npcurout,[self.curout])

      
      """The function sendmesg write the arbitration_id and data to the CAN bus network and waits for a delay time arguments arbitration id message data of length 8 bytes and delay in seconds"""
      def sendmesg(self,ai,message,dly):
            msg= can.Message(arbitration_id=ai,data=message,extended_id=True,is_remote_frame=False,dlc=8)
            self.bus.send(msg)
            tm.sleep(dly)

      """The function onrecive message is called on reciving the message from CAN bus network it will also respond to the instructions  arguments are decoded arbitration id message recived of length 8 bytes"""
      def setcurrent(self,setcur):
            self.setcur=setcur
      def onrecive(self,messbyid,data):
            if messbyid=="BHM":
                  self.sendCRM(0x0)
            elif messbyid=="BSD":
                  self.sendCSD()
            elif messbyid=="BRO":
                  if  int(data[0],16)==0xaa:
                      self.sendCRO(0x00)
                      self.sendCRO(0xaa)
            elif messbyid=="BCL":
                      self.voltdem=(((int(data[1],16))<<8)|(int(data[0],16)))/10
                      self.curdem=((((int(data[3],16))<<8)|(int(data[2],16)))-400)/10
                      self.mode=int(data[5],16)
                      voltset=int(self.voltdem*100)+155
                #      smps(voltset,self.setcur,1)
                #      print(self.mode)
                      self.sendCCS()
            elif messbyid=="BRM" or messbyid=="BCP" or messbyid=="BCS":   # or "BCP" or "BCS":
                      self.sendCRBI()  
            elif messbyid=="BMD":
                  if  int(data[0],16)==self.terbrm:
                      if self.pgnbrm==0x02:
                         self.sendCRBT()
                         self.sendCRM(0xaa)
                      elif self.pgnbrm==0x06:
                         self.sendCRBT()
                         self.sendCML()
                      else:
                         self.sendCRBT()
                         if int(data[0],16)==2:
                            self.estrem=(((int(data[2],16))<<8)|(int(data[1],16)))
                  else:
                      if self.pgnbrm==0x11:
                        if int(data[0],16)==1:
                            self.mesvolt=(((int(data[2],16))<<8)|(int(data[1],16)))/10
                            self.mescur=((((int(data[4],16))<<8)|(int(data[3],16)))-400)/10
                            self.soc=int(data[7],16)
                            self.setnpmes(self.mesvolt,self.mescur)
            elif messbyid=="BEM":
                  self.sendCSD()
                  self.stopins()
      def sendCSD(self):
            self.sendmesg(self.idencchr["CSD"],[self.cummin&0Xff,(self.cummin>>8)&0xff,self.cumoeng&0Xff,(self.cumoeng>>8)&0xff,0x1,0,0,0],0.25)

      def sendCCS(self):
            voltout=self.voltout*10
            curout=(self.curout*10)+400
            self.sendmesg(self.idencchr["CCS"],[voltout&0xff,(voltout>>8)&0xff,(curout)&0xff,(curout>>8)&0xff,self.cummin&0Xff,(self.cummin>>8)&0xff,0x1,0x00],0.25)
            for name,data in self.getbmsSOCVOLTCUR():
               #           print(name)
                          self.writetoUI(name,data)
            for name,data in self.getbmsVOLTCURDEMMODE():
               #           print(name)
                          self.writetoUI(name,data)

      def sendCST(self):
            self.sendmesg(self.idencchr["CST"],[0x04,0x00,0x00,0x00,0Xff,0xff,0xff,0xff],0.25)                            
            
      def sendCRO(self,first_byte):
            self.sendmesg(self.idencchr["CRO"],[first_byte,0xff,0xff,0xff,0Xff,0xff,0xff,0xff],0.25)                            



      def sendCRBI(self):
            self.sendmesg(self.idencchr["CRB"],[0x11,self.numbrm,1,0xff,0Xff,0,self.pgnbrm,0],0.25)                            


      def sendCRBT(self):
            self.sendmesg(self.idencchr["CRB"],[0x13,self.lenbrm,0,self.terbrm,0Xff,0,self.pgnbrm,0],0.25)
            if self.pgnbrm==0x11:
                    for name,data in self.getbmsSOCVOLTCUR():
               #           print(name)
                          self.writetoUI(name,data)
                    for name,data in self.getbmsVOLTCURDEMMODE():
               #           print(name)
                          self.writetoUI(name,data)



      def sendCRM(self,first_byte):
            self.sendmesg(self.idencchr["CRM"],[first_byte,0x1,0,0,0,0x44,0x45,0x4c],0.25)




      def sendCML(self):
            maxvolt=self.maxvolt*10
            minvolt=self.minvolt*10
            maxcur=(self.maxcur*10)+400
            mincur=(self.mincur*10)+400
            self.sendmesg(self.idencchr["CML"],[maxvolt&0xff,(maxvolt>>8)&0xff,minvolt&0xff,(minvolt>>8)&0xff,maxcur&0xff,(maxcur>>8)&0xff,mincur&0xff,(mincur>>8)&0xff],0.25)
            
      def sendCHM(self):
            self.sendmesg(self.idencchr["CHM"],[0x1,0x1,0x80,0xff,0xff,0xff,0xff,0xff],0.25)

      def getchrMMVOLTMMCUR(self):
            return zip(("mxv","mnv","mxc","mnc"),(self.maxvolt,self.minvolt,self.maxcur,self.mincur))
      def getbmsSOCVOLTCUR(self):
            return zip(("soc","mcv","mcc"),(self.soc,self.mesvolt,self.mescur))
      def getbmsVOLTCURDEMMODE(self):
            return zip(("vod","cod","mode"),(self.voltdem,self.curdem,self.mode))
      def getSTATUS(self):
            self.status={"charger_handshake":("CHM","BHM","CRM","BRM","CRB"),
                         "charger_perameter_config":("BCP","CCP","CML","BRO","CRO"),
                         "charger_charging":("BCL","BMD","CCS","CCB","BSM","BCS"),
                         "BMS_suspend_charging":("BST"),
                         "charger_suspend_charging":("CST")}
            for prest in self.status.keys():
                  if self.recmsg in self.status[prest]:
                        return prest
            

      def writetoUI(self,name,data):
           # WsHandler.send_message(self.wrsoc,name,data)
            cpconn={"name":name,"data":data}
            self.wrsoc.write_message(json.dumps(cpconn))
      def run(self):
            pass
      def run1(self):
            if self.startf:
             cumtm=((dt.datetime.utcnow()-self.inittm).total_seconds()%3600)//60
             if cumtm!=self.cumtmp:
                  self.cumtmp=cumtm
                  
                  if len(self.npmesvolt)!=0:
                      print(np.mean(self.npmesvolt))
                      if self.cummin%1==0 and self.cummin>=1:
                        pw=np.mean(self.npmesvolt*self.npmescur)
                        pw1=np.mean(self.npvoltout*self.npcurout)
                        self.cumeng+=(quad(powintgration,self.cummin-1,self.cummin,args=(pw1))[0])/60000
                        self.cumoeng+=(quad(powintgration,self.cummin-1,self.cummin,args=(pw))[0])/60000 
                        print("cumeng=",self.cumoeng,pw,self.cummin-1,self.cummin)
                        self.resetnparr()
                  self.cummin+=1
             if self.recmsg=="CHM":
                self.sendCHM() 
             inpmsg=self.bus.recv(0.25)
             if inpmsg!=None:
               try:    
                decmsg=str(inpmsg).split("   ")
                data=[hex(int(ii,16)) for ii in decmsg[len(decmsg)-2].split(" ")[1:]]
                id=int(decmsg[1].split(":")[1].lstrip(),16)
                if id!=0x1CEC56F4:
                      self.recmsg=self.iddecbms[id]
                      self.onrecive(self.iddecbms[id],data)
                else:
                      self.recmsg=self.iddecbms[id][int(data[6],16)]
                      if self.recmsg=="BRM" or self.recmsg=="BCP" or self.recmsg=="BCS":   # or "BCP" or "BCS":
                       self.lenbrm=(int(data[2],16)<<16)|int(data[1],16)
                       self.numbrm=int(data[3],16)
                       self.terbrm=int(data[4],16)
                       self.pgnbrm=int(data[6],16)
                       self.onrecive(self.recmsg,data)
               except:
                     print(decmsg)

             else:
                   pass
URL = "ws://localhost"
def powintgration(t,pw):
            pwi=pw
            return pwi
th=extendcan()
class Application(tornado.web.Application): 
   def __init__(self):
         
       handlers = [
           (r"/charger", IndexHandler),
           (r"/ws", WsHandler)
           ]
       settings = dict(
           template_path=os.path.join(os.path.dirname(__file__), "template"), 
           static_path=os.path.join(os.path.dirname(__file__), "static"), 
       )
       tornado.web.Application.__init__(self, handlers, **settings)

class IndexHandler(tornado.web.RequestHandler): 
   def get(self):
       self.render("index_test.html")

class WsHandler(tornado.websocket.WebSocketHandler):   
   def open(self):
#         tornado_connections["wsconnect"]=self
         th.setwrsoc(self)
         print("opened")
         

   def on_message(self, message):
         ins=json.loads(message)
         if (ins["name"])=="StartCharger" :
               th.startins()
         elif (ins["name"])=="StopCharger" :
               self.cummin=0
               th.stopins()
         elif (ins["name"])=="currs":
               setcur=int(ins["data"])//3
               th.setcurrent(setcur)
               
        
   def on_close(self):
         print('TORNADO: client disconnected.')
   


async def create_thread():
      th.run1()
      


async def start_tornado_server():
   
   app = Application()
   server = tornado.httpserver.HTTPServer(app) 
   app.listen(8000)
   
#   tornado.ioloop.IOLoop.instance().start()
   
async def main():
   await start_tornado_server()
   th.start()
#   await asyncio.gather(th.start(),loop=th.run1())   
#   print("hello")
   while True:
         await asyncio.create_task(create_thread())
     #    await asyncio.gather(th.start(),loop=th.run1())
         pass


      
      
if __name__ == '__main__':
    try:
        # asyncio.run() is used when running this example with Python 3.7 and
        # higher.
        asyncio.run(main())
    except AttributeError:
        # For Python 3.6 a bit more code is required to run the main() task on
        # an event loop.
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
        loop.close()
