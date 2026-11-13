..
   Licensed to the Apache Software Foundation (ASF) under one
   or more contributor license agreements.  See the NOTICE file
   distributed with this work for additional information
   regarding copyright ownership.  The ASF licenses this file
   to you under the Apache License, Version 2.0 (the
   "License"); you may not use this file except in compliance
   with the License.  You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing,
   software distributed under the License is distributed on an
   "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
   KIND, either express or implied.  See the License for the
   specific language governing permissions and limitations
   under the License.


------------------------
Monitoring in Production
------------------------

Burr's telemetry UI is meant both for debugging and running in production. It can consume `OpenTelemetry traces <https://burr.apache.org/reference/integrations/opentelemetry/>`_,
and has a suite of useful capabilities for debugging Burr applications.

It has two (current) implementations:

1. `Local (filesystem) tracking <https://burr.apache.org/concepts/tracking/>`_ (default, for debugging or lower-scale production use-cases with a distributed file-system)
2. `S3-based tracking <https://github.com/apache/burr/blob/main/burr/tracking/server/s3/README.md>`_ (meant for production use-cases)

Which each come with an implementation of data storage on the server.

To deploy these in production, you can follow the following examples:

1. `Burr + FastAPI + docker <https://github.com/mdrideout/burr-fastapi-docker-compose>`_ by `Matthew Rideout <https://github.com/mdrideout>`_. This contains a sample API + UI + tracking server all bundled in one!
2. `Docker compose + nginx proxy <https://github.com/apache/burr/tree/main/examples/email-assistant#running-the-ui-with-email-server-backend-in-a-docker-container>`_ by `Aditha Kaushik <https://github.com/97k>`_ for the email assistant example, demonstrates running the docker image with the tracking server.

We also have a few issues to document deploying Burr's monitoring system in production:

- `deploy on AWS <https://github.com/apache/burr/issues/391>`_
- `deploy on GCP <https://github.com/apache/burr/issues/392>`_
- `deploy on Azure <https://github.com/apache/burr/issues/393>`_
