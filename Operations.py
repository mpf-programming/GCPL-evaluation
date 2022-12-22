import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def get_whole_dataframe(name_mps, method, startzeile, quality_indicator, active_mass, area, I, column_value, factor):
    """ Zweck der Methode get_whole_dataframe ist es, die Textdatei zu öffnen, 
    die Zykleninformation (Zyklusnummer, Startzeile, Endzeile) zu extrahieren
    und die Ladung und Spannung für jeden Zyklus zu ermitteln. Am Ende wird 
    eine Liste zurückgegeben, die [Ladung/Spannung, Zykleninformation] ausgibt
    """
    # Dateipfad der Messdatei ermitteln
    pfad = name_mps + method
    # Messdatei hat eine Zeile mehr wenn Quality-Indikatoren aktiviert wurden, 
    # dies muss bei dem Lesen der Textdatei mit zusätzlicher Zeile berück-
    # sichtigt werden
    startzeile =+ 1 if quality_indicator == "j" else startzeile
        
    
    # Öffnen der MG- bzw. CP .mpt-Datei
    d = open(pfad)
    # Lesen der Zeile "number of loops : XY" um XY (also die Anzahl an 
    # Loops) zu ermitteln
    content = d.readlines()
    n_loops = int(content[startzeile].strip("\n").split(" ")[4])
    # Lesen der darunterligenden Zeilen, welche u.a. die Zykleninformationen über 
    # den Loop und dessen Start- und Endzeile enthalten
    loop_information = content[startzeile +1:startzeile + n_loops + 2]
    # In der folgenden if Schleife werden die Information in eine Liste extrahiert
    # cycle_information returns (Zyklus, Startzeile des Zyklus, 
    # Endzeile des Zyklus). Z.B.[(0,0,127), (1,128,257), (2, 258, 489), etc]
    cycle_information = []
    for i in range(0, len(loop_information)-1):
        loop = int(loop_information[i].strip("\n").split(" ")[1])
        line_loop_starts = int(loop_information[i].strip("\n").split(" ")[5])
        line_loop_ends = int(loop_information[i].strip("\n").split(" ")[7])
        cycle_information.append((loop, line_loop_starts, line_loop_ends))
    d.close()

    # Die Textdatei in Pandas öffnen und die allgemeinen Informationen 
    # überspringen (skiprows), das Komma als Trennzeichen festlegen und den  
    # Tabstopp zur Trennung der Daten verwenden
    data = pd.read_csv(pfad, delimiter = "\t", decimal = ",", 
                       skiprows = startzeile + n_loops + 2)
    # DataFrame erstellen mit den Informationen des ersten Zyklus' (=0)
    line_loop_stops = cycle_information[0][2]
    charge = pd.DataFrame(data.iloc[0:line_loop_stops, column_value])
    #Umrechnung in mAh / g
    charge = ((charge.astype(float))/(factor * active_mass))
    voltage = pd.DataFrame(data.iloc[0:line_loop_stops,column_value-2])
    # Ladung und Spannung sollen nebeneinander stehen -> axis = 1
    final_df = pd.concat([charge, voltage], axis = 1)
    
    # Ladung und Spannung der restlichen Loops zum Dataframe hinzufügen
    counter = 1
    total_rows_in_data = data.shape[0]
    while line_loop_stops+1 < total_rows_in_data:
        line_loop_starts = cycle_information[counter][1]
        line_loop_stops = cycle_information[counter][2]
        #Umrechnung von mAh in mAh/g 
        charge = pd.DataFrame(data.iloc[line_loop_starts:line_loop_stops, column_value])
        charge = ((charge.astype(float))/(factor * active_mass))
        voltage = pd.DataFrame(data.iloc[line_loop_starts:line_loop_stops,column_value-2])
        mediate_df = pd.concat([charge, voltage], axis = 1)
        mediate_df.reset_index(drop=True, inplace=True)
        final_df.reset_index(drop=True, inplace=True)
        final_df = pd.concat([final_df, mediate_df], axis = 1)
        counter += 1
    return [final_df, cycle_information]


