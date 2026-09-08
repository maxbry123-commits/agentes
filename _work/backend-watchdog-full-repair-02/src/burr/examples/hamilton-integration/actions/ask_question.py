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

import lancedb
import openai


def relevant_chunks(user_query: str) -> list[dict]:
    chunks_table = lancedb.connect("./blogs").open_table("chunks")
    search_results = (
        chunks_table.search(user_query).select(["text", "url", "position"]).limit(3).to_list()
    )
    return search_results


def system_prompt(relevant_chunks: list[dict]) -> str:
    relevant_content = "\n".join([c["text"] for c in relevant_chunks])
    return (
        "Answer the user's questions based on the provided blog post content. "
        "Answer in a concise and helpful manner, and tell the user "
        "if you don't know the answer or you're unsure.\n\n"
        f"BLOG CONTENT:\n{relevant_content}"
    )


def llm_answer(system_prompt: str, user_query: str) -> str:
    client = openai.OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query},
        ],
    )
    return response.choices[0].message.content
