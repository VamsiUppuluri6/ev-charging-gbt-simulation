var can = require('socketcan');
var fs = require('fs');
var multm;
var reqcnt=0;
const WebSocket = require('ws');
var express = require('express');
var app = express();
var startstat=false;
app.use(express.static("./"));

app.get('/', function(req, res) {
//    console.log(reqcnt);	
//    if(reqcnt==0){	
    res.render('bmsemu.html');
//	    reqcnt++;
//    }
//    else{
//    res.render('erroremu.html');
//    }
});

app.listen(8082, '')
//var sleep=require('sleep')
// Parse database
//channel.addListener("onMessage", function(msg) { console.log(msg); } );
var stat_bhm=true;
var tmpcv,protid,domainid,packlen,nummess,channel;
var reqpgn,nummessl,setres,voltdemand=75,currentdemand=20,constcurvol=2,SOC=50,endstati,cntloop;

//StartCharging();
// server.js
function initcharging(){
    endstat=false;
    stat_bhm=true;
	cntloop=true;
     network = can.parseNetworkDescription("can_bmsandcharger.kcd");
     channel = can.createRawChannel("vcan0",false);
     db_charger = new can.DatabaseService(channel, network.buses["Charger"]);
     db_bms = new can.DatabaseService(channel, network.buses["BMS"]);
    
}

var wsstat=false;
const wss = new WebSocket.Server({ port: 9988 })
var ws1=0;
wsstat=true;
/*wss.on('disconnection',ws=>{
    //connstat=false;
    StopCharging();	
});
*/
wss.on('connection', ws => {
if(ws1 !=0){
if(ws1.readyState !==  WebSocket.OPEN){
	ws1=ws;
   reqcnt=1;
    }
}else{
	ws1=ws;
	 reqcnt=1;
    }
	first();
  ws.on('message', message => {
     var  messfc=JSON.parse(message);
     console.log(messfc.name);
      if(messfc.name=="StartCharger"){
        if(startstat==false){
		endstate=false;
          StartCharging();
        //  if(startstat==false)
          startstat=true;
        }
      }
      if(messfc.name=="StopCharger"){
        if(startstat==true){
        StopCharging();
        startstat=false;
        }
    }
        if(messfc.name=="soc"){
            SOC=messfc.data;
    }
  });
//  ws.send('Hello! Message From Server!!')
});
function StopCharging(){
	console.log("stop chatrging");
//   clearInterval(multm);
    stat_bhm=false;
    endstat=false;
    stopchannel();
    }
function stopchannel(){
    if(startstat==true){
channel.stop();
	    startstat=false;
}
}
//var wsfun=setInterval(first,2000);
function first(){
//	for(var ii in wss.clients){
//	reqcnt=ii;
//	}
//    reqcnt=wss.clients.length;
        wss.clients.forEach(function each(client) {
        if(client!=ws1){
	console.log(reqcnt);
        client.send(JSON.stringify({"name":"count","data":reqcnt}));
	}else{
		ws1.send(JSON.stringify({"name":"count","data":0}));
	}
	});
	}
