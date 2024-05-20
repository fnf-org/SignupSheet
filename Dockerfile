FROM node:16 as builder 

COPY package.json package-lock.json / 
RUN npm ci 

COPY src/ /src/ 
COPY webpack.config.js / 
RUN npm run build

FROM docker.io/ubuntu:24.04

RUN apt update -y && DEBIAN_FRONTEND=noninteractive apt install -y python3-pip tzdata libmariadb-dev python3-venv mariadb-client build-essential pkg-config

COPY . /app
RUN mkdir /db

WORKDIR /app
RUN python3 -m venv venv && . ./venv/bin/activate && pip install -r requirements.txt
COPY --from=builder /dist /app/dist 

CMD /bin/sh /app/entrypoint.sh
EXPOSE 8000
