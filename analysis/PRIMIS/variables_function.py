# This study definition defines implements the PRIMIS specification for identifying those considered to be
# "clinically vulnerable" or "clinically extremely vulnerable".
# PRIMIS are the company responsible for creating clinical codelists and algorithms to define those eligible for COVID-19 vaccination
# as advised by The Joint Committee for Vaccination and Immunisation (JCVI) and published in Chapter 14a of the Green Book.
# The variables below are an implementation of these definitions in ehrQL. 
# The current specification is based on version XXXXXX


# Green book: 
# https://www.gov.uk/government/publications/covid-19-the-green-book-chapter-14a
# Clinical risk groups aged >16 years (16/9/2024): 
#   chronic respiratory disease (include asthma), 
#   chronic heart disease and vascular disease, 
#   chronic kidney disease
#   chronic liver disease
#   chronic neurological disease (include severe learning disability)
#   diabetes mellitus and other endocrine disorders
#   immunosupression
#   asplenia or dysfunction of the spleen
#   morbid obesity
#   severe mental illness
#   x young adults Younger adults in long-stay nursing and residential care settings
#   x pregnancy


#####################################################
# Import relevant functions and scripts
#####################################################

from ehrql import case, when, days, years

import codelists

from ehrql.tables.core import (
  medications,
  patients
)

from ehrql.tables.tpp import (
  clinical_events,
)


#####################################################
# Common functions for contructing clinical queries 
#####################################################

# events occurring before a specified date

# query prior_events for existence of event-in-codelist, returns a patientSeries
def has_prior_event(codelist, index_date, where=True):
    prior_events = clinical_events.where(clinical_events.date.is_on_or_before(index_date))
    return (
        prior_events
        .where(where)
        .where(prior_events.snomedct_code.is_in(codelist))
        .exists_for_patient()
    )

# query prior_events for date of most recent event-in-codelist, returns a patientFrame
def last_prior_event(codelist, index_date, where=True):
    prior_events = clinical_events.where(clinical_events.date.is_on_or_before(index_date))
    return (
        prior_events.where(where)
        .where(prior_events.snomedct_code.is_in(codelist))
        .sort_by(clinical_events.date)
        .last_for_patient()
    )

# meds occurring before a specified date

# query prior_meds for existence of event-in-codelist, returns a patientSeries
def has_prior_meds(codelist, index_date, where=True):
    prior_meds = medications.where(medications.date.is_on_or_before(index_date))
    return (
        prior_meds.where(where)
        .where(prior_meds.dmd_code.is_in(codelist))
        .exists_for_patient()
    )
    
# query prior meds for date of most recent med-in-codelist, returns a patientFrame
def last_prior_meds(codelist, index_date, where=True):
    prior_meds = medications.where(medications.date.is_on_or_before(index_date))
    return (
        prior_meds.where(where)
        .where(prior_meds.dmd_code.is_in(codelist))
        .sort_by(medications.date)
        .last_for_patient()
    )


#######################################################
# PRIMIS
#######################################################

# Asthma
def has_asthma(index_date):
    # Asthma diagnosis
    has_astdx = has_prior_event(codelists.ast, index_date)
    # Asthma admision
    has_astadm = has_prior_event(
        codelists.astadm,
        index_date,
        where = clinical_events.date.is_on_or_between(index_date - years(2), index_date)
    )
    # Inhaled asthma prescription in previous year
    has_astrx_inhaled = has_prior_meds(
        codelists.astrxm1,
        index_date,
        where = medications.date.is_on_or_after(index_date - years(1))
    )
    # count of systemic steroid prescription inpast 2 years
    prior_meds = medications.where(medications.date.is_on_or_before(index_date))
    count_astrx_oral = (
        prior_meds
        .where(prior_meds.dmd_code.is_in(codelists.astrxm2))
        .where(prior_meds.date.is_on_or_between(index_date - years(2), index_date))
        .count_for_patient()
    )
    # Asthma 
    asthma = case(
        when(has_astadm).then(True),
        when(has_astdx & has_astrx_inhaled & (count_astrx_oral >= 2)).then(True),
        otherwise=False
    )
    return asthma

