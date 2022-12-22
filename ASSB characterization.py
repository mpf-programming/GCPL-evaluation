"""
Die Datei ASSB characterization berechnet aus .mpt Dateien von BioLogic
v11.40 Performanz-Kennwerte (s. README).
Stand: 27.09.2021
Spyder 5.0.0
Python 3.7
pandas v1.2.4
openpyxl v3.0.7
"""

import Operations as op
import def_imp_from_txt as imp

# Abfrage verschiedener Parameter, die zur weiteren Berechnung benötigt werden
# und sich von Versuch zu Versuch unterscheiden

#Fläche der Positrode-Seite in cm² (Positrode-Durchmesser = 18 mm)
area = float((input("Enter the AREA of the POSITIVE ELECTRODE in [cm²]: ")).replace(",","."))
name_mps = input("Enter the name of the .mps file (without .mps): ")
active_mass = float((input("Enter the ACTIVE mass in [g]: ")).replace(",","."))
cathode_mass = float((input("Enter the mass of the POSITIVE ELECTRODE in [g]: ")).replace(",","."))
I = float((input("Enter the current in [mA]: ")).replace(",","."))
quality_indicator = input("Were Quality-Indicator activated? (j/n): " )
channel = input("Enter measuring channel (e.g. C01): ")
filename_xlsx = name_mps+"_AM"+str(active_mass)+"g_CM"+str(cathode_mass)+"g.xlsx"


''' FÜR MG: Ermittlung der Spannung/Ladung-Paare und Berechnung der Größen
wie Leistung und Energie für den Ladeprozess (MG). 
Anschließendes Speichern in Excel-Datei. '''
# Methode muss angepasst werden, sofern sich die Reihenfolge im Biologic-
# Programm ändert, z.B. ein OCV/PEIS zuvor eingefügt wird
# Bei Fehlermeldung "IndexError: list index out of range": Startzeile checken!
# Startzeile = Zeile(number of loops) - 1.
# column_value definiert die erste Spalte mit relevanten Daten im Dataframe
# dQ in Spalte 10 ist bereits in mAh. Daher Faktor 1 (keine Umrechnung)
method = f"_04_MG_{channel}.mpt"

startzeile, column_value, factor = 69, 10, 1
full_dataframe_mg = op.get_whole_dataframe(name_mps, method, startzeile, 
                                      quality_indicator, active_mass, area,
                                      I, column_value, factor)
dataframe_mg, cycle_information = full_dataframe_mg[0], full_dataframe_mg[1]
values_mg_df = op.get_characteristic_values(dataframe_mg, active_mass, area, I,
                                         cycle_information, cathode_mass)
op.save_datafiles_initial(name_mps, active_mass, dataframe_mg, filename_xlsx, 
                          sheet_name="Data MG")
op.save_datafiles_append(name_mps, active_mass, values_mg_df, filename_xlsx, 
                         sheet_name="MG_Charact.Values")
print("MG done")



''' CP. Selbiges Vorgehen wie für MG, aber Öffnung anderer Datei. '''
method = f"_08_CP_{channel}.mpt"
# Bei Fehlermeldung "IndexError: list index out of range": Startzeile checken!
# Startzeile = Zeile(number of loops) - 1.

# Bei Methode CP ist dQ (erster relevanter Wert) in 11. Spalte. Einheit ist 
# -dQ in Coulomb, daher ist Umrechnungsfaktor zu mAh nötig
# Methode get_whole_dataframe returned eine Liste: Den Dataframe mit 
# Ladungs/Spannungsspalten für jeden Zyklus, sowie die 
# Zykleninformation (Zyklus, Startzeile, Endzeile)
startzeile, column_value, factor = 2, 11, -3.6
full_dataframe_cp = op.get_whole_dataframe(name_mps, method, startzeile, 
                                      quality_indicator, active_mass, area,
                                      I, column_value, factor)
dataframe_cp, cycle_information = full_dataframe_cp[0], full_dataframe_cp[1]
values_cp_df = op.get_characteristic_values(dataframe_cp, active_mass, area, I,
                                         cycle_information, cathode_mass)
op.save_datafiles_append(name_mps, active_mass, dataframe_cp, filename_xlsx, 
                         sheet_name= "Data CP")
op.save_datafiles_append(name_mps, active_mass, values_cp_df, filename_xlsx, 
                         sheet_name="CP_Charact.Values")
print("CP done")


'''Berechnung der Effizienzen und Retentionen unter Verwendung der zwei 
vorangegangenen Dataframes'''
eff_and_ret_df = op.compare_charge_discharge(values_mg_df, values_cp_df, I)
op.save_datafiles_append(name_mps, active_mass, eff_and_ret_df, filename_xlsx, sheet_name="Eff._and_Ret.")
print("Efficiencies and Retentions done")

'''Schreiben der PEIS-Daten'''

peis_num = "02"
imp.imp_txt(name_mps, active_mass, peis_num, quality_indicator, filename_xlsx, channel)
peis_num = "06"
imp.imp_txt(name_mps, active_mass, peis_num, quality_indicator, filename_xlsx, channel)

#peis_num = "10"
#imp.imp_txt(name_mps, active_mass, peis_num, quality_indicator, filename_xlsx, channel)
print("PEIS done")

op.draw_charge_discharge_curve(dataframe_mg, dataframe_cp, name_mps)

print("The task was completed successfully") 


