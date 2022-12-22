# GCPL-evaluation
Written in my master thesis and during my Ph.D., the code evaluates GCPL measurements while calculating important key performance parameters

Author: Micha P. Fertig
Text written: 01/27/22

## Anaconda environment 
  EC-Lab 		v11.40
	Spyder 		v5.0.0
	Python 		v3.7
	pandas 		v1.2.4
	openpyxl 	v3.0.7
	matplotlib 	v3.5.0
	seaborn		v0.11.2

## General description
Charge and discharge data saved as .mpt from a SP-240 (Biologic) potentiostat is written in an excel file. Characteristic performance parameters are calculated, based on the paper from Randau et al. "Benchmarking the performance of 
all-solid state lithium batteries" (https://doi.org/10.1038/s41560-020-0565-1). 

## Status
Working but under development

## Usage 
To calculate key performance parameter, "ASSB characterization.py" must be opened. An input query asks for relevant parameters. All data must be at the same file path as the python file. 
Commata as well as dots can be used for separating decimal places. 
Decimal separation must be american in Excel, i.e., dots for separating decimal places must be used.
The file only works for the measurement techniques in following order: PEIS;OCV;MG;OCV;PEIS;OCV;CP;OCV;PEIS (Loop), but can be easily modified for any other order of the mentioned techniques

## Known errors
Error: "IndexError: list index out of range", oder "invalid literal for int() with base 10: 'number'": 
  -> Check "startzeile" variable
Error: "ValueError: invalid literal for int() with base 10: 'cycle\tQ'"
  -> Start and end rows are not properly saved in the .mpt file, mostly when the data was copied while the measurement was still running. Hence, copy the final data and try evaluation again. 
Error: Problems with ExcelWriter
  -> Pandas must have the correct version, otherwise ExcelWriter raises an error

## Copyright
Scripting was done during master thesis and Ph.D. from Micha P. Fertig at Fraunhofer IKTS from April 2020 until December 2023.
