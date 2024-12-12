
from ehrql import create_dataset
from ehrql.tables.tpp import patients, practice_registrations

#import function for clinical variables
from variables_function import *

#Import codelists
from codelists import *

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


# Add specific variables

# demographic variables
dataset.age= patients.age_on(index_date)
dataset.region= registered_patients.practice_nuts1_region_name
dataset.stp= registered_patients.practice_stp
dataset.imd= addresses.for_patient_on(index_date).imd_rounded
dataset.ethn_16= last_prior_event(ethnicity_codelist16, index_date).snomedct_code.to_category(ethnicity_codelist16)
dataset.ethn_5= last_prior_event(ethnicity_codelist5, index_date).snomedct_code.to_category(ethnicity_codelist5)

# PRIMIS variables:
dataset.crd= has_prior_event(resp_cov, index_date) #chronic respiratory disease
dataset.ast= has_asthma(index_date) #asthma
dataset.chd= has_prior_event(chd_cov, index_date) #chronic heart disease
dataset.ckd= has_ckd(index_date) #chronic kidney disease
dataset.cld= has_prior_event(cld, index_date) # chronic liver disease
dataset.cns= has_prior_event(cns_cov, index_date) # chronic neurological disease
dataset.learndis= has_prior_event(learndis, index_date) # learning Disability
dataset.diab= has_diab(index_date) #diabetes
dataset.immuno= is_immunosuppressed(index_date) #immunosuppress grouped
dataset.asplen= has_prior_event(spln_cov, index_date) # asplenia or dysfunction of the Spleen
dataset.obes= has_sev_obes(index_date) #immunosuppress grouped
dataset.sev_ment= has_sev_mental(index_date) #severe mental illness
dataset.one_primis= at_least_one_primis(index_date) #at least one primis

## others cx variables of interest
dataset.sol_org_trans= has_prior_event(solid_organ_transplant, index_date) # Organs transplant
dataset.hiv= has_prior_event(hiv_aids, index_date) #HIV/AIDS
dataset.cancer= has_prior_event(cancer_nonhaem_snomed, index_date, where=clinical_events.date.is_after(index_date - days(int(3 * 365.25))))|has_prior_event(cancer_haem_snomed, index_date, where=clinical_events.date.is_after(index_date - days(int(3 * 365.25))))
        