What is it?
===========

A quick and dirty script that gets metadata (datasets, organizations, contacts, ...) from the GBIF network and populate
a CKAN portal instance.

It's basically a simple bridge between the GBIF API and the CKAN portal API.

Limitations
===========

- For now, it only loads data about a given country, and is therefore better adapted to national portals.
- It only loads metadata and not GBIF-mediated data itself (users will have to go to the global GBIF portal)
- It destroys and recreate data in CKAN on each run (no update of existing datasets/organizations/contacts)

How to use
==========

- install requirements with pip:

    $ pip install -r requirements.txt

- copy conf.example.py to conf.py and edit it to suit your needs

- run gbif2ckan.py