def get_characteristic_values(final_df, active_mass, area, I, cycle_information, cathode_mass):
    '''
    Im nächsten Teil werden aus dem vorigen Dataframe final_df Parameter
    entnommen und damit weitere Parameter zur ASSB-Charakterisierung berechnet.
    Die Ergebnisse für jeden Zyklus werden in einem weiteren Dataframe ausge-
    geben
    
    Die Werte beziehen sich auf entweder den Lade- oder den Entlade-
    vorgang
    
    q: spezifische Kapazität der Kathode im Lade/Entladevorgang [mAh/g]
    Q: Kapazität der Kathode im Lade/Entladevorgang [mAh]
    t: Zeit des Lade/Entladevorgangs [h]
    C_rate: Lade/Entladerate in h^-1
    U_avg: Mittelwert der Spannungswerte des kompletten Zyklus [V]
    E: Energiegehalt der Kathode [mWh]
    P: Leistungsabgabe der Kathode [mW]
    '''
    
    # Herausfinden der charakteristischen Werte für den ersten Zyklus
    q_1st_cycle = final_df.iloc[(cycle_information[0][2]-cycle_information[0][1]-1), 0]
    Q_1st_cycle = q_1st_cycle*active_mass
    t_1st = Q_1st_cycle/I
    C_rate_1st = 1/t_1st
    U_avg_1st = final_df.iloc[:, 1].mean()

    #Integral der Spannungskurve ist bei kleinem delta x = delta U gleich mit 
    #dem Mittelwert der Spannung mal der ladung
    E_1st = U_avg_1st*Q_1st_cycle
    P_1st = U_avg_1st*I
    #Normalized to cell active area of cathodic side, 
    #E_area in Wh/m², P_area in W/m²
    j, E_1st_area, P_1st_area, Q_1st_area = (I/area), (E_1st/area)*10, (P_1st/area)*10, Q_1st_cycle/area
    #Normalized to cathode active material mass, E_m in Wh/kg
    j_cam, E_cam_1st, P_cam_1st = I/active_mass, E_1st/active_mass, P_1st/active_mass
    #Normalized to cathode mass
    # cam: Cathode active mass, cm: cathode mass (total)
    j_cm, E_cm_1st, P_cm_1st = I/cathode_mass, E_1st/cathode_mass, P_1st/cathode_mass
    kennwerte_df = pd.DataFrame({"Cycle #": [1],
                                 "Spec. capacity q [mAh/g]":[q_1st_cycle],
                                 "Charge Q [mAh]":[Q_1st_cycle],
                                 "Duration T [h]": [t_1st],
                                 "C-Rate [1/h]": [C_rate_1st], 
                                 "Avg. Voltage [V]": [U_avg_1st],
                                 "Energy W [mWh]": [E_1st],
                                 "Power P [mW]": [P_1st],
                                 "Current density j [mA/cm²]": [j],
                                 "W_area [Wh/m²]": [E_1st_area],
                                 "P_area [W/m²]": [P_1st_area],
                                 "Q_area [mAh/cm²]": [Q_1st_area],
                                 "j_cam / mA/g": [j_cam],
                                 "W_cam / Wh/kg": [E_cam_1st],
                                 "P_cam / W/kg": [P_cam_1st],
                                 "j_cm / mA/g": [j_cm],
                                 "W_cm / Wh/kg": [E_cm_1st],
                                 "P_cm / W/kg": [P_cm_1st]})
    
    counter = 1
    column = 2
    while column+1 < final_df.shape[1]:
        q_nth_cycle = final_df.iloc[(cycle_information[counter][2]-cycle_information[counter][1]-1), column]
        Q_nth_cycle = q_nth_cycle*active_mass
        t_nth = Q_nth_cycle/I
        C_rate_nth = 1/t_nth
        U_avg_nth = final_df.iloc[:, column+1].mean()
        E_nth = U_avg_nth*Q_nth_cycle
        P_nth = U_avg_nth*I
        #Normalized to cell area, E_area in Wh/m², P_area in W/m²
        E_nth_area, P_nth_area, Q_nth_area =  (E_nth/area)*10, (P_nth/area)*10, Q_nth_cycle/area
        #Normalized to cathode active material mass, E_m in Wh/kg
        E_cam_nth, P_cam_nth = E_nth/active_mass, P_nth/active_mass
        #Normalized to cathode mass
        j_cm, E_cm_nth, P_cm_nth = I/cathode_mass, E_nth/cathode_mass, P_nth/cathode_mass
        
        kennwerte_df_mediate = pd.DataFrame({"Cycle #": [cycle_information[counter][0]+1],
                                 "Spec. capacity q [mAh/g]":[q_nth_cycle],
                                 "Charge Q [mAh]":[Q_nth_cycle],
                                 "Duration T [h]": [t_nth],
                                 "C-Rate [1/h]": [C_rate_nth], 
                                 "Avg. Voltage [V]": [U_avg_nth],
                                 "Energy W [mWh]": [E_nth],
                                 "Power P [mW]": [P_nth],
                                 "Current density j [mA/cm²]": [j],
                                 "W_area [Wh/m²]": [E_nth_area],
                                 "P_area [W/m²]": [P_nth_area],
                                 "Q_area [mAh/cm²]": [Q_nth_area],
                                 "j_cam / mA/g": [j_cam],
                                 "W_cam / Wh/kg": [E_cam_nth],
                                 "P_cam / W/kg": [P_cam_nth],
                                 "j_cm / mA/g": [j_cm],
                                 "W_cm / Wh/kg": [E_cm_nth],
                                 "P_cm / W/kg": [P_cm_nth]})
        #mediate_df = pd.concat([charge, voltage], axis = 1)
        #mediate_df.reset_index(drop=True, inplace=True)
        #final_df.reset_index(drop=True, inplace=True)
        kennwerte_df = pd.concat([kennwerte_df, kennwerte_df_mediate])
        counter += 1
        column += 2
    return kennwerte_df

    
