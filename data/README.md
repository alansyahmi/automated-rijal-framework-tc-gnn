# Data Management

## Directory policy

- `raw/`: immutable source snapshots where storage and licence terms permit.
- `temporaries/`: intermediate extracts and transformations.
- `processed/`: versioned, analysis-ready datasets.
- `documentation/`: schemas, data dictionaries, provenance, validation reports, and dataset cards.

Do not commit large external corpora or restricted source material without checking the licence and repository visibility implications. Use documented download scripts or stable source identifiers where redistribution is not permitted.

## Required documentation for every dataset version

- dataset identifier and version;
- source work(s), edition(s), and acquisition date;
- licence and permitted use;
- extraction and transformation code/version;
- inclusion and exclusion criteria;
- schema and data dictionary;
- record counts before and after each transformation;
- duplicate handling;
- missingness and unresolved identity statistics;
- validation sample and findings;
- known limitations.

## Raw-data immutability

Never overwrite raw data to correct, normalise, or filter it. Create a new derived version and record the transformation. Keep checksums for source files when feasible.

## Sensitive and secret material

Never commit access tokens, passwords, private keys, personal credentials, or unrelated personal data. Use environment variables and local secret files excluded by `.gitignore`.
