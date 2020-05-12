import genologics
import requests_cache
from genologics.lims_utils import lims
import logging

logging.basicConfig(level=logging.INFO)


# NOTE: You must remove the cache file to get fresh data!
requests_cache.install_cache()

samples = lims.get_samples(projectname="Covid19")
limit = None
all_udfs = set()
reported = dict()

for ix, s in enumerate(samples):
    if ix % 100 == 0:
        logging.info("Processing #{}".format(ix))
    if limit and ix >= limit:
        break
    reported[s.id] = (s.name, s.udf._lookup)
    all_udfs.update(s.udf._lookup.keys())

all_udfs = list(sorted(all_udfs))

# Print headers:
print('LimsId,Name,' + ','.join(all_udfs))


def csvify(val):
    try:
        return val.replace(",", "<comma>")
    except AttributeError:
        return str(val)

for limsid, name_and_udfs in reported.items():
    name, udfs = name_and_udfs
    vals = [udfs.get(key, "") for key in all_udfs]
    vals = [csvify(val) for val in vals]
    print(",".join([limsid, name]) + "," + ",".join(vals))