def save_datafiles_initial(name_mps, active_mass, dataframe, filename_xlsx, sheet_name):
    '''Eine Excel-Datei (.xlsx) wird erstellt. Deren Inhalt besteht aus einem
    Dataframe'''
    ### https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.ExcelWriter.html
    date = name_mps[0:7]
    writer = pd.ExcelWriter(filename_xlsx)
    dataframe.to_excel(writer, sheet_name = date + sheet_name)
    print(".xlsx-file was created")
    writer.save()

def save_datafiles_append(name_mps, active_mass, dataframe, filename_xlsx, sheet_name):
    ''' Alle weiteren Berechnungen werden mit dieser Methode in die selbe 
    Excel-Datei abgespeichert, die mittels der Methode save_datafiles_initial
    erstellt wurde. Die Speicherung erfolgt in einem neuen Blatt.'''
    date = name_mps[0:7]
    writer = pd.ExcelWriter(filename_xlsx, mode='a', engine ="openpyxl")
    dataframe.to_excel(writer, sheet_name = date + sheet_name)
    print("Dataframe was added to .xlsx-file")
    writer.save()
    
def compare_charge_discharge(values_mg, values_cp, I):
    '''
    Da durch die Methode "get_characteristic_values" nun Daten für den Lade-
    und Entladevorgang berechnet wurden, können diese in dieser Methode mit-
    einander verglichen werden
    '''
    
    #Initializing efficiency values for (Discharge/Charge)*100 in the same cycle
    capacity_ch = values_mg.iloc[0, 1]
    capacity_dis = values_cp.iloc[0, 1]
    phi_capacity_dis_ch = (capacity_dis/capacity_ch)*100
    U_ch = values_mg.iloc[0, 5]
    U_dis = values_cp.iloc[0, 5]
    phi_U_dis_ch = (U_dis/U_ch)*100
    E_ch = values_mg.iloc[0,6]
    E_dis = values_cp.iloc[0,6]
    phi_E_dis_ch = (E_dis/E_ch)*100
    
    #Die Überspannung eta gilt für Lade- und Entladevorgang gleichermaßen, 
    #vorausgesetzt LADE UND ENTLADESTROM sind GLEICH
    eta_ch = (U_ch-U_dis)/2
    eta_dis = eta_ch
    R_eta_ch = (eta_ch / I) * 1000
    # Trifft nur zu wenn Lade- und Entladestrom gleich ist
    R_eta_dis = R_eta_ch
    
    #Initializing retention values, bezogen auf den zweiten Zyklus! 
    ch_capacity_2nd_cycle = values_mg.iloc[1, 1]
    ch_voltage_2nd_cycle = values_mg.iloc[1, 5]
    ch_energy_2nd_cycle = values_mg.iloc[1,6]
    dis_capacity_2nd_cycle = values_cp.iloc[1, 1]
    dis_voltage_2nd_cycle = values_cp.iloc[1, 5]
    dis_energy_2nd_cycle = values_cp.iloc[1,6]
    
    phi_retention_capacity_ch = (capacity_ch/ch_capacity_2nd_cycle)*100
    phi_retention_voltage_ch = (U_ch/ch_voltage_2nd_cycle)*100
    phi_retention_energy_ch = (E_ch/ch_energy_2nd_cycle)*100
    
    phi_retention_capacity_dis = (capacity_dis/dis_capacity_2nd_cycle)*100
    phi_retention_voltage_dis = (U_dis/dis_voltage_2nd_cycle)*100
    phi_retention_energy_dis = (E_dis/dis_energy_2nd_cycle)*100
    
    #Initalizing Dataframe to append further data
    efficiency_and_retention_df = pd.DataFrame({"Cycle #": [1],
                                 "q_eff_dis/ch [%]": [phi_capacity_dis_ch],
                                 "U_eff_dis/ch [%]": [phi_U_dis_ch],
                                 "E_eff_dis/ch [%]": [phi_E_dis_ch],
                                 "q_ret_ch [%]": [phi_retention_capacity_ch],
                                 "U_ret_ch [%]": [phi_retention_voltage_ch],
                                 "W_ret_ch [%]": [phi_retention_energy_ch],
                                 "q_ret_dis [%]": [phi_retention_capacity_dis],
                                 "U_ret_dis [%]": [phi_retention_voltage_dis],
                                 "W_ret_dis [%]": [phi_retention_energy_dis],
                                 "Übersp._ch [V]": [eta_ch],
                                 "Übersp._dis [V]": [eta_dis],
                                 "R wg.Eta_ch[Ohm]": [R_eta_ch],
                                 "R wg.Eta_dis[Ohm]": [R_eta_dis]})
    # Calculating values above for the ten cycles and appending to existing 
    # dataframe
    counter = 1
    while counter < values_mg.shape[0]:
        capacity_ch = values_mg.iloc[counter, 1]
        try:
            capacity_dis = values_cp.iloc[counter, 1]
        except:
            capacity_dis = 0
        phi_capacity_dis_ch = (capacity_dis/capacity_ch)*100
        U_ch = values_mg.iloc[counter, 5]
        try:
            U_dis = values_cp.iloc[counter, 5]
        except:
            U_dis = 0
        phi_U_dis_ch = (U_dis/U_ch)*100
        E_ch = values_mg.iloc[counter,6]
        try:
            E_dis = values_cp.iloc[counter,6]
        except:
            E_dis = 0
        phi_E_dis_ch = (E_dis/E_ch)*100
        eta_ch = (U_ch-U_dis)/2
        eta_dis = eta_ch
        R_eta_ch = (eta_ch / I) * 1000
        R_eta_dis = R_eta_ch
        
        ch_capacity_2nd_cycle = values_mg.iloc[1, 1]
        ch_voltage_2nd_cycle = values_mg.iloc[1, 5]
        ch_energy_2nd_cycle = values_mg.iloc[1,6]
        dis_capacity_2nd_cycle = values_cp.iloc[1, 1]
        dis_voltage_2nd_cycle = values_cp.iloc[1, 5]
        dis_energy_2nd_cycle = values_cp.iloc[1,6]
        
        phi_retention_capacity_ch = (capacity_ch/ch_capacity_2nd_cycle)*100
        phi_retention_voltage_ch = (U_ch/ch_voltage_2nd_cycle)*100
        phi_retention_energy_ch = (E_ch/ch_energy_2nd_cycle)*100
        
        phi_retention_capacity_dis = (capacity_dis/dis_capacity_2nd_cycle)*100
        phi_retention_voltage_dis = (U_dis/dis_voltage_2nd_cycle)*100
        phi_retention_energy_dis = (E_dis/dis_energy_2nd_cycle)*100
        
        efficiency_df_mediate = pd.DataFrame({"Cycle #": [counter+1],
                                 "q_eff_dis/ch [%]": [phi_capacity_dis_ch],
                                 "U_eff_dis/ch [%]": [phi_U_dis_ch],
                                 "E_eff_dis/ch [%]": [phi_E_dis_ch],
                                 "q_ret_ch [%]": [phi_retention_capacity_ch],
                                 "U_ret_ch [%]": [phi_retention_voltage_ch],
                                 "W_ret_ch [%]": [phi_retention_energy_ch],
                                 "q_ret_dis [%]": [phi_retention_capacity_dis],
                                 "U_ret_dis [%]": [phi_retention_voltage_dis],
                                 "W_ret_dis [%]": [phi_retention_energy_dis],
                                 "Übersp._ch [V]": [eta_ch],
                                 "Übersp._dis [V]": [eta_dis],
                                 "R wg.Eta_ch[Ohm]": [R_eta_ch],
                                 "R wg.Eta_dis[Ohm]": [R_eta_dis]})
        efficiency_and_retention_df = pd.concat([efficiency_and_retention_df, efficiency_df_mediate])
        counter += 1
    return efficiency_and_retention_df
    
    
