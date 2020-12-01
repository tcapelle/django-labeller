# Building the main container
FROM python:3.8-slim

# Copy and install requirements.txt first for caching
COPY . /django-labeller
WORKDIR /django-labeller

RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install .

ENV PORT="5000"
ENV HOST=0.0.0.0

EXPOSE ${PORT}

RUN python -m image_labelling_tool.flask_labeller --enable_dextr

ENTRYPOINT /bin/bash

