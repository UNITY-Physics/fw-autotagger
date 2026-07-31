FROM nialljb/njb-ants-fsl-base:0.0.1 as base

ENV HOME=/root/
ENV FLYWHEEL="/flywheel/v0"
WORKDIR $FLYWHEEL
RUN mkdir -p $FLYWHEEL/input
COPY ./ $FLYWHEEL/

# Replace dead Buster sources with archived ones
RUN sed -i 's|http://deb.debian.org/debian|http://archive.debian.org/debian|g' /etc/apt/sources.list && \
    sed -i 's|http://security.debian.org/debian-security|http://archive.debian.org/debian-security|g' /etc/apt/sources.list && \
    apt-get update

RUN apt-get update && \
    apt-get install -y --no-install-recommends gnupg && \
    apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 8B48AD6246925553 && \
    apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 7638D0442B90D010 && \
    apt-get update
    
# Dev dependencies (conda, jq, poetry, flywheel installed in base)
RUN apt-get update && \
    apt-get clean && \
    pip install flywheel-gear-toolkit && \
    pip install flywheel-sdk && \
    pip install nibabel && \
    pip install pydicom && \
    pip install matplotlib && \
    pip install numpy && \
    pip install typing && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Configure entrypoint
RUN bash -c 'chmod +rx $FLYWHEEL/run.py'
ENTRYPOINT ["python","/flywheel/v0/run.py"] 
# Flywheel reads the config command over this entrypoint