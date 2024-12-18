# This function extracts vaccination history (dates and products) up to a given date

# vaccination target diseases are here: 
# https://jobs.opensafely.org/opensafely-internal/tpp-database-categorical-columns/outputs/99/output/results_tpp.csv

# vaccination product names are here: 
# https://reports.opensafely.org/reports/opensafely-tpp-vaccination-names/



#####################################################
# Import relevant functions and scripts
#####################################################

from ehrql.tables.tpp import (
  vaccinations
)

#####################################################
# Define function to extract vaccine history
#####################################################


def add_vaccine_history(dataset, index_date, target_disease, target_disease_short, number_of_vaccines = 10):

    # select all vaccination events that target {target_disease} on or before {index_date}
    covid_vaccinations = (
        vaccinations
        .where(vaccinations.target_disease == target_disease)
        .where(vaccinations.date <= index_date)
        .sort_by(vaccinations.date)
    )
        
    # Arbitrary date guaranteed to be before any vaccination events of interest
    previous_vax_date = "1899-01-01"

    # loop over first, second, ..., nth vaccination event for each person
    # extract info on vaccination date and type
    for i in range(1, number_of_vaccines + 1):

        # vaccine variables
        current_vax = covid_vaccinations.where(covid_vaccinations.date>previous_vax_date).first_for_patient()
        dataset.add_column(f"vax_{target_disease_short}_{i}_date", current_vax.date)
        dataset.add_column(f"vax_{target_disease_short}_{i}_type", current_vax.product_name)
        
        previous_vax_date = current_vax.date

