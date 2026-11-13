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

import re

import lancedb
import requests
from bs4 import BeautifulSoup
from lancedb.embeddings import get_registry
from lancedb.pydantic import LanceModel, Vector

embedding_model = get_registry().get("openai").create()


class TextDocument(LanceModel):
    """Simple data structure to hold a piece of text associated with a url."""

    url: str
    position: int
    text: str = embedding_model.SourceField()
    vector: Vector(dim=embedding_model.ndims()) = embedding_model.VectorField()


def html_content(blog_post_url: str) -> str:
    return requests.get(blog_post_url).text


def parsed_text(html_content: str) -> str:
    soup = BeautifulSoup(html_content, "html.parser")
    return soup.get_text(separator=" ", strip=True)


def sentences(parsed_text: str) -> list[str]:
    return [sentence.strip() for sentence in re.split(r"[.!?]+", parsed_text) if sentence.strip()]


def overlapping_chunks(
    sentences: list[str], window: int = 5, stride: int = 3, min_window_size: int = 2
) -> list[str]:
    overlapping_chunks = []
    n_chunks = len(sentences)
    for start_i in range(0, n_chunks, stride):
        if (start_i + window <= n_chunks) or (n_chunks - start_i >= min_window_size):
            overlapping_chunks.append(
                " ".join(sentences[start_i : min(start_i + window, n_chunks)])
            )
    return overlapping_chunks


def embed_chunks(overlapping_chunks: list[str], blog_post_url: str) -> dict:
    # embed and store the chunks using LanceDB
    con = lancedb.connect("./blogs")
    table = con.create_table("chunks", exist_ok=True, schema=TextDocument)
    table.add(
        [{"text": c, "url": blog_post_url, "position": i} for i, c in enumerate(overlapping_chunks)]
    )
    return {"n_chunks_embedded": len(overlapping_chunks)}
