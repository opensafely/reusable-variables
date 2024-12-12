#####################################################
# Common functions for contructing clinical queries #
#####################################################

from ehrql.codes import CTV3Code, ICD10Code

from ehrql import case, days, when, years

from codelists import *

from ehrql.tables.core import (
  medications,
  patients
)

from ehrql.tables.tpp import (
  addresses,
#  opa_cost,
  clinical_events,
  practice_registrations,
# appointments,
# vaccinations
)



#####################
# Clinical functions#
#####################

# events occurring before spec date
# prior_events = clinical_events.where(clinical_events.date.is_on_or_before(index_date))

# query prior_events for existence of event-in-codelist
def has_prior_event(codelist, index_date, where=True):
    prior_events = clinical_events.where(clinical_events.date.is_on_or_before(index_date))
    return (
        prior_events
        .where(where)
        .where(prior_events.snomedct_code.is_in(codelist))
        .exists_for_patient()
    )

# query prior_events for date of most recent event-in-codelist
def last_prior_event(codelist, index_date, where=True):
    prior_events = clinical_events.where(clinical_events.date.is_on_or_before(index_date))
    return (
        prior_events.where(where)
        .where(prior_events.snomedct_code.is_in(codelist))
        .sort_by(clinical_events.date)
        .last_for_patient()
    )

# query prior_events for date of earliest event-in-codelist
def first_prior_event(codelist, index_date, where=True):
    prior_events = clinical_events.where(clinical_events.date.is_on_or_before(index_date))
    return (
        prior_events.where(where)
        .where(prior_events.snomedct_code.is_in(codelist))
        .sort_by(clinical_events.date)
        .first_for_patient()
    )

# meds occurring before spec date

# query prior_meds for existence of event-in-codelist
def has_prior_meds(codelist, index_date, where=True):
    prior_meds = medications.where(medications.date.is_on_or_before(index_date))
    return (
        prior_meds.where(where)
        .where(prior_meds.dmd_code.is_in(codelist))
        .exists_for_patient()
    )
    
# query prior meds for date of most recent med-in-codelist
def last_prior_meds(codelist, index_date, where=True):
    prior_meds = medications.where(medications.date.is_on_or_before(index_date))
    return (
        prior_meds.where(where)
        .where(prior_meds.dmd_code.is_in(codelist))
        .sort_by(medications.date)
        .last_for_patient()
    )

# query prior_events for date of earliest event-in-codelist
def first_prior_meds(codelist, index_date, where=True):
    prior_meds = medications.where(medications.date.is_on_or_before(index_date))
    return (
        prior_meds.where(where)
        .where(prior_meds.dmd_code.is_in(codelist))
        .sort_by(medications.date)
        .first_for_patient()
    )

######################
# Composed variables #
######################
# Patients with immunosuppression
def is_immunosuppressed(index_date):
    # Immunosuppression diagnosis
    immdx = has_prior_event(immdx_cov, index_date)
    # Immunosuppression medication (within the last 3 years)
    immrx_cov = has_prior_meds(
        immrx,
        index_date,
        where=medications.date.is_on_or_after(index_date - days(int(3 * 365.25)))
    )
    # Immunosuppression admin date (within the last 3 years)
    immadm_cov = has_prior_event(
        immadm,
        index_date,
        where=clinical_events.date.is_on_or_after(index_date - days(int(3 * 365.25)))
    )
    # Chemotherapy medication date (within the last 3 years)
    dxt_chemo_cov = has_prior_event(
        dxt_chemo,
        index_date,
        where=clinical_events.date.is_on_or_after(index_date - days(int(3 * 365.25)))
    )
    # Immunosuppression
    immunosupp = case(
        when(immdx.is_not_null()).then(True),
        when(immrx_cov.is_not_null()).then(True),
        when(immadm_cov.is_not_null()).then(True),
        when(dxt_chemo_cov.is_not_null()).then(True),
        otherwise=False
    )
    return immunosupp

#Patients with Chronic Kidney Disease
def has_ckd(index_date, where=True):
    # Chronic kidney disease diagnostic codes
    ckd = has_prior_event(ckd_cov, index_date)
    # Chronic kidney disease codes - all stages
    ckd15_date = last_prior_event(ckd15, index_date).date
    # Chronic kidney disease codes-stages 3 - 5
    ckd35_date = last_prior_event(ckd35, index_date).date
    # Chronic kidney disease
    ckd_def = case(
        when(ckd).then(True),
        when((ckd35_date >= ckd15_date)).then(True),
        otherwise=False
    )
    return ckd_def

