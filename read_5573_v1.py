#!/usr/bin/python
# -*- coding: utf-8 -*-
import time
from elasticsearch import Elasticsearch
import minimalmodbus

def read_reg(id=0, ndec=0):
  try:
    val = instrument.read_register(id, ndec, signed=True) # Registernumber, number of decimals
  except Exception as e:
    val = -1
    print("Error reading modbus register " + str(id) + " with message: "  + str(e))
  return val

def read_bit(id=0):
  try:
    val = instrument.read_bit(id, 1) # Registernumber, number of decimals
  except Exception as e:
    val = -1
    print("Error reading modbus coil " + str(id) + " with message: "  + str(e))
  return val



print("Starte Skript.")

# 1-Wire Slave-Liste lesen
time.sleep(15)
file = open('/sys/devices/w1_bus_master1/w1_master_slaves')
w1_slaves = file.readlines()
file.close()
temp_list=[0,0,0,0,0,0,0]
print("Devices: " + str(w1_slaves))

# Modbus Setup
instrument = minimalmodbus.Instrument('/dev/ttyUSB0', 10) # port name, slave address (in decimal)
instrument.serial.timeout = 1.0
instrument.serial.baudrate = 19200

sig_list=[]
sig_list.append({"name": "Temp_Aussenfuehler", "id": 9, "type": 0, "Dezimalstellen": 1})
sig_list.append({"name": "Pos_Regelventil", "id": 106, "type": 0, "Dezimalstellen": 0})
sig_list.append({"name": "Stat_HK_Pumpe", "id": 56, "type": 1, "Dezimalstellen": 0})
sig_list.append({"name": "Temp_HK_TW_Vorlauf", "id": 12 , "type": 0, "Dezimalstellen": 1})
sig_list.append({"name": "Temp_HK_TW_Ruecklauf", "id": 16 , "type": 0, "Dezimalstellen": 1})
sig_list.append({"name": "Stat_TW_Ladepumpe", "id": 59 , "type": 1, "Dezimalstellen": 0})
sig_list.append({"name": "Stat_TW_Zirkulation", "id": 60 , "type": 1, "Dezimalstellen": 0})
sig_list.append({"name": "Temp_TW_Ist", "id": 22 , "type": 0, "Dezimalstellen": 1})
sig_list.append({"name": "Temp_TW_Soll", "id": 1799 , "type": 0, "Dezimalstellen": 1})
sig_list.append({"name": "Temp_TW_Desinfekt", "id": 1829 , "type": 0, "Dezimalstellen": 1})
sig_list.append({"name": "Stat_TW_Desinfekt", "id": 1837 , "type": 1, "Dezimalstellen": 0})
sig_list.append({"name": "Stat_TW_Mode", "id": 111 , "type": 0, "Dezimalstellen": 0})
sig_list.append({"name": "Stat_HK_Mode", "id": 105 , "type": 0, "Dezimalstellen": 0})
sig_list.append({"name": "Temp_HK_TW_Vorlauf_Soll", "id": 999, "type": 0, "Dezimalstellen": 1})
sig_list.append({"name": "Temp_HK_TW_Ruecklauf_Soll", "id": 1032, "type": 0, "Dezimalstellen": 1})
# sig_list.append({"name": "Temp_TW_Min", "id": 1860 , "type": 0, "Dezimalstellen": 1})



# ES Setup
es = Elasticsearch(hosts=["https://user:pass@your_elasticsearch_api:9200"],
                           timeout=60)

# Fuer jeden 1-Wire Slave aktuelle Temperatur ausgeben
while 1:
  i=0
  for line in w1_slaves:
    # 1-wire Slave extrahieren
    w1_slave = line.split("\n")[0]
    # 1-wire Slave Datei lesen
    file = open('/sys/bus/w1/devices/' + str(w1_slave) + '/w1_slave')
    filecontent = file.read()
    file.close()
    
    # Temperaturwerte auslesen und konvertieren
    stringvalue = filecontent.split("\n")[1].split(" ")[9]
    temperature = float(stringvalue[2:]) / 1000
    
    # Temperatur ausgeben
    # print(i)
    temp_list[i]=temperature
    i=i+1
    #print(str(w1_slave) + ': %6.2f °C' % temperature)
    
  #  print(str(int(time.time())) + " -- " + str(temp_list))
  
  # ModBus Teil
  res = "Id - Name - Value\n"
  i = 0
  val_list = 15 * [0.0]
  while i < len(sig_list):
    sig_id   = sig_list[i]["id"]
    sig_name = sig_list[i]["name"]
    sig_ndec = sig_list[i]["Dezimalstellen"]
    sig_type = sig_list[i]["type"]

    if sig_type == 0:
      val = read_reg(sig_id, sig_ndec)
    elif sig_type == 1:
      val = read_bit(sig_id)
      if sig_id == 59:
        val = val + 2
      elif sig_id == 60:
        val = val + 4
      else:
        pass
    else:
      val = -1
    res = res + str(i) + " - " + str(sig_name) + " - "  + str(val) + "\n"
    val_list[i] = val
    print(str(i) + " - " + str(sig_name) + " - " + str(val))
    i = i + 1

  payload={
    "T1": temp_list[0],
    "T2": temp_list[1],
    "T3": temp_list[2],
    "T4": temp_list[3],
    "T5": temp_list[4],
    sig_list[0]["name"]: val_list[0],
    sig_list[1]["name"]: val_list[1],
    sig_list[2]["name"]: val_list[2],
    sig_list[3]["name"]: val_list[3],
    sig_list[4]["name"]: val_list[4],
    sig_list[5]["name"]: val_list[5],
    sig_list[6]["name"]: val_list[6],
    sig_list[7]["name"]: val_list[7],
    sig_list[8]["name"]: val_list[8],
    sig_list[9]["name"]: val_list[9],
    sig_list[10]["name"]: val_list[10],
    sig_list[11]["name"]: val_list[11],
    sig_list[12]["name"]: val_list[12],
    sig_list[13]["name"]: val_list[13],
    sig_list[14]["name"]: val_list[14],
    "Time": int(time.time())
    }
  print(payload)
  es.index("at_home_v1", "doc", payload)

  time.sleep(1)

