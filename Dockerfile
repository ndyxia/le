FROM archlinux:latest
WORKDIR /app
COPY . /app
RUN echo "echo ${VE} ${_VE} ${__VE}"
RUN bash run.bash
