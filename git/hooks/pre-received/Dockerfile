FROM centos:centos7 AS base-dependencies
# Install dev and runtime dependencies
RUN yum group install -y "Development Tools" \
    && yum install -y https://repo.ius.io/ius-release-el7.rpm \
    && yum install -y centos-release-scl \
    && yum install -y python36u python36u-libs python36u-devel python36u-pip && \
    yum clean -y all && \
    rm -rf /var/lib/apt/lists/*
