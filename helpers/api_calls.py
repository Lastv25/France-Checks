import time
from functools import wraps

import requests


# Simple rate limiter
def rate_limited(max_calls, period):
    """
    Decorator that limits the number of times a function can be called
    within a specified time period (in seconds).
    """
    calls = 0
    last_reset = time.time()

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal calls, last_reset
            current_time = time.time()
            elapsed = current_time - last_reset

            if elapsed > period:
                calls = 0
                last_reset = current_time

            if calls >= max_calls:
                time.sleep(1)
                calls = 0
                last_reset = current_time
            calls += 1
            # Call the original function and return its result
            return func(*args, **kwargs)

        return wrapper

    return decorator


def get_publications_from_bodacc(
    FirstName: str, LastName: str, MaxNumberHits: int = 100
) -> dict:
    if MaxNumberHits is None or MaxNumberHits <= 0:
        max_nbr_hits = 100
        offsets = [0]
        print("Wrong input value for nbr of hits so setting it to 100")
    elif MaxNumberHits > 100:
        offsets = [x for x in range(0, MaxNumberHits, 100)]
        max_nbr_hits = 100

    else:
        offsets = [0]
        max_nbr_hits = MaxNumberHits

    full_data = {}
    # since the limit field is maxed to 100 we need to use offset to get all the max_nbr_hits
    for offset in offsets:
        api_url = f"https://bodacc-datadila.opendatasoft.com/api/explore/v2.1/catalog/datasets/annonces-commerciales/records?where=search%28%22{FirstName}%22%29%20and%20search%28%22{LastName}%22%29&limit={max_nbr_hits}&offset={offset}&timezone=UTC&include_links=false&include_app_metas=false"

        response = requests.get(api_url, verify=False)
        response.raise_for_status()

        data = response.json()
        total_count = data.get("total_count")
        if offset == 0:
            full_data = data
        else:
            full_data["results"] += data["results"]
        if offset + 100 >= total_count:
            break

    return full_data


# can only be called 7 times per seconds
@rate_limited(7, 1)
def get_company_info_from_recherche_entreprise(Siren: str, limit_establishments: int = 1) -> dict:
    api_url = f"https://recherche-entreprises.api.gouv.fr/search?q={Siren}&minimal=true&limite_matching_etablissements={limit_establishments}&include=siege%2Cdirigeants%2Cfinances%2Cscore&page=1&per_page=1"

    response = requests.get(api_url, verify=False)
    response.raise_for_status()

    data = response.json()
    return data


def get_pcl_record_from_bodacc(Siren: str) -> dict:
    api_url = f"https://bodacc-datadila.opendatasoft.com/api/explore/v2.1/catalog/datasets/annonces-commerciales/records?where=search%28%22Proc%C3%A9dures%20collectives%22%29%20and%20search%28%22{Siren}%22%29&limit=100&offset=0&timezone=UTC&include_links=false&include_app_metas=false"

    response = requests.get(api_url, verify=False)
    response.raise_for_status()

    data = response.json()
    return data
