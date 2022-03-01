import requests


def scrape(url):
    """
    Scrapes the given URL and returns the content as a string.
    """
    r = requests.get(url)
    return r.text


if __name__ == "__main__":

    berlin_url = "https://www.neubaukompass.de/neubau-immobilien/berlin-region/"

    scrape(berlin_url)