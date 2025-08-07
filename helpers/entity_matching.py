from thefuzz.fuzz import ratio


def compare_names(reference_name, input_name):
    return ratio(reference_name, input_name)


def compute_name_similarity_score(ReferenceEntity, InputEntity):
    """
    returns a score from 0 to 100 where 100 is exact match
    """
    input_full_name = ""
    last_name = InputEntity.nom
    if last_name is not None:
        last_name = last_name.replace(" ", "")
        input_full_name += last_name
    first_names = InputEntity.prenoms
    if first_names is not None:
        first_names = first_names.replace(" ", "")
        input_full_name += first_names
    if len(input_full_name) > 0:
        match_ratio = compare_names(
            ReferenceEntity.nom + ReferenceEntity.prenoms, input_full_name
        )
        return match_ratio
    return 0


def compute_date_similarity_score(ReferenceEntity, InputEntity):
    """
    returns a value between 0 and 200 where 200 is a perfect match
    """
    if InputEntity.date_de_naissance is None or len(InputEntity.date_de_naissance) == 0:
        return 0

    if (
        ReferenceEntity.date_de_naissance is None
        or len(ReferenceEntity.date_de_naissance) == 0
    ):
        return 0
    # this only works because date_de_naissance is formatted like YYYY-mm
    input_month = int(InputEntity.date_de_naissance.split("-")[1])
    input_year = int(InputEntity.date_de_naissance.split("-")[0])

    ref_month = int(ReferenceEntity.date_de_naissance.split("-")[1])
    ref_year = int(ReferenceEntity.date_de_naissance.split("-")[0])

    delta_months = abs(ref_month - input_month)
    delta_year = abs(ref_year - input_year)

    score_months = (1 - delta_months // 11.0) * 100
    if delta_year == 0:
        score_years = 100
    elif delta_year == 1:
        score_years = 50
    else:
        score_years = 0

    # this sum should be weighted
    return score_years + score_months


def compute_nationality_similarity_score(ReferenceEntity, InputEntity):
    if InputEntity.nationalite is None:
        return 0
    if ReferenceEntity.date_de_naissance is None:
        return 0
    match_ratio = compare_names(ReferenceEntity.nationalite, InputEntity.nationalite)
    return match_ratio
