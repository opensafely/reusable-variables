# Import code building blocks from ehrql package
from ehrql import codelist_from_csv

#######################################################
# ethnicity
#######################################################

ethnicity5 = codelist_from_csv(
  "codelists/opensafely-ethnicity-snomed-0removed.csv",
  column="code",
  category_column="Label_6", # it's 6 because there is an additional "6 - Not stated" category, but this is not represented in SNOMED, instead corresponding to no ethnicity code
)

ethnicity16 = codelist_from_csv(
  "codelists/opensafely-ethnicity-snomed-0removed.csv",
  column="code",
  category_column="Label_16",
)
