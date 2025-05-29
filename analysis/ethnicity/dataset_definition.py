
# import libraries
from ehrql import (
    create_dataset,
)
from ehrql.tables.tpp import (
  patients,
  practice_registrations, 
  clinical_events
)

#Import codelists
import codelists

# initialise dataset
dataset = create_dataset()
dataset.configure_dummy_data(population_size=1000)

index_date = "2020-01-01"

# define dataset population
dataset.define_population(
  practice_registrations.for_patient_on(index_date).exists_for_patient() &
  ((patients.date_of_death> index_date) | patients.date_of_death.is_null())
)

# Ethnicity 
# Note that enthicity is documented using codelists, not as a value-restricted categorical variable.
# If a patient moves to another practice, ethnicity codes might be transferred, but the date might not have been captured and in TPP will default to 1900-01-01
# Therefore, defining "last recorded ethnicity code relative to an index date" is not guaranteed to return what it should.
# Typically, we choose to look at the last known ethnicity recorded _across the entire record_ 
# rather than latest ethnicity known on a given index date, even though this looks into the future relative to the index date.
# The rationale is that ethnicity only rarely changes within a person and future-recorded ethnicity is likely to be a good reflection of the ethnicity as at an index date.
# This approach favours more complete ethnicity data in those who survive longer or who do not move practices (or move overseas), and therefore introduces a bias.
# Use with caution!

# For more information on ethnicity in OpenSAFELY, see https://doi.org/10.1186/s12916-024-03499-5

ethnicity = (clinical_events
  .where(clinical_events.snomedct_code.is_in(codelists.ethnicity16))
  .sort_by(clinical_events.date)
  .last_for_patient()
)

# EXAMPLE USAGE

# ethnicity using 5 groups + unknown
dataset.ethnicity5 = ethnicity.snomedct_code.to_category(codelists.ethnicity5)

# ethnicity using 16 groups + unknown
dataset.ethnicity16 = ethnicity.snomedct_code.to_category(codelists.ethnicity16)




