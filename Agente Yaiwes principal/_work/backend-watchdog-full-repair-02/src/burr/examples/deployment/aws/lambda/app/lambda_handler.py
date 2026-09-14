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

from . import counter_app


def lambda_handler(event, context):
    count_up_to = int(event["body"]["number"])

    app = counter_app.application(count_up_to)
    action, result, state = app.run(halt_after=["result"])

    return {"statusCode": 200, "body": state.serialize()}


if __name__ == "__main__":
    print(lambda_handler({"body": {"number": 10}}, None))
