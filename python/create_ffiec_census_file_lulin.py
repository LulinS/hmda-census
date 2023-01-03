from census_functions_lulin import CensusTools

Censustool = CensusTools()

#Replace <year> with the year for which you want to generate the combined census file
year = []

#download census files
# Censustool.get_ffiec_census_file(years=year, download=True, unzip=True)

#extract_census_fields
Censustool.extract_census_fields(years=year, save_csv=True)
