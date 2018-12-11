BEL Enrichment
==============
A package for generating curation sheets for rationally enriching a BEL graph using INDRA [1]_ and PyBEL [2]_.

Installation
------------
``bel_enrichment`` can be installed from directly GitHub with the following command:

.. code-block:: bash

   $ pip install git+https://github.com/cthoyt/bel-enrichment.git

Usage
-----
Generate a folder full of curation sheets based on the given BEL graph that has been pre-compiled by PyBEL.
Use ``--info-cutoff`` to specify the minimum information density cutoff. 1.0 means that the node has no edges, .5 means
one edge, and so on. Use ``--belief-cutoff`` to specify the minimum belief score from INDRA for adding the statement
to the sheet. Higher belief means the more chance a statement is already right.

.. code-block:: bash

   $ bel-enrichment make_sheet zhang2011.bel --directory ~/Desktop/zhang-enrichment

Generate a ranking for genes based on the information content in a given BEL graph that has been pre-compiled by PyBEL.

.. code-block:: bash

   $ bel-enrichment ranks zhang2011.bel

References
----------
.. [1] Gyori, B. M., *et al.* (2017). `From word models to executable models of signaling networks using automated
       assembly <https://doi.org/10.15252/msb.20177651>`_. Molecular Systems Biology, 13(11), 954.
.. [2] Hoyt, C. T., Konotopez, A., Ebeling, C., (2017). `PyBEL: a computational framework for Biological Expression
       Language <https://doi.org/10.1093/bioinformatics/btx660>`_. Bioinformatics (Oxford, England), 34(4), 703–704.
