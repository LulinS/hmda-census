### This is a code utility library that contains logic to download and combine the FFIEC Census flat file and
# Census/OMB delineation file for use with HMDA data.

import os
from os import path
from os import listdir
from os.path import isfile, join
import shutil

import pandas as pd
import requests
import yaml
import zipfile
import sqlite3

#handle in config load


class CensusTools(object):
    """
	"""

    def __init__(self, config_file="census_config.yaml"):
        """
		Sets up the configuration for file paths and download URLs
		"""

        with open(config_file, "r") as in_config:
            self.config_data = yaml.safe_load(in_config)

        print()
        for path in self.config_data["FOLDER_PATHS"]:
            if not os.path.exists(self.config_data[path]):
                print(
                    "creating {folder}".format(folder=self.config_data[path]))
                os.makedirs(self.config_data[path])

    def connect(self, db):
        """
			Connects to a sqlite database instance
			"""

        conn = sqlite3.connect(db)
        return conn, conn.cursor()

    def get_ffiec_census_file(self, years=[], unzip=True, download=True):
        """
		Retrieves Census flat file data from the FFIEC website.
		Each file is 1 year of data intended to be used with HMDA data.
		Files are available from 1990-2021. New files are typically published in the fall.

		PARAMETERS:
		years: a list of which years of data to download, unzip and rename
		unzip, if true: unzips all zip files in the DATA_PATH location
		move, if true: moves all files in the from sub folders to the main data folder
		"""
        if len(years) < 1:
            years = self.config_data["ALL_YEARS"]

        if download:

            base_url = self.config_data["FFIEC_CENSUS_BASE_URL"]
            for year in years:

                local_file_name = "ffiec_census_{year}.zip".format(year=year)
                print()
                print("getting data for {year}".format(year=year))

                if int(year) >= 2020:
                    census_year_url = base_url + "Census{year}.zip".format(
                        year=year)

                elif int(year) >= 2015:
                    census_year_url = base_url + "CENSUS{year}.zip".format(
                        year=year)

                elif int(year) == 2014:
                    census_year_url = base_url + "CENSUS{year}.ZIP".format(
                        year=year)

                elif int(year) in [2012, 2013]:
                    census_year_url = base_url + "Census{year}.zip".format(
                        year=year)

                elif int(year) >= 2008:
                    census_year_url = base_url + "census{year}.zip".format(
                        year=year)

                else:
                    census_year_url = base_url + "Zip%20Files/{year}.zip".format(
                        year=year)

                if self.config_data["DEBUG"]:
                    print(census_year_url)

                census_resp = requests.get(census_year_url)
                print("saving data for {year} as {name}".format(
                    year=year, name=local_file_name))

                with open(self.config_data["CENSUS_PATH"] + local_file_name,
                          "wb") as infile:
                    infile.write(census_resp.content)

        if unzip:

            ##get all files in data dir with .zip extension
            print()
            print("Unzipping files in {folder}".format(
                folder=self.config_data["CENSUS_PATH"]))
            census_files = [
                f for f in listdir(self.config_data["CENSUS_PATH"])
                if isfile(join(self.config_data["CENSUS_PATH"], f))
            ]
            census_files = [f for f in census_files if f[-4:] == ".zip"]

            if self.config_data["DEBUG"]:
                print()
                print("census files to unzip")
                print(census_files)

            #unzip all census files
            for file in census_files:
                if file[-8:-4] in years:
                    with zipfile.ZipFile(
                            self.config_data["CENSUS_PATH"] + file,
                            'r') as zip_ref:

                        if self.config_data["DEBUG"]:
                            print()
                            print("files in archive:")
                            print(zip_ref.namelist())

                        for file in zip_ref.namelist(
                        ):  #iterate over files in archive
                            print()
                            print("extracting data and docs for ", file)
                            #handle txt file: extract and rename to census_dict_year.doc or census_dict_year.docx
                            if file[-4:] in [".doc"]:
                                new_name = "census_docs_{year}".format(
                                    year=file[-8:-4]) + file[-4:]
                                new_name = new_name.lower()

                                with open(
                                        self.config_data["CENSUS_DOCS"] +
                                        new_name, "wb") as outfile:
                                    outfile.write(zip_ref.read(file))

                            elif file[-4:] in ["docx"]:
                                new_name = "census_docs_{year}".format(
                                    year=file[-9:-5]) + file[-5:]
                                new_name = new_name.lower()

                                with open(
                                        self.config_data["CENSUS_DOCS"] +
                                        new_name, "wb") as outfile:
                                    outfile.write(zip_ref.read(file))

                            #handle data file: extract and rename to census_data_year.DAT or census_data_year.csv
                            elif file[-4:] in [".DAT", ".csv", ".dat"]:
                                new_name = "census_data_{year}".format(
                                    year=file[-8:-4]) + file[-4:]
                                new_name = new_name.lower()

                                with open(
                                        self.config_data["CENSUS_PATH"] +
                                        new_name, "wb") as outfile:
                                    outfile.write(zip_ref.read(file))

                            elif file[-4:] == ".zip":
                                print("extracting nested zip archive")
                                new_name = "census_data_{year}".format(
                                    year=file[-8:-4]) + file[-4:]
                                new_name = new_name.lower()

                                with open(
                                        self.config_data["CENSUS_PATH"] +
                                        new_name, "wb") as outfile:
                                    outfile.write(zip_ref.read(file))

                                with zipfile.ZipFile(
                                        self.config_data["CENSUS_PATH"] +
                                        new_name, 'r') as myzip:
                                    for f in myzip.namelist():
                                        nm = "census_data_{year}".format(
                                            year=file[-8:-4]) + f[-4:]
                                        with open(
                                                self.config_data["CENSUS_PATH"]
                                                + nm, 'wb') as outfile:
                                            outfile.write(myzip.read(f))

                                os.remove(self.config_data["CENSUS_PATH"] +
                                          new_name)

    def extract_census_fields(self, years=[], save_csv=True):
        """
		Extracts the enumerated fields from an FFIEC Census data CSV
		Returns a pandas dataframe with the selected fields

		Notes: 
		- not all FFIEC census data is in CSV format and data contents may change between years
		- 2011 and earlier files are in .DAT format and require fixed width file loads
		
		
		PARAMETERS:
		field_dict: a name, field number dictionary. The keys will be used as column names, 
					the values will be used to select fields from the FFIEC Census file.
			- The data file documentation is not zero-indexed.
			- Pass in the index in the documentation. Do not adjust for zero-indexing, 
				that is handled in this code.

		census_files: the names of the census files used for the extracts
		data_path: the path to the census file to be used for extracts
		save_csv: write the extracts to a CSV file
		sep: separater character to use when writing file extracts
		"""
        if len(years) < 1:
            print()
            print("No year list passed, using ALL_YEARS from config file")
            years = self.config_data["ALL_YEARS"]

        data_path = self.config_data["CENSUS_PATH"]  #set path to data files

        #fields to extract from file
        field_dict_2004_2021 = self.config_data[
            "extract_fields_2004_2021"]
        field_dict_2003 = self.config_data[
            "extract_fields_2003"]  
        field_dict_1996_2002 = self.config_data[
            "extract_fields_1996_2002"]  
        field_dict_1993_1995 = self.config_data[
            "extract_fields_1993_1995"]  
        field_dict_1990_1992 = self.config_data[
            "extract_fields_1990_1992"]  

        field_names_2004_2021 = list(field_dict_2004_2021.keys())
        field_names_2003 = list(field_dict_2003.keys())
        field_names_1996_2002 = list(field_dict_1996_2002.keys())
        field_names_1993_1995 = list(field_dict_1993_1995.keys())
        field_names_1990_1992 = list(field_dict_1990_1992.keys())

        field_nums_one_idx_2004_2021 = list(field_dict_2004_2021.values())
        field_nums_one_idx_2003 = list(field_dict_2003.values())
        field_nums_one_idx_1996_2002 = list(field_dict_1996_2002.values())
        field_nums_one_idx_1993_1995 = list(field_dict_1993_1995.values())
        field_nums_one_idx_1990_1992 = list(field_dict_1990_1992.values())

        #adjust for non-0 indexing in FFIEC file dictionary
        field_nums_2004_2021 = [
            int(num) - 1 for num in field_nums_one_idx_2004_2021
        ]
        field_nums_2003 = [
            int(num) - 1 for num in field_nums_one_idx_2003
        ]  
        field_nums_1996_2002 = [
            int(num) - 1 for num in field_nums_one_idx_1996_2002
        ]
        field_nums_1993_1995 = [
            int(num) - 1 for num in field_nums_one_idx_1993_1995
        ]
        field_nums_1990_1992 = [
            int(num) - 1 for num in field_nums_one_idx_1990_1992
        ]

        return_dict = {}  #for returning year keyed dataframes of census data
        for year in years:
            #set file name
            print()
            print("processing data for {year}".format(year=year))
            #data are loaded as objects to preserve integrity of geographic identifiers with leading 0s
            if int(year) >= 2012:
                print("using CSV data file")
                census_data = pd.read_csv(
                    data_path + "census_data_{year}.csv".format(year=year),
                    usecols=field_nums_2004_2021,
                    header=None,
                    dtype=object,
                    sep=","
                )  #csv is the base format after extraction, don't change this unless you really mean it

                census_data = census_data[field_nums_2004_2021]
                census_data.columns = field_names_2004_2021

            else:
                #load fixed width spec for old FFIEC census data
                #set fixed width format spec
                print("using fixed width data file")
                if int(year) >= 2006:
                    fwf_spec = pd.read_csv(
                        self.config_data["ffiec_census_2006_fwf_spec"])
                elif int(year) >= 2004:
                    fwf_spec = pd.read_csv(
                        self.config_data["ffiec_census_2004_fwf_spec"])
                elif int(year) == 2003:
                    fwf_spec = pd.read_csv(
                        self.config_data["ffiec_census_2003_fwf_spec"])
                elif int(year) >= 1997:
                    fwf_spec = pd.read_csv(
                        self.config_data["ffiec_census_1997_fwf_spec"])
                elif int(year) >= 1996:
                    fwf_spec = pd.read_csv(
                        self.config_data["ffiec_census_1996_fwf_spec"])
                elif int(year) >= 1993:
                    fwf_spec = pd.read_csv(
                        self.config_data["ffiec_census_1993_fwf_spec"])  
                else:
                    fwf_spec = pd.read_csv(
                        self.config_data["ffiec_census_1990_fwf_spec"])

                col = list(zip(fwf_spec.Starting-1, fwf_spec.Ending))
                census_data = pd.read_fwf(
                    data_path + "census_data_{year}.dat".format(year=year),
                    colspecs=col,
                    header=None,
                    dtype=object)

                if int(year) >= 2004:
                    #remove fields not in extract dictionary
                    census_data = census_data[field_nums_2004_2021]
                    #set column names
                    census_data.columns = field_names_2004_2021
                elif int(year) == 2003:
                    census_data = census_data[field_nums_2003]
                    census_data.columns = field_names_2003
                elif int(year) >= 1996:
                    census_data = census_data[field_nums_1996_2002]
                    census_data.columns = field_names_1996_2002
                elif int(year) >= 1993:
                    census_data = census_data[field_nums_1993_1995]
                    census_data.columns = field_names_1993_1995
                else:
                    census_data = census_data[field_nums_1990_1992]
                    census_data.columns = field_names_1990_1992

            if save_csv:
                census_data.to_csv(
                    self.config_data["OUT_PATH"] +
                    "census_data_extract_{year}.txt".format(year=year),
                    index=False,
                    sep="|")
                census_data.to_csv(
                    self.config_data["OUT_PATH"] +
                    "census_data_extract_{year}.csv".format(year=year),
                    index=False,
                    sep=",")
            return_dict[
                year] = census_data  #add data extract to return dictionary

        return return_dict

    def get_census_omb_delineation_file(self,
                                        years=[],
                                        sep=None,
                                        convert=True):
        """

		PARAMETERS:
		years: list of years for which to retrieve data files.
			Note: not all years have a distinct delineation file
		convert: if true, convert the file from XLS to CSV and trim unusable rows
		"""
        if len(years) < 1:
            print("no years passed in list, using config data for ALL YEARS")
            years = self.config_data["ALL_YEARS"]

        if sep is None:
            sep = self.config_data["SEP"]

        if sep == "|":
            file_ending = "txt"
        else:
            file_ending = "csv"

        for year in years:
            if int(year) < 2003:
                print()
                print(
                    "not yet configured for OMB delineation parsing prior to 2003"
                )
                return

            local_file_name = "excel_delineation_{year}.xls".format(
                year=year)  #set filename for writing to disk

            print()
            print("getting Census/OMB delineation data for {year}".format(
                year=year))

            #request data from site
            print("calling: \n {url}".format(
                url=self.config_data["msa_md_delineation"]["omb_{year}".format(
                    year=str(year))]))
            delin_resp = requests.get(
                self.config_data["msa_md_delineation"]["omb_{year}".format(
                    year=str(year))])

            print("saving data for {year} as {name}".format(
                year=year, name=local_file_name))

            with open(self.config_data["CENSUS_PATH"] + local_file_name,
                      "wb") as infile:
                infile.write(delin_resp.content)

            if convert:
                #configure Excel load based on OMB delineation year file
                sheet_name = self.config_data["omb_sheet_names"][
                    "omb_{year}".format(year=year)]
                skip_rows = self.config_data["omb_skip_rows"][
                    "omb_{year}".format(year=year)]

                #read Excel file
                data_xls = pd.read_excel(self.config_data["CENSUS_PATH"] +
                                         local_file_name,
                                         sheet_name,
                                         index_col=None)
                #save sheet as CSV
                data_xls.to_csv(self.config_data["CENSUS_PATH"] +
                                "full_omb_delin_{year}.{end}".format(
                                    year=year, end=file_ending),
                                encoding='utf-8',
                                index=False,
                                sep=sep)

                #load CSV to dataframe to extract needed columns
                census_df = pd.read_csv(self.config_data["CENSUS_PATH"] +
                                        "full_omb_delin_{year}.{end}".format(
                                            year=year, end=file_ending),
                                        skiprows=skip_rows,
                                        dtype=object,
                                        sep=sep)

                if int(year) >= 2013:
                    #create 5 digit county FIPS
                    census_df["full_county_fips"] = census_df.apply(
                        lambda x: x["FIPS State Code"] + x["FIPS County Code"],
                        axis=1)

                    #List3_2008
                else:
                    #rename county FIPS column to match other Census OMB files
                    census_df.rename(columns={"FIPS": "full_county_fips"},
                                     inplace=True)

                #get single name for each Metropolitan or Micropolitan statistical area using:
                #MD name first and CBSA title second in precedence for determining MSA/MD name
                #CSA references were removed as they are above the MSA level used for HMDA work
                #Metropolitan Division Title, CBSA Title
                census_df["MSA/MD Name"] = census_df.apply(
                    lambda x: x["CBSA Title"]
                    if pd.notnull(x["CBSA Title"]) else "",
                    axis=1)
                census_df["MSA/MD Name"] = census_df.apply(lambda x: str(x["Metropolitan Division Title"]) \
                 if (pd.notnull(x["Metropolitan Division Title"]) and str(x["Metropolitan Division Title"]).strip() != "")
                 else x["MSA/MD Name"], axis=1)

                #Remove unneeded columns
                census_df = census_df[[
                    "CBSA Code", "full_county_fips", "MSA/MD Name"
                ]]
                #write census omb names to disk
                census_df.to_csv(self.config_data["CENSUS_PATH"] +
                                 "msa_md_names_{year}.txt".format(year=year),
                                 index=False,
                                 sep="|")
                census_df.to_csv(self.config_data["CENSUS_PATH"] +
                                 "msa_md_names_{year}.csv".format(year=year),
                                 index=False,
                                 sep=",")

    def combine_omb_ffiec(self, years=[], sep=None, both=True):
        """
		
		PARAMETERS:
		years: list of years for which to combine files

		"""
        if len(years) < 1:
            years = self.config_data["ALL_YEARS"]
            print(
                "no year data passed in list, using config data for ALL YEARS")

        if sep is None:
            sep = self.config_data["SEP"]

        if sep == "|":
            file_ending = "txt"
        else:
            file_ending = "csv"

        return_dict = {
        }  #year keyed dictionary to return combined Census data files

        for year in years:
            if int(year) < 2003:
                print()
                print(
                    "not yet configured for OMB delineation parsing prior to 2003"
                )
                continue
            print()
            print("Combining FFIEC Census and OMB data for {year}".format(
                year=year))
            #load FFIEC Census File Cut
            ffiec_census_df = pd.read_csv(
                self.config_data["OUT_PATH"] +
                "census_data_extract_{year}.{end}".format(year=year,
                                                          end=file_ending),
                dtype=object,
                sep=sep,
                keep_default_na=False)
            print(ffiec_census_df.head())
            #load MSA/MD name file
            msa_md_name_df = pd.read_csv(
                self.config_data["CENSUS_PATH"] +
                "msa_md_names_{year}.{end}".format(year=year, end=file_ending),
                dtype=object,
                sep=sep,
                keep_default_na=False)

            #Create 5 digit county FIPS in FFIEC file
            ffiec_census_df["full_county_fips"] = ffiec_census_df.apply(
                lambda x: str(x.State) + str(x.County), axis=1)
            print(ffiec_census_df.head())
            if self.config_data["DEBUG"]:
                print()
                print(ffiec_census_df.columns)
                print(msa_md_name_df.columns)

            #Merge FFIEC Census data cut with MSA/MD name file to add MSA/MD names
            ffiec_census_df = ffiec_census_df.merge(msa_md_name_df,
                                                    how="left",
                                                    on="full_county_fips")

            #set columns for output
            ffiec_census_df = ffiec_census_df[
                self.config_data["OUT_COLUMNS"].keys()]

            #Write file to disk
            ffiec_census_df.to_csv(
                self.config_data["OUT_PATH"] +
                "ffiec_census_msamd_names_{year}.{end}".format(
                    year=year, end=file_ending),
                index=False,
                sep=sep)

            #map FIPS State Code to letter code in column "State" for MSA/MD description file
            ffiec_census_df["State"] = ffiec_census_df["State"].map(
                self.config_data["state_codes_rev"])

            ffiec_census_df["MSA/MD Name"] = ffiec_census_df[
                "MSA/MD Name"].apply(lambda x: str(x).strip())
            msa_md_desc_df = ffiec_census_df[
                self.config_data["msa_name_cols"]][
                    (ffiec_census_df["MSA/MD"] != "99999")
                    & (ffiec_census_df["MSA/MD Name"] != "") &
                    (ffiec_census_df["MSA/MD Name"] != "nan")].copy()

            #remove duplicates. These are the records for county and tract that need to be removed from the MSA/MD list
            msa_md_desc_df.columns = self.config_data["msa_md_desc_out_cols"]
            msa_md_desc_df.drop_duplicates(inplace=True)
            msa_md_desc_df.to_csv(self.config_data["OUT_PATH"] +
                                  "msa_md_description_{year}.{end}".format(
                                      year=year, end=file_ending),
                                  index=False,
                                  sep=sep)

            if both:
                msa_md_desc_df.to_csv(
                    self.config_data["OUT_PATH"] +
                    "msa_md_description_{year}.csv".format(year=year),
                    index=False,
                    sep=",")

            return_dict[
                year] = ffiec_census_df  #add combined census data to return dict for handoff

            if self.config_data["DEBUG"]:
                print(ffiec_census_df.head())
                print()
                print(msa_md_name_df.head())
                print()

        return return_dict
