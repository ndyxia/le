FROM archlinux:latest
WORKDIR /app
RUN pwd && ls -alh
RUN bash run.bash
RUN pwd && ls -alh