# Chronic Kidney Disease (CKD)
def has_ckd(index_date):
    # Chronic kidney disease diagnostic codes
    has_ckd_cov = has_prior_event(codelists.ckd_cov, index_date)
    # Chronic kidney disease codes - all stages
    ckd15_date = last_prior_event(codelists.ckd15, index_date).date
    # Chronic kidney disease codes-stages 3 - 5
    ckd35_date = last_prior_event(codelists.ckd35, index_date).date
    # Chronic kidney disease
    ckd = case(
        when(has_ckd_cov).then(True),
        when(ckd15_date.is_null()).then(False),
        when((ckd35_date >= ckd15_date)).then(True),
        otherwise=False
    )
    return ckd

# Chronic Respiratory Disease (CRD)
def has_crd(index_date, where=True):
    has_resp_cov = has_prior_event(codelists.resp_cov, index_date)
    has_crd = has_resp_cov | has_asthma(index_date)
    return has_crd

# Severe Obesity
def has_severe_obesity(index_date): 
    # Severe obesity only defined for people aged 18 and over
    aged18plus = patients.age_on(index_date) >= 18
    # Last BMI stage event
    date_bmi_stage = last_prior_event(
        codelists.bmi_stage, 
        index_date
    ).date
    # Last severe obesity event
    date_sev_obesity = last_prior_event(
        codelists.sev_obesity, 
        index_date
    ).date
    # Last BMI event not null
    event_bmi = last_prior_event(
        codelists.bmi, 
        index_date,
        where=(
            clinical_events.numeric_value.is_not_null() & 
            # Ignore out-of-range values
            (clinical_events.numeric_value > 4) & 
            (clinical_events.numeric_value < 200)
        )
    )
    # Severe obesity
    severe_obesity = case(
        when(aged18plus).then(False),
        when(
            (date_sev_obesity > event_bmi.date) | 
            (date_sev_obesity.is_not_null() & event_bmi.date.is_null())
        ).then(True),
        when(
            (event_bmi.date >= date_bmi_stage) & 
            (event_bmi.numeric_value >= 40.0)
        ).then(True),
        when(
            (date_bmi_stage.is_null()) & 
            (event_bmi.numeric_value >= 40.0)
        ).then(True),
        otherwise=False
    )
    return severe_obesity

# Pregnant variable to identify gestational diabetes
def has_pregnancy(index_date):
    # Pregnancy delivery code date (a delivery code between 8 and 15 months prior to index date)
    pregAdel_date = last_prior_event(
        codelists.pregdel,
        index_date,
        where=clinical_events.date.is_on_or_between(index_date - days(7 * 65), index_date - days((7 * 30) + 1))
    ).date
    # Pregnancy: 8 months and 15 months (a pregnancy code between 8 and 15 months prior to index date)
    pregA_date = last_prior_event(
        codelists.preg,
        index_date,
        where=clinical_events.date.is_on_or_between(index_date - days(7 * 65), index_date - days((7 * 30) + 1))
    ).date
    # Pregnancy: <8 months (a pregnancy code within 8 months prior to index date)
    pregB = has_prior_event(
        codelists.preg,
        index_date,
        where=clinical_events.date.is_on_or_between(index_date - days(7 * 30), index_date)
    )
    # Pregnancy group
    has_pregnancy = case(
        when(pregB).then(True),
        when(
            pregAdel_date.is_not_null() & 
             pregA_date.is_not_null() & 
             (pregA_date > pregAdel_date)
        ).then(True),
        otherwise=False
    )
    return has_pregnancy

# Diabetes
def has_diabetes(index_date, where=True):
    date_diab = last_prior_event(codelists.diab, index_date).date
    date_dmres = last_prior_event(codelists.dmres, index_date).date
    has_gdiab = has_prior_event(codelists.gdiab, index_date)
    has_diab_group = has_gdiab & has_pregnancy(index_date)
    has_addis = has_prior_event(codelists.addis, index_date)
    # Diabetes condition
    diabetes = case(
        when(date_dmres < date_diab).then(True),
        when(date_diab.is_not_null() & date_dmres.is_null()).then(True),
        when(has_addis).then(True),
        when(has_diab_group).then(True),
        otherwise=False
    )
    return diabetes

# Immunosuppression
def is_immunosuppressed(index_date):
    # Immunosuppression diagnosis
    has_immdx_cov = has_prior_event(
        codelists.immdx_cov, 
        index_date
    )
    # Immunosuppression medication (within the last 3 years)
    has_immrx = has_prior_meds(
        codelists.immrx,
        index_date,
        where=medications.date.is_on_or_after(index_date - years(3))
    )
    # Immunosuppression admin date (within the last 3 years)
    has_immadm = has_prior_event(
        codelists.immadm,
        index_date,
        where=clinical_events.date.is_on_or_after(index_date - years(3))
    )
    # Chemotherapy medication date (within the last 3 years)
    has_dxt_chemo = has_prior_event(
        codelists.dxt_chemo,
        index_date,
        where=clinical_events.date.is_on_or_after(index_date - years(3))
    )
    # Immunosuppression
    immunosupp = case(
        when(has_immdx_cov).then(True),
        when(has_immrx).then(True),
        when(has_immadm).then(True),
        when(has_dxt_chemo).then(True),
        otherwise=False
    )
    return immunosupp

# Severe mental illness 
def has_smi(index_date, where=True):
    date_sev_mental = last_prior_event(codelists.sev_mental, index_date).date
    # Remission codes relating to Severe Mental Illness
    date_smhres = last_prior_event(codelists.smhres, index_date).date
    # Severe mental illness
    smi = case(
        when(date_smhres < date_sev_mental).then(True),
        when(date_sev_mental.is_not_null() & date_smhres.is_null()).then(True),
        otherwise=False
    )
    return smi

# At risk group
def primis_atrisk(index_date):

    # This definition excludes the following groups:
    #   younger adults in long-stay nursing and residential care settings
    #   pregnancy

    return (
        is_immunosuppressed(index_date) |       # immunosuppression grouped
        has_ckd(index_date) |                   # chronic kidney disease
        has_crd(index_date) |                   # chronic respiratory disease
        has_diabetes(index_date) |              # diabetes        
        has_prior_event(codelists.cld, index_date) |      # chronic liver disease
        has_prior_event(codelists.cns_cov, index_date) |  # chronic neurological disease
        has_prior_event(codelists.chd_cov, index_date) |  # chronic heart disease
        has_prior_event(codelists.spln_cov, index_date) | # asplenia or spleen dysfunction
        has_prior_event(codelists.learndis, index_date) | # learning disability
        has_smi(index_date) |                   # severe mental illness
        has_severe_obesity(index_date)          # severe obesity
    )

## function to define variables across multiple dataset definitions
def primis_variables(dataset, index_date, var_name_suffix=""):
    dataset.add_column(f"immunosuppressed{var_name_suffix}", is_immunosuppressed(index_date)) #immunosuppress grouped
    dataset.add_column(f"ckd{var_name_suffix}", has_ckd(index_date)) #chronic kidney disease
    dataset.add_column(f"crd{var_name_suffix}", has_prior_event(codelists.resp_cov, index_date)) #chronic respiratory disease
    dataset.add_column(f"diabetes{var_name_suffix}", has_diabetes(index_date)) #diabetes
    dataset.add_column(f"cld{var_name_suffix}", has_prior_event(codelists.cld, index_date)) # chronic liver disease
    dataset.add_column(f"chd{var_name_suffix}", has_prior_event(codelists.chd_cov, index_date)) #chronic heart disease
    dataset.add_column(f"cns{var_name_suffix}", has_prior_event(codelists.cns_cov, index_date)) # chronic neurological disease
    dataset.add_column(f"asplenia{var_name_suffix}", has_prior_event(codelists.spln_cov, index_date)) # asplenia or dysfunction of the Spleen
    dataset.add_column(f"learndis{var_name_suffix}", has_prior_event(codelists.learndis, index_date)) # learning Disability
    dataset.add_column(f"smi{var_name_suffix}", has_smi(index_date)) #severe mental illness
    dataset.add_column(f"severe_obesity{var_name_suffix}", has_severe_obesity(index_date)) # severe obesity
    dataset.add_column(f"primis_atrisk{var_name_suffix}", primis_atrisk(index_date)) # at risk 
