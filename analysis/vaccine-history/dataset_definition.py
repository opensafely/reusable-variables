
# import libraries
from ehrql import (
    create_dataset,
)
from ehrql.tables.tpp import (
  patients,
  practice_registrations, 
)

# import variable definitions
from vaccine_variables import *

# initialise dataset
dataset = create_dataset()
dataset.configure_dummy_data(population_size=1000)

index_date = "2022-12-31"

# define dataset population
dataset.define_population(
  practice_registrations.for_patient_on(index_date).exists_for_patient() &
  ((patients.date_of_death> index_date) | patients.date_of_death.is_null())
)

# EXAMPLE USAGE

add_vaccine_history(
    dataset = dataset, index_date = index_date, 
    target_disease = "SARS-2 Coronavirus", target_disease_short ="covid", 
    number_of_vaccines = 10
)


