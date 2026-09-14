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

import contextlib
import logging
from typing import Optional

import application
import fastapi
import uvicorn

from burr.core import Application

logger = logging.getLogger(__name__)

# define a global `burr_app` variable
burr_app: Optional[Application] = None


def get_burr_app() -> Application:
    """Retrieve the global Burr app."""
    if burr_app is None:
        raise RuntimeError("Burr app wasn't instantiated.")
    return burr_app


@contextlib.asynccontextmanager
async def lifespan(app: fastapi.FastAPI):
    """Instantiate the Burr application on FastAPI startup."""
    # set value for the global `burr_app` variable
    global burr_app
    burr_app = application.build_application()
    yield


app = fastapi.FastAPI(lifespan=lifespan)


@app.get("/social_media_post")
def social_media_post(youtube_url: str, burr_app: Application = fastapi.Depends(get_burr_app)):
    """Creates a completion for the chat message"""
    _, _, state = burr_app.run(halt_after=["generate_post"], inputs={"youtube_url": youtube_url})

    post = state["post"]
    return {"formatted_post": post.display(), "post": post.model_dump()}


if __name__ == "__main__":
    uvicorn.run("server:app", host="127.0.0.1", port=7443, reload=True)
