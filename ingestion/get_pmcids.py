import requests
import xml.etree.ElementTree as ET
import argparse

def get_pmcids(query, limit):
    """
    Searches PubMed Central and returns a list of PMCIDs.
    """
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": "pmc",
        "term": query,
        "retmax": limit,
    }
    response = requests.get(base_url, params=params)
    response.raise_for_status()  # Raise an exception for bad status codes

    root = ET.fromstring(response.content)
    id_list = root.find("IdList")
    if id_list is None:
        return []

    pmcids = [id_tag.text for id_tag in id_list.findall("Id")]
    return pmcids

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get PMCIDs from PubMed Central.")
    parser.add_argument("--query", type=str, required=True, help="Search query")
    parser.add_argument("--limit", type=int, default=100, help="Number of PMCIDs to return")
    args = parser.parse_args()

    pmcids = get_pmcids(args.query, args.limit)
    for pmcid in pmcids:
        print(pmcid)
