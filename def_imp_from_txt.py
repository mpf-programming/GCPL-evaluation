import pandas as pd
def imp_txt(name_mps, active_mass, peis_num, quality_indicator, filename_xlsx, channel):
    pfad_imp = name_mps + "_"+peis_num+f"_PEIS_{channel}.mpt"
    date = pfad_imp[0:7]
    # Bei Fehlermeldung "IndexError: list index out of range": Startzeile checken!
    # Startzeile = Zeile(number of loops) - 1.
    startzeile_imp = 66
    if quality_indicator == "j":
        startzeile_imp += 1
    else:
        pass

    d = open(pfad_imp)
    content = d.readlines()
    n_loops = int(content[startzeile_imp].strip("\n").split(" ")[4])
    d.close()
    
    d = open(pfad_imp)
    line_of_loops = []
    ende = startzeile_imp + n_loops
    for linenumber, line in enumerate(d):
        for i in range(startzeile_imp +1, ende + 2):
            if linenumber == i:
                line_of_loops.append(line)
    cycle_information = []
    for i in range(0, len(line_of_loops)-1):
        loop = int(line_of_loops[i].strip("\n").split(" ")[1])
        start_loop = int(line_of_loops[i].strip("\n").split(" ")[5])
        end_loop = int(line_of_loops[i].strip("\n").split(" ")[7])
        cycle_information.append((loop, start_loop, end_loop))
    d.close()
    data = pd.read_csv(pfad_imp, delimiter = "\t", decimal = ",", skiprows = startzeile_imp + n_loops+3)
    total_rows = data.shape[0]
    # DataFrame Initialisieren
    loop_stop = cycle_information[0][2]
    Re_Z = pd.DataFrame(data.iloc[0:loop_stop, 1])
    Re_Z = Re_Z.astype(float)
    Im_Z = pd.DataFrame(data.iloc[0:loop_stop, 2])
    final_df = pd.concat([Re_Z, Im_Z], axis = 1)
    # Restlichen Loops zu df hinzufügen
    counter = 1
    while loop_stop+1 < total_rows:
        loop_start = cycle_information[counter][1]
        loop_stop = cycle_information[counter][2]
        #Umrechnung von mAh in mAh/g 
        Re_Z = pd.DataFrame(data.iloc[loop_start:loop_stop, 1])
        Re_Z = Re_Z.astype(float)
        Im_Z = pd.DataFrame(data.iloc[loop_start:loop_stop, 2])
        mediate_df = pd.concat([Re_Z, Im_Z], axis = 1)
        mediate_df.reset_index(drop=True, inplace=True)
        final_df.reset_index(drop=True, inplace=True)
        final_df = pd.concat([final_df, mediate_df], axis = 1)
        counter += 1
    ### https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.ExcelWriter.html
    writer = pd.ExcelWriter(filename_xlsx, engine ="openpyxl", mode="a")
    final_df.to_excel(writer, sheet_name = date + " - PEIS (" +peis_num+")")
    writer.save()
    print("Impedance data added to .xlsx-file")
