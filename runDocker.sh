#!/bin/bash

docker build -t validator . && docker run -it --rm -p 8080:8080 --name validator validator:latest
