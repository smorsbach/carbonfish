import matplotlib.pylab as plt
import networkx as nx
import sys
import os
import pandas as pd
import numpy as np

import clr
import codecs
from ctypes import *

import random as rand

import hashlib


########################################################################################################################
########################################################################################################################
# specify following block

scenario = "BAU"
start = 2050
end = 2060

########################################################################################################################
########################################################################################################################






# import python library
path0 = os.getcwd()
path1 ='\\'.join(path0.split('\\')+['Sourcecode'])
if path1 not in sys.path:
    sys.path.append(path1)
import EweApi_3 as EA # should be requested from Tushith Islam (https://gitlab.com/tushith)

# connect to ecopath core
# -> path to dll
dllf = r"C:\Program Files (x86)\Ecopath with Ecosim 6.7.0 α 64-bit\EwECore.dll"
core = EA.getcore(dllf)

# set up egestion and respiration dataframes

species_resp = ["seals", "seabirds", "harbour porpoises", "cod >35 cm", "cod <=35 cm", "flatfish", "other demersal fish",
                "herring", "sprat", "other pelagic fish", "pelagic macrofauna", "benthic macrofauna", "benthic meiofauna",
                "zooplankton", "bacteria/microorganisms"]

species_eges = ["seals", "seabirds", "harbour porpoises", "cod >35 cm", "cod <=35 cm", "flatfish", "other demersal fish",
                "herring", "sprat", "other pelagic fish", "pelagic macrofauna", "benthic macrofauna", "benthic meiofauna",
                "zooplankton"]

species_biom = ["seals", "seabirds", "harbour porpoises", "cod >35 cm", "cod <=35 cm", "flatfish", "other demersal fish",
                "herring", "sprat", "other pelagic fish", "pelagic macrofauna", "benthic macrofauna", "benthic meiofauna",
                "zooplankton", "bacteria/microorganisms", "phytoplankton", "benthic producers", "detritus/DOM"]

respiration_df_final = pd.DataFrame(np.column_stack([species_resp]),
                                    columns = ['species'])

egestion_df_final = pd.DataFrame(np.column_stack([species_eges]),
                                 columns = ['species'])

biosink_df_final = pd.DataFrame(np.column_stack([species_eges]),
                                 columns = ['species'])

flowtodet_df_final = pd.DataFrame(np.column_stack([species_eges]),
                                 columns = ['species'])

biomass_df_final = pd.DataFrame(np.column_stack([species_biom]),
                                columns = ['species'])

catch_df_final = pd.DataFrame(np.column_stack([species_eges]),
                                columns = ['species'])


dirlc = r"C:\Users\samuelmorsbach\OneDrive\Uni\Master\Master Thesis\EwE\Ecopath Model Files" + "\\" + scenario

file_list = os.listdir(dirlc)
file_list = [word for word in file_list if ".ewemdb" in word]
file_list = [scen for scen in file_list if scenario in scen]
file_list1 = [scen2 for scen2 in file_list if (scenario + "_2") in scen2]
file_list2 = [scen3 for scen3 in file_list if (scenario + "_1") in scen3]

file_list = file_list1 + file_list2

period = list(range(start,end +1))

for y in range(0, len(period)):
    period[y] = str(period[y])

def Filter(file_list, period):
    return [str for str in file_list if
            any(sub in str for sub in period)]

file_list = Filter(file_list, period)

