FROM ubuntu:24.04

SHELL ["/bin/bash", "-o", "pipefail", "-c"]
ENV DEBIAN_FRONTEND=noninteractive

# Single shared build environment for ALL FrontierSmith tasks. Nothing
# task-specific lives here, so every task hashes to ONE Daytona snapshot.
# The in-container judge (g++ compile of the testlib special-checker + the
# contestant's solution.cpp) needs only g++ and python3; all per-problem
# assets (statement, chk.cc, testlib.h, testdata) are carried in /tests.
RUN set -eux; \
    for attempt in 1 2 3 4 5; do \
        apt-get clean; \
        rm -rf /var/lib/apt/lists/*; \
        if apt-get update -o Acquire::Retries=5 && \
            apt-get install -y --no-install-recommends -o Acquire::Retries=5 \
                g++ python3 ca-certificates; then \
            break; \
        fi; \
        if [ "$attempt" = "5" ]; then exit 1; fi; \
        sleep $((attempt * 20)); \
    done; \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
RUN mkdir -p /output && chmod 777 /output
