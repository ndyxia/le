FROM archlinux:latest
WORKDIR /app
COPY . .
RUN bash run.bash