def draw_charge_discharge_curve(dataframe_mg, dataframe_cp, name_mps):
    sns.set_theme()
    # Die Zyklen werden peu a peu zum Graph hinzugefügt. Auf die einzelnen
    # Spalten (zwei Spalten sind ein Zyklus mit Ladung/Spannung) wird mittels
    # iloc zugegriffen. Von einem Zyklus sollen alle Reihen gezeichnet werden
    
    # .shape[1] gibt die Anzahl an Spalten im DF zurück. Es sind Zyklus*2 Spalten.
    zyklus = ["Cycle "+str(i+1) for i in range(int(dataframe_mg.shape[1]/2))]
    counter = 0
    while counter < dataframe_mg.shape[1]:
        p = sns.lineplot(x=dataframe_mg.iloc[:, counter], y=dataframe_mg.iloc[:, counter+1])
        counter += 2
    counter = 0
    while counter < dataframe_cp.shape[1]:
        p = sns.lineplot(x=dataframe_cp.iloc[:, counter], y=dataframe_cp.iloc[:, counter+1])
        counter += 2
    # Graph soll immer bei x = 0 beginnen und nach oben hin "offen" sein
    plt.xlim(0,)
    # Die Legende soll auf Größe 5 und oben rechts sein
    plt.legend(labels=(zyklus), fontsize = 5, loc = "center right")
    # Beschriftung x und y-Achse
    p.set(xlabel = "Specific charge q / mAh/g", ylabel = "Voltage U/ V", 
          title = "Measurement " + name_mps)
    plt.savefig(fname = name_mps+"_CDC.png", dpi = 300)
    plt.show()
    