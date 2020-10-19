# ld-tools
Linked Data Management Tools for UNBIS SKOS and MARC

manage.py is the main utility for interfacing with this set of tools and provides examples on how to accomplish things with them.

Create a new term:

`python manage.py create http://metadata.un.org/thesaurus/999999`

Update an existing term without reindexing in metadata.un.org:

`python manage.py update http://metadata.un.org/thesaurus/2000002 909877`

Update an existing term and reindex it in metadata.un.org:

`python manage.py update --reindex=True http://metadata.un.org/thesaurus/2000002 909877`

Note: Reindexing can take some time as all of the term's relationships are traversed and reindexed as well.
