ARG version=3.9
FROM python:${version}-slim


WORKDIR /app
ADD . /app

RUN pip install --trusted-host pypi.python.org -r requirements.txt

EXPOSE 8080
CMD ["/usr/local/bin/python", "/app/iiif-presentation-validator.py", "--hostname", "0.0.0.0"]
