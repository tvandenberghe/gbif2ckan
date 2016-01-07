What is it?
===========

A quick and dirty script that gets metadata (datasets, organizations, contacts, ...) from the GBIF network and populate
a CKAN portal instance.

It's basically a simple bridge between the GBIF API and the CKAN portal API.

For now, it only loads data about a given country, and is therefore better adapted to natial portals.

How to use
==========

- install requirements with pip:

    $ pip install -r requirements.txt

- copy conf.example.py to conf.py and edit it to suit your needs

- run gbif2ckan.py