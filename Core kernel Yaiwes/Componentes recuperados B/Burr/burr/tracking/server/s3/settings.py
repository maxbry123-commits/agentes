# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import os

BURR_SERVER_ROOT = os.environ.get("BURR_SERVER_ROOT", os.path.expanduser("~/.burr_server"))
BURR_DB_FILENAME = os.environ.get("BURR_DB_FILENAME", "db.sqlite3")

DB_PATH = os.path.join(
    BURR_SERVER_ROOT,
    BURR_DB_FILENAME,
)
TORTOISE_ORM = {
    "connections": {"default": f"sqlite:///{DB_PATH}"},
    "apps": {
        "models": {
            "models": ["burr.tracking.server.s3.models", "aerich.models"],
            "default_connection": "default",
        },
    },
}
