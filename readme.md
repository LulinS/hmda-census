## HMDA Census Geographic and Demographic Data 

## Table of Contents
- [Repository Purpose and Scope]()
- [Sources of Data]()
- [Uses of Data]()

## Repository Purpose
- Provide an ETL for geographic and Census data used by the HMDA Platform
- Check to ensure the accuracy of Census data in the HMDA Platform

## Sources of Data
The Office of Management and Budget produces annual updates to MSA data. These updates can include changes to an MSA's boundaries or creation of new MSAs. These data have no regular publication cycle. 
- [OMB Publications on MSA](https://www.census.gov/programs-surveys/metro-micro/about/omb-bulletins.html)

HMDA uses the MSA definitions in effect on 12/31 of the year preceding collection. This is the date used to check all filing criteria that determines if an institution is required to report HMDA data.

The FFIEC Census Flat File contains a mapping of MSA data to tract and demographic data used by the FFIEC. This file is produced annually and is the primary source of the geographic and demographic data used by the HMDA Platform.
- The [FFIEC Census Flat File](https://www.ffiec.gov/censusapp.htm) is produced by annually the FRB on behalf of the FFIEC  
*Note: the Census Flat File is indexed starting at 1*

The Census reference files contain MSA/MD, micropolitan statistical area definitions, names, and maps to county and tract codes.
- [Census Publications on MSA](https://www.census.gov/geographies/reference-files/time-series/demo/metro-micro/delineation-files.html)

**Needed**
A list of small counties identified by FIPs code. This is used to check whether filers can claim an exemption from certain geographic reporting.

## Uses of Data
The HMDA Platform uses data during data submission and publication. 

During submission Census data are used to verify the relationship between reported geographic identifiers for loans and applications.  

In publication the Census demographic and geographic data are used to add demographic information to LAR datasets. 
The variables added include:
- Total Population   
- Minority Population Percentage   
- FFIEC Median Family Income  
- Tract to MSA/MD Income Percentage  
- Number of Owner Occupied Units  
- Number of 1 to 4 Family Units   
- MSA (new in 2018, was previously submitted by FIs)

Census geographic data are used to map MSAs to county and tract areas in the Aggregate and Disclosure reports and for geographic lookup features in HMDA data tools web interfaces. 

**HMDA Publication Products**
- [Aggregate Reports](https://ffiec.cfpb.gov/data-publication/aggregate-reports): contain MSA level data on application and lending activity for all institutions reporting HMDA data.
- [Disclosure Reports](https://ffiec.cfpb.gov/data-publication/disclosure-reports): contain MSA level data on application and lending activity for a single institution.
- [LAR snapshot publication](https://ffiec.cfpb.gov/data-publication/snapshot-national-loan-level-dataset): contains the entire dataset of loans and applications submitted in accordance with Regulation C.

## HMDA Platform Census Files
- [Base resource folder](https://raw.githubusercontent.com/cfpb/hmda-platform/v2.10.5/common/src/main/resources/)
- [Raw v2 2018 MSA data](https://raw.githubusercontent.com/cfpb/hmda-platform/v2.10.5/common/src/main/resources/census_2018_MSAMD_name.txt)






