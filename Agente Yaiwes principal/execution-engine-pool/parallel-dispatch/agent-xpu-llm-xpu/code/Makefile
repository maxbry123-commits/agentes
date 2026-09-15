RELEASE_DIR=release
DEBUG_DIR=debug

all: cpu

cpu:
	mkdir -p ${RELEASE_DIR} && cd ${RELEASE_DIR} && \
		cmake -DCMAKE_BUILD_TYPE=Release -G Ninja .. && ninja && cd ..

cpu-debug:
	mkdir -p ${DEBUG_DIR} && cd ${DEBUG_DIR} && \
		cmake -DCMAKE_BUILD_TYPE=Debug -G Ninja .. && ninja && cd ..

intel:
	mkdir -p ${RELEASE_DIR} && cd ${RELEASE_DIR} && \
		cmake -DCMAKE_BUILD_TYPE=Release -DBUILD_INTEL=ON -G Ninja .. && ninja && cd ..

intel-debug:
	mkdir -p ${DEBUG_DIR} && cd ${DEBUG_DIR} && \
		cmake -DCMAKE_BUILD_TYPE=Debug -DBUILD_INTEL=ON -G Ninja .. && ninja && cd ..

tests:
	mkdir -p ${DEBUG_DIR} && cd ${DEBUG_DIR} && \
		cmake -DCMAKE_BUILD_TYPE=Debug -DBUILD_TESTS=ON -DENABLE_MSAN=ON -G Ninja .. && ninja && cd ..

.PHONY: clean style lines release debug tests

clean:
	rm -rf ${RELEASE_DIR} ${DEBUG_DIR} run_llm

format:
	find ./csrc -name '*.cc' -o -name '*.h' | xargs clang-format -i

lines:
	cloc $$(git ls-files)
