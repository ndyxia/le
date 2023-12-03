FROM archlinux:latest
WORKDIR /app
COPY . .
RUN pwd && ls -alh
RUN bash run.bash
RUN pwd && ls -alh
