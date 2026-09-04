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

# Dockerfile for Email Assistant
# This container sets up a Python environment for running the Email Assistant server
# along with the Burr UI. It exposes ports 7241 and 7242 for the UI and API respectively.

FROM python:3.11-bookworm

# Set the working directory in the container
WORKDIR /app

# Install any needed packages specified in requirements.txt
# Assuming you have a requirements.txt file with all the necessary dependencies
COPY requirements.txt /app/
RUN pip install -r requirements.txt

# Copy the current directory contents into the container at /app
COPY server.py /app
COPY wrapper.sh /app

# Make port 7241 and 7242 available to the world outside this container
EXPOSE 7241 7242

# Make the wrapper script executable
RUN chmod +x wrapper.sh

# Run wrapper.sh when the container launches
CMD ["./wrapper.sh"]
