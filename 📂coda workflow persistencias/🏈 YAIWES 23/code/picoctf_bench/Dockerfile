FROM ubuntu:latest

# Install system dependencies
RUN apt-get update && apt-get install -y \
	python3 \
	pip \
	upx-ucl \
	exiftool \
	tshark \
	ruby \
	git \
	binutils \
	gawk \
	gzip \
	binwalk \
	unzip \
	curl \
	steghide \
	apktool \
	sleuthkit \
	tesseract-ocr \
	ncat \
	gdb \
	&& rm -rf /var/lib/apt/lists/*

# Install ruby dependencies
RUN gem install \
	zsteg

# Install python dependencies
RUN pip install --break-system-packages --no-cache-dir --root-user-action ignore \
	gmpy2 \
	pytesseract \
	itsdangerous \
	flask \
	pwntools \
	pymupdf \
	frontend \
	tools \
	capstone==5.0.3

# Drop privileges
WORKDIR /app
RUN chown ubuntu:ubuntu /app
USER ubuntu
CMD ["python3", "challenge_solver.py"]
