# Use a lightweight Ubuntu base
FROM ubuntu:22.04

# Avoid timezone prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies for Python, Node.js (JS/TS), and Java
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    nodejs \
    npm \
    default-jdk \
    && rm -rf /var/lib/apt/lists/*

# Set a working directory for the code execution
WORKDIR /sandbox_env

# Command will be overridden by the functionality agent, but keep it running by default
CMD ["tail", "-f", "/dev/null"]