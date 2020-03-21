Verydisco
=========

Verydisco is a Python library for creating HTTP APIs from JSON documents in Google's service discovery document format. It requires Python 3.7 or newer and uses the Pydantic library for generating models.


Getting started
---------------

Install Verydisco with pip:

    $ pip install https://github.com/davidwtbuxton/verydisco/archive/master.zip

Now you can use Verydisco to generate Pydantic models for resources described in a service discovery document. Let's create models for the Google Cloud Storage API service:

    $ python -m verydisco https://www.googleapis.com/discovery/v1/apis/storage/v1/rest


Tests
-----

Install nox and run tests:

    $ pip install nox
    $ nox
