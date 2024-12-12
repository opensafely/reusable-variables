from ehrql import create_dataset
from ehrql.tables.tpp import patients, practice_registrations

#import function for clinical variables
from variables_function import *

# initialise dataset

dataset = create_dataset()

# Index date (choose a date)
index_date = "2020-03-31"
#Dummy data
dataset.configure_dummy_data(population_size=1000)

#Data set definition
registered_patients = practice_registrations.for_patient_on(index_date)
registered = registered_patients.exists_for_patient()

alive = (patients.date_of_death> index_date) | patients.date_of_death.is_null()

# define dataset poppulation
dataset.define_population(
  registered 
  & alive
)

# Add groups of variables
#Demographic
demographic_variables(dataset = dataset, index_date = index_date)

#Primis variables
primis_variables(dataset = dataset, index_date = index_date)

#Clinical variables
other_cx_variables(dataset = dataset, index_date = index_date)

