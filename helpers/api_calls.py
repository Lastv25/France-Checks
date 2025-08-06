import requests


def get_publications_from_bodacc(
    FirstName: str, LastName: str, MaxNumberHits: int = 100
) -> dict:
    if MaxNumberHits is None or MaxNumberHits <= 0:
        max_nbr_hits = 100
        print("Wrong input value for nbr of hits so setting it to 100")
    else:
        max_nbr_hits = MaxNumberHits
    api_url = f"https://bodacc-datadila.opendatasoft.com/api/explore/v2.1/catalog/datasets/annonces-commerciales/records?where=search%28%22{FirstName}%22%29%20and%20search%28%22{LastName}%22%29&limit={max_nbr_hits}&offset=0&timezone=UTC&include_links=false&include_app_metas=false"

    response = requests.get(api_url, verify=False)
    response.raise_for_status()

    data = response.json()
    return data


def get_company_info_from_recherche_entreprise(Siren: str) -> dict:
    api_url = f"https://recherche-entreprises.api.gouv.fr/search?q={Siren}&minimal=true&limite_matching_etablissements=1&include=siege%2Cdirigeants%2Cfinances%2Cscore&page=1&per_page=1"

    response = requests.get(api_url, verify=False)
    response.raise_for_status()

    data = response.json()
    return data
