FROM debian:latest

COPY prepare_docker_image.sh .
RUN ./prepare_docker_image.sh
RUN pip install qcache==0.2.0

EXPOSE 9401 9402 9403 9404 9405 9406 9407 9408
ENV QCACHE_PORT 9401

# The start container like this:
# - docker run -p 9401:9401 qcache
# - docker run --env QCACHE_PORT=9402 -p 9402:9402 qcache
CMD [ "sh", "-c", "qcache -p $QCACHE_PORT"]