function StartCharging(){
initcharging();
//console.log("startted");    
channel.start();
db_charger.messages["CHM"].signals["ProtocolId"].onUpdate(function(s){
    
if(ws1.readyState ===  WebSocket.CLOSE){
//    connstat=false;
    reqcnt=0;
    StopCharging();	

}

    protid=s.value;
});
db_charger.messages["CHM"].signals["Publicid"].onUpdate(function(s){
    domainid=s.value;
});
db_charger.messages["CRM"].signals["BmsRec"].onUpdate(function(s){
    stat_bhm=false;
    if(s.value==0){
        packlen=0x45;
        nummess=0x0a;
        db_bms.messages["BRM"].signals["BmsReq"].update(0x10);
        db_bms.messages["BRM"].signals["BmsReqlen"].update(packlen);
        db_bms.messages["BRM"].signals["BmsReqpac"].update(nummess);
        db_bms.messages["BRM"].signals["BmsReqpac1"].update(nummess);
        db_bms.messages["BRM"].signals["BmsReqpgn"].update(512);
        db_bms.send("BRM");
                
    }
if(ws1.readyState !==  WebSocket.OPEN){
//    connstat=false;
    reqcnt--;
    reqcnt=0;
    StopCharging();	

}

});
db_charger.messages["CRS"].signals["Clearsend"].onUpdate(function(s){
var temp=s.value;
setres=temp&0xff;
temp=temp>>>8;

if(ws1.readyState !==  WebSocket.OPEN){
//    connstat=false;
    reqcnt--;
    reqcnt=0;
    StopCharging();	

}

});
db_charger.messages["CML"].signals["Maxvolt"].onUpdate(function(s){
    var temp=s.value;   
    for(ii=0;ii<4;ii++){
    db_bms.messages["BRO"].signals["Broready"].update(0x00);
    db_bms.messages["BRO"].signals["Broter"].update(0x00);
    db_bms.send("BRO");
    }
    db_bms.messages["BRO"].signals["Broready"].update(0xaa);
    db_bms.messages["BRO"].signals["Broter"].update(0x00);
    db_bms.send("BRO");
    

if(ws1.readyState !==  WebSocket.OPEN){
//    connstat=false;
    reqcnt--;
    reqcnt=0;
    StopCharging();	

}

});



db_charger.messages["CRO"].signals["Chargerready"].onUpdate(function(s){
    var temp=s.value;   
    if(temp=0xaa){
   db_bms.messages["BRO"].signals["Broready"].update(0xaa);
    db_bms.messages["BRO"].signals["Broter"].update(0x00);
    db_bms.send("BRO");
    ContinuesMess();
    }

});
function Bcdm(){
var vd=voltdemand*10;
var cd=(currentdemand*10)+400;
    db_bms.messages["BCDM"].signals["Bcdvoltdem"].update(vd);
    db_bms.messages["BCDM"].signals["Bcdcurrdem"].update(cd);
    db_bms.messages["BCDM"].signals["Bcdconst"].update(constcurvol);
    db_bms.messages["BCDM"].signals["Bcdres"].update(0);

    db_bms.send("BCDM");
if(ws1.readyState !==  WebSocket.OPEN){
//    connstat=false;
endstat=false;
    reqcnt--;
    reqcnt=0;
    StopCharging();	

}

}

function MULTMessage(){
    if(endstat){
    Bcdm();
    //console.log("open");
    packlen=9;
    nummess=2;
    db_bms.messages["BRM"].signals["BmsReq"].update(0x10);
    db_bms.messages["BRM"].signals["BmsReqlen"].update(packlen);
    db_bms.messages["BRM"].signals["BmsReqpac"].update(nummess);
    db_bms.messages["BRM"].signals["BmsReqpac1"].update(nummess);
    db_bms.messages["BRM"].signals["BmsReqpgn"].update(4352);
    db_bms.send("BRM");
    }else{
    console.log("cleared");	    
//    clearInterval(multm);
    //StopCharging();	
//	    return;
    }


if(ws1.readyState !==  WebSocket.OPEN){
//    connstat=false;
    clearInterval(multm);
    reqcnt--;
    reqcnt=0;
    StopCharging();	

}

   } 
    

function ContinuesMess(){
endstat=true;
MULTMessage();
/*if(cntloop==true){	
multm=setInterval(MULTMessage,500);
cntloop=false;	
}*/
}
db_charger.messages["CST"].signals["Cscause"].onUpdate(function(s){



    

});
db_charger.messages["CST"].signals["Csfault"].onUpdate(function(s){

});
db_charger.messages["CST"].signals["Cserror"].onUpdate(function(s){

});



db_charger.messages["CRS"].signals["Cleardata"].onUpdate(function(s){
    var temp=s.value;   
    
    if(setres==0x11){
        nummessl=temp&0xff;
        }
        if(setres==0x13){
            nummessl=temp;
        }
                
});


db_charger.messages["CRS"].signals["Clearpgn"].onUpdate(function(s){
    var temp=s.value;
    if(setres==0x13){
        if(512==temp){
            packlen=0x0d;
            nummess=0x02;
            db_bms.messages["BRM"].signals["BmsReq"].update(0x10);
            db_bms.messages["BRM"].signals["BmsReqlen"].update(packlen);
            db_bms.messages["BRM"].signals["BmsReqpac"].update(nummess);
            db_bms.messages["BRM"].signals["BmsReqpac1"].update(nummess);
            db_bms.messages["BRM"].signals["BmsReqpgn"].update(1536);
            db_bms.send("BRM");
     
 
 
 
        }
    }





    if(setres==0x11){
        if(nummessl==nummess){
            if(512==temp){
                
             for(ii=1;ii<=nummess;ii++){
                db_bms.messages["BRMBCPBCS"].signals["BrPackCount"].update(ii);
                 if(ii==1){
                    db_bms.messages["BRMBCPBCS"].signals["BrPac1"].update((protid>>8)&0xff);
                    db_bms.messages["BRMBCPBCS"].signals["BrPac2"].update((protid)&0xff);
                    db_bms.messages["BRMBCPBCS"].signals["BrPac3"].update((domainid));
                    db_bms.messages["BRMBCPBCS"].signals["BrPac4"].update((0x08));
                    db_bms.messages["BRMBCPBCS"].signals["BrPac5"].update((0xb4));
                    db_bms.messages["BRMBCPBCS"].signals["BrPac6"].update((0x0a));
                    db_bms.messages["BRMBCPBCS"].signals["BrPac7"].update((0x53));
                 }
                 if(ii==2){
                    db_bms.messages["BRMBCPBCS"].signals["BrPac1"].update(3);
                    db_bms.messages["BRMBCPBCS"].signals["BrPac2"].update(0xff);
                    db_bms.messages["BRMBCPBCS"].signals["BrPac3"].update(0xff);
                    db_bms.messages["BRMBCPBCS"].signals["BrPac4"].update((0xff));
                    db_bms.messages["BRMBCPBCS"].signals["BrPac5"].update((0xff));
                    db_bms.messages["BRMBCPBCS"].signals["BrPac6"].update((0xff));
                    db_bms.messages["BRMBCPBCS"].signals["BrPac7"].update((0xff));
                 }
                 if(ii==3){
                    db_bms.messages["BRMBCPBCS"].signals["BrPac1"].update(0xff);
                    db_bms.messages["BRMBCPBCS"].signals["BrPac2"].update(0xff);
                    db_bms.messages["BRMBCPBCS"].signals["BrPac3"].update(0xff);
                    db_bms.messages["BRMBCPBCS"].signals["BrPac4"].update((0xff));
                    db_bms.messages["BRMBCPBCS"].signals["BrPac5"].update((0xff));
                    db_bms.messages["BRMBCPBCS"].signals["BrPac6"].update((0xff));
                    db_bms.messages["BRMBCPBCS"].signals["BrPac7"].update((0xff));
                 }
                 if(ii==4){
                    db_bms.messages["BRMBCPBCS"].signals["BrPac1"].update(0xff);
                    db_bms.messages["BRMBCPBCS"].signals["BrPac2"].update(0xff);
                    db_bms.messages["BRMBCPBCS"].signals["BrPac3"].update(0xff);
                    db_bms.messages["BRMBCPBCS"].signals["BrPac4"].update((0x4d));
                    db_bms.messages["BRMBCPBCS"].signals["BrPac5"].update((0x41));
                    db_bms.messages["BRMBCPBCS"].signals["BrPac6"].update((0x31));
                    db_bms.messages["BRMBCPBCS"].signals["BrPac7"].update((0x4c));
                 }
                 if(ii==5){
                    db_bms.messages["BRMBCPBCS"].signals["BrPac1"].update(0x53);
                    db_bms.messages["BRMBCPBCS"].signals["BrPac2"].update(0x45);
                    db_bms.messages["BRMBCPBCS"].signals["BrPac3"].update(0x57);
                    db_bms.messages["BRMBCPBCS"].signals["BrPac4"].update((0x37));
                    db_bms.messages["BRMBCPBCS"].signals["BrPac5"].update((0x39));
                    db_bms.messages["BRMBCPBCS"].signals["BrPac6"].update((0x4a));
                    db_bms.messages["BRMBCPBCS"].signals["BrPac7"].update((0x32));
                 }
                 if(ii==6){
                    db_bms.messages["BRMBCPBCS"].signals["BrPac1"].update(0x42);
                    db_bms.messages["BRMBCPBCS"].signals["BrPac2"].update(0x38);
                    db_bms.messages["BRMBCPBCS"].signals["BrPac3"].update(0x30);
                    db_bms.messages["BRMBCPBCS"].signals["BrPac4"].update((0x31));
                    db_bms.messages["BRMBCPBCS"].signals["BrPac5"].update((0x33));
                    db_bms.messages["BRMBCPBCS"].signals["BrPac6"].update((0x32));
                    db_bms.messages["BRMBCPBCS"].signals["BrPac7"].update((0xff));
                 }
                 if(ii>6){
                    db_bms.messages["BRMBCPBCS"].signals["BrPac1"].update(0xff);
                    db_bms.messages["BRMBCPBCS"].signals["BrPac2"].update(0xff);
                    db_bms.messages["BRMBCPBCS"].signals["BrPac3"].update(0xff);
                    db_bms.messages["BRMBCPBCS"].signals["BrPac4"].update((0xff));
                    db_bms.messages["BRMBCPBCS"].signals["BrPac5"].update((0xff));
                    db_bms.messages["BRMBCPBCS"].signals["BrPac6"].update((0xff));
                    db_bms.messages["BRMBCPBCS"].signals["BrPac7"].update((0xff));
                 }
                 db_bms.send("BRMBCPBCS")

             }                
            }
        }
  
        

        //console.log("4352"+temp)
        if(4352==temp){
             //console.log(nummess);   
            for(ii=1;ii<=nummess;ii++){
               db_bms.messages["BRMBCPBCS"].signals["BrPackCount"].update(ii);
                if(ii==1){
                   db_bms.messages["BRMBCPBCS"].signals["BrPac1"].update(0xf5);  //f5 02 85 01 49 01 47
                   db_bms.messages["BRMBCPBCS"].signals["BrPac2"].update(2);
                   db_bms.messages["BRMBCPBCS"].signals["BrPac3"].update(0x85);
                   db_bms.messages["BRMBCPBCS"].signals["BrPac4"].update(0x02);
                   db_bms.messages["BRMBCPBCS"].signals["BrPac5"].update((0x49));
                   db_bms.messages["BRMBCPBCS"].signals["BrPac6"].update((0x01));
                   db_bms.messages["BRMBCPBCS"].signals["BrPac7"].update((SOC));
                }
                if(ii==2){
                   db_bms.messages["BRMBCPBCS"].signals["BrPac1"].update(0xaa);  //
                   db_bms.messages["BRMBCPBCS"].signals["BrPac2"].update(0x00);
                   db_bms.messages["BRMBCPBCS"].signals["BrPac3"].update(0xff);
                   db_bms.messages["BRMBCPBCS"].signals["BrPac4"].update((0xff));
                   db_bms.messages["BRMBCPBCS"].signals["BrPac5"].update((0xff));
                   db_bms.messages["BRMBCPBCS"].signals["BrPac6"].update((0xff));
                   db_bms.messages["BRMBCPBCS"].signals["BrPac7"].update((0xff));
                }
            
                db_bms.send("BRMBCPBCS")

     
            }

        }

































            if(1536==temp){
                
                for(ii=1;ii<=nummess;ii++){
                   db_bms.messages["BRMBCPBCS"].signals["BrPackCount"].update(ii);
                    if(ii==1){
                       db_bms.messages["BRMBCPBCS"].signals["BrPac1"].update(0x72);  //72 01 f4 0b c7 00 70
                       db_bms.messages["BRMBCPBCS"].signals["BrPac2"].update(1);
                       db_bms.messages["BRMBCPBCS"].signals["BrPac3"].update(0xf4);
                       db_bms.messages["BRMBCPBCS"].signals["BrPac4"].update(0x0b);
                       db_bms.messages["BRMBCPBCS"].signals["BrPac5"].update((0xc7));
                       db_bms.messages["BRMBCPBCS"].signals["BrPac6"].update((0x00));
                       db_bms.messages["BRMBCPBCS"].signals["BrPac7"].update((0x70));
                    }
                    if(ii==2){
                       db_bms.messages["BRMBCPBCS"].signals["BrPac1"].update(3);  //03 65 cc 02 f5 02 ff
                       db_bms.messages["BRMBCPBCS"].signals["BrPac2"].update(0x65);
                       db_bms.messages["BRMBCPBCS"].signals["BrPac3"].update(0xcc);
                       db_bms.messages["BRMBCPBCS"].signals["BrPac4"].update((0x02));
                       db_bms.messages["BRMBCPBCS"].signals["BrPac5"].update((0xf5));
                       db_bms.messages["BRMBCPBCS"].signals["BrPac6"].update((0x02));
                       db_bms.messages["BRMBCPBCS"].signals["BrPac7"].update((0xff));
                    }
                
                    db_bms.send("BRMBCPBCS")

         
                }
    
            }
        }
            
 
 
 
    });





function BHMMessage(){

    
if(stat_bhm){
    
tnpvc=88;
db_bms.messages["BHM"].signals["ChargingVoltage"].update(tnpvc*10);
db_bms.messages["BHM"].signals["Truncate"].update(0x000000);
db_bms.send("BHM");
}else{
//   console.log("clear");	
   clearInterval(bhmmess);
}
}
var bhmmess=setInterval(BHMMessage,500);

}