for f in range(0, (len(file_list))):
    file = file_list[f]
    print(file)
    year = ("year_" + file[-17:-7])
    file2 = os.path.join(dirlc, file)
    core, dout = EA.buildup(core, file2)

    if f == 0:
        year_begin = file[-17:-13]

    if f == (len(file_list)-1):
        year_end = file[-17:-13]

    if f == 0:
        year_end = ""

    # respiration

    biom = EA.get_EcoValues(core, dout, 'get_EcopathGroupOutputs', 'get_Biomass')
    pb = EA.get_EcoValues(core, dout, 'get_EcopathGroupOutputs', 'get_PBOutput')
    neteff = EA.get_EcoValues(core, dout, 'get_EcopathGroupOutputs', 'get_NetEfficiency')

    biom_list = list(biom.values())
    pb_list = list(pb.values())
    prod = [biom_list[i] * pb_list[i] for i in range(len(biom_list))]
    neteff_list = list(neteff.values())

    resp = list([0] * 15)

    if any(v == 0 for v in neteff_list[0:15]):
        print("List contains 0!")
    else:
        for i in range(0,15):
            resp[i] = [((-neteff_list[i]) * prod[i] + prod[i]) / neteff_list[i]]

    respiration_df = pd.DataFrame(np.column_stack([resp]), columns = [year])

    respiration_df_final = pd.concat([respiration_df_final, respiration_df], axis = 1)

    # egestion + sinking biomass + flow to detritus

    qb = EA.get_EcoValues(core, dout, 'get_EcopathGroupOutputs', 'get_QBOutput')
    assim = EA.get_EcoValues(core, dout, 'get_EcopathGroupOutputs', 'get_Assimilation')

    fishmort = EA.get_EcoValues(core, dout, 'get_EcopathGroupOutputs', 'get_MortCoFishRate')
    netmigr = EA.get_EcoValues(core, dout, 'get_EcopathGroupOutputs', 'get_MortCoNetMig')
    baccum = EA.get_EcoValues(core, dout, 'get_EcopathGroupOutputs', 'get_BioAccumRatePerYear')
    predmort = EA.get_EcoValues(core, dout, 'get_EcopathGroupOutputs', 'get_PredMort')

    qb_list = list(qb.values())

    assim_list = list([0] * 17)

    for i in range(1,15):
        assim_list[i-1] = assim[i]

    fishmort_list = list(fishmort.values())
    netmigr_list = list(netmigr.values())
    baccum_list = list(baccum.values())

    predmort_list = list([0] * 17)

    for i in range(1,17):
        predmort_list[i-1] = sum(predmort[i].values())

    eges = list([0] * 14)
    biosink = list([0] * 14)
    flowtodet = list([0] * 14)

    for i in range(0,14):
        cons = biom_list[i] * qb_list[i]
        other_mort = pb_list[i] - fishmort_list[i] - predmort_list[i] - baccum_list[i] - netmigr_list[i]
        eges[i] = (cons - assim_list[i])
        biosink[i] = (biom_list[i] * other_mort)
        flowtodet[i] = (cons - assim_list[i]) + (biom_list[i] * other_mort)

    egestion_df = pd.DataFrame(np.column_stack([eges]),
                              columns = [year])

    biosink_df = pd.DataFrame(np.column_stack([biosink]),
                              columns = [year])

    flowtodet_df = pd.DataFrame(np.column_stack([flowtodet]),
                              columns = [year])

    egestion_df_final = pd.concat([egestion_df_final, egestion_df], axis = 1)

    biosink_df_final = pd.concat([biosink_df_final, biosink_df], axis = 1)

    flowtodet_df_final = pd.concat([flowtodet_df_final, flowtodet_df], axis = 1)

    # biomass

    biomass_df = pd.DataFrame(np.column_stack([biom_list]),
                              columns = [year])

    biomass_df_final = pd.concat([biomass_df_final, biomass_df], axis = 1)

    # catch

    catch = list([0] * 14)

    for i in range(0,14):
        catch[i] = (biom_list[i] * fishmort_list[i])

    catch_df = pd.DataFrame(np.column_stack([catch]),
                            columns = [year])

    catch_df_final = pd.concat([catch_df_final, catch_df], axis = 1)


csv_dir_resp = r"C:\Users\samuelmorsbach\OneDrive\Uni\Master\Master Thesis\R Master Thesis\data\Model Output" + "\\" + scenario + "_" + year_begin + year_end + "_respiration.csv"
csv_dir_eges = r"C:\Users\samuelmorsbach\OneDrive\Uni\Master\Master Thesis\R Master Thesis\data\Model Output" + "\\" + scenario + "_" + year_begin + year_end + "_egestion.csv"
csv_dir_bios = r"C:\Users\samuelmorsbach\OneDrive\Uni\Master\Master Thesis\R Master Thesis\data\Model Output" + "\\" + scenario + "_" + year_begin + year_end + "_biosink.csv"
csv_dir_flow = r"C:\Users\samuelmorsbach\OneDrive\Uni\Master\Master Thesis\R Master Thesis\data\Model Output" + "\\" + scenario + "_" + year_begin + year_end + "_detflow.csv"
csv_dir_biom = r"C:\Users\samuelmorsbach\OneDrive\Uni\Master\Master Thesis\R Master Thesis\data\Model Output" + "\\" + scenario + "_" + year_begin + year_end + "_biomass.csv"
csv_dir_catch = r"C:\Users\samuelmorsbach\OneDrive\Uni\Master\Master Thesis\R Master Thesis\data\Model Output" + "\\" + scenario + "_" + year_begin + year_end + "_catch.csv"


respiration_df_final.to_csv(csv_dir_resp)
egestion_df_final.to_csv(csv_dir_eges)
biosink_df_final.to_csv(csv_dir_bios)
flowtodet_df_final.to_csv(csv_dir_flow)
biomass_df_final.to_csv(csv_dir_biom)
catch_df_final.to_csv(csv_dir_catch)