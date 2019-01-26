## -*- coding: utf-8 -*-
import pandas as pd
from elasticsearch import Elasticsearch
import minimalmodbus
import unicodedata
import pprint
import json
import time

# Init Elasticsearch
es = Elasticsearch(hosts=["https://user:pass@server.tld"],
                           timeout=60)

# Init modbus
instrument = minimalmodbus.Instrument('/dev/ttyUSB0', 10) # port name, slave address (in decimal)
instrument.serial.timeout=0.8

# read excelfile
df = pd.read_excel('Trovis 5575 STR_HoldingReg.xlsx', sheet_name='Tabelle1')

# Offset von den Registernummern abziehen
df.loc[:,'HRNr'] += -40001

# Liste der zu lesenden Registerbereiche festlegen

idx_list = list()
idx_list.append([0, 5])
idx_list.append([9, 36])
idx_list.append([98, 154])
#idx_list.append([200, 214])
#idx_list.append([299, 319])
idx_list.append([999, 1044])
idx_list.append([1053, 1071])
idx_list.append([1089, 1095])
idx_list.append([1199, 1243])
idx_list.append([1255, 1271])
idx_list.append([1455, 1470])
idx_list.append([1799, 1812])
idx_list.append([1827, 1838])
idx_list.append([1855, 1870])
idx_list.append([2999, 3099])
idx_list.append([3100, 3199])
idx_list.append([3199, 3250])
idx_list.append([3499, 3548])
idx_list.append([6399, 6423])
#idx_list.append([6469, 6487])
idx_list.append([9999, 10099])
idx_list.append([10100, 10199])
idx_list.append([10200, 10253])


# Liste aus einzelnen DataFrames erzeugen, die nur die relevanten Register beinhaltet
ref_list = list()
for idx_range in idx_list:
  res = df.loc[df['HRNr'].isin(range(idx_range[0], idx_range[1]+1))]
  if res.shape[0]>0:
    ref_list.append(res)
  else:
    pass

  #print(range(idx_range[0], idx_range[1]+1))
  #print(res.index.values)
  #print(res['Bezeichnung'])
  #print("-------")


res_str={}
for df_tmp in ref_list:
  idx_start = int(df_tmp['HRNr'].iloc[0])
  idx_end   = int(df_tmp['HRNr'].iloc[-1])
  idx_vec   = range(idx_start, idx_end+1)
  # print(idx_start)
  # print(idx_end)
  # print(df_tmp)
  # print(idx_vec)
  # print(df_tmp.index.values)

  size = len(df_tmp.index.values)
  #  print(size)

  try:
    res = list(map(int, instrument.read_registers(idx_start, size)))
  except Exception as e:
    res = e

  # get list of matchin indicies in data dictionary
  df_tmp['raw'] = res
  df_tmp['val'] = df_tmp['raw'].values.astype(float)/(10**df_tmp["NkS"].values.astype(float))

  for index, row in df_tmp.iterrows():
#    print(row)
    key = str("%04d" % int(row['HRNr']) ) + "-" + row['Bezeichnung'].encode("utf-8")
#    print(key.decode('ascii', 'ignore'))
    res_str[str(key.decode('ascii', 'ignore'))] = float(row['val'])

#  print(res_str)
#  print(df_tmp)
#  exit()
  print("------------------------")

res_str["Time"]=int(time.time())
#res = json.dumps(res_str)
es.index("at_home_v2", "doc", res_str)
pprint.pprint(res_str)
