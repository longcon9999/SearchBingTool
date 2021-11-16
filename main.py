from requests import exceptions
import argparse
import requests
import cv2
import os

ap = argparse.ArgumentParser()
ap.add_argument("-q", "--query", required=True, help="search query to search Bing Image API for")
ap.add_argument("-o", "--output", required=True, help="path to output directory of images")
args = vars(ap.parse_args())

if os.path.isdir(args["output"]) is False:
    os.mkdir(args["output"])

api_key = '58a234ceabc84097ab0e3f40f63c460e'
max_results = 500
group_size = 100

EXCEPTIONS = set([IOError, FileNotFoundError, exceptions.RequestException, exceptions.HTTPError, exceptions.ConnectionError, exceptions.Timeout])

search_url = "https://api.bing.microsoft.com/v7.0/images/search"

# store the search term in a convenience variable then set the
# headers and search parameters
term = args["query"]
headers = {"Ocp-Apim-Subscription-Key": api_key}
params = {"q": term, "offset": 0, "count": group_size}
# make the search
print("[INFO] searching Bing API for '{}'".format(term))
search = requests.get(search_url, headers=headers, params=params)
search.raise_for_status()
# grab the results from the search, including the total number of
# estimated results returned by the Bing API
results = search.json()
estNumResults = min(results["totalEstimatedMatches"], max_results)
print(len(results["value"]))
print("[INFO] {} total results for '{}'".format(estNumResults, term))
# initialize the total number of images downloaded thus far
total = 0
# loop over the estimated number of results in `GROUP_SIZE` groups
for offset in range(0, estNumResults, group_size):
    # update the search parameters using the current offset, then
    # make the request to fetch the results
    print("[INFO] making request for group {}-{} of {}...".format(
        offset, offset + group_size, estNumResults))
    params["offset"] = offset
    search = requests.get(search_url, headers=headers, params=params)
    search.raise_for_status()
    results = search.json()
    print("[INFO] saving images for group {}-{} of {}...".format(
        offset, offset + group_size, estNumResults))

    # loop over the results
    for v in results["value"]:
        # try to download the image
        try:
            # make a request to download the image
            print("[INFO] fetching: {}".format(v["contentUrl"]))
            r = requests.get(v["contentUrl"], timeout=30)
            # build the path to the output image
            ext = v["contentUrl"][v["contentUrl"].rfind("."):]
            if len(ext) > 4:
                ext = ext[:ext.find("?")]
            p = os.path.sep.join([args["output"], "{}{}".format(
                str(total).zfill(8), ext)])
            # write the image to disk
            f = open(p, "wb")
            f.write(r.content)
            f.close()
        # catch any errors that would not unable us to download the
        # image
        except Exception as e:
            # check to see if our exception is in our list of
            # exceptions to check for
            if type(e) in EXCEPTIONS:
                print("[INFO] skipping: {}".format(v["contentUrl"]))
                continue
        # try to load the image from disk
        image = cv2.imread(p)
        # if the image is `None` then we could not properly load the
        # image from disk (so it should be ignored)
        if image is None:
            print("[INFO] deleting: {}".format(p))
            if os.path.isdir(p):
                os.remove(p)
            continue
        # update the counter
        total += 1

