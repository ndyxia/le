FROM archlinux:latest
WORKDIR /app
COPY . /app
RUN bash run.bash
