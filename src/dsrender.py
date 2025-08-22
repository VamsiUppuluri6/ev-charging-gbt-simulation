import asyncio
import logging
import time
import json
import socket
from datetime import datetime
try:
    import websockets
except ModuleNotFoundError:
    print("This example relies on the 'websockets' package.")
    print("Please install it by running: ")
    print()
    print(" $ pip install websockets")
    import sys
    sys.exit(1)
from ocpp.routing import on    
from ocpp.v16 import call_result
from ocpp.v16.enums import * 
from ocpp.v16 import call
from ocpp.v16 import ChargePoint as cp
from ocpp.v16.enums import RegistrationStatus,AvailabilityType
import os.path
import tornado.web
import tornado.websocket
import tornado.httpserver
import asyncio
# from ws_client import WebsocketClient

cpmodel=""
cpvendor=""
cpconn={"name":"connection status","1":ChargePointStatus.available,"2":ChargePointStatus.available,"3":ChargePointStatus.available}
cpconnst={"1":"","2":"","3":""}
cptagid={1:"",2:"",3:""}
cpmeter={1:0,2:0,3:0}
cptransid={1:0,2:0,3:0}
cpstatus={1:0,2:0,3:0}
cpoperst={1:"",2:"",3:""}
cpstart={"status":0,"connector":""}
cpsenstno={"status":1}

URL = "ws://localhost"
tornado_connections ={"wsconnect":""}
ws_echo = None

