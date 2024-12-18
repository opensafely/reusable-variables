from ehrql import create_dataset
from ehrql.tables.tpp import patients, practice_registrations

# import variable definitions
from variables_function import *

#Import codelists
from codelists import *

# initialise dataset
dataset = create_dataset()

# Choose an index date
index_date = "2020-12-08"

#Dummy data
dataset.configure_dummy_data(population_size=1000)

# define dataset population
dataset.define_population(
  practice_registrations.for_patient_on(index_date).exists_for_patient() &
  ((patients.date_of_death> index_date) | patients.date_of_death.is_null())
)

# Example 1: Add specific PRIMIS variables

dataset.immunosuppressed = is_immunosuppressed(index_date) #immunosuppress grouped
dataset.ckd = has_ckd(index_date) #chronic kidney disease
dataset.crd = has_crd(index_date) # chronis respratory disease
dataset.diabetes = has_diabetes(index_date) #diabetes
dataset.cld = has_prior_event(cld, index_date) # chronic liver disease
dataset.chd = has_prior_event(chd_cov, index_date) #chronic heart disease
dataset.cns = has_prior_event(cns_cov, index_date) # chronic neurological disease
dataset.asplenia = has_prior_event(spln_cov, index_date) # asplenia or dysfunction of the Spleen
dataset.learndis = has_prior_event(learndis, index_date) # learning Disability
dataset.smi = has_smi(index_date) #severe mental illness
dataset.severe_obesity = has_severe_obesity(index_date) #immunosuppress grouped

# Example 2: add the single PRIMIS "at risk" variable

dataset.primis_atrisk = primis_atrisk(index_date) # at risk (at least one of the conditions above)

# EXAMPLE 3: alternatively, use the `primis_variables` function to add variables programmatically:

for i in range(0, 2):
  suffix = f"_{i}"
  primis_variables(dataset = dataset, index_date = index_date+years(i), var_name_suffix = suffix)

