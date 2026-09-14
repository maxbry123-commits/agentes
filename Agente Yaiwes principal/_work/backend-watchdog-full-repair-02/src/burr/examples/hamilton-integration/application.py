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

from hamilton.driver import Builder, Driver

from burr.core import ApplicationBuilder, State, action


@action(reads=[], writes=[])
def ingest_blog(state: State, blog_post_url: str, dr: Driver) -> State:
    """Download a blog post and parse it"""
    dr.execute(["embed_chunks"], inputs={"blog_post_url": blog_post_url})
    return state


@action(reads=[], writes=["llm_answer"])
def ask_question(state: State, user_query: str, dr: Driver) -> State:
    """Reply to the user's query using the blog's content."""
    results = dr.execute(["llm_answer"], inputs={"user_query": user_query})
    return state.update(llm_answer=results["llm_answer"])


if __name__ == "__main__":
    # renames to avoid name conflicts with the @action functions
    from actions import ask_question as ask_module
    from actions import ingest_blog as ingest_module
    from hamilton.plugins.h_opentelemetry import OpenTelemetryTracer
    from opentelemetry.instrumentation.lancedb import LanceInstrumentor
    from opentelemetry.instrumentation.openai import OpenAIInstrumentor

    OpenAIInstrumentor().instrument()
    LanceInstrumentor().instrument()

    dr = (
        Builder()
        .with_modules(ingest_module, ask_module)
        .with_adapters(OpenTelemetryTracer())
        .build()
    )

    app = (
        ApplicationBuilder()
        .with_actions(ingest_blog.bind(dr=dr), ask_question.bind(dr=dr))
        .with_transitions(("ingest_blog", "ask_question"))
        .with_entrypoint("ingest_blog")
        .with_tracker(project="modular-rag", use_otel_tracing=True)
        .build()
    )

    action_name, results, state = app.run(
        halt_after=["ask_question"],
        inputs={
            "blog_post_url": "https://blog.dagworks.io/p/from-blog-to-bot-build-a-rag-app",
            "user_query": "What do you need to monitor in a RAG app?",
        },
    )
    print(state["llm_answer"])
