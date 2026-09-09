Welcome to Cerberus
===================

    ``CERBERUS``, n. The watch-dog of Hades, whose duty it was to guard the
    entrance; everybody, sooner or later, had to go there, and nobody wanted to
    carry off the entrance.
    - *Ambrose Bierce, The Devil's Dictionary*

Cerberus provides powerful yet simple and lightweight data validation
functionality out of the box and is designed to be easily extensible, allowing
for custom validation. It has no dependencies and is thoroughly.

At a Glance
-----------
You define a validation schema and pass it to an instance of the
:class:`~cerberus.Validator` class: ::

    >>> schema = {'name': {'type': 'string'}}
    >>> v = Validator(schema)

Then you simply invoke the :meth:`~cerberus.Validator.validate` to validate
a dictionary against the schema. If validation succeeds, ``True`` is returned:

::

    >>> document = {'name': 'john doe'}
    >>> v.validate(document)
    True


Table of Contents
-----------------
.. toctree::
    :maxdepth: 2

    Installation <install>
    Usage <usage>
    schemas
    validation-rules
    normalization-rules
    errors
    Extending <customize>
    Contributing <contribute>
    API <api>
    FAQ <faq>
    external_resources
    changelog
    upgrading
    authors
    contact
    license

Copyright Notice
----------------
Cerberus is an open source project by `Nicola Iarocci
<https://nicolaiarocci.com>`_. See the original `LICENSE
<https://github.com/pyeve/cerberus/blob/1.3.x/LICENSE>`_ for more
information.

.. _`Cerberus campaign on Patreon`: https://www.patreon.com/nicolaiarocci