class Application(tornado.web.Application): 
   def __init__(self):
       handlers = [
           (r"/", IndexHandler),
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
   async def open(self):
       if self not in tornado_connections:
           tornado_connections["wsconnect"]=self
#           await ws_echo.update_connections(connections=tornado_connections)

   def on_message(self, message): 
#       print(message)
       tornado_connections["wsconnect"].write_message(json.dumps(cpconn))

   def on_close(self):
       if self in tornado_connections:
           tornado_connections.remove(self)
           print('TORNADO: client disconnected.')


def isConnected():
    try:
        # connect to the host -- tells us if the host is actually
        # reachable
        sock = socket.create_connection(("www.google.com", 80))
        if sock is not None:
            print('Clossing socket')
            sock.close
        return True
    except OSError:
        pass
    return False





async def start_tornado_server():
   app = Application()
   server = tornado.httpserver.HTTPServer(app) 
   server.listen(8000)
   print("hello")
#async def start_ws_client():
#   ws_echo = WebsocketClient(url=URL, connections=tornado_connections)
#   await ws_echo.connect()

logging.basicConfig(level=logging.INFO)

class ChargePoint(cp):



    def connectstart(self,connid):
        time.sleep(5)
        cpconn[connid]=ChargePointStatus.charging
        
   
    async def repeat(self,interval, func):
      while True:
         await asyncio.gather(
            func(),
            asyncio.sleep(interval),
         )





    @on(Action.ClearCache)
    async def on_clearcache(self):
        return call_result.ClearCachePayload(
               ClearCacheStatus.accepted)
    
    @on(Action.ChangeConfiguration)
    async def on_changeconfig(self,key:str,value:any,**kwargs):
        return call_result.ChangeConfigurationPayload(
                ConfigurationStatus.not_supported)
   
    @on(Action.ChangeAvailability)
    async def on_changeavailability(self,connector_id:int,type:AvailabilityType,**kwargs):
        cpoperst[connector_id]=type
        cpsenstno["status"]=1
        if(type==AvailabilityType.inoperative):
            if(cpconn[str(connector_id)]==ChargePointStatus.charging):
                   return call_result.ChangeAvailabilityPayload(
                   status=AvailabilityStatus.rejected
                   )
            else:
                   cpconn[str(connector_id)]=ChargePointStatus.unavailable 
                   return call_result.ChangeAvailabilityPayload(
                   status=AvailabilityStatus.accepted
                   )
        else:
            cpconn[str(connector_id)]=ChargePointStatus.available
            return call_result.ChangeAvailabilityPayload(
                   status=AvailabilityStatus.accepted
                   )
 





    @on(Action.RemoteStartTransaction)
    async def on_remotestarttransaction(self,connector_id:int,id_tag:str,**kwargs):
       if(cpconn[str(connector_id)]==ChargePointStatus.available):
        cpconn[str(connector_id)]=ChargePointStatus.preparing
        cptagid[str(connector_id)]=id_tag
        cpsenstno["status"]=1
        cpstart["status"]=1
        cpstart["connector"]=str(connector_id)
 #       await self.send_statusnotification()
        return call_result.RemoteStartTransactionPayload(
                status=RegistrationStatus.accepted
                )
       else:
        return call_result.RemoteStartTransactionPayload(
                status=RegistrationStatus.rejected
                )

    @on(Action.RemoteStopTransaction)
    async def on_remotestoptransaction(self,transaction_id:int,**kwargs):
        for key,value in cptransid.items():
            if value==transaction_id:
                cpstatus[key]=1

        cpsenstno["status"]=1
 #       await self.send_statusnotification()
        return call_result.RemoteStopTransactionPayload(
                status=RegistrationStatus.accepted
                )


#class ChargePoint(cp):

    async def start_state(self):
        if cpstart["status"]==1:
           cpstart["status"]=0 
           self.connectstart(cpstart["connector"])
           cpsenstno["status"]=1
           cpstart["connector"]=""
    async def send_heartbeat(self):
 #       while True:
 #              asyncio.sleep(intervel/1000.0)
         try:
               request= call.HeartbeatPayload()
               response = await self.call(request)
         except:
             loop=asyncio.get_running_loop()
             loop.close()




#           self.send_statusnotification()




    async def send_statusnotification(self):
        try: 
         if tornado_connections["wsconnect"]!="":
            await tornado_connections["wsconnect"].write_message(json.dumps(cpconn))
         if cpsenstno["status"]==1:
            cpsenstno["status"]=0
            for key,value in cpstatus.items():
               if value==1:
                   request=call.StopTransactionPayload(transaction_id=cptransid[key],id_tag=cptagid[key],meter_stop=cpmeter[key],timestamp=datetime.utcnow().isoformat())
                   response = await self.call(request)
                   cpstatus[key]=0
                   cpconn[str(key)]=ChargePointStatus.available
            if cpconn["1"]!=cpconnst["1"]:
                cpconnst["1"]=cpconn["1"]
                request= call.StatusNotificationPayload(connector_id=1,error_code="NoError",status=cpconnst["1"])
                response = await self.call(request)
                if cpconnst["1"]==ChargePointStatus.charging:
                   request=call.StartTransactionPayload(connector_id=1,id_tag=cptagid[1],meter_start=cpmeter[1],timestamp=datetime.utcnow().isoformat())
                   response = await self.call(request)
                   cptransid[1]=response.transaction_id




            if cpconn["2"]!=cpconnst["2"]:
                cpconnst["2"]=cpconn["2"]
                request= call.StatusNotificationPayload(connector_id=2,error_code="NoError",status=cpconnst["2"])
                response = await self.call(request)
                if cpconnst["2"]==ChargePointStatus.charging:
                   request=call.StartTransactionPayload(connector_id=2,id_tag=cptagid[2],meter_start=cpmeter[2],timestamp=datetime.utcnow().isoformat())
                   response = await self.call(request)
                   cptransid[2]=response.transaction_id


            if cpconn["3"]!=cpconnst["3"]:
                cpconnst["3"]=cpconn["3"]
                request= call.StatusNotificationPayload(connector_id=3,error_code="NoError",status=cpconnst["3"])
                response = await self.call(request)

                if cpconnst["3"]==ChargePointStatus.charging:
                   request=call.StartTransactionPayload(connector_id=3,id_tag=cptagid[3],meter_start=cpmeter[3],timestamp=datetime.utcnow().isoformat())
                   response = await self.call(request)
                   cptransid[3]=response.transaction_id
        except:
             loop=asyncio.get_running_loop()
             loop.close()






#           if ii==2:
#             cpconn[1]="Charging"
          
#           await self.send_heartbeat(intervel) 



    async def send_boot_notification(self):
        request = call.BootNotificationPayload(
            charge_point_model=cpmodel,
            charge_point_vendor=cpvendor
        )

        response = await self.call(request)

        if response.status == RegistrationStatus.accepted:
           t1 = asyncio.ensure_future(self.repeat(response.interval/1000.0,self.send_heartbeat))
           t2 = asyncio.ensure_future(self.repeat(1,self.send_statusnotification))
           t3 = asyncio.ensure_future(self.repeat(4,self.start_state))
           try:
            await t1
            await t2
            await t3
           except:
               t1.close()
               t2.close()
               t3.close()


#            loop=asyncio.get_running_loop()
#            loop.create_task(self.send_heartbeat(response.interval))
#            print(cpconn[1])
#            loop.create_task(self.send_statusnotification()) 
        
async def hello():
    print("xyz")
async def main():
 await start_tornado_server()
 
 while True:
     await asyncio.create_task(hello())
     pass
#    asyncio.create_task(start_ws_client())
'''  try:
    async with websockets.connect(
        'ws://server.dsreddyconsultancy.co.in:8085/steve/websocket/CentralSystemService/DC001',
        subprotocols=['ocpp1.6']
    ) as ws:

        cp = ChargePoint('DC001', ws)
#        cp1 = ChargePoint1('CP_1', ws)
#        await cp1.start()

        await asyncio.gather(cp.start(), cp.send_boot_notification())
  except KeyboardInterrupt:

      import sys
ys.exit(1)
  except:     
      print("finally")
#      loop=asyncio.get_running_loop()
#      await loop.close()
      while isConnected()==False:
          await asyncio.sleep(4)
          pass
'''
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
