BEL Enrichment |build|
======================
A package for generating curation sheets for rationally enriching a BEL graph.

If you find ``bel_enrichment`` useful in your work, please consider citing [1]_:

.. [1] Hoyt, C. T., *et al* (2019). `Re-curation and Rational Enrichment of Knowledge Graphs in
       Biological Expression Language <https://doi.org/10.1093/database/baz068>`_. *Database*, Volume 2019, 2019, baz068.

Additionally, this package also heavily builds on INDRA [2]_ and PyBEL [3]_.

Installation |pypi_version| |python_versions| |pypi_license|
------------------------------------------------------------
``bel_enrichment`` can be installed from PyPI with the following command:

.. code-block:: bash

   $ pip install bel_enrichment

The latest version can be installed from GitHub with:

.. code-block:: bash

   $ pip install git+https://github.com/bel-enrichment/bel-enrichment.git

You'll need to set the `INDRA_DB_REST_URL` and `INDRA_DB_REST_API_KEY`
in the `~/.config/indra/config.ini` file. Please contact the INDRA team
for credentials.

Rational Enrichment
-------------------
Generate a folder full of curation sheets based on the given BEL graph that has been pre-compiled by PyBEL.
Use ``--info-cutoff`` to specify the minimum information density cutoff. 1.0 means that the node has no edges, .5 means
one edge, and so on. Use ``--belief-cutoff`` to specify the minimum belief score from INDRA for adding the statement
to the sheet. Higher belief means the more chance a statement is already right.

.. code-block:: bash

   $ bel-enrichment from-graph zhang2011.bel --directory ~/Desktop/zhang-enrichment

Generate a ranking for genes based on the information content in a given BEL graph that has been pre-compiled by PyBEL.

.. code-block:: bash

   $ bel-enrichment ranks zhang2011.bel

Document-Based Curation
-----------------------
If you want to make a curation sheet based on a PubMed identifier (or list of them) do this:

.. code-block:: bash

   $ bel-enrichment from-pmids 20585587 20585588 > ~/Desktop/document_based.tsv

Topic-Based Curation
--------------------
If you want to make a curation sheet based on an entity, do this:

.. code-block:: bash

   $ bel-enrichment from-agents MAPT GSK3B > ~/Desktop/topic_based.tsv

References
----------
.. [2] Gyori, B. M., *et al.* (2017). `From word models to executable models of signaling networks using automated
       assembly <https://doi.org/10.15252/msb.20177651>`_. Molecular Systems Biology, 13(11), 954.
.. [3] Hoyt, C. T., Konotopez, A., Ebeling, C., (2017). `PyBEL: a computational framework for Biological Expression
       Language <https://doi.org/10.1093/bioinformatics/btx660>`_. Bioinformatics (Oxford, England), 34(4), 703–704.

.. |build| image:: https://travis-ci.com/bel-enrichment/bel-enrichment.svg?branch=master
    :target: https://travis-ci.com/bel-enrichment/bel-enrichment

.. |python_versions| image:: https://img.shields.io/pypi/pyversions/bel_enrichment.svg
    :alt: Stable Supported Python Versions

.. |pypi_version| image:: https://img.shields.io/pypi/v/bel_enrichment.svg
    :alt: Current version on PyPI

.. |pypi_license| image:: https://img.shields.io/pypi/l/bel_enrichment.svg
    :alt: License