#Patients with asthma

def has_asthma(index_date, where=True):
    prior_meds = medications.where(medications.date.is_on_or_before(index_date))
    #Asthma diagnosis
    astdx = has_prior_event(
        ast, 
        index_date)
    #Asthma admision
    asthadm = has_prior_event(
        astadm,
        index_date,
        where=clinical_events.date.is_on_or_between(index_date - days(730), index_date)
    )
    # Inhaled asthma prescription in previous year
    astrx_inhaled = has_prior_meds(
        astrxm1,
        index_date,
        where=medications.date.is_on_or_after(index_date - days(365)))
    # count of systemic steroid prescription inpast 2 years
    astrx_oral_count = (
        prior_meds
        .where(prior_meds.dmd_code.is_in(astrx))
        .where(prior_meds.date.is_on_or_between(index_date - days(730), index_date))
        .count_for_patient())
    # Asthma 
    asthma = case(
        when(asthadm).then(True),
        when(astdx & astrx_inhaled & (astrx_oral_count >= 2)).then(True),
        otherwise=False
    )
    return asthma

# Patients with Morbid Obesity
#Need to include that they need to be >18yo
def has_sev_obes(index_date): 
    # Last BMI stage event
    bmi_stage_event = last_prior_event(
        bmi_stage, 
        index_date
        )  
    # Last severe obesity event (after the BMI stage event, with valid numeric value)
    sev_obesity_event = last_prior_event(
        sev_obesity, 
        index_date,
        where=((clinical_events.date >= bmi_stage_event.date) & 
               (clinical_events.numeric_value != 0.0)
               )
        ) 
    # Last BMI event not 0
    bmi_event = last_prior_event(
        bmi, 
        index_date,
        where=(clinical_events.numeric_value != 0.0)
        )
    # Severe obesity
    severe_obesity = case(
        when(sev_obesity_event.date > bmi_event.date).then(True),
        when(bmi_event.numeric_value >= 40.0).then(True),
        otherwise=False
    )
    return severe_obesity


# Pregnant variable to identify gestational diabetes
def preg_group(index_date):
    # Pregnancy delivery code date
    pregAdel_date = last_prior_event(
        pregdel,
        index_date,
        where=clinical_events.date.is_on_or_between(index_date - days(7 * 65), index_date - days((7 * 30) + 1))
    ).date
    # Pregnancy:8 months and 15 months
    pregA_date = last_prior_event(
        preg,
        index_date,
        where=clinical_events.date.is_on_or_between(index_date - days(7 * 65), index_date - days((7 * 30) + 1))
    ).date
    # Pregnancy: <8 months
    pregB = has_prior_event(
        preg,
        index_date,
        where=clinical_events.date.is_on_or_between(index_date - days(7 * 30), index_date)
    )
    # Pregnancy group
    pregnancy_group = case(
        when(pregB).then(True),
        when(
            (pregAdel_date.is_not_null() & 
             pregA_date.is_not_null() & 
             pregA_date.is_on_or_after(pregAdel_date))
        ).then(True),
        otherwise=False
    )
    return pregnancy_group

#Patients with Diabetes
def has_diab(index_date, where=True):
    diab_date = last_prior_event(diab, index_date).date
    dmres_date = last_prior_event(dmres, index_date).date
    gesdiab = has_prior_event(gdiab, index_date)
    gdiab_group = gesdiab & preg_group(index_date)
    addis_cov = has_prior_event(addis, index_date)
    # Diabetes condition
    diabetes = case(
        when(dmres_date < diab_date).then(True),
        when(diab_date.is_not_null() & dmres_date.is_null()).then(True),
        when(addis_cov).then(True),
        when(gdiab_group).then(True),
        otherwise=False
    )
    return diabetes

# Severe mental illness 
def has_sev_mental(index_date, where=True):
    sev_mental_date = last_prior_event(sev_mental, index_date).date
    # Remission codes relating to Severe Mental Illness
    smhres_date = last_prior_event(smhres, index_date).date
    # Severe mental illness
    sev_mental_ill = case(
        when(smhres_date < sev_mental_date).then(True),
        when(sev_mental_date.is_not_null() & smhres_date.is_null()).then(True),
        otherwise=False
    )
    return sev_mental_ill

