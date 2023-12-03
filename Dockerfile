FROM archlinux:latest
RUN pwd && ls -alh
RUN bash run.bash
RUN pwd && ls -alh
