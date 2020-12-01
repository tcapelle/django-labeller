# Building the main container
FROM python:3.8-slim

# Copy and install requirements.txt first for caching
COPY . /fastlabel
WORKDIR /fastlabel

RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install .

ENV PORT="5000"
ENV HOST=0.0.0.0

EXPOSE ${PORT}

CMD python -m fastlabel.flask_labeller