# At least one primis variable
def has_at_least_one_primis(index_date):
    return (
        has_prior_event(resp_cov, index_date) |  # chronic respiratory disease
        has_asthma(index_date) |                # asthma
        has_prior_event(chd_cov, index_date) |  # chronic heart disease
        has_ckd(index_date) |                   # chronic kidney disease
        has_prior_event(cld, index_date) |      # chronic liver disease
        has_prior_event(cns_cov, index_date) |  # chronic neurological disease
        has_prior_event(learndis, index_date) | # learning disability
        has_diab(index_date) |                  # diabetes
        is_immunosuppressed(index_date) |       # immunosuppression grouped
        has_prior_event(spln_cov, index_date) | # asplenia or spleen dysfunction
        has_sev_obes(index_date) |              # severe obesity
        has_sev_mental(index_date)              # severe mental illness
    )


## functions to define variables across  multiple study definitions

# demographic variables
def demographic_variables(dataset, index_date, var_name_suffix=""):
    registration = practice_registrations.for_patient_on(index_date)
    dataset.add_column(f"age{var_name_suffix}", patients.age_on(index_date))
    dataset.add_column(f"region{var_name_suffix}", registration.practice_nuts1_region_name)
    dataset.add_column(f"stp{var_name_suffix}", registration.practice_stp)
    dataset.add_column(f"imd{var_name_suffix}", addresses.for_patient_on(index_date).imd_rounded)
    dataset.add_column(f"ethn_16{var_name_suffix}", last_prior_event(ethnicity_codelist16, index_date).snomedct_code.to_category(ethnicity_codelist16))
    dataset.add_column(f"ethn_5{var_name_suffix}", last_prior_event(ethnicity_codelist5, index_date).snomedct_code.to_category(ethnicity_codelist5))

# PRIMIS variables
# Green book: 
# Clinical risk groups >16 (16/9/2024): 
#   chronic respiratory disease (include asthma), 
#   chronic heart disease and vascular disease, 
#   chronic kidney disease
#   chronic liver disease
#   chronic neurological disease (include severe learning disability)
#   diabetes mellitus  and other endocrine disorders
#   immunosupression
#   asplenia or dysfunction of the spleen
#   morbid obesity
#   severe mental illness
#   x young adults Younger adults in long-stay nursing and residential care settings
#   x pregnancy

def primis_variables(dataset, index_date, var_name_suffix=""):
    dataset.add_column(f"crd{var_name_suffix}", has_prior_event(resp_cov, index_date)) #chronic respiratory disease
    dataset.add_column(f"ast{var_name_suffix}", has_asthma(index_date)) #asthma
    dataset.add_column(f"chd{var_name_suffix}", has_prior_event(chd_cov, index_date)) #chronic heart disease
    dataset.add_column(f"ckd{var_name_suffix}", has_ckd(index_date)) #chronic kidney disease
    dataset.add_column(f"cld{var_name_suffix}", has_prior_event(cld, index_date)) # chronic liver disease
    dataset.add_column(f"cns{var_name_suffix}", has_prior_event(cns_cov, index_date)) # chronic neurological disease
    dataset.add_column(f"learndis{var_name_suffix}", has_prior_event(learndis, index_date)) # learning Disability
    dataset.add_column(f"diab{var_name_suffix}", has_diab(index_date)) #diabetes
    dataset.add_column(f"immuno{var_name_suffix}", is_immunosuppressed(index_date)) #immunosuppress grouped
    dataset.add_column(f"asplen{var_name_suffix}", has_prior_event(spln_cov, index_date)) # asplenia or dysfunction of the Spleen
    dataset.add_column(f"obes{var_name_suffix}", has_sev_obes(index_date)) #immunosuppress grouped
    dataset.add_column(f"sev_ment{var_name_suffix}", has_sev_mental(index_date)) #severe mental illness
    dataset.add_column(f"one_primis{var_name_suffix}", has_at_least_one_primis(index_date)) #at least one primis

# No:
#   younger adults in long-stay nursing and residential care settings
#   pregnancy 

    ## other cx variables of interest
def other_cx_variables(dataset, index_date, var_name_suffix=""):
    dataset.add_column(f"sol_org_trans{var_name_suffix}", has_prior_event(solid_organ_transplant, index_date)) # Organs transplant
    dataset.add_column(f"hiv{var_name_suffix}", has_prior_event(hiv_aids, index_date)) #HIV/AIDS
    dataset.add_column(f"cancer{var_name_suffix}", 
                       has_prior_event(cancer_nonhaem_snomed, index_date, where=clinical_events.date.is_after(index_date - days(int(3 * 365.25))))|
                       has_prior_event(cancer_haem_snomed, index_date, where=clinical_events.date.is_after(index_date - days(int(3 * 365.25))))
                       ) #cancer